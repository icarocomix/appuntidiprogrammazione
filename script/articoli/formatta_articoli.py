import os
import re

def process_articles(directory):
    if not os.path.exists(directory):
        print(f"Errore: La cartella '{directory}' non esiste.")
        return

    # Pattern per trovare "Problema:" e "Perché:" ripulendo qualsiasi formattazione esistente
    re_problema = re.compile(r'[^a-zA-Z\s]*Problema:[^a-zA-Z\s]*', re.IGNORECASE)
    re_perche = re.compile(r'[^a-zA-Z\s]*Perch[eéè]:[^a-zA-Z\s]*', re.IGNORECASE)

    for filename in os.listdir(directory):
        if filename.endswith(".md"):
            filepath = os.path.join(directory, filename)
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Lavoro sul contenuto intero per gestire meglio i ritorni a capo tra paragrafi
            if "## Analisi Tecnica" in content:
                # 1. Pulizia totale: riporto le parole chiave allo stato "nudo"
                # Rimuovo gli asterischi pasticciati (es. ****Problema:**** -> Problema:)
                new_content = re_problema.sub("Problema:", content)
                new_content = re_perche.sub("Perché:", new_content)

                # 2. Applico la formattazione corretta con DOPPIO ritorno a capo
                # Cerco "Problema:" e lo rendo grassetto
                new_content = new_content.replace("Problema:", "**Problema:**")
                
                # Cerco "Perché:" e mi assicuro che abbia due newline davanti
                # Questo lo separa nettamente dal paragrafo precedente
                new_content = new_content.replace("Perché:", "\n\n**Perché:**")

                # 3. Normalizzazione (Idempotenza)
                # Se per caso ci sono troppi spazi o troppi ritorni a capo dopo il rimpiazzo,
                # comprimo tutto in massimo due \n per evitare spazi bianchi infiniti
                new_content = re.sub(r'\n{3,}', '\n\n', new_content)
                
                # Evito che si crei uno spazio vuoto subito dopo il titolo della sezione
                new_content = new_content.replace("## Analisi Tecnica\n\n", "## Analisi Tecnica\n")

                if new_content != content:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"Sistemato (doppia linea inclusa): {filename}")

if __name__ == "__main__":
    process_articles("_articoli")