import os, requests, time, json
from animeflv import AnimeFLV

def log(message):
    print(f"[{time.strftime('%H:%M:%S')}] {message}")

def run_scraper():
    # Cargar variables de entorno desde GitHub Actions
    anime_name = os.getenv('ANIME_NAME')
    tmdb_id = os.getenv('TMDB_ID')
    api_url = os.getenv('API_URL')

    with AnimeFLV() as api:
        log(f"🔍 Buscando en AnimeFLV: {anime_name}")
        try:
            # Intento por slug directo (ej: jigokuraku)
            info = api.get_anime_info(anime_name.lower().replace(" ", "-"))
        except:
            res = api.search(anime_name)
            if not res: return log("❌ Anime no encontrado en la web")
            info = api.get_anime_info(res[0].id)

        log(f"🚀 Procesando {len(info.episodes)} episodios para TMDB ID: {tmdb_id}")

        # Cabeceras para simular un navegador real y evitar bloqueos de ByetHost
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        # Procesar de forma reversa (opcional) o normal
        for ep in info.episodes:
            try:
                # Extraer número de episodio
                num_ep = ep.id if isinstance(ep.id, int) else int(str(ep.id).split('-')[-1])
                
                # Obtener enlaces de video
                video_links = api.get_links(info.id, ep.id)
                if not video_links: continue

                # Formatear servidores
                links_data = [{"server": l.server.capitalize(), "url": l.url} for l in video_links if l.url]
                
                payload = {
                    "tmdb_id": int(tmdb_id),
                    "numero": num_ep,
                    "links": json.dumps(links_data)
                }
                
                # Enviar al servidor con reintentos automáticos
                for intento in range(3):
                    try:
                        r = requests.post(api_url, json=payload, headers=headers, timeout=30)
                        if r.status_code == 200:
                            log(f"➡️ Ep {num_ep}: {r.text}")
                            break
                        else:
                            log(f"⚠️ Ep {num_ep}: Error HTTP {r.status_code}")
                    except Exception as e:
                        log(f"🔄 Ep {num_ep}: Reintentando por fallo de conexión...")
                        time.sleep(5)
                
                # Pausa de 10 segundos para no saturar el hosting gratuito
                time.sleep(10)

            except Exception as e:
                log(f"❌ Error crítico en episodio: {str(e)}")

if __name__ == "__main__":
    run_scraper()
