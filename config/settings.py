#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
File di configurazione principale per l'aggregatore di idee business.
Contiene tutte le impostazioni e parametri configurabili del sistema.
"""

import os
from pathlib import Path

# Directory di base del progetto
BASE_DIR = Path(__file__).resolve().parent.parent

# Directory per i dati
DATA_DIR = os.path.join(BASE_DIR, "data")

# Configurazione degli scraper
SCRAPER_CONFIG = {
    "ProductHunt": {
        "enabled": True,
        "params": {
            "pages_to_scrape": 3,
            "min_upvotes": 5,
            "rate_limit": 1.5  # Secondi tra le richieste
        }
    },
    "Reddit": {
        "enabled": True,
        "params": {
            "subreddits": ["SaaS", "microsaas", "SomeoneShouldMake", "Entrepreneur", "startups"],
            "time_filter": "week",
            "limit": 100,
            "min_score": 10
        }
    },
    "HackerNews": {
        "enabled": True,
        "params": {
            "sections": ["new", "show"],
            "pages": 2,
            "min_points": 5
        }
    },
    "HuntScreens": {
        "enabled": True,
        "params": {
            "pages_to_scrape": 2
        }
    },
    "Aquaire": {
        "enabled": True,
        "params": {
            "pages_to_scrape": 2
        }
    }
}

# Configurazione LLM
LLM_CONFIG = {
    "model": "mistral:latest",  # Modello Ollama da utilizzare
    "batch_size": 5,  # Numero di idee da processare in batch
    "temperature": 0.3,  # Temperatura per la generazione
    "max_tokens": 500,  # Massimo numero di token per risposta
    "similarity_threshold": 0.85,  # Soglia per deduplicazione (0-1)
    "min_score_threshold": 65  # Punteggio minimo per archiviazione permanente
}

# Configurazione database
DB_CONFIG = {
    "type": "supabase",  # "supabase" o "sqlite"
    "sqlite": {
        "db_path": os.path.join(DATA_DIR, "ideas.db")
    },
    # Le credenziali Supabase vengono caricate da variabili d'ambiente
    # SUPABASE_URL e SUPABASE_KEY
}

# Configurazione notifiche
NOTIFICATION_CONFIG = {
    "telegram": {
        "enabled": True,
        "min_score_to_notify": 80  # Punteggio minimo per inviare notifica
    },
    # Le credenziali Telegram vengono caricate da variabili d'ambiente
    # TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID
}

# Configurazione frontend
FRONTEND_CONFIG = {
    "items_per_page": 10,
    "default_sort": "score",  # "score", "date", "source"
    "default_filter": "all"  # "all", "high_potential", "low_difficulty", etc.
}

# Configurazione logging
LOGGING_CONFIG = {
    "level": "INFO",
    "retention": "10 days",
    "log_dir": os.path.join(DATA_DIR, "logs")
}