import os, json
from animeflv import AnimeFLV

def run_scraper():
    anime_name = "Hell's Paradise"
    id_en_tu_db = 6 

    # Lista de servidores que SI permiten embed y suelen funcionar mejor
    SERVIDORES_EMBED = ['Streamwish', 'Voex', 'Vidoza', 'Yourupload', 'Okru', 'Doodstream']

    with AnimeFLV() as api:
        print(f"🔍 Buscando servidores embed para: {anime_name}")
        search = api.search(anime_name)
        if not search: return print("❌ No encontrado")
        
        info = api.get_anime_info(search[0].id)
        sql_values = []

        for ep in info.episodes:
            try:
                num_ep = ep.id if isinstance(ep.id, int) else int(str(ep.id).split('-')[-1])
                links = api.get_links(info.id, ep.id)
                
                if links:
                    # Filtramos: Solo servidores en nuestra lista de "Embed"
                    embed_links = [l for l in links if l.server.capitalize() in SERVIDORES_EMBED]
                    
                    # Si no hay de los preferidos, usamos los que haya pero priorizamos
                    final_links = embed_links if embed_links else links
                    
                    links_list = [{"server": l.server.capitalize(), "url": l.url} for l in final_links]
                    links_json = json.dumps(links_list).replace("'", "''")
                    
                    # El enlace principal será el primer embed encontrado
                    enlace_p = final_links[0].url
                    
                    sql_values.append(f"({id_en_tu_db}, {num_ep}, '{enlace_p}', '{links_json}', 1)")
                    print(f"✅ Ep {num_ep}: Servidores encontrados ({len(links_list)})")
            except Exception as e:
                print(f"⚠️ Error en Ep {num_ep}: {e}")

        if sql_values:
            print("\n" + "="*50)
            print("👇 COPIA ESTE SQL PARA SERVIDORES EMBED 👇")
            print("="*50 + "\n")
            sql_final = "INSERT INTO episodios (anime_id, numero_episodio, enlace, servidores, temporada) VALUES \n"
            sql_final += ",\n".join(sql_values)
            sql_final += "\nON DUPLICATE KEY UPDATE enlace=VALUES(enlace), servidores=VALUES(servidores);"
            print(sql_final)
