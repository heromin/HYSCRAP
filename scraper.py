import os
import json
import sys
from animeflv import AnimeFLV

def run_scraper():
    # Parámetros dinámicos desde GitHub Actions o Consola
    # Uso: python scraper.py "Nombre Anime" ID_DB
    try:
        anime_query = sys.argv[1] if len(sys.argv) > 1 else os.getenv('ANIME_NAME')
        anime_id_db = sys.argv[2] if len(sys.argv) > 2 else os.getenv('ANIME_ID_DB')
        
        if not anime_query or not anime_id_db:
            raise ValueError("Faltan variables")
    except Exception as e:
        print(f"❌ Error de parámetros: {e}")
        return

    # Servidores que suelen permitir IFRAME/Embed directo (Opción B)
    SERVIDORES_EMBED = ['Streamwish', 'Voex', 'Yourupload', 'Vidoza', 'Okru', 'Doodstream']

    with AnimeFLV() as api:
        print(f"🔍 Buscando en AnimeFLV: {anime_query}")
        search = api.search(anime_query)
        
        if not search:
            print(f"❌ No se encontró el anime '{anime_query}'")
            return
        
        # Obtenemos la info del primer resultado
        info = api.get_anime_info(search[0].id)
        print(f"🚀 {len(info.episodes)} episodios encontrados para vincular al ID {anime_id_db}")

        sql_values = []
        for ep in info.episodes:
            try:
                # Obtener número de episodio
                num_ep = ep.id if isinstance(ep.id, int) else int(str(ep.id).split('-')[-1])
                links = api.get_links(info.id, ep.id)
                
                if links:
                    # Filtramos servidores recomendados para Embed
                    embed_links = [l for l in links if l.server.capitalize() in SERVIDORES_EMBED]
                    
                    # Si hay embeds preferidos usamos esos, si no, todos los disponibles
                    final_list = embed_links if embed_links else links
                    
                    links_data = [{"server": l.server.capitalize(), "url": l.url} for l in final_list]
                    links_json = json.dumps(links_data).replace("'", "''")
                    
                    # El enlace principal será el primero de la lista optimizada
                    enlace_p = final_list[0].url
                    
                    sql_values.append(f"({anime_id_db}, {num_ep}, '{enlace_p}', '{links_json}', 1)")
            except:
                continue

        # Generación del bloque SQL para pegar en phpMyAdmin
        if sql_values:
            print("\n" + "="*60)
            print(f"👇 COPIA ESTE SQL PARA: {anime_query} 👇")
            print("="*60 + "\n")
            
            sql_final = "INSERT INTO episodios (anime_id, numero_episodio, enlace, servidores, temporada) VALUES \n"
            sql_final += ",\n".join(sql_values)
            sql_final += "\nON DUPLICATE KEY UPDATE enlace=VALUES(enlace), servidores=VALUES(servidores);"
            
            print(sql_final)
            print("\n" + "="*60)

if __name__ == "__main__":
    run_scraper()
