import os, json, sys
from animeflv import AnimeFLV

def run_scraper():
    # Recibir parámetros de GitHub o consola: nombre, id_db, tmdb_id
    try:
        anime_query = sys.argv[1] if len(sys.argv) > 1 else os.getenv('ANIME_NAME')
        anime_id_db = sys.argv[2] if len(sys.argv) > 2 else os.getenv('ANIME_ID_DB')
    except:
        print("❌ Error: Faltan parámetros (ANIME_NAME, ANIME_ID_DB)")
        return

    # Servidores que suelen funcionar mejor (intentan ser Embed)
    SERVIDORES_PRO = ['Streamwish', 'Voex', 'Yourupload', 'Vidoza', 'Okru', 'Doodstream']

    with AnimeFLV() as api:
        print(f"🔍 Buscando: {anime_query} para ID Local: {anime_id_db}")
        search = api.search(anime_query)
        if not search: return print("❌ No encontrado")
        
        info = api.get_anime_info(search[0].id)
        sql_values = []

        for ep in info.episodes:
            try:
                num_ep = ep.id if isinstance(ep.id, int) else int(str(ep.id).split('-')[-1])
                links = api.get_links(info.id, ep.id)
                
                if links:
                    # Priorizar servidores de la lista PRO
                    links_filtrados = [l for l in links if l.server.capitalize() in SERVIDORES_PRO]
                    final_links = links_filtrados if links_filtrados else links
                    
                    links_data = [{"server": l.server.capitalize(), "url": l.url} for l in final_list]
                    links_json = json.dumps(links_data).replace("'", "''")
                    
                    sql_values.append(f"({anime_id_db}, {num_ep}, '{final_list[0].url}', '{links_json}', 1)")
            except: continue

        if sql_values:
            print("\n" + "="*50 + "\n👇 COPIA ESTE SQL 👇\n" + "="*50)
            sql = "INSERT INTO episodios (anime_id, numero_episodio, enlace, servidores, temporada) VALUES \n"
            sql += ",\n".join(sql_values) + "\nON DUPLICATE KEY UPDATE servidores=VALUES(servidores);"
            print(sql)
