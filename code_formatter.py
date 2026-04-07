"""
Formattatore di codice multi-linguaggio v6.
Preserva le interfacce normalize_to_lines e indent_lines per compatibilità esterna.
Risolve il problema del codice "piatto" forzando i newline sui token strutturali.
"""

import os
import re
import sys

# Indentazione standard 4 spazi
INDENT = "    "

CURLY_BRACE_LANGUAGES = {"java", "javascript", "js", "typescript", "ts", "c", "cpp", "csharp", "cs", "php", "kotlin"}
SQL_LANGUAGES = {"sql", "plpgsql"}
MARKUP_LANGUAGES = {"html", "xml", "thymeleaf", "svg"}

_CODE = 0
_STRING_DOUBLE = 1
_STRING_SINGLE = 2
_COMMENT_LINE = 3
_COMMENT_BLOCK = 4

# Regex per identificare l'inizio di una riga logica in Java/C-like
_RE_BREAK_KEYWORDS = re.compile(r'^(public|protected|private|static|final|class|interface|enum|record|@|void|return|if|for|while)\b', re.IGNORECASE)

# ─────────────────────────────────────────────
# NORMALIZZAZIONE (Scomposizione in righe)
# ─────────────────────────────────────────────

def _normalize_curly_logic(code: str) -> list:
    """
    Versione 7:
    - Impedisce ai commenti // di 'mangiare' il codice successivo se sulla stessa riga.
    - Forza 'return' a inizio riga.
    - Mantiene ';' e '{' a fine riga.
    """
    result = []
    buf = []
    state = _CODE
    i = 0
    n = len(code)

    def emit_buf():
        content = "".join(buf).strip()
        if content:
            # Collassiamo gli spazi ma preserviamo la logica
            result.append(" ".join(content.split()))
        buf.clear()

    while i < n:
        ch = code[i]
        next_ch = code[i+1] if i+1 < n else ""

        # --- GESTIONE COMMENTI A RIGA (//) ---
        if state == _COMMENT_LINE:
            # INTERRUZIONE CRITICA: Se nel commento piatto troviamo ';' o '{' o '}' 
            # o una parola chiave come 'return', il commento DEVE finire.
            # Altrimenti il codice dopo // non verrà mai eseguito dal parser.
            
            # Controllo se quello che segue nel buffer (escludendo //) 
            # assomiglia a un'istruzione Java
            current_comment_text = "".join(buf)
            
            if ch == "\n":
                emit_buf(); state = _CODE; i += 1
            elif ch in "{};" or (ch == "r" and code[i:i+7] == "return "):
                # Ho trovato un trigger di codice: chiudo il commento qui
                emit_buf()
                state = _CODE
                # NON incremento i, così il ciclo successivo gestisce ch come CODICE
            else:
                buf.append(ch)
                i += 1
            continue

        # --- GESTIONE ALTRI STATI (Commenti blocco e Stringhe) ---
        if state == _COMMENT_BLOCK:
            buf.append(ch)
            if ch == "*" and next_ch == "/":
                buf.append("/"); i += 2; state = _CODE; emit_buf()
            else: i += 1
            continue

        if state in (_STRING_DOUBLE, _STRING_SINGLE):
            quote = '"' if state == _STRING_DOUBLE else "'"
            buf.append(ch)
            if ch == "\\" and next_ch:
                buf.append(next_ch); i += 2
            elif ch == quote:
                state = _CODE; i += 1
            else: i += 1
            continue

        # --- LOGICA DI TOKENIZZAZIONE CODICE ---
        if ch == "/" and next_ch == "*":
            emit_buf(); buf.append("/*"); state = _COMMENT_BLOCK; i += 2
        elif ch == "/" and next_ch == "/":
            emit_buf(); buf.append("//"); state = _COMMENT_LINE; i += 2
        
        # 1. FINE RIGA: ';' e '{' (Vanno a capo DOPO)
        elif ch in ";{":
            buf.append(ch)
            emit_buf()
            i += 1
        
        # 2. INIZIO RIGA: '}' e '@' (Vanno a capo PRIMA)
        elif ch == "}":
            emit_buf()
            result.append("}")
            i += 1
        elif ch == "@":
            emit_buf()
            buf.append("@")
            i += 1

        # 3. PAROLE CHIAVE SPECIALI (Modificatori e return)
        elif ch.isspace():
            word = "".join(buf).strip()
            # Se la parola è 'return' o un modificatore, deve stare a inizio riga
            if word == "return" or _RE_BREAK_KEYWORDS.match(word):
                # Mi assicuro che la parola non rimanga attaccata a quella precedente
                temp_word = word
                buf.clear()
                emit_buf() # Svuota ciò che c'era prima
                buf.append(temp_word + " ")
            else:
                buf.append(" ")
            i += 1
        else:
            buf.append(ch)
            i += 1

    emit_buf()
    return [l for l in result if l]

def normalize_to_lines(code: str, language: str) -> list:
    """Interfaccia obbligatoria per lo script esterno."""
    if language in CURLY_BRACE_LANGUAGES:
        return _normalize_curly_logic(code)
    
    if language in MARKUP_LANGUAGES:
        # Split sui tag e sui commenti
        parts = re.split(r'(<[^>]+>|/\*.*?\*/|//.*?\n)', code, flags=re.DOTALL)
        return [p.strip() for p in parts if p.strip()]
    
    # Fallback per altri linguaggi
    return [l.strip() for l in code.splitlines() if l.strip()]

# ─────────────────────────────────────────────
# INDENTAZIONE
# ─────────────────────────────────────────────

def indent_lines(lines: list, language: str) -> list:
    """Interfaccia obbligatoria per lo script esterno. Applica 4 spazi."""
    formatted = []
    depth = 0
    
    # Gestione specifica per SQL (semplice)
    if language in SQL_LANGUAGES:
        for l in lines:
            s = l.strip()
            if re.match(r'^(SELECT|INSERT|UPDATE|DELETE|FROM|WHERE|JOIN|GROUP|ORDER|LIMIT)', s, re.I):
                formatted.append(s)
            else:
                formatted.append(INDENT + s)
        return formatted

    # Gestione per linguaggi a graffe (Java, JS, etc.) e Markup
    for line in lines:
        s = line.strip()
        if not s: continue
        
        # Chiusura tag o graffa: riduco indentazione prima di scrivere
        is_closing = s.startswith("}") or s.startswith("</") or s.endswith("]]>")
        if is_closing:
            depth = max(0, depth - 1)
        
        formatted.append(INDENT * depth + s)
        
        # Apertura: aumento indentazione per la riga successiva
        # Non aumento se è un tag auto-chiudente o un commento a riga singola
        is_opening = (
            (s.endswith("{") or s == "{") or 
            (s.startswith("<") and not s.startswith("</") and not s.endswith("/>") and not s.startswith("<!"))
        )
        if is_opening:
            depth += 1
            
    return formatted

# ─────────────────────────────────────────────
# ESECUZIONE (Se chiamato direttamente)
# ─────────────────────────────────────────────

def detect_language(code: str) -> str:
    if "@" in code or "public class" in code: return "java"
    if "th:" in code or "<html" in code: return "thymeleaf"
    return "java"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python code_formatter.py <file_input>")
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        raw_content = f.read()

    lang = detect_language(raw_content)
    lines = normalize_to_lines(raw_content, lang)
    final_output = indent_lines(lines, lang)
    
    print("\n".join(final_output))