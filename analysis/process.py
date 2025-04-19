#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Processor per l'analisi delle idee tramite LLM
Elabora le idee raccolte dagli scraper, esegue deduplicazione e analisi tramite LLM.
"""

import os
import sys
import json
import time
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor

# Fuzzy matching per deduplicazione
from fuzzywuzzy import fuzz

# Client Ollama per LLM
import requests

# Logging
from loguru import logger

# Configurazione
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.settings import LLM_CONFIG, DATA_DIR

# Assicurati che le directory esistano
Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
Path(os.path.join(DATA_DIR, "processed")).mkdir(parents=True, exist_ok=True)


class IdeaProcessor:
    """
    Classe per il processing e l'analisi delle idee raccolte.
    Gestisce deduplicazione, batch processing e analisi LLM.
    """
    
    def __init__(self, config=None):
        """
        Inizializza il processor con la configurazione specificata.
        
        Args:
            config: Configurazione per il processor e LLM
        """
        self.config = config or LLM_CONFIG
        self.model = self.config.get("model", "mistral:latest")
        self.batch_size = self.config.get("batch_size", 5)
        self.similarity_threshold = self.config.get("similarity_threshold", 0.85)
        self.min_score_threshold = self.config.get("min_score_threshold", 65)
        
        # Verifica che Ollama sia disponibile
        self._check_ollama_availability()
        
        logger.info(f"Processor inizializzato con modello {self.model}")
    
    def _check_ollama_availability(self):
        """
        Verifica che Ollama sia disponibile e che il modello sia caricato.
        """
        try:
            # Verifica che Ollama sia in esecuzione
            response = requests.get("http://localhost:11434/api/tags")
            if response.status_code != 200:
                logger.warning("Ollama non sembra essere in esecuzione. Assicurati che sia avviato.")
                return
            
            # Verifica che il modello sia disponibile
            models = response.json().get("models", [])
            model_names = [m.get("name") for m in models]
            
            if self.model not in model_names:
                logger.warning(f"Modello {self.model} non trovato in Ollama. ")
                logger.info(f"Modelli disponibili: {', '.join(model_names)}")
                logger.info(f"Puoi scaricare il modello con: ollama pull {self.model}")
        except Exception as e:
            logger.warning(f"Impossibile verificare Ollama: {str(e)}")
    
    def _load_raw_ideas(self, input_file=None):
        """
        Carica le idee grezze dal file JSON più recente.
        
        Args:
            input_file: File di input specifico (opzionale)
            
        Returns:
            Lista di idee grezze
        """
        if input_file and os.path.exists(input_file):
            file_path = input_file
        else:
            # Trova il file più recente nella directory data
            data_files = list(Path(DATA_DIR).glob("raw_ideas_*.json"))
            if not data_files:
                logger.error("Nessun file di idee grezze trovato")
                return []
            
            # Ordina per data di modifica (più recente prima)
            file_path = str(sorted(data_files, key=lambda x: x.stat().st_mtime, reverse=True)[0])
        
        logger.info(f"Caricamento idee da: {file_path}")
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                ideas = json.load(f)
            logger.info(f"Caricate {len(ideas)} idee grezze")
            return ideas
        except Exception as e:
            logger.error(f"Errore nel caricamento delle idee: {str(e)}")
            return []
    
    def _deduplicate_ideas(self, ideas):
        """
        Rimuove idee duplicate utilizzando fuzzy matching.
        
        Args:
            ideas: Lista di idee da deduplicare
            
        Returns:
            Lista di idee uniche
        """
        if not ideas:
            return []
        
        logger.info(f"Deduplicazione di {len(ideas)} idee")
        
        # Prima deduplicazione basata su hash
        hash_map = {}
        for idea in ideas:
            idea_hash = idea.get("hash")
            if idea_hash and idea_hash not in hash_map:
                hash_map[idea_hash] = idea
        
        # Lista di idee dopo deduplicazione per hash
        hash_deduped = list(hash_map.values())
        logger.info(f"Dopo deduplicazione per hash: {len(hash_deduped)} idee")
        
        # Seconda deduplicazione basata su fuzzy matching
        unique_ideas = []
        for idea in hash_deduped:
            # Controlla se l'idea è simile a una già presente
            is_duplicate = False
            for unique_idea in unique_ideas:
                # Calcola similarità tra titoli e descrizioni
                title_similarity = fuzz.ratio(idea.get("title", ""), unique_idea.get("title", ""))
                desc_similarity = fuzz.ratio(idea.get("description", "")[:200], 
                                           unique_idea.get("description", "")[:200])
                
                # Media ponderata (titolo ha più peso)
                similarity = (title_similarity * 0.7) + (desc_similarity * 0.3)
                
                if similarity >= (self.similarity_threshold * 100):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_ideas.append(idea)
        
        logger.success(f"Dopo deduplicazione fuzzy: {len(unique_ideas)} idee uniche")
        return unique_ideas
    
    def _analyze_idea_with_llm(self, idea):
        """
        Analizza una singola idea utilizzando il LLM.
        
        Args:
            idea: Idea da analizzare
            
        Returns:
            Idea con analisi LLM aggiunta
        """
        # Prepara il prompt per il LLM
        prompt = f"""Analizza la seguente idea di business/prodotto:

Titolo: {idea.get('title', '')}
Descrizione: {idea.get('description', '')}
Fonte: {idea.get('source', '')}

Rispondi SOLO in formato JSON con questi campi:
{{
  "score": [punteggio da 0-100 basato su originalità, fattibilità, potenziale di mercato],
  "tags": [massimo 3 tag/categorie che descrivono l'idea],
  "summary": [sintesi concisa in 1-2 frasi],
  "difficulty": ["low", "medium", "high"],
  "market_potential": ["niche", "moderate", "large"],
  "insight": [breve analisi del potenziale di business e suggerimenti]
}}
"""
        
        try:
            # Chiamata a Ollama API
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "temperature": self.config.get("temperature", 0.3),
                    "max_tokens": self.config.get("max_tokens", 500),
                    "stream": False
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Errore nella chiamata LLM: {response.text}")
                return idea
            
            # Estrai il testo della risposta
            llm_response = response.json().get("response", "")
            
            # Estrai il JSON dalla risposta
            try:
                # Trova l'inizio e la fine del JSON nella risposta
                json_start = llm_response.find("{")
                json_end = llm_response.rfind("}")
                
                if json_start >= 0 and json_end > json_start:
                    json_str = llm_response[json_start:json_end+1]
                    analysis = json.loads(json_str)
                    
                    # Aggiungi l'analisi all'idea
                    idea["analysis"] = analysis
                    
                    # Aggiungi timestamp dell'analisi
                    idea["analysis_timestamp"] = datetime.now().isoformat()
                    
                    logger.info(f"Idea analizzata: '{idea.get('title', '')[:30]}...' - Score: {analysis.get('score', 'N/A')}")
                else:
                    logger.warning(f"Impossibile trovare JSON nella risposta LLM")
            except json.JSONDecodeError as e:
                logger.error(f"Errore nel parsing JSON dalla risposta LLM: {str(e)}")
                logger.debug(f"Risposta LLM: {llm_response}")
        
        except Exception as e:
            logger.error(f"Errore nell'analisi dell'idea: {str(e)}")
        
        return idea
    
    def _process_ideas_batch(self, ideas_batch):
        """
        Processa un batch di idee con il LLM.
        
        Args:
            ideas_batch: Batch di idee da processare
            
        Returns:
            Batch di idee processate
        """
        processed_batch = []
        
        for idea in ideas_batch:
            try:
                processed_idea = self._analyze_idea_with_llm(idea)
                processed_batch.append(processed_idea)
                # Pausa tra le chiamate LLM
                time.sleep(1)
            except Exception as e:
                logger.error(f"Errore nel processing dell'idea: {str(e)}")
                processed_batch.append(idea)  # Aggiungi l'idea non processata
        
        return processed_batch
    
    def process_ideas(self, input_file=None):
        """
        Processa tutte le idee: carica, deduplicazione, analisi LLM.
        
        Args:
            input_file: File di input specifico (opzionale)
            
        Returns:
            Tuple (idee_processate, idee_rilevanti)
        """
        # Carica le idee grezze
        raw_ideas = self._load_raw_ideas(input_file)
        if not raw_ideas:
            return [], []
        
        # Deduplicazione
        unique_ideas = self._deduplicate_ideas(raw_ideas)
        
        # Dividi in batch per il processing
        batches = [unique_ideas[i:i+self.batch_size] 
                  for i in range(0, len(unique_ideas), self.batch_size)]
        
        logger.info(f"Processing di {len(unique_ideas)} idee in {len(batches)} batch")
        
        # Processa i batch
        all_processed = []
        for i, batch in enumerate(batches):
            logger.info(f"Processing batch {i+1}/{len(batches)}")
            processed_batch = self._process_ideas_batch(batch)
            all_processed.extend(processed_batch)
        
        # Filtra le idee rilevanti (score >= min_score_threshold)
        relevant_ideas = []
        for idea in all_processed:
            if "analysis" in idea and idea["analysis"].get("score", 0) >= self.min_score_threshold:
                relevant_ideas.append(idea)
        
        logger.success(f"Processing completato. {len(relevant_ideas)}/{len(all_processed)} idee rilevanti")
        
        # Salva i risultati
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Salva tutte le idee processate
        processed_file = os.path.join(DATA_DIR, "processed", f"processed_ideas_{timestamp}.json")
        with open(processed_file, "w", encoding="utf-8") as f:
            json.dump(all_processed, f, ensure_ascii=False, indent=2)
        
        # Salva solo le idee rilevanti
        if relevant_ideas:
            relevant_file = os.path.join(DATA_DIR, "processed", f"relevant_ideas_{timestamp}.json")
            with open(relevant_file, "w", encoding="utf-8") as f:
                json.dump(relevant_ideas, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Risultati salvati in: {processed_file}")
        
        return all_processed, relevant_ideas


def main():
    """
    Funzione principale per il processing delle idee.
    """
    logger.info("Avvio processo di analisi idee")
    
    # Inizializza il processor
    processor = IdeaProcessor()
    
    # Processa le idee
    all_ideas, relevant_ideas = processor.process_ideas()
    
    logger.info(f"Analisi completata. {len(relevant_ideas)}/{len(all_ideas)} idee rilevanti")
    
    return relevant_ideas


if __name__ == "__main__":
    main()