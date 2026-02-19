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
        results = api.search(anime_name)
        if not results:
            log("❌ No se encontro el anime")
            return
        
        anime = results[0]
        info = api.get_anime_info(anime.id)
        log(f"✅ Encontrado: {info.title}. Procesando {len(info.episodes)} episodios...")

        for ep in info.episodes:
            try:
                # Extraer numero de episodio
                num_ep = ep.id if isinstance(ep.id, int) else int(str(ep.id).split('-')[-1])
                
                video_links = api.get_links(anime.id, ep.id)
                if not video_links: continue

                # Preparar JSON de servidores
                links_data = [{"server": l.server, "url": l.code} for l in video_links]
                
                payload = {
                    "tmdb_id": int(tmdb_id),
                    "numero": num_ep,
                    "links": json.dumps(links_data) # Enviamos como string para evitar errores de parseo
                }
                
                # Enviamos el token tanto en Header como en URL para asegurar que ByetHost lo vea
                target_url = f"{api_url}?token={api_token}"
                headers = {"Authorization": api_token, "Content-Type": "application/json"}

                response = requests.post(target_url, json=payload, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    log(f"✔️ Ep {num_ep}: OK")
                else:
                    log(f"⚠️ Ep {num_ep}: Error {response.status_code} - {response.text[:100]}")
                
                time.sleep(2) # Pausa para no saturar el hosting gratuito

            except Exception as e:
                log(f"❌ Error en ep: {e}")

if __name__ == "__main__":
    run_scraper()
