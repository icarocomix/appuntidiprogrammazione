Hai ragione, ho interrotto bruscamente la formattazione. Ecco il documento completo, strutturato in modo più leggibile e professionale, pronto per essere salvato come `README.md` o `MANUALE.md`.

---

# 📘 Manuale Operativo Script Python & Bash

Questo manuale descrive le funzionalità e le modalità di utilizzo della suite di script per la gestione del blog tecnico e la generazione automatizzata di contenuti.

## 🛠 Script di Automazione e Core

### 1. `avvia_generazione_notizie.sh`
È l'entry-point principale del sistema. Automatizza l'intero ambiente di lavoro prima di avviare la generazione.
* **Cosa fa:** Verifica lo stato di **Ollama**, controlla la presenza dei modelli (`mistral`, `qwen2.5-coder`), imposta le variabili d'ambiente per Python e avvia la pipeline salvando i log in tempo reale.
* **Come si usa:**
    ```bash
    ./avvia_generazione_notizie.sh
    ```
* **Parametri:** Nessuno (configurazione interna tramite variabili `PROJECT_DIR` e `LOG_FILE`).

### 2. `genera_notizie.py`
Il motore centrale di intelligenza artificiale per il recupero di news.
* **Cosa fa:** Esegue scraping, trascrizione video (Whisper) e analisi contenuti per generare articoli e slide.
* **Come si usa:**
    ```bash
    pipenv run python genera_notizie.py [opzioni]
    ```
* **Parametri:**
    * `--date YYYY-MM-DD`: Forza una data specifica (default: oggi).
    * `--regenerate`: Rigenera le immagini/slide senza scaricare nuovi dati.
    * `--fix-frontmatter`: Corregge solo le intestazioni YAML dei file MD.
    * `--libri`: Genera slide dedicate ai consigli di lettura dalla cartella `_libri`.

---

## 🖋 Script di Formattazione Codice

### 3. `code_formatter.py`
Il motore logico di formattazione multi-linguaggio.
* **Cosa fa:** Normalizza l'indentazione, gestisce i commenti a blocco e rifinisce il codice tramite **Prettier** e **Ollama**. Supporta Java, JS, SQL e linguaggi di markup.
* **Come si usa:**
    ```bash
    python code_formatter.py <file_input>
    ```
* **Parametri:**
    * `<file_input>` (**Obbligatorio**): Percorso del file sorgente da processare.

### 4. `formatta_codice_articoli.py`
Versione "bulk" (massiva) del formattatore per il blog.
* **Cosa fa:** Scansiona i file Markdown, individua i blocchi di codice dentro la sezione "Esempio Implementativo" e li sovrascrive con la versione formattata correttamente.
* **Come si usa:**
    ```bash
    python formatta_codice_articoli.py
    ```
* **Parametri:** Nessuno. Opera sulla cartella `_articoli/` e produce l'output in `_nuovi_articoli/`.

---

## 📊 Script di Importazione e Refactoring Testi

### 5. `excel_to_articoli.py`
Importatore dai fogli di calcolo.
* **Cosa fa:** Converte righe Excel in file Markdown per Jekyll. Gestisce la sanificazione dei caratteri speciali di Excel (`\xa0`, `\r\n`) e formatta il codice integrato.
* **Come si usa:**
    ```bash
    python excel_to_articoli.py
    ```
* **Parametri:** Nessuno. Richiede una cartella `excel_input/` con i file `.xlsx`.

### 6. `formatta_articoli.py`
Refactoring stilistico dei testi.
* **Cosa fa:** Pulisce i tag "Problema:" e "Perché:", assicurando che siano in grassetto e con la corretta spaziatura tra i paragrafi per una leggibilità ottimale.
* **Come si usa:**
    ```bash
    python formatta_articoli.py
    ```
* **Parametri:** Nessuno. Processa i file nella cartella `_articoli/`.

---

## 🔍 Utility di Diagnostica

### 7. `debug_formatter.py`
* **Cosa fa:** Analizza passo-passo come il codice viene interpretato dal sistema (Step 1: Raw, Step 2: List Debug, Step 3: Final Output).
* **Come si usa:**
    ```bash
    python debug_formatter.py <file_input> [tecnologia]
    ```
* **Parametri:**
    * `<file_input>` (**Obbligatorio**): File di testo/codice da testare.
    * `[tecnologia]` (Facoltativo): es. `java`, `sql`, `html`. Default: `java`.