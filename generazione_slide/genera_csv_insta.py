# python genera_csv_insta.py 2026-04-01 --path ./output_img
# link di condivisione privata come Visualizzatore:
# https://drive.google.com/drive/folders/14JQQyOTjsfml0TBfvVdaqadmNKFvDOUZ?usp=sharing
import os
import csv
import argparse
from datetime import datetime, timedelta
from pathlib import Path

def get_next_post_date(current_date):
    """Calcola il prossimo Lunedì (0) o Mercoledì (2)."""
    while True:
        current_date += timedelta(days=1)
        if current_date.weekday() in [0, 2]:
            return current_date

def generate_insta_csv(root_path, start_date_str):
    root = Path(root_path).resolve() # Converte in path assoluto reale
    print(f"--- Inizio scansione in: {root} ---")
    
    # Data di partenza (sottraggo 1 giorno per includere la data stessa se valida)
    current_date = datetime.strptime(start_date_str, '%Y-%m-%d') - timedelta(days=1)
    
    tag_map = {
        "java": "#java #springboot #developers #programmers #backend",
        "js": "#javascript #vanillajs #nodejs #typescript #webdev",
        "thymeleaf": "#thymeleaf #springboot #java #frontend #webdev",
        "db": "#database #db #postgresql #sql #backend"
    }
    universal_tags = "#developers #coding #programming"
    
    data_rows = []
    image_extensions = {'.png', '.jpg', '.jpeg', '.webp'} # Aggiunto webp per sicurezza

    # Scansione ricorsiva di tutte le cartelle
    for dirpath, dirnames, filenames in os.walk(root):
        # Escludi cartelle nascoste (che iniziano con .)
        if any(part.startswith('.') for part in Path(dirpath).parts):
            continue
            
        # Controlla se ci sono immagini nella cartella attuale
        images_in_folder = [f for f in filenames if Path(f).suffix.lower() in image_extensions]
        
        if images_in_folder:
            print(f"✅ Trovate {len(images_in_folder)} immagini in: {dirpath}")
            post_path = Path(dirpath)
            
            # 1. Calcolo Data
            current_date = get_next_post_date(current_date)
            date_str = current_date.strftime('%Y-%m-%d')
            
            # 2. Path assoluto (per Pipedream)
            folder_path = str(post_path.absolute())
            
            # 3. Estrazione Categoria (la prima cartella dopo la root)
            # Esempio: root=/output_img, dir=/output_img/java/post1 -> categoria=java
            relative_to_root = post_path.relative_to(root)
            category_name = relative_to_root.parts[0] if relative_to_root.parts else "General"
            
            # 4. Generazione Caption (Nome cartella pulito)
            clean_name = post_path.name.replace('_', ' ')
            caption = f"{category_name.capitalize()}: {clean_name}"
            
            # 5. Generazione Tags
            specific_tags = tag_map.get(category_name.lower(), "")
            final_tags = f"{specific_tags} {universal_tags}".strip()
            
            data_rows.append([date_str, folder_path, caption, final_tags])

    # Se non ha trovato nulla, avvisa l'utente
    if not data_rows:
        print("❌ ERRORE: Nessuna cartella contenente immagini (.png, .jpg, .webp) trovata!")
        print(f"Controlla che il percorso '{root}' sia corretto e contenga file immagine.")
        return

    # Ordinamento per data
    data_rows.sort(key=lambda x: x[0])

    # Scrittura del file CSV nella cartella dove lanci lo script
    output_file = "calendario_instagram.csv"
    try:
        with open(output_file, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['data', 'folder', 'caption', 'tags'])
            writer.writerows(data_rows)
        print(f"\n✨ Successo! Generato '{output_file}' con {len(data_rows)} post.")
    except Exception as e:
        print(f"❌ Errore durante la scrittura del file: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Genera CSV per automazione Instagram")
    parser.add_argument("date", help="Data di inizio in formato YYYY-MM-DD")
    parser.add_argument("--path", default="./output_img", help="Path della cartella root")
    
    args = parser.parse_args()
    generate_insta_csv(args.path, args.date)