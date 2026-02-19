import os
import requests
from animeflv import AnimeFLV
import sys
import time
from datetime import datetime

def log(message, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")

def send_episode_with_retry(api_url, payload, headers, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.post(api_url, json=payload, headers=headers, timeout=20)
            if response.status_code == 200:
                return True, response.text
            log(f"⚠️ Intento {attempt + 1} falló: {response.status_code}", "WARN")
        except Exception as e:
            log(f"⚠️ Error de red: {e}", "WARN")
        
        if attempt < max_retries - 1:
            time.sleep(2 ** attempt)
    return False, "Reintentos agotados"

def run_scraper():
    anime_name = os.getenv('ANIME_NAME')
    tmdb_id = os.getenv('TMDB_ID')
    api_url = os.getenv('API_URL')
    security_token = os.getenv('API_TOKEN')

    if not all([anime_name, tmdb_id, api_url, security_token]):
        log("❌ Faltan Secrets de configuración", "ERROR")
        sys.exit(1)

    with AnimeFLV() as api:
        try:
            log(f"🔍 Buscando: {anime_name}")
            results = api.search(anime_name)
            if not results: return
            
            anime = results[0]
            info = api.get_anime_info(anime.id)
            log(f"✅ Procesando {len(info.episodes)} episodios")

            for ep in info.episodes:
                try:
                    num_ep = int(ep.id.split('-')[-1])
                    video_links = api.get_links(anime.id, ep.id)
                    
                    if not video_links: continue

                    links_payload = [{"server": l.server.capitalize(), "url": l.code} for l in video_links]
                    
                    payload = {"tmdb_id": int(tmdb_id), "numero": num_ep, "links": links_payload}
                    headers = {"Authorization": security_token, "Content-Type": "application/json"}

                    success, resp = send_episode_with_retry(api_url, payload, headers)
                    if success:
                        log(f"✔️ Ep {num_ep} guardado")
                        time.sleep(1.5) # Pausa de seguridad para VistaPanel
                except Exception as e:
                    log(f"❌ Error en ep {ep.id}: {e}", "ERROR")

        except Exception as e:
            log(f"💥 Error crítico: {e}", "ERROR")

if __name__ == "__main__":
    run_scraper()
