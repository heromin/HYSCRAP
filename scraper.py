import os
import requests
from animeflv import AnimeFLV
import sys
import time
import json

def log(message):
    print(f"[{time.strftime('%H:%M:%S')}] {message}")

def run_scraper():
    anime_name = os.getenv('ANIME_NAME')
    tmdb_id = os.getenv('TMDB_ID')
    api_url = os.getenv('API_URL')
    api_token = os.getenv('API_TOKEN')

    with AnimeFLV() as api:
        log(f"🔍 Buscando: {anime_name}")
        
        try:
            # Intento por slug (jigokuraku) o búsqueda general
            info = api.get_anime_info(anime_name.lower().replace(" ", "-"))
            log(f"✅ Encontrado!")
        except:
            results = api.search(anime_name)
            if results:
                info = api.get_anime_info(results[0].id)
                log(f"✅ Encontrado en buscador: {info.title}")
            else:
                log("❌ No se encontró el anime.")
                return

        # Procesar episodios (del más nuevo al más viejo para asegurar los últimos primero)
        log(f"🚀 Procesando {len(info.episodes)} episodios...")
        
        for ep in info.episodes:
            try:
                num_ep = ep.id if isinstance(ep.id, int) else int(str(ep.id).split('-')[-1])
                
                # Obtener links de video
                video_links = api.get_links(info.id, ep.id)
                if not video_links: continue

                # Extraer datos reales del objeto DownloadLinkInfo
                links_data = []
                for l in video_links:
                    srv = getattr(l, 'server', 'Unknown').capitalize()
                    u = getattr(l, 'url', '')
                    if u: links_data.append({"server": srv, "url": u})
                
                if not links_data: continue

                payload = {
                    "tmdb_id": int(tmdb_id),
                    "numero": num_ep,
                    "links": json.dumps(links_data)
                }
                
                # Envío con token en URL para máxima compatibilidad
                target_url = f"{api_url}?token={api_token}"
                headers = {"Content-Type": "application/json"}

                try:
                    response = requests.post(target_url, json=payload, headers=headers, timeout=15)
                    if response.status_code == 200:
                        log(f"✔️ Ep {num_ep}: Guardado en BD")
                    else:
                        log(f"⚠️ Ep {num_ep}: Error {response.status_code} - {response.text[:50]}")
                except requests.exceptions.ConnectionError:
                    log(f"❌ ByetHost cerró la conexión en Ep {num_ep}. Reintentando en el próximo...")
                
                time.sleep(5) # Pausa crucial para evitar el "Remote end closed connection"

            except Exception as e:
                log(f"❌ Error en ep {getattr(ep, 'id', '??')}: {str(e)}")

if __name__ == "__main__":
    run_scraper()
