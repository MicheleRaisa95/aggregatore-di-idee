#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Main Scraper Orchestrator
Coordina l'esecuzione di tutti gli scraper e gestisce il flusso di lavoro complessivo.
"""

import os
import sys
import json
import time
import logging
import hashlib
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# Configurazione logging
import logging
from loguru import logger

# Importazione scraper
from scrapers.producthunt import ProductHuntScraper
from scrapers.reddit import RedditScraper
from scrapers.hackernews import HackerNewsScraper
from scrapers.huntscreens import HuntScreensScraper
from scrapers.aquaire import AquaireScraper

# Configurazione
from config.settings import SCRAPER_CONFIG, DATA_DIR

# Assicurati che la directory dei dati esista
Path(DATA_DIR).mkdir(parents=True, exist_ok=True)

# Configurazione logger
logger.add(
    os.path.join(DATA_DIR, "logs", "scraper_{time}.log"),
    rotation="500 MB",
    retention="10 days",
    level="INFO"
)


def normalize_data(data, source):
    """
    Normalizza i dati in un formato JSON unificato.
    
    Args:
        data (dict): Dati grezzi dal scraper
        source (str): Nome della fonte
        
    Returns:
        dict: Dati normalizzati
    """
    # Genera un hash unico per deduplicazione
    content_hash = hashlib.md5(
        f"{data.get('title', '')}{data.get('description', '')}".encode()
    ).hexdigest()
    
    return {
        "title": data.get("title", ""),
        "description": data.get("description", ""),
        "url": data.get("url", ""),
        "source": source,
        "timestamp": datetime.now().isoformat(),
        "raw_content": json.dumps(data),  # Salva i dati grezzi come JSON
        "hash": content_hash
    }


def run_scraper(scraper_class, config):
    """
    Esegue un singolo scraper con gestione degli errori e retry.
    
    Args:
        scraper_class: Classe dello scraper da eseguire
        config (dict): Configurazione dello scraper
        
    Returns:
        list: Lista di idee normalizzate
    """
    source_name = scraper_class.__name__.replace("Scraper", "")
    logger.info(f"Avvio scraper: {source_name}")
    
    # Verifica se lo scraper è abilitato
    if not config.get("enabled", True):
        logger.info(f"Scraper {source_name} disabilitato, salto")
        return []
    
    try:
        # Inizializza lo scraper con la configurazione
        scraper = scraper_class(**config.get("params", {}))
        
        # Esegui lo scraper con retry
        raw_ideas = scraper.run()
        
        # Normalizza i dati
        normalized_ideas = [
            normalize_data(idea, source_name) for idea in raw_ideas
        ]
        
        logger.success(f"Scraper {source_name} completato: {len(normalized_ideas)} idee raccolte")
        return normalized_ideas
        
    except Exception as e:
        logger.error(f"Errore durante l'esecuzione di {source_name}: {str(e)}")
        return []


def main():
    """
    Funzione principale che coordina tutti gli scraper.
    """
    logger.info("Avvio processo di scraping")
    
    # Mappa delle classi scraper
    scraper_map = {
        "ProductHunt": ProductHuntScraper,
        "Reddit": RedditScraper,
        "HackerNews": HackerNewsScraper,
        "HuntScreens": HuntScreensScraper,
        "Aquaire": AquaireScraper
    }
    
    all_ideas = []
    
    # Esegui gli scraper in parallelo
    with ThreadPoolExecutor(max_workers=3) as executor:
        future_to_scraper = {
            executor.submit(run_scraper, scraper_map[name], config): name
            for name, config in SCRAPER_CONFIG.items()
            if name in scraper_map
        }
        
        for future in future_to_scraper:
            ideas = future.result()
            all_ideas.extend(ideas)
    
    # Salva i risultati
    output_file = os.path.join(DATA_DIR, f"raw_ideas_{datetime.now().strftime('%Y%m%d')}.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_ideas, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Scraping completato. Totale idee raccolte: {len(all_ideas)}")
    logger.info(f"Risultati salvati in: {output_file}")
    
    return all_ideas


if __name__ == "__main__":
    main()