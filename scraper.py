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
        
        # Lógica de búsqueda mejorada
        info = None
        try:
            # Intentar búsqueda directa por slug (ej: jigokuraku)
            info = api.get_anime_info(anime_name.lower().replace(" ", "-"))
            log(f"✅ Encontrado por slug!")
        except:
            results = api.search(anime_name)
            if results:
                info = api.get_anime_info(results[0].id)
                log(f"✅ Encontrado en buscador: {info.title}")
            else:
                log("❌ No se encontro el anime. Intenta usando la slug de la URL.")
                return
        
        if not info: return

        log(f"🚀 Procesando {len(info.episodes)} episodios...")

        for ep in info.episodes:
            try:
                # Extraer numero de episodio de forma segura
                num_ep = ep.id if isinstance(ep.id, int) else int(str(ep.id).split('-')[-1])
                
                # Obtener links de descarga/video
                video_links = api.get_links(info.id, ep.id)
                if not video_links: continue

                # CORRECCIÓN AQUÍ: Usamos .server y .url (no .code)
                links_data = []
                for l in video_links:
                    links_data.append({
                        "server": getattr(l, 'server', 'Unknown').capitalize(),
                        "url": getattr(l, 'url', '') 
                    })
                
                payload = {
                    "tmdb_id": int(tmdb_id),
                    "numero": num_ep,
                    "links": json.dumps(links_data)
                }
                
                # Envío robusto a ByetHost
                target_url = f"{api_url}?token={api_token}"
                headers = {
                    "Authorization": api_token,
                    "Content-Type": "application/json"
                }

                response = requests.post(target_url, json=payload, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    log(f"✔️ Ep {num_ep}: Guardado")
                else:
                    log(f"⚠️ Ep {num_ep}: Error servidor ({response.status_code})")
                
                time.sleep(2) # Pausa anti-bloqueo

            except Exception as e:
                log(f"❌ Error en ep {ep.id}: {str(e)}")

if __name__ == "__main__":
    run_scraper()
