# pipenv run python genera_notizie.py --regenerate
import os
import json
import asyncio
import re
import sys
import argparse
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import yt_dlp
import whisper
import ollama
from playwright.async_api import async_playwright

# --- CONFIGURAZIONE ---
DEBUG_DATE = "2026-04-09" 
TARGET_TOPICS = ["java", "js", "javascript", "postgresql", "postgis", "ai", "ia", "intelligenza artificiale"]
BASE_URLS = [
    "https://techfromthenet.it/software/news-produttivita/",
    "https://www.infoq.com/java/news/",
    "https://inside.java/",
    "https://www.zeusnews.it/"
]

TECH_PALETTE = {
    "java": {"accent": "#f89820", "bg": "#FFF9F2", "label": "JAVA"},
    "js": {"accent": "#F7DF1E", "bg": "#FFFFF0", "label": "JAVASCRIPT"},
    "postgresql": {"accent": "#336791", "bg": "#F0F5F9", "label": "POSTGRESQL"},
    "ia": {"accent": "#8E44AD", "bg": "#F8F4FB", "label": "AI & INNOVATION"},
    "default": {"accent": "#2ECC71", "bg": "#F2FBF6", "label": "TECH NEWS"}
}

def log(message):
    """Stampo un log con timestamp dettagliato per monitorare i tempi di esecuzione."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{timestamp} - {message}")
    sys.stdout.flush()

def parse_arguments():
    """Configuro argparse per gestire la rigenerazione delle immagini da terminale."""
    parser = argparse.ArgumentParser(description="Sistema di generazione articoli e slide tecniche.")
    parser.add_argument(
        '--regenerate', 
        action='store_true', 
        help='Se presente, forza la rigenerazione delle slide PNG leggendo il file .md locale.'
    )
    return parser.parse_args()

log("Inizializzazione Whisper (modello base)...")
whisper_model = whisper.load_model("base")

# --- UTILS ---

def slugify(text):
    """Converto il titolo in un formato adatto ai nomi delle cartelle."""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    return re.sub(r'[-\s]+', '-', text).strip('-')

def find_youtube_links(soup):
    """Identifico link YouTube nel corpo della pagina, escludendo duplicati."""
    yt_links = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        if "youtube.com/watch" in href or "youtu.be/" in href:
            clean_url = href.split('&')[0]
            yt_links.append(clean_url)
    return list(set(yt_links))

def extract_article_data(url):
    """Recupero il testo dell'articolo e identifico link video tramite scraping BeautifulSoup."""
    try:
        log(f"Analisi testuale (Scraping): {url}")
        resp = requests.get(url, timeout=15)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        video_links = find_youtube_links(soup)
        
        # Pulisco il DOM dagli elementi di disturbo
        for tag in soup(['nav', 'footer', 'header', 'aside', 'script', 'style']):
            tag.decompose()
            
        # Cerco il contenitore principale del testo
        article_body = (soup.find('article') or 
                        soup.find('main') or 
                        soup.find('div', id=re.compile('entry|content|post')))
        
        text = article_body.get_text(separator='\n', strip=True) if article_body else soup.get_text(separator='\n', strip=True)
        return text, video_links
    except Exception as e:
        log(f"❌ Errore durante lo scraping di {url}: {e}")
        return "", []

def transcribe_video(url):
    """Scarico l'audio del video con yt-dlp e lo trascrivo con Whisper."""
    log(f"🎥 Elaborazione video rilevato: {url}")
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'temp_audio.%(ext)s',
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}],
        'quiet': True, 'no_warnings': True
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        log("🎙️ Whisper sta elaborando la trascrizione...")
        result = whisper_model.transcribe("temp_audio.mp3")
        
        if os.path.exists("temp_audio.mp3"):
            os.remove("temp_audio.mp3")
            
        return result['text']
    except Exception as e:
        log(f"❌ Errore download/trascrizione: {e}")
        return ""

# --- INTELLIGENZA ARTIFICIALE ---

def generate_article(full_context, source_url):
    """Mistral crea l'articolo tecnico in italiano partendo dal contesto raccolto."""
    log("🤖 [Mistral] Avvio stesura nuovo articolo tecnico...")
    prompt = f"""
    Agisci come un programmatore senior. Crea un articolo tecnico approfondito in ITALIANO.
    Se il materiale sorgente è in inglese, traducilo accuratamente.

    CONTESTO:
    {full_context[:15000]}

    VINCOLI:
    1. Formato: Markdown (.md).
    2. Privacy: Rimuovi nomi propri di persone (usa "il team di sviluppo").
    3. Stile: Professionale e tecnico.
    4. FONTE: Alla fine dell'articolo, aggiungi una sezione '---' seguita da 'Fonte originale: {source_url}'.
    """
    response = ollama.chat(model='mistral', messages=[{'role': 'user', 'content': prompt}])
    return response['message']['content']

def extract_slides(article):
    """Qwen estrae i punti chiave per il carosello grafico in formato JSON."""
    log("🤖 [Qwen] Estrazione pillole carosello...")
    prompt = f"""
    Analizza questo articolo: {article}
    Estrai esattamente 10 concetti chiave in ITALIANO.
    
    REGOLE:
    - Massimo 5 righe per ogni pillola.
    - Restituisci esclusivamente un array JSON di stringhe.
    """
    response = ollama.chat(model='qwen2.5-coder', messages=[{'role': 'user', 'content': prompt}])
    match = re.search(r'\[.*\]', response['message']['content'], re.DOTALL)
    return json.loads(match.group()) if match else []

# --- ENGINE GRAFICO ---

async def create_images(topic, slides, folder_path):
    """Rendering delle slide 1080x1080 con numerazione progressiva."""
    log(f"🖼️ Rendering grafico per topic: {topic}...")
    
    # Rimuovo eventuali slide precedenti
    for f in os.listdir(folder_path):
        if f.endswith(".png"):
            os.remove(os.path.join(folder_path, f))

    config = TECH_PALETTE.get(topic.lower(), TECH_PALETTE["default"])
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={'width': 1080, 'height': 1080})
        
        for i, text in enumerate(slides[:10]):
            formatted_text = text.replace("Java", f"<b style='color:{config['accent']}'>Java</b>")
            html_content = f"""
            <html><style>
                body {{ background: {config['bg']}; font-family: 'Poppins', sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; padding: 100px; box-sizing: border-box; position: relative; }}
                .container {{ width: 100%; border-left: 20px solid {config['accent']}; padding-left: 60px; }}
                .label {{ font-weight: 900; color: {config['accent']}; text-transform: uppercase; font-size: 26px; margin-bottom: 25px; letter-spacing: 2px; }}
                .text {{ font-size: 42px; line-height: 1.4; color: #111; font-weight: 500; }}
                .page-num {{ position: absolute; bottom: 50px; right: 80px; font-size: 32px; font-weight: 900; color: {config['accent']}; opacity: 0.6; }}
            </style><body>
                <div class="container">
                    <div class="label">{config['label']}</div>
                    <div class="text">{formatted_text}</div>
                </div>
                <div class="page-num">{i+1}/10</div>
            </body></html>"""
            
            await page.set_content(html_content)
            await page.screenshot(path=os.path.join(folder_path, f"slide_{i+1}.png"))
            
        # Slide 11: CTA finale — ho ridotto il font-size a 36px perché l'URL lungo
        # fuoriusciva dai bordi della canvas 1080x1080 con la dimensione di default del tag <h1>
        cta_html = f"<html><body style='background:{config['accent']}; display:flex; align-items:center; justify-content:center; height:100vh; color:white; font-family:sans-serif; text-align:center; padding:50px;'><h1 style='font-size:36px;'>icarocomix.github.io/appuntidiprogrammazione</h1></body></html>"
        await page.set_content(cta_html)
        await page.screenshot(path=os.path.join(folder_path, "slide_11.png"))
        await browser.close()

# --- MAIN ENGINE ---

async def main():
    args = parse_arguments()
    log(f"--- 🚀 START SESSION: {DEBUG_DATE} (Regenerate: {args.regenerate}) ---")
    
    output_root = "output"
    if not os.path.exists(output_root): 
        os.makedirs(output_root)

    # Raccolta link dai feed configurati
    news_links = set()
    for url in BASE_URLS:
        try:
            resp = requests.get(url, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')
            for a in soup.find_all('a', href=True):
                if any(t in a.text.lower() for t in TARGET_TOPICS) and len(a.text.strip()) > 15:
                    full_link = a['href']
                    if full_link.startswith('/'): 
                        full_link = "/".join(url.split('/')[:3]) + full_link
                    news_links.add((full_link, a.text.strip()))
        except: 
            continue

    processed_count = 0
    for link, title in news_links:
        if processed_count >= 5: 
            break
        
        slug = slugify(title[:50])
        folder_path = os.path.join(output_root, f"{DEBUG_DATE}-{slug}")
        md_filename = f"{DEBUG_DATE}-{slug}.md"
        md_path = os.path.join(folder_path, md_filename)

        # 1. VERIFICA IMMEDIATA: Se il file esiste già, evito ogni operazione costosa
        if os.path.exists(md_path):
            log(f"ℹ️ Articolo già presente localmente: {md_filename}")
            
            # Leggo il file esistente
            with open(md_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Controllo se il link originale è presente, altrimenti lo aggiungo
            if link not in content:
                log(f"🔗 Integro link sorgente mancante in {md_filename}")
                with open(md_path, "a", encoding="utf-8") as f:
                    f.write(f"\n\n---\nFonte originale: {link}")
            
            # Se l'utente ha chiesto --regenerate, rigenero le immagini leggendo il MD
            if args.regenerate:
                log(f"🔄 Richiesta rigenerazione grafica per: {slug}")
                slides = extract_slides(content)
                topic_key = next((k for k in TECH_PALETTE if k in content.lower()), "default")
                await create_images(topic_key, slides, folder_path)
            
            # Passo alla notizia successiva senza scaricare nulla
            continue

        # 2. SE IL FILE NON ESISTE: Procedo con scraping, trascrizione e AI
        page_text, video_urls = extract_article_data(link)
        
        video_text = ""
        for v_url in video_urls:
            video_text += "\n" + transcribe_video(v_url)

        full_context = page_text + "\n" + video_text
        
        if len(full_context) < 300:
            log(f"⏭️ Contenuto troppo povero per '{title}'. Salto.")
            continue

        if not os.path.exists(folder_path): 
            os.makedirs(folder_path)
        
        # Generazione Articolo
        article_md = generate_article(full_context, link)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(article_md)
            
        # Generazione Slide
        slides = extract_slides(article_md)
        topic_key = next((k for k in TECH_PALETTE if k in article_md.lower()), "default")
        await create_images(topic_key, slides, folder_path)
        
        processed_count += 1
        log(f"✅ Notizia completata con successo: {folder_path}")

if __name__ == "__main__":
    asyncio.run(main())