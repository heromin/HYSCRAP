import os
import requests
from animeflv import AnimeFLV
import sys
import time
from datetime import datetime

def log(message, level="INFO"):
    """Logging con timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")

def send_episode_with_retry(api_url, payload, headers, max_retries=3):
    """Envía episodio con reintentos exponenciales"""
    for attempt in range(max_retries):
        try:
            response = requests.post(api_url, json=payload, headers=headers, timeout=15)
            
            if response.status_code == 200:
                return True, response.text
            elif response.status_code == 403:
                log(f"❌ Autenticación fallida (403). Token inválido.", "ERROR")
                return False, response.text
            elif response.status_code == 404:
                log(f"❌ API endpoint no encontrado (404).", "ERROR")
                return False, response.text
            else:
                log(f"⚠️ Intento {attempt + 1}/{max_retries} - Código HTTP {response.status_code}", "WARN")
                
        except requests.exceptions.Timeout:
            log(f"⏱️ Timeout en intento {attempt + 1}/{max_retries}", "WARN")
        except requests.exceptions.ConnectionError:
            log(f"🔗 Error de conexión en intento {attempt + 1}/{max_retries}", "WARN")
        except requests.exceptions.RequestException as e:
            log(f"⚠️ Error en intento {attempt + 1}/{max_retries}: {e}", "WARN")
        
        if attempt < max_retries - 1:
            wait_time = 2 ** attempt  # 1s, 2s, 4s
            log(f"⏳ Esperando {wait_time}s antes de reintentar...", "INFO")
            time.sleep(wait_time)
    
    return False, "Agotados los reintentos"

def run_scraper():
    """Ejecuta el scraper de animes"""
    
    # 1. Validar variables de entorno
    anime_name = os.getenv('ANIME_NAME')
    tmdb_id = os.getenv('TMDB_ID')
    api_url = os.getenv('API_URL')
    security_token = os.getenv('API_TOKEN')

    if not all([anime_name, tmdb_id, api_url, security_token]):
        missing = []
        if not anime_name: missing.append("ANIME_NAME")
        if not tmdb_id: missing.append("TMDB_ID")
        if not api_url: missing.append("API_URL")
        if not security_token: missing.append("API_TOKEN")
        
        log(f"❌ Faltan variables de entorno: {', '.join(missing)}", "ERROR")
        sys.exit(1)

    log(f"🚀 Iniciando scraper", "INFO")
    log(f"   Anime: {anime_name}", "INFO")
    log(f"   TMDB ID: {tmdb_id}", "INFO")
    log(f"   API URL: {api_url}", "INFO")

    # 2. Conectar a AnimeFLV
    try:
        with AnimeFLV() as api:
            # 3. Búsqueda
            log(f"🔍 Buscando '{anime_name}'...", "INFO")
            search_results = api.search(anime_name)
            
            if not search_results:
                log(f"❌ No se encontró '{anime_name}' en AnimeFLV", "ERROR")
                sys.exit(1)

            anime_match = search_results[0]
            log(f"✅ Encontrado: {anime_match.title} (ID: {anime_match.id})", "INFO")

            # 4. Obtener episodios
            log(f"📺 Obteniendo lista de episodios...", "INFO")
            info = api.get_anime_info(anime_match.id)
            total_episodes = len(info.episodes)
            log(f"📦 Total de episodios: {total_episodes}", "INFO")

            if total_episodes == 0:
                log(f"⚠️ No hay episodios disponibles", "WARN")
                return

            # 5. Procesar cada episodio
            success_count = 0
            error_count = 0

            for idx, ep in enumerate(info.episodes, 1):
                try:
                    # Extraer número del episodio
                    try:
                        num_ep = int(ep.id.split('-')[-1])
                    except (ValueError, IndexError):
                        log(f"⚠️ No se pudo extraer número del episodio: {ep.id}", "WARN")
                        error_count += 1
                        continue

                    log(f"📺 Procesando episodio {num_ep} ({idx}/{total_episodes})...", "INFO")

                    # Obtener servidores/links
                    video_links = api.get_links(anime_match.id, ep.id)
                    
                    if not video_links:
                        log(f"   ⚠️ Sin servidores disponibles para episodio {num_ep}", "WARN")
                        error_count += 1
                        continue

                    log(f"   📡 {len(video_links)} servidor(s) encontrado(s)", "INFO")

                    # Formatear servidores
                    links_payload = []
                    for link in video_links:
                        try:
                            links_payload.append({
                                "server": str(link.server).strip().capitalize(),
                                "url": str(link.code).strip()
                            })
                        except Exception as e:
                            log(f"   ⚠️ Error formateando servidor: {e}", "WARN")
                            continue

                    if not links_payload:
                        log(f"   ❌ No hay URLs válidas para episodio {num_ep}", "ERROR")
                        error_count += 1
                        continue

                    # Preparar payload
                    payload = {
                        "tmdb_id": int(tmdb_id),
                        "numero": num_ep,
                        "links": links_payload
                    }

                    headers = {
                        "Authorization": security_token,
                        "Content-Type": "application/json"
                    }

                    # Enviar con reintentos
                    success, response = send_episode_with_retry(api_url, payload, headers, max_retries=3)
                    
                    if success:
                        log(f"   ✅ Episodio {num_ep} guardado correctamente", "INFO")
                        success_count += 1
                    else:
                        log(f"   ❌ Fallo al guardar episodio {num_ep}: {response}", "ERROR")
                        error_count += 1

                except Exception as e:
                    log(f"   💥 Error procesando episodio: {e}", "ERROR")
                    error_count += 1
                    continue

            # 6. Resumen final
            log(f"\n{'='*60}", "INFO")
            log(f"📊 RESUMEN", "INFO")
            log(f"   ✅ Exitosos: {success_count}", "INFO")
            log(f"   ❌ Errores: {error_count}", "INFO")
            log(f"   📺 Total procesados: {success_count + error_count}/{total_episodes}", "INFO")
            log(f"{'='*60}\n", "INFO")

            if error_count > 0:
                sys.exit(1)  # Salir con error si hubo fallos

    except Exception as e:
        log(f"💥 Error crítico: {e}", "ERROR")
        import traceback
        log(traceback.format_exc(), "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    run_scraper()
