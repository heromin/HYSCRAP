import os, json, sys, requests
from animeflv import AnimeFLV

def run_scraper():
    # Parámetros dinámicos (se pueden pasar por terminal o variables de entorno)
    # Ejemplo de uso: python scraper.py "One Piece" 12 11023
    try:
        anime_query = sys.argv[1] if len(sys.argv) > 1 else os.getenv('ANIME_NAME')
        anime_id_db = sys.argv[2] if len(sys.argv) > 2 else os.getenv('ANIME_ID_DB')
        tmdb_id = sys.argv[3] if len(sys.argv) > 3 else os.getenv('TMDB_ID')
    except Exception:
        print("❌ Error: Faltan parámetros. Uso: python scraper.py 'Nombre' ID_DB TMDB_ID")
        return

    # Servidores que sí permiten Embed (Opción B)
    SERVIDORES_EMBED = ['Streamwish', 'Voex', 'Yourupload', 'Vidoza', 'Okru', 'Doodstream']

    with AnimeFLV() as api:
        print(f"🔍 Buscando en AnimeFLV: {anime_query} (Vincular a ID DB: {anime_id_db})")
        search = api.search(anime_query)
        
        if not search:
            print(f"❌ No se encontró nada para '{anime_query}'")
            return
        
        # Tomamos el primer resultado
        info = api.get_anime_info(search[0].id)
        print(f"🚀 {len(info.episodes)} episodios encontrados.")

        sql_values = []
        for ep in info.episodes:
            try:
                # Extraer número de episodio de forma segura
                num_ep = ep.id if isinstance(ep.id, int) else int(str(ep.id).split('-')[-1])
                links = api.get_links(info.id, ep.id)
                
                if links:
                    # Filtramos solo los servidores que permiten Embed
                    embed_links = [l for l in links if l.server.capitalize() in SERVIDORES_EMBED]
                    
                    # Si no hay embeds, usamos los disponibles pero priorizamos
                    res_links = embed_links if embed_links else links
                    
                    links_data = [{"server": l.server.capitalize(), "url": l.url} for l in res_links]
                    links_json = json.dumps(links_data).replace("'", "''")
                    enlace_p = res_links[0].url
                    
                    # Estructura para el SQL
                    sql_values.append(f"({anime_id_db}, {num_ep}, '{enlace_p}', '{links_json}', 1)")
                    print(f"  ✅ Ep {num_ep} listo.")
            except:
                continue

        # Resultado final
        if sql_values:
            print("\n" + "="*60)
            print(f"👇 SQL PARA: {anime_query} (ID: {anime_id_db}) 👇")
            print("="*60)
            
            sql_final = "INSERT INTO episodios (anime_id, numero_episodio, enlace, servidores, temporada) VALUES \n"
            sql_final += ",\n".join(sql_values)
            sql_final += "\nON DUPLICATE KEY UPDATE enlace=VALUES(enlace), servidores=VALUES(servidores);"
            
            print(sql_final)
            print("="*60)

if __name__ == "__main__":
    run_scraper()
