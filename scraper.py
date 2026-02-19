# ... (mantén tus funciones log y send_episode_with_retry igual)

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

                    # Formatear servidores
                    links_payload = []
                    for link in video_links:
                        try:
                            links_payload.append({
                                "server": str(link.server).strip().capitalize(),
                                "url": str(link.code).strip()
                            })
                        except Exception as e:
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
                        # --- CAMBIO AQUÍ: Pausa para no saturar VistaPanel ---
                        time.sleep(1.5) 
                        # -----------------------------------------------------
                    else:
                        log(f"   ❌ Fallo al guardar episodio {num_ep}: {response}", "ERROR")
                        error_count += 1

                except Exception as e:
                    log(f"   💥 Error procesando episodio: {e}", "ERROR")
                    error_count += 1
                    continue

            # 6. Resumen final
            log(f"\n{'='*60}")
            log(f"📊 RESUMEN FINAL")
            log(f"   ✅ Exitosos: {success_count}")
            log(f"   ❌ Errores: {error_count}")
            log(f"{'='*60}\n")

    except Exception as e:
        log(f"💥 Error crítico: {e}", "ERROR")
        sys.exit(1)
