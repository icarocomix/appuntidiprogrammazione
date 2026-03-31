import os
import pandas as pd
import re
import subprocess
from pathlib import Path

# --- CONFIGURAZIONE ---
INPUT_DIR = "excel_input"
OUTPUT_DIR = "_articoli"
MAX_CHARS_WIDTH = 100

TECH_CONFIG = {
    "java": {"parser": "java", "plugins": ["prettier-plugin-java"]},
    "js": {"parser": "espree", "plugins": []},
    "db": {"parser": "sql", "plugins": []},
    "thymeleaf": {"parser": "html", "plugins": []},
    "default": {"parser": "babel", "plugins": []}
}

def format_code_tech(code_text, tech):
    """Formatta il codice usando Prettier o SQL-Formatter"""
    code = str(code_text).replace("\\n", "\n").strip()
    code = re.sub(r"```[a-zA-Z]*\n?", "", code).replace("```", "")
    
    cfg = TECH_CONFIG.get(tech.lower(), TECH_CONFIG["default"])
    
    if tech.lower() == "db":
        try:
            cmd = ['npx', 'sql-formatter', '-l', 'postgresql', '--config', '{"keywordCase": "upper"}']
            p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
            stdout, _ = p.communicate(input=code)
            if p.returncode == 0: return stdout.strip()
        except: pass

    try:
        cmd = ['npx', 'prettier', '--parser', cfg["parser"], '--tab-width', '4', '--print-width', str(MAX_CHARS_WIDTH)]
        if cfg.get("plugins"):
            for pl in cfg["plugins"]: cmd.extend(['--plugin', pl])
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        stdout, _ = p.communicate(input=code)
        if p.returncode == 0: return stdout.strip()
    except: pass
    
    return code

def sanitize_filename(text):
    s = str(text).lower()
    s = re.sub(r'[^a-z0-9\s-]', '', s)
    return re.sub(r'[\s-]+', '-', s).strip('-')

def clean_excel_text(text):
    if pd.isna(text): return ""
    return str(text).replace("\\n", "\n").replace("\r", "")

def process_excels():
    input_path = Path(INPUT_DIR)
    out_path = Path(OUTPUT_DIR)
    
    # Debug: Verifica cartelle
    print(f"🔍 Cerco file .xlsx in: {input_path.absolute()}")
    
    if not input_path.exists():
        print(f"❌ Errore: La cartella {INPUT_DIR} non esiste!")
        return

    out_path.mkdir(parents=True, exist_ok=True)
    
    excel_files = list(input_path.glob("*.xlsx"))
    
    if not excel_files:
        print(f"⚠️ Nessun file .xlsx trovato in {INPUT_DIR}")
        return

    print(f"📂 Trovati {len(excel_files)} file da elaborare.")

    for file in excel_files:
        tech_name = file.stem.lower()
        print(f"\n🚀 Elaborazione tecnologia: {tech_name.upper()}")
        
        try:
            xls = pd.ExcelFile(file)
            for sheet_name in xls.sheet_names:
                print(f"  📄 Foglio: {sheet_name}")
                df = pd.read_excel(file, sheet_name=sheet_name)
                df.columns = [str(c).strip().upper() for c in df.columns]
                
                for idx, row in df.iterrows():
                    titolo = str(row.get('TITOLO', f'Topic-{idx}'))
                    filename = f"{pd.Timestamp.now().strftime('%Y-%m-%d')}-{sanitize_filename(titolo)}.md"
                    
                    # Estrazione dati
                    analisi = clean_excel_text(row.get('ANALISI TECNICA', ''))
                    esigenza = clean_excel_text(row.get('ESIGENZA REALE', ''))
                    sintesi = clean_excel_text(row.get('SINTESI DEL PROBLEMA', '')).replace("\n", " ").strip()[:250]
                    
                    # Codice
                    code_cols = [col for col in df.columns if 'ESEMPIO' in col and pd.notna(row[col])]
                    raw_code = "\n".join([clean_excel_text(row[col]) for col in code_cols])
                    
                    print(f"    🛠 Formatto: {titolo[:30]}...")
                    formatted_code = format_code_tech(raw_code, tech_name)
                    
                    tags = [tech_name, sheet_name.lower().replace("_", " ")]

                    # Scrittura
                    with open(out_path / filename, "w", encoding="utf-8") as f:
                        f.write("---\n")
                        f.write(f"layout: post\n")
                        f.write(f"title: \"{titolo}\"\n")
                        f.write(f"date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S %z')}\n")
                        f.write(f"sintesi: \"{sintesi}\"\n")
                        f.write(f"tech: {tech_name}\n")
                        f.write(f"tags: {tags}\n")
                        f.write(f"pdf_file: \"{sanitize_filename(titolo)}.pdf\"\n")
                        f.write("---\n\n")
                        
                        if esigenza: f.write(f"## Esigenza Reale\n{esigenza}\n\n")
                        if analisi: f.write(f"## Analisi Tecnica\n{analisi}\n\n")
                        if formatted_code:
                            f.write(f"## Esempio Implementativo\n\n")
                            f.write(f"```{tech_name}\n")
                            f.write(f"{formatted_code}\n")
                            f.write(f"```\n")
                    
                    print(f"    ✅ Generato: {filename}")
        except Exception as e:
            print(f"  ❌ Errore durante l'elaborazione di {file.name}: {e}")

if __name__ == "__main__":
    process_excels()