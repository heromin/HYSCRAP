import os, json
from animeflv import AnimeFLV

def run_scraper():
    anime_name = "Hell's Paradise" 
    tmdb_id = 117465
    anime_id_db = 6 # El ID que confirmamos en tu tabla

    with AnimeFLV() as api:
        print(f"🔍 Buscando: {anime_name}")
        search = api.search(anime_name)
        if not search: return print("❌ No encontrado")
        
        info = api.get_anime_info(search[0].id)
        print(f"🚀 Generando SQL para {len(info.episodes)} episodios...")

        sql_values = []
        for ep in info.episodes:
            try:
                # Extraer número de episodio
                num_ep = ep.id if isinstance(ep.id, int) else int(str(ep.id).split('-')[-1])
                links = api.get_links(info.id, ep.id)
                
                if links:
                    # Formateamos los servidores para que se vean bien en tu web
                    links_list = [{"server": l.server.capitalize(), "url": l.url} for l in links]
                    links_json = json.dumps(links_list).replace("'", "''")
                    enlace_principal = links[0].url
                    
                    sql_values.append(f"({anime_id_db}, {num_ep}, '{enlace_principal}', '{links_json}', 1)")
            except:
                continue

        # Construcción del comando SQL final
        if sql_values:
            print("\n--- COPIA DESDE LA SIGUIENTE LÍNEA ---")
            full_sql = "INSERT INTO episodios (anime_id, numero_episodio, enlace, servidores, temporada) VALUES \n"
            full_sql += ",\n".join(sql_values)
            full_sql += "\nON DUPLICATE KEY UPDATE enlace=VALUES(enlace), servidores=VALUES(servidores);"
            print(full_sql)
            print("--- HASTA AQUÍ ---\n")

if __name__ == "__main__":
    run_scraper()
