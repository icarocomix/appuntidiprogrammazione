import os
import re

def process_articles(directory):
    # Pattern per individuare le righe specifiche
    # Cerco 'Problema:' e 'Perché:' all'inizio della riga o dopo uno spazio
    problema_regex = re.compile(r'^(Problema:)', re.MULTILINE)
    perche_regex = re.compile(r'^(Perché:)', re.MULTILINE)

    if not os.path.exists(directory):
        print(f"Errore: La cartella '{directory}' non esiste.")
        return

    for filename in os.listdir(directory):
        if filename.endswith(".md"):
            filepath = os.path.join(directory, filename)
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Verifico se il contenuto ha la sezione Analisi Tecnica
            if "## Analisi Tecnica" in content:
                # Trasformo 'Problema:' in '**Problema:**'
                # e 'Perché:' in '**Perché:**'
                new_content = problema_regex.sub(r'**\1**', content)
                new_content = perche_regex.sub(r'**\1**', new_content)

                # Salvo solo se ci sono state modifiche
                if new_content != content:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"Aggiornato: {filename}")
                else:
                    print(f"Nessuna modifica necessaria per: {filename}")

if __name__ == "__main__":
    # Assicurati che lo script sia nella cartella superiore a _articoli 
    # o cambia il percorso qui sotto
    target_dir = "_articoli"
    process_articles(target_dir)