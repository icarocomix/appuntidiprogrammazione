import sys
import os
# Importiamo il tuo file (assicurati che si chiami code_formatter.py nella stessa cartella)
try:
    import code_formatter as cf
except ImportError:
    print("Errore: Assicurati che code_formatter.py sia nella stessa cartella.")
    sys.exit(1)

def debug_formatting(input_path, tech="java"):
    if not os.path.exists(input_path):
        print(f"File non trovato: {input_path}")
        return

    with open(input_path, "r", encoding="utf-8") as f:
        raw_code = f.read()

    print("--- STEP 1: INPUT GREZZO ---")
    print(raw_code)
    print("\n" + "="*50 + "\n")

    try:
        # 1. Chiamata alla normalizzazione (Scomposizione in elementi di lista)
        # Qui verifichiamo se il parser "spezza" le righe piatte
        lines = cf.normalize_to_lines(raw_code, tech)
        
        print(f"--- STEP 2: DEBUG LISTA (Elementi individuati: {len(lines)}) ---")
        for i, line in enumerate(lines):
            # Stampo ogni elemento tra [ ] per vedere se ci sono spazi residui o split errati
            print(f"Linea {i:03}: [{line}]")
        
        print("\n" + "="*50 + "\n")

        # 2. Chiamata all'indentazione
        indented = cf.indent_lines(lines, tech)
        
        # 3. Join finale (qui gli elementi della lista diventano testo con \n)
        formatted_output = "\n".join(indented)

        print("--- STEP 3: OUTPUT FINALE FORMATTATO ---")
        print(formatted_output)

        # Scrittura su file di debug
        output_path = "debug_output.txt"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(formatted_output)
        
        print(f"\n✓ Debug completato. File generato: {output_path}")

    except Exception as e:
        print(f"ERRORE DURANTE IL DEBUG: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Uso: python debug_formatter.py input.txt java
    file_in = sys.argv[1] if len(sys.argv) > 1 else "test_input.txt"
    tecnologia = sys.argv[2] if len(sys.argv) > 2 else "java"
    
    debug_formatting(file_in, tecnologia)