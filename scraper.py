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
            # Busqueda robusta
            search_results = api.search(anime_name)
            if not search_results:
                return log(f"❌ No se encontro el anime '{anime_name}'")
            
            info = api.get_anime_info(search_results[0].id)
        except Exception as e:
            return log(f"❌ Error al conectar con AnimeFLV: {str(e)}")

        log(f"🚀 {len(info.episodes)} episodios encontrados para TMDB: {tmdb_id}")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/121.0.0.0",
            "Content-Type": "application/json"
        }

        # Procesamos episodios
        for ep in info.episodes:
            try:
                # Extraer numero de episodio de forma segura
                num_ep = ep.id if isinstance(ep.id, int) else int(str(ep.id).split('-')[-1])
                
                # Obtener links de video
                video_links = api.get_links(info.id, ep.id)
                if not video_links: continue

                links_data = [{"server": l.server.capitalize(), "url": l.url} for l in video_links if l.url]
                
                payload = {
                    "tmdb_id": int(tmdb_id),
                    "numero": num_ep,
                    "links": json.dumps(links_data)
                }
                
                # Enviar al PHP
                r = requests.post(api_url, json=payload, headers=headers, timeout=30)
                
                if r.status_code == 200:
                    log(f"✔️ Ep {num_ep}: {r.text}")
                else:
                    log(f"⚠️ Ep {num_ep}: Error HTTP {r.status_code}")
                
                # PAUSA CRITICA: ByetHost es muy estricto
                time.sleep(15)

            except Exception as e:
                log(f"❌ Error en episodio: {str(e)}")

if __name__ == "__main__":
    run_scraper()
