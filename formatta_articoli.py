import os
import re
from pathlib import Path
# Importiamo direttamente le funzioni core dal tuo script
import code_formatter as cf

# Configurazione percorsi
INPUT_DIR = "_articoli/"
OUTPUT_DIR = "_nuovi_articoli/"

def process_articles():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    articles = Path(INPUT_DIR).glob("*.md")

    for article_path in articles:
        print(f"Elaborazione: {article_path.name}...")
        
        with open(article_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Regex per trovare il blocco di codice dopo "## Esempio Implementativo"
        # Catturiamo il linguaggio (group 2) e il codice (group 3)
        pattern = r"(## Esempio Implementativo[\s\S]*?)(```(\w+)?\n([\s\S]*?)```)"
        
        match = re.search(pattern, content)
        
        if match:
            full_code_block = match.group(2) # Include ```lang ... ```
            lang = match.group(3) or "text"
            raw_code = match.group(4)
            
            # Utilizziamo la logica di code_formatter.py senza passare per file esterni
            # 1. Normalizzazione
            lines = cf.normalize_to_lines(raw_code, lang)
            # 2. Indentazione
            indented_lines = cf.indent_lines(lines, lang)
            formatted_inner_code = "\n".join(indented_lines)
            
            # 3. Ricostruiamo il blocco con i tag originali
            formatted_full_block = f"```{lang}\n{formatted_inner_code}\n```"
            
            # Sostituzione nel contenuto finale
            new_content = content.replace(full_code_block, formatted_full_block)
            
            output_path = os.path.join(OUTPUT_DIR, article_path.name)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"✓ Completato: {output_path}")
        else:
            print(f"! Salto {article_path.name}: sezione '## Esempio Implementativo' non trovata.")

if __name__ == "__main__":
    process_articles()