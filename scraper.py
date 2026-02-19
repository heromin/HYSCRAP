import os, requests, time, json
from animeflv import AnimeFLV

def log(message):
    print(f"[{time.strftime('%H:%M:%S')}] {message}")

def run_scraper():
    anime_name = os.getenv('ANIME_NAME')
    tmdb_id = os.getenv('TMDB_ID')
    api_url = os.getenv('API_URL')

    with AnimeFLV() as api:
        log(f"🔍 Buscando: {anime_name}")
        try:
            # Intento por slug
            info = api.get_anime_info(anime_name.lower().replace(" ", "-"))
        except:
            res = api.search(anime_name)
            if not res: return log("❌ No encontrado")
            info = api.get_anime_info(res[0].id)

        log(f"🚀 Procesando episodios para TMDB: {tmdb_id}")
        
        # Disfraz de navegador para evitar bloqueos de ByetHost
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Content-Type": "application/json"
        }

        for ep in info.episodes:
            try:
                num_ep = ep.id if isinstance(ep.id, int) else int(str(ep.id).split('-')[-1])
                video_links = api.get_links(info.id, ep.id)
                
                if not video_links: continue

                links_data = [{"server": l.server.capitalize(), "url": l.url} for l in video_links if l.url]
                payload = {
                    "tmdb_id": int(tmdb_id),
                    "numero": num_ep,
                    "links": json.dumps(links_data)
                }
                
                # Enviamos el JSON
                r = requests.post(api_url, data=json.dumps(payload), headers=headers, timeout=30)
                
                if r.status_code == 200:
                    # Si el PHP responde con éxito o con error de "ID no encontrado"
                    log(f"➡️ Ep {num_ep}: {r.text}")
                else:
                    log(f"⚠️ Ep {num_ep}: Error HTTP {r.status_code}")
                
                time.sleep(10) # Pausa de 10 segundos (Seguridad máxima)

            except Exception as e:
                log(f"❌ Error en ep: {str(e)}")

if __name__ == "__main__":
    run_scraper()
