# Guida Rapida: Aggregatore di Idee Business a Budget Zero

Questa guida rapida ti aiuterà a iniziare subito con l'implementazione dell'aggregatore di idee business. Per istruzioni più dettagliate, consulta il file `TUTORIAL.md` nella root del progetto e la `GUIDA_IMPLEMENTAZIONE.md` nella cartella `docs/`.

## Passaggi Essenziali

### 1. Preparazione dell'Ambiente

```bash
# Clona il repository (se non l'hai già fatto)
git clone <url-del-tuo-repository>
cd progetto-se4freto

# Installa le dipendenze
pip install -r requirements.txt
```

### 2. Configurazione delle API Keys

Crea un file `.env` nella root del progetto con le seguenti variabili:

```
# Reddit API
REDDIT_CLIENT_ID=il_tuo_client_id
REDDIT_CLIENT_SECRET=il_tuo_client_secret
REDDIT_USER_AGENT=IdeaAggregator/1.0

# Supabase (se usi Supabase)
SUPABASE_URL=https://tuo-progetto.supabase.co
SUPABASE_KEY=tua-chiave-api

# Telegram (per le notifiche)
TELEGRAM_BOT_TOKEN=token_del_tuo_bot
TELEGRAM_CHAT_ID=id_della_chat
```

### 3. Completamento del Sistema di Notifiche

Crea o modifica il file `analysis/notify.py` con il seguente contenuto:

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Notification System
Invia notifiche delle idee migliori tramite Telegram.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
import requests
from loguru import logger

# Configurazione
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.settings import DATA_DIR

# Configurazione Telegram
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def load_processed_ideas():
    """
    Carica le idee processate dal file JSON più recente.
    
    Returns:
        Lista di idee processate
    """
    processed_dir = os.path.join(DATA_DIR, "processed")
    Path(processed_dir).mkdir(parents=True, exist_ok=True)
    
    # Trova il file più recente
    files = list(Path(processed_dir).glob("*.json"))
    if not files:
        logger.warning("Nessun file di idee processate trovato")
        return []
    
    latest_file = max(files, key=lambda x: x.stat().st_mtime)
    logger.info(f"Caricando idee da {latest_file}")
    
    try:
        with open(latest_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Errore nel caricamento delle idee: {str(e)}")
        return []


def send_telegram_notification(message):
    """
    Invia una notifica tramite Telegram.
    
    Args:
        message: Messaggio da inviare
    
    Returns:
        True se l'invio è riuscito, False altrimenti
    """
    if not all([TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID]):
        logger.warning("Token o chat ID Telegram mancanti")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info("Notifica Telegram inviata con successo")
        return True
    except Exception as e:
        logger.error(f"Errore nell'invio della notifica Telegram: {str(e)}")
        return False


def format_idea_message(idea):
    """
    Formatta un'idea per la notifica Telegram.
    
    Args:
        idea: Dizionario contenente i dati dell'idea
    
    Returns:
        Messaggio formattato
    """
    title = idea.get("title", "Titolo non disponibile")
    description = idea.get("description", "Descrizione non disponibile")
    score = idea.get("score", 0.0)
    source = idea.get("source", "Fonte sconosciuta")
    url = idea.get("url", "")
    
    # Tronca la descrizione se troppo lunga
    if len(description) > 200:
        description = description[:197] + "..."
    
    message = f"<b>💡 Nuova idea promettente!</b>\n\n"
    message += f"<b>{title}</b>\n\n"
    message += f"{description}\n\n"
    message += f"<b>Punteggio:</b> {score:.2f}/1.0\n"
    message += f"<b>Fonte:</b> {source}\n"
    
    if url:
        message += f"<a href=\"{url}\">Vedi originale</a>"
    
    return message


def main():
    """
    Funzione principale per l'invio delle notifiche.
    """
    logger.info("Avvio sistema di notifiche")
    
    # Carica le idee processate
    ideas = load_processed_ideas()
    if not ideas:
        logger.warning("Nessuna idea da notificare")
        return
    
    # Filtra le idee con punteggio alto (> 0.8)
    high_score_ideas = [idea for idea in ideas if idea.get("score", 0) > 0.8]
    logger.info(f"Trovate {len(high_score_ideas)} idee con punteggio alto")
    
    # Limita a massimo 5 notifiche per non spammare
    ideas_to_notify = sorted(
        high_score_ideas, 
        key=lambda x: x.get("score", 0), 
        reverse=True
    )[:5]
    
    # Invia notifiche
    for idea in ideas_to_notify:
        message = format_idea_message(idea)
        send_telegram_notification(message)
    
    logger.info(f"Inviate {len(ideas_to_notify)} notifiche")


if __name__ == "__main__":
    main()
```

### 4. Esecuzione Manuale del Sistema

Per testare il sistema manualmente:

```bash
# Esegui gli scraper
python scrapers/main.py

# Esegui l'analisi LLM (assicurati che Ollama sia in esecuzione)
python analysis/process.py

# Archivia i risultati nel database
python database/store.py

# Invia notifiche
python analysis/notify.py
```

### 5. Configurazione di GitHub Actions

1. Vai su GitHub > Settings > Secrets and variables > Actions
2. Aggiungi tutti i segreti necessari (REDDIT_CLIENT_ID, SUPABASE_URL, ecc.)
3. Attiva il workflow manualmente dalla scheda Actions

### 6. Deployment del Frontend

1. Configura GitHub Pages:
   - Vai su Settings > Pages
   - Seleziona la branch `main` e la cartella `/docs`
   - Clicca su Save

2. Il frontend sarà disponibile all'URL: `https://tuo-username.github.io/tuo-repository/`

## Risoluzione Problemi Comuni

### Errori di Scraping

- Verifica che le API keys siano corrette
- Controlla i rate limit delle piattaforme target
- Verifica che i selettori HTML non siano cambiati (per scraper basati su HTML)

### Errori di Analisi LLM

- Assicurati che Ollama sia in esecuzione
- Verifica che il modello sia stato scaricato correttamente
- Controlla i log per errori specifici

### Errori di Database

- Verifica le credenziali Supabase
- Controlla che le tabelle siano state create correttamente
- Verifica i permessi RLS (Row Level Security)

## Prossimi Passi

- Aggiungi nuovi scraper per altre fonti di idee
- Migliora i prompt LLM per un'analisi più accurata
- Implementa funzionalità di feedback degli utenti
- Aggiungi analisi di tendenze e statistiche

Per assistenza e ulteriori informazioni, consulta la documentazione completa nei file `TUTORIAL.md` e `docs/GUIDA_IMPLEMENTAZIONE.md`.