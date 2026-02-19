import os, requests, time, json
from animeflv import AnimeFLV

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
            info = api.get_anime_info(anime_name.lower().replace(" ", "-"))
        except:
            res = api.search(anime_name)
            if not res: return log("❌ No encontrado")
            info = api.get_anime_info(res[0].id)

        log(f"🚀 Procesando {len(info.episodes)} episodios...")
        
        for ep in info.episodes:
            num_ep = ep.id if isinstance(ep.id, int) else int(str(ep.id).split('-')[-1])
            video_links = api.get_links(info.id, ep.id)
            if not video_links: continue

            links_data = [{"server": l.server.capitalize(), "url": l.url} for l in video_links if l.url]
            payload = {"tmdb_id": int(tmdb_id), "numero": num_ep, "links": json.dumps(links_data)}
            
            # Reintentos si ByetHost desconecta
            for intento in range(3):
                try:
                    r = requests.post(f"{api_url}?token={api_token}", json=payload, timeout=20)
                    if r.status_code == 200:
                        log(f"✔️ Ep {num_ep}: Guardado")
                        break
                    log(f"⚠️ Ep {num_ep}: Error {r.status_code}")
                except:
                    log(f"🔄 Ep {num_ep}: ByetHost desconectó. Reintentando...")
                    time.sleep(10) # Espera extra si falla
            
            time.sleep(7) # Pausa obligatoria entre episodios

if __name__ == "__main__":
    run_scraper()
