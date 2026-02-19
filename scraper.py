import os, json
from animeflv import AnimeFLV

def run_scraper():
    anime_name = "Hell's Paradise" # O usa os.getenv
    tmdb_id = 117465
    anime_id_db = 6 # El ID que vimos en tu tabla animes

    with AnimeFLV() as api:
        res = api.search(anime_name)
        info = api.get_anime_info(res[0].id)

        print("\n--- COPIA DESDE AQUÍ ABAJO ---\n")
        
        sql_final = "INSERT INTO episodios (anime_id, numero_episodio, enlace, servidores, temporada) VALUES "
        values = []

        for ep in info.episodes:
            num_ep = ep.id if isinstance(ep.id, int) else int(str(ep.id).split('-')[-1])
            links = api.get_links(info.id, ep.id)
            if not links: continue
            
            links_data = json.dumps([{"server": l.server, "url": l.url} for l in links])
            enlace_p = links[0].url
            
            # Escapar comillas simples para SQL
            links_data_esc = links_data.replace("'", "''")
            
            values.append(f"({anime_id_db}, {num_ep}, '{enlace_p}', '{links_data_esc}', 1)")

        print(sql_final + ",\n".join(values) + " ON DUPLICATE KEY UPDATE enlace=VALUES(enlace), servidores=VALUES(servidores);")
        
        print("\n--- HASTA AQUÍ ---\n")

if __name__ == "__main__":
    run_scraper()
