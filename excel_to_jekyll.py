import os
import pandas as pd
import re
import textwrap
from pathlib import Path

# --- CONFIGURAZIONE ---
INPUT_DIR = "excel_input"
OUTPUT_DIR = "_articoli"

def sanitize_filename(text):
    """Trasforma il titolo in un nome file valido per Jekyll"""
    s = text.lower().replace(" ", "-")
    return re.sub(r'[^a-z0-9\-]', '', s)

def format_markdown_body(row, tech, sheet):
    """Costruisce il corpo dell'articolo unendo analisi e codice"""
    # 1. Recupero Analisi
    analisi = str(row.get('ANALISI TECNICA', row.get('SINTESI DEL PROBLEMA', '')))
    analisi = analisi.replace("\\n", "\n")
    
    # 2. Recupero ed unione di tutte le colonne ESEMPIO
    code_cols = [col for col in row.index if 'ESEMPIO' in col and pd.notna(row[col])]
    full_code = "\n".join([str(row[col]) for col in code_cols]).replace("\\n", "\n")
    
    # 3. Composizione Markdown
    md_content = f"## Esigenza Reale\n{row.get('ESIGENZA REALE', 'N/A')}\n\n"
    md_content += f"## Analisi Tecnica\n{analisi}\n\n"
    
    if full_code.strip():
        # Determiniamo il linguaggio per il syntax highlighting
        lang = "sql" if tech.lower() == "db" else tech.lower()
        md_content += f"## Esempio Implementativo\n\n```{lang}\n{full_code}\n```"
    
    return md_content

def process_excels():
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    # Cerchiamo tutti i file .xlsx nella cartella input
    for file in Path(INPUT_DIR).glob("*.xlsx"):
        tech_name = file.stem.lower() # es: java
        print(f"📦 Elaborazione tecnologia: {tech_name}")
        
        xls = pd.ExcelFile(file)
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(file, sheet_name=sheet_name)
            # Pulizia nomi colonne
            df.columns = [str(c).strip().upper() for c in df.columns]
            
            for _, row in df.iterrows():
                titolo = str(row.get('TITOLO', 'Senza Titolo'))
                filename = f"{pd.Timestamp.now().strftime('%Y-%m-%d')}-{sanitize_filename(titolo)}.md"
                
                # Creazione Frontmatter (Meta-dati per Jekyll)
                # Qui aggiungiamo i tag base: tech e sheet
                tags = [tech_name, sheet_name.lower().replace("_", " ")]
                
                frontmatter = [
                    "---",
                    f"layout: post",
                    f"title: \"{titolo}\"",
                    f"date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')} +0200",
                    f"sintesi: \"{str(row.get('SINTESI DEL PROBLEMA', ''))[:150]}...\"",
                    f"tech: {tech_name}",
                    f"tags: {tags}",
                    "---",
                    ""
                ]
                
                body = format_markdown_body(row, tech_name, sheet_name)
                
                # Scrittura file finale
                with open(Path(OUTPUT_DIR) / filename, "w", encoding="utf-8") as f:
                    f.write("\n".join(frontmatter))
                    f.write(body)
                
                print(f"  ✅ Generato: {filename}")

if __name__ == "__main__":
    process_excels()