import os, json
from animeflv import AnimeFLV

def run_scraper():
    anime_name = "Hell's Paradise"
    id_en_tu_db = 6 

    # Servidores que suelen permitir IFRAME directo
    SERVIDORES_OK = ['Streamwish', 'Voex', 'Yourupload', 'Vidoza', 'Okru']

    with AnimeFLV() as api:
        search = api.search(anime_name)
        if not search: return print("❌ No encontrado")
        
        info = api.get_anime_info(search[0].id)
        sql_values = []

        for ep in info.episodes:
            num_ep = ep.id if isinstance(ep.id, int) else int(str(ep.id).split('-')[-1])
            links = api.get_links(info.id, ep.id)
            
            if links:
                # Filtrar solo los servidores que funcionan bien en web
                embed_links = [l for l in links if l.server.capitalize() in SERVIDORES_OK]
                
                # Si no hay preferidos, usamos todos
                final_list = embed_links if embed_links else links
                
                links_data = [{"server": l.server.capitalize(), "url": l.url} for l in final_list]
                links_json = json.dumps(links_data).replace("'", "''")
                enlace_p = final_list[0].url
                
                sql_values.append(f"({id_en_tu_db}, {num_ep}, '{enlace_p}', '{links_json}', 1)")

        if sql_values:
            print("\n--- COPIA ESTE SQL ---")
            sql = "INSERT INTO episodios (anime_id, numero_episodio, enlace, servidores, temporada) VALUES \n"
            sql += ",\n".join(sql_values) + "\nON DUPLICATE KEY UPDATE enlace=VALUES(enlace), servidores=VALUES(servidores);"
            print(sql)
