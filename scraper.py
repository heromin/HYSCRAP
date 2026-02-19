import os, requests, time, json
from animeflv import AnimeFLV

def log(message):
    print(f"[{time.strftime('%H:%M:%S')}] {message}")

def run_scraper():
    # Cargar variables de entorno
    anime_name = os.getenv('ANIME_NAME')
    tmdb_id = os.getenv('TMDB_ID')
    api_url = os.getenv('API_URL')

    with AnimeFLV() as api:
        log(f"🔍 Buscando en AnimeFLV: {anime_name}")
        try:
            # Buscamos por el término exacto para evitar fallos
            res = api.search(anime_name)
            if not res: 
                log(f"❌ No se encontro nada con '{anime_name}', probando slug...")
                info = api.get_anime_info("jigokuraku") # Backup directo
            else:
                info = api.get_anime_info(res[0].id)
        except Exception as e:
            return log(f"❌ Error en busqueda: {str(e)}")

        log(f"🚀 Procesando episodios para TMDB ID: {tmdb_id}")

        # Cabeceras para saltar el firewall de ByetHost
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Referer": "https://google.com"
        }

        for ep in info.episodes:
            try:
                # CORRECCIÓN: Manejar el ID si es entero o string
                if isinstance(ep.id, int):
                    num_ep = ep.id
                else:
                    num_ep = int(str(ep.id).split('-')[-1])
                
                video_links = api.get_links(info.id, ep.id)
                if not video_links: continue

                links_data = [{"server": l.server.capitalize(), "url": l.url} for l in video_links if l.url]
                
                payload = {
                    "tmdb_id": int(tmdb_id),
                    "numero": num_ep,
                    "links": json.dumps(links_data)
                }
                
                # Intentar envío
                try:
                    r = requests.post(api_url, json=payload, headers=headers, timeout=30)
                    if r.status_code == 200:
                        log(f"✔️ Ep {num_ep}: {r.text}")
                    else:
                        log(f"⚠️ Ep {num_ep}: Status {r.status_code}")
                except Exception as e:
                    log(f"🔄 Ep {num_ep}: Reintentando por red...")
                
                # Pausa obligatoria para hostings gratuitos (12 seg)
                time.sleep(12)

            except Exception as e:
                log(f"❌ Error en ep: {str(e)}")

if __name__ == "__main__":
    run_scraper()
