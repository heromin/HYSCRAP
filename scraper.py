import os, requests, time, json
from animeflv import AnimeFLV

def run_scraper():
    anime_name = os.getenv('ANIME_NAME')
    tmdb_id = os.getenv('TMDB_ID')
    api_url = os.getenv('API_URL')

    with AnimeFLV() as api:
        res = api.search(anime_name)
        if not res: return print("❌ No encontrado")
        info = api.get_anime_info(res[0].id)

        # Usamos una Sesión para mantener cookies si fuera necesario
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/121.0.0.0"
        })

        for ep in info.episodes:
            try:
                num_ep = ep.id if isinstance(ep.id, int) else int(str(ep.id).split('-')[-1])
                video_links = api.get_links(info.id, ep.id)
                if not video_links: continue

                links_data = [{"server": l.server.capitalize(), "url": l.url} for l in video_links if l.url]
                
                # Parametros para la URL
                params = {
                    "tmdb_id": tmdb_id,
                    "numero": num_ep,
                    "links": json.dumps(links_data)
                }
                
                # ENVIAR POR GET
                r = session.get(api_url, params=params, timeout=30)
                
                print(f"✔️ Ep {num_ep}: {r.text[:100]}")
                time.sleep(15) # Pausa vital

            except Exception as e:
                print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    run_scraper()
