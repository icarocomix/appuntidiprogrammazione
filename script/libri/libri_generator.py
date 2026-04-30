#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
antigravity_processor.py

Ho strutturato questo script come pipeline multi-modello per elaborare
file .txt di libri e generare tre artefatti per ognuno:
  1. review.md     → recensione Jekyll
  2. mindmap.json  → mappa mentale
  3. cheatsheet.json → cheat sheet tecnico

Uso: python antigravity_processor.py [--force]
  --force  → Rigenera tutti i file anche se già esistono
"""

import os
import re
import sys
import json
import traceback
from pathlib import Path
from datetime import datetime
from openai import OpenAI

# ---------------------------------------------------------------------------
# CONFIGURAZIONE MODELLI
# ---------------------------------------------------------------------------

# Ho separato i due modelli per funzione: uno più "creativo" per la recensione,
# uno più "deterministico" per i JSON strutturati.
MODEL_CRITIC = "nvidia/nemotron-3-super-120b-a12b:free"
KEY_CRITIC   = "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"

MODEL_LOGIC  = "minimax/minimax-m2.5:free"
KEY_LOGIC    = "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"

# Quanti caratteri del libro invio al modello. Ho scelto 70k per stare
# abbondantemente sotto il limite di contesto di entrambi i modelli,
# lasciando spazio al system prompt e alla risposta attesa.
MAX_BOOK_CHARS = 70_000


# ---------------------------------------------------------------------------
# UTILITY
# ---------------------------------------------------------------------------

def get_client(api_key: str, label: str) -> OpenAI | None:
    """
    Inizializzo il client OpenRouter per il modello richiesto.
    Ritorno None se l'inizializzazione fallisce, in modo che il chiamante
    possa decidere se interrompere o saltare i task che dipendono da questo client.
    """
    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "https://antigravity-project.local",
                "X-Title": "Antigravity Multi-Model Processor",
            }
        )
        print(f"  [OK] Client '{label}' inizializzato.")
        return client
    except Exception as e:
        # Mostro il traceback completo: voglio capire esattamente dove fallisce
        print(f"  [ERRORE] Impossibile creare il client '{label}': {e}")
        traceback.print_exc()
        return None


def read_file(filepath: Path) -> str | None:
    """
    Leggo il contenuto del file in UTF-8.
    Ritorno None in caso di errore per non interrompere la pipeline su altri libri.
    """
    try:
        return filepath.read_text(encoding="utf-8")
    except Exception as e:
        print(f"  [ERRORE] Lettura file '{filepath.name}': {e}")
        return None


def clean_json_output(content: str) -> str:
    """
    Isolo il JSON grezzo rimuovendo i blocchi markdown che alcuni modelli
    inseriscono nella risposta anche quando istruiti a non farlo.
    Estraggo poi solo ciò che sta tra il primo '{' e l'ultimo '}'.
    """
    # Rimuovo i fence ```json ... ``` o ``` ... ```
    content = re.sub(r"```(?:json)?\s*(.*?)\s*```", r"\1", content, flags=re.DOTALL)

    start = content.find("{")
    end   = content.rfind("}")

    if start == -1 or end == -1:
        # Il modello non ha restituito un oggetto JSON: lo segnalo e restituisco
        # il contenuto così com'è per permettere un'analisi manuale dell'output.
        print("  [WARN] Impossibile isolare un oggetto JSON nella risposta.")
        return content.strip()

    return content[start : end + 1].strip()


def validate_json(content: str, task_name: str) -> bool:
    """
    Verifico che il contenuto sia JSON valido prima di scriverlo su disco.
    Un file JSON malformato sarebbe inutilizzabile e difficile da diagnosticare
    senza questo controllo esplicito.
    """
    try:
        json.loads(content)
        return True
    except json.JSONDecodeError as e:
        print(f"  [WARN] Il JSON per '{task_name}' non è valido: {e}")
        return False


def save_file(path: Path, content: str, task_name: str) -> bool:
    """
    Scrivo il contenuto su disco. Ho separato questa operazione in una funzione
    dedicata per centralizzare la gestione degli errori di I/O.
    Ritorno True se il salvataggio ha avuto successo.
    """
    try:
        path.write_text(content, encoding="utf-8")
        print(f"  [OK] Salvato: {path.name}")
        return True
    except Exception as e:
        print(f"  [ERRORE] Scrittura '{path.name}': {e}")
        traceback.print_exc()
        return False


# ---------------------------------------------------------------------------
# GENERAZIONE
# ---------------------------------------------------------------------------

def generate_task_output(
    client: OpenAI,
    model: str,
    task_name: str,
    instructions: str,
    book_content: str,
    expected_format: str = "text",
) -> str | None:
    """
    Invio il prompt al modello e restituisco il testo grezzo della risposta.
    Gestisco tutti i possibili errori dell'API restituendo None, così il
    chiamante può decidere se saltare o ritentare.
    """
    print(f"  -> Task: [{task_name}] | Modello: {model.split('/')[-1]}")

    system_prompt = (
        "Sei un assistente esperto del protocollo 'Antigravity'.\n"
        f"Devi eseguire il seguente task:\n{instructions}\n\n"
        "Restituisci SOLO l'output richiesto, senza preamboli o spiegazioni.\n"
        "Se l'output è JSON, restituisci solo il codice JSON valido e nient'altro."
    )

    # Tronco il libro per non superare la finestra di contesto del modello.
    # Ho scelto di troncare (non chunking) perché i task richiedono una visione
    # globale del libro, non un'elaborazione sequenziale di segmenti.
    truncated_content = book_content[:MAX_BOOK_CHARS]
    if len(book_content) > MAX_BOOK_CHARS:
        print(f"  [WARN] Libro troncato a {MAX_BOOK_CHARS} caratteri "
              f"(originale: {len(book_content)}).")

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": f"Contenuto del libro:\n\n{truncated_content}"},
            ],
            temperature=0.3,
        )

        content = response.choices[0].message.content

        # Alcuni modelli restituiscono None in casi di filtro o errore interno.
        if content is None:
            print(f"  [ERRORE] Il modello ha restituito una risposta vuota per '{task_name}'.")
            return None

        content = content.strip()

        if expected_format == "json":
            content = clean_json_output(content)

        return content

    except Exception as e:
        print(f"  [ERRORE] API call fallita per '{task_name}': {e}")
        traceback.print_exc()
        return None


# ---------------------------------------------------------------------------
# ISTRUZIONI TASK
# ---------------------------------------------------------------------------

def build_instructions(data_oggi: str) -> dict:
    """
    Definisco le istruzioni per i tre task in un dizionario.
    Ho separato questa logica dal main per tenere il flusso di controllo
    pulito e le istruzioni facilmente modificabili.
    """
    task1 = f"""TASK 1: RECENSIONE JEKYLL (.md). Genera una recensione da critico letterario e programmatore.
Inizia con il seguente front matter ESATTO:
---
layout: libro
title: TITOLO DEL LIBRO
autore: AUTORE
sintesi: >
      BREVE SINTESI DI MAX 50 PAROLE
date: {data_oggi}
tech: SINGOLO TAG CHE IDENTIFICA IL GENERE
link: LINK AD AMAZON DEL LIBRO
link_img: LINK DELL'IMMAGINE DEL LIBRO PRESA DA AMAZON
---

Dopo il front matter, includi 15 punti chiave (H4 + paragrafo).
Lunghezza corpo: 1200-1800 parole.
Tono: prima persona, divulgativo ma tecnico."""

    task2 = """TASK 2: MAPPA MENTALE JSON (mindmap.json)
Crea una mappa mentale bilanciata e profonda basata sui concetti chiave del libro.
Suddividi gli argomenti in macro-categorie logiche (3 per il lato 'left' e 3 per il lato 'right').

REGOLE STRUTTURALI OBBLIGATORIE:
1. "title": Titolo del Libro. Se lungo, usa '\\n' per andare a capo.
2. "left" e "right": Ciascuno deve contenere esattamente 3 oggetti categoria.
3. Ogni categoria deve avere:
   - "name": titolo evocativo per la macro-categoria.
   - "color": codice esadecimale (es: #e74c3c).
   - "items": lista di esattamente 4 sotto-punti.
4. Ogni sotto-punto è un array di due stringhe: ["Etichetta Breve", "Descrizione di una riga"].

ESEMPIO FORMATO:
{
  "title": "Titolo\\nLibro",
  "left": [
    {
      "name": "Nome Categoria",
      "color": "#hex",
      "items": [["Concetto", "Spiegazione breve."]]
    }
  ],
  "right": [...]
}

Restituisci SOLO il JSON valido."""

    task3 = """TASK 3: LOGIC TABLES JSON (cheatsheet.json)
Genera un cheat sheet tecnico in formato JSON basato sui concetti pratici del libro.

REGOLE DI STRUTTURA:
1. "meta": titoli e colori.
   - "title_accent", "title_rest", "accent_color_hex", "title_rest_color_hex", "background".

2. "cards": esattamente 15 card numerate, ognuna con "id", "title", "color" e "content".
   - Colori disponibili: orange, green, blue, navy, amber, teal, red, darkgreen, purple.

3. COMPONENTI SUPPORTATI:
   - {"type": "table", "headers": [...], "rows": [[...]], "key_col": true}
   - {"type": "list", "style": "arrow|bullet|numbered", "items": [...]}
   - {"type": "kv_list", "items": [{"key": "...", "value": "..."}]}
   - {"type": "shot_grid", "items": [{"label": "TAG", "style": "zero|one|few", "text": "..."}]}
   - {"type": "check_grid", "items": [...]}
   - {"type": "note", "content": "...", "html": true}
   - {"type": "section_label", "content": "..."}
   - {"type": "divider"}

4. Se una card ha molti contenuti, aggiungi "force_layout": "full" alla card.

Restituisci SOLO il JSON valido."""

    return {"review": task1, "mindmap": task2, "cheatsheet": task3}


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    # Leggo il flag --force: se presente, rigenero tutti gli artefatti
    # anche se i file esistono già. Utile per aggiornare dopo modifiche ai prompt.
    force_regenerate = "--force" in sys.argv

    if force_regenerate:
        print("[INFO] Modalità --force attiva: i file esistenti verranno sovrascritti.\n")

    base_dir  = Path(__file__).parent
    libri_dir = base_dir / "libri"
    out_dir   = base_dir / "output"

    libri_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    txt_files = list(libri_dir.glob("*.txt"))
    if not txt_files:
        print(f"[INFO] Nessun file .txt trovato in '{libri_dir}'. Termino.")
        return

    print(f"[INFO] Trovati {len(txt_files)} file da elaborare.\n")

    # Inizializzo i client una sola volta fuori dal loop.
    # Se un client non riesce ad avviarsi, lo segnalo ma non blocco l'intera pipeline:
    # i task che dipendono da quel client verranno saltati con un messaggio chiaro.
    print("[SETUP] Inizializzazione client API...")
    client_critic = get_client(KEY_CRITIC, "critic")
    client_logic  = get_client(KEY_LOGIC,  "logic")
    print()

    data_oggi    = datetime.now().strftime("%Y-%m-%d")
    instructions = build_instructions(data_oggi)

    for filepath in txt_files:
        book_name = filepath.stem
        print(f"{'='*60}")
        print(f"--- ELABORAZIONE: {book_name} ---")
        print(f"{'='*60}")

        book_content = read_file(filepath)
        if book_content is None:
            print(f"  [SKIP] Salto '{book_name}' per errore di lettura.\n")
            continue

        if not book_content.strip():
            print(f"  [SKIP] Il file '{filepath.name}' è vuoto.\n")
            continue

        print(f"  [INFO] Lunghezza libro: {len(book_content):,} caratteri.")

        book_out_dir = out_dir / book_name
        book_out_dir.mkdir(parents=True, exist_ok=True)

        # ------------------------------------------------------------------
        # TASK 1: RECENSIONE
        # Uso il client "critic" perché questo modello è ottimizzato per
        # testo narrativo e analisi critica con stile coerente.
        # ------------------------------------------------------------------
        md_path = book_out_dir / "review.md"
        if force_regenerate or not md_path.exists():
            if client_critic is None:
                print("  [SKIP] Task Review: client 'critic' non disponibile.")
            else:
                result = generate_task_output(
                    client_critic, MODEL_CRITIC,
                    "Review", instructions["review"],
                    book_content, "text"
                )
                if result:
                    save_file(md_path, result, "Review")
                else:
                    print("  [WARN] Review non generata: risposta vuota o errore API.")
        else:
            print(f"  [SKIP] review.md già esistente (usa --force per rigenerare).")

        # ------------------------------------------------------------------
        # TASK 2: MINDMAP
        # Uso il client "logic" perché questo modello segue in modo più
        # rigoroso gli schemi JSON strutturati rispetto al critic.
        # ------------------------------------------------------------------
        mm_path = book_out_dir / "mindmap.json"
        if force_regenerate or not mm_path.exists():
            if client_logic is None:
                print("  [SKIP] Task Mindmap: client 'logic' non disponibile.")
            else:
                result = generate_task_output(
                    client_logic, MODEL_LOGIC,
                    "Mindmap", instructions["mindmap"],
                    book_content, "json"
                )
                if result:
                    if validate_json(result, "Mindmap"):
                        save_file(mm_path, result, "Mindmap")
                    else:
                        # Salvo comunque con estensione .broken per analisi manuale
                        broken_path = mm_path.with_suffix(".broken.json")
                        save_file(broken_path, result, "Mindmap (broken)")
                else:
                    print("  [WARN] Mindmap non generata: risposta vuota o errore API.")
        else:
            print(f"  [SKIP] mindmap.json già esistente (usa --force per rigenerare).")

        # ------------------------------------------------------------------
        # TASK 3: CHEATSHEET
        # ------------------------------------------------------------------
        cs_path = book_out_dir / "cheatsheet.json"
        if force_regenerate or not cs_path.exists():
            if client_logic is None:
                print("  [SKIP] Task Cheatsheet: client 'logic' non disponibile.")
            else:
                result = generate_task_output(
                    client_logic, MODEL_LOGIC,
                    "Cheatsheet", instructions["cheatsheet"],
                    book_content, "json"
                )
                if result:
                    if validate_json(result, "Cheatsheet"):
                        save_file(cs_path, result, "Cheatsheet")
                    else:
                        broken_path = cs_path.with_suffix(".broken.json")
                        save_file(broken_path, result, "Cheatsheet (broken)")
                else:
                    print("  [WARN] Cheatsheet non generata: risposta vuota o errore API.")
        else:
            print(f"  [SKIP] cheatsheet.json già esistente (usa --force per rigenerare).")

        print()

    print("[DONE] Pipeline completata.")


if __name__ == "__main__":
    main()