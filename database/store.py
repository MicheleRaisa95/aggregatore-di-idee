#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Database Storage Manager
Gestisce l'archiviazione delle idee analizzate nel database (Supabase o SQLite).
"""

import os
import sys
import json
import sqlite3
import datetime
from pathlib import Path
from typing import List, Dict, Any

# Supabase client
from supabase import create_client, Client

# Logging
from loguru import logger

# Configurazione
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.settings import DB_CONFIG, DATA_DIR

# Assicurati che le directory esistano
Path(DATA_DIR).mkdir(parents=True, exist_ok=True)


class DatabaseManager:
    """
    Gestisce l'archiviazione e il recupero delle idee dal database.
    Supporta sia Supabase che SQLite come backend.
    """
    
    def __init__(self, config=None):
        """
        Inizializza il database manager con la configurazione specificata.
        
        Args:
            config: Configurazione del database
        """
        self.config = config or DB_CONFIG
        self.db_type = self.config.get("type", "sqlite")
        
        # Inizializza il database appropriato
        if self.db_type == "supabase":
            self._init_supabase()
        else:
            self._init_sqlite()
        
        logger.info(f"Database manager inizializzato con backend {self.db_type}")
    
    def _init_supabase(self):
        """
        Inizializza la connessione a Supabase.
        """
        try:
            supabase_url = os.environ.get("SUPABASE_URL")
            supabase_key = os.environ.get("SUPABASE_KEY")
            
            if not supabase_url or not supabase_key:
                logger.error("Credenziali Supabase mancanti. Imposta SUPABASE_URL e SUPABASE_KEY")
                raise ValueError("Credenziali Supabase mancanti")
            
            self.supabase: Client = create_client(supabase_url, supabase_key)
            logger.info("Connessione a Supabase stabilita")
            
            # Verifica che le tabelle esistano
            self._ensure_supabase_tables()
            
        except Exception as e:
            logger.error(f"Errore nell'inizializzazione di Supabase: {str(e)}")
            logger.warning("Fallback a SQLite")
            self.db_type = "sqlite"
            self._init_sqlite()
    
    def _ensure_supabase_tables(self):
        """
        Verifica che le tabelle necessarie esistano in Supabase.
        Nota: In Supabase, le tabelle devono essere create manualmente o tramite migrations.
        Questo metodo è solo per documentazione della struttura.
        """
        # Struttura delle tabelle in Supabase:
        # 
        # Table: raw_ideas
        # - id: uuid (primary key)
        # - title: text
        # - description: text
        # - url: text
        # - source: text
        # - timestamp: timestamptz
        # - hash: text
        # - raw_content: jsonb
        # - created_at: timestamptz
        #
        # Table: analyzed_ideas
        # - id: uuid (primary key)
        # - title: text
        # - description: text
        # - url: text
        # - source: text
        # - timestamp: timestamptz
        # - hash: text
        # - analysis: jsonb
        # - score: integer
        # - tags: text[]
        # - difficulty: text
        # - market_potential: text
        # - created_at: timestamptz
        #
        # Table: users
        # - id: uuid (primary key)
        # - email: text
        # - created_at: timestamptz
        #
        # Table: feedback
        # - id: uuid (primary key)
        # - idea_id: uuid (foreign key to analyzed_ideas.id)
        # - user_id: uuid (foreign key to users.id)
        # - rating: integer
        # - comment: text
        # - created_at: timestamptz
        pass
    
    def _init_sqlite(self):
        """
        Inizializza il database SQLite.
        """
        try:
            db_path = self.config.get("sqlite", {}).get("db_path")
            if not db_path:
                db_path = os.path.join(DATA_DIR, "ideas.db")
            
            # Assicurati che la directory del database esista
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
            self.db_path = db_path
            self.conn = sqlite3.connect(db_path)
            self.conn.row_factory = sqlite3.Row
            
            # Crea le tabelle se non esistono
            self._create_sqlite_tables()
            
            logger.info(f"Database SQLite inizializzato: {db_path}")
            
        except Exception as e:
            logger.error(f"Errore nell'inizializzazione di SQLite: {str(e)}")
            raise
    
    def _create_sqlite_tables(self):
        """
        Crea le tabelle necessarie nel database SQLite.
        """
        cursor = self.conn.cursor()
        
        # Tabella raw_ideas (archiviazione temporanea)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS raw_ideas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            url TEXT,
            source TEXT,
            timestamp TEXT,
            hash TEXT UNIQUE,
            raw_content TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Tabella analyzed_ideas (storage permanente)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS analyzed_ideas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            url TEXT,
            source TEXT,
            timestamp TEXT,
            hash TEXT UNIQUE,
            analysis TEXT,
            score INTEGER,
            tags TEXT,
            difficulty TEXT,
            market_potential TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Tabella users
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Tabella feedback
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            idea_id INTEGER,
            user_id INTEGER,
            rating INTEGER,
            comment TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (idea_id) REFERENCES analyzed_ideas (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """)
        
        # Crea indici per migliorare le performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_raw_ideas_hash ON raw_ideas (hash)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_analyzed_ideas_hash ON analyzed_ideas (hash)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_analyzed_ideas_score ON analyzed_ideas (score)")
        
        self.conn.commit()
    
    def store_raw_ideas(self, ideas):
        """
        Archivia le idee grezze nel database.
        
        Args:
            ideas: Lista di idee grezze da archiviare
            
        Returns:
            Numero di idee archiviate
        """
        if not ideas:
            return 0
        
        logger.info(f"Archiviazione di {len(ideas)} idee grezze")
        
        if self.db_type == "supabase":
            return self._store_raw_ideas_supabase(ideas)
        else:
            return self._store_raw_ideas_sqlite(ideas)
    
    def _store_raw_ideas_supabase(self, ideas):
        """
        Archivia le idee grezze in Supabase.
        
        Args:
            ideas: Lista di idee grezze
            
        Returns:
            Numero di idee archiviate
        """
        count = 0
        
        for idea in ideas:
            try:
                # Converti raw_content in JSON se è una stringa
                if isinstance(idea.get("raw_content"), str):
                    try:
                        idea["raw_content"] = json.loads(idea["raw_content"])
                    except json.JSONDecodeError:
                        # Se non è JSON valido, lascialo come stringa
                        pass
                
                # Inserisci l'idea
                result = self.supabase.table("raw_ideas").insert(idea).execute()
                
                if result.data:
                    count += 1
                
            except Exception as e:
                logger.error(f"Errore nell'archiviazione dell'idea grezza in Supabase: {str(e)}")
        
        logger.success(f"Archiviate {count}/{len(ideas)} idee grezze in Supabase")
        return count
    
    def _store_raw_ideas_sqlite(self, ideas):
        """
        Archivia le idee grezze in SQLite.
        
        Args:
            ideas: Lista di idee grezze
            
        Returns:
            Numero di idee archiviate
        """
        cursor = self.conn.cursor()
        count = 0
        
        for idea in ideas:
            try:
                # Converti raw_content in JSON string se non lo è già
                if not isinstance(idea.get("raw_content"), str):
                    idea["raw_content"] = json.dumps(idea["raw_content"])
                
                # Inserisci l'idea
                cursor.execute("""
                INSERT OR IGNORE INTO raw_ideas 
                (title, description, url, source, timestamp, hash, raw_content)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    idea.get("title", ""),
                    idea.get("description", ""),
                    idea.get("url", ""),
                    idea.get("source", ""),
                    idea.get("timestamp", datetime.datetime.now().isoformat()),
                    idea.get("hash", ""),
                    idea.get("raw_content", "{}")
                ))
                
                if cursor.rowcount > 0:
                    count += 1
                
            except Exception as e:
                logger.error(f"Errore nell'archiviazione dell'idea grezza in SQLite: {str(e)}")
        
        self.conn.commit()
        logger.success(f"Archiviate {count}/{len(ideas)} idee grezze in SQLite")
        return count
    
    def store_analyzed_ideas(self, ideas):
        """
        Archivia le idee analizzate nel database.
        
        Args:
            ideas: Lista di idee analizzate da archiviare
            
        Returns:
            Numero di idee archiviate
        """
        if not ideas:
            return 0
        
        # Filtra solo le idee che hanno un'analisi
        analyzed = [idea for idea in ideas if "analysis" in idea]
        
        if not analyzed:
            logger.warning("Nessuna idea con analisi da archiviare")
            return 0
        
        logger.info(f"Archiviazione di {len(analyzed)} idee analizzate")
        
        if self.db_type == "supabase":
            return self._store_analyzed_ideas_supabase(analyzed)
        else:
            return self._store_analyzed_ideas_sqlite(analyzed)
    
    def _store_analyzed_ideas_supabase(self, ideas):
        """
        Archivia le idee analizzate in Supabase.
        
        Args:
            ideas: Lista di idee analizzate
            
        Returns:
            Numero di idee archiviate
        """
        count = 0
        
        for idea in ideas:
            try:
                analysis = idea.get("analysis", {})
                
                # Prepara i dati per l'inserimento
                idea_data = {
                    "title": idea.get("title", ""),
                    "description": idea.get("description", ""),
                    "url": idea.get("url", ""),
                    "source": idea.get("source", ""),
                    "timestamp": idea.get("timestamp", datetime.datetime.now().isoformat()),
                    "hash": idea.get("hash", ""),
                    "analysis": analysis,
                    "score": analysis.get("score", 0),
                    "tags": analysis.get("tags", []),
                    "difficulty": analysis.get("difficulty", "medium"),
                    "market_potential": analysis.get("market_potential", "moderate")
                }
                
                # Inserisci l'idea
                result = self.supabase.table("analyzed_ideas").insert(idea_data).execute()
                
                if result.data:
                    count += 1
                
            except Exception as e:
                logger.error(f"Errore nell'archiviazione dell'idea analizzata in Supabase: {str(e)}")
        
        logger.success(f"Archiviate {count}/{len(ideas)} idee analizzate in Supabase")
        return count
    
    def _store_analyzed_ideas_sqlite(self, ideas):
        """
        Archivia le idee analizzate in SQLite.
        
        Args:
            ideas: Lista di idee analizzate
            
        Returns:
            Numero di idee archiviate
        """
        cursor = self.conn.cursor()
        count = 0
        
        for idea in ideas:
            try:
                analysis = idea.get("analysis", {})
                
                # Converti tags in stringa JSON
                tags = json.dumps(analysis.get("tags", []))
                
                # Inserisci l'idea
                cursor.execute("""
                INSERT OR REPLACE INTO analyzed_ideas 
                (title, description, url, source, timestamp, hash, analysis, score, tags, difficulty, market_potential)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    idea.get("title", ""),
                    idea.get("description", ""),
                    idea.get("url", ""),
                    idea.get("source", ""),
                    idea.get("timestamp", datetime.datetime.now().isoformat()),
                    idea.get("hash", ""),
                    json.dumps(analysis),
                    analysis.get("score", 0),
                    tags,
                    analysis.get("difficulty", "medium"),
                    analysis.get("market_potential", "moderate")
                ))
                
                if cursor.rowcount > 0:
                    count += 1
                
            except Exception as e:
                logger.error(f"Errore nell'archiviazione dell'idea analizzata in SQLite: {str(e)}")
        
        self.conn.commit()
        logger.success(f"Archiviate {count}/{len(ideas)} idee analizzate in SQLite")
        return count
    
    def get_top_ideas(self, limit=10, min_score=65):
        """
        Recupera le idee con il punteggio più alto.
        
        Args:
            limit: Numero massimo di idee da recuperare
            min_score: Punteggio minimo
            
        Returns:
            Lista di idee
        """
        logger.info(f"Recupero delle top {limit} idee con score >= {min_score}")
        
        if self.db_type == "supabase":
            return self._get_top_ideas_supabase(limit, min_score)
        else:
            return self._get_top_ideas_sqlite(limit, min_score)
    
    def _get_top_ideas_supabase(self, limit, min_score):
        """
        Recupera le idee con il punteggio più alto da Supabase.
        
        Args:
            limit: Numero massimo di idee
            min_score: Punteggio minimo
            
        Returns:
            Lista di idee
        """
        try:
            result = self.supabase.table("analyzed_ideas") \
                .select("*") \
                .gte("score", min_score) \
                .order("score", desc=True) \
                .limit(limit) \
                .execute()
            
            return result.data
            
        except Exception as e:
            logger.error(f"Errore nel recupero delle idee da Supabase: {str(e)}")
            return []
    
    def _get_top_ideas_sqlite(self, limit, min_score):
        """
        Recupera le idee con il punteggio più alto da SQLite.
        
        Args:
            limit: Numero massimo di idee
            min_score: Punteggio minimo
            
        Returns:
            Lista di idee
        """
        cursor = self.conn.cursor()
        
        try:
            cursor.execute("""
            SELECT * FROM analyzed_ideas 
            WHERE score >= ? 
            ORDER BY score DESC 
            LIMIT ?
            """, (min_score, limit))
            
            # Converti i risultati in dizionari
            ideas = []
            for row in cursor.fetchall():
                idea = dict(row)
                
                # Converti JSON strings in oggetti Python
                if "analysis" in idea and isinstance(idea["analysis"], str):
                    idea["analysis"] = json.loads(idea["analysis"])
                
                if "tags" in idea and isinstance(idea["tags"], str):
                    idea["tags"] = json.loads(idea["tags"])
                
                ideas.append(idea)
            
            return ideas
            
        except Exception as e:
            logger.error(f"Errore nel recupero delle idee da SQLite: {str(e)}")
            return []
    
    def cleanup_old_raw_ideas(self, days=30):
        """
        Rimuove le idee grezze più vecchie di un certo numero di giorni.
        
        Args:
            days: Numero di giorni dopo i quali rimuovere le idee
            
        Returns:
            Numero di idee rimosse
        """
        logger.info(f"Pulizia delle idee grezze più vecchie di {days} giorni")
        
        if self.db_type == "supabase":
            return self._cleanup_old_raw_ideas_supabase(days)
        else:
            return self._cleanup_old_raw_ideas_sqlite(days)
    
    def _cleanup_old_raw_ideas_supabase(self, days):
        """
        Rimuove le idee grezze più vecchie da Supabase.
        
        Args:
            days: Numero di giorni
            
        Returns:
            Numero di idee rimosse
        """
        try:
            # Calcola la data limite
            cutoff_date = (datetime.datetime.now() - datetime.timedelta(days=days)).isoformat()
            
            # Rimuovi le idee più vecchie
            result = self.supabase.table("raw_ideas") \
                .delete() \
                .lt("created_at", cutoff_date) \
                .execute()
            
            count = len(result.data) if result.data else 0
            logger.success(f"Rimosse {count} idee grezze vecchie da Supabase")
            return count
            
        except Exception as e:
            logger.error(f"Errore nella pulizia delle idee da Supabase: {str(e)}")
            return 0
    
    def _cleanup_old_raw_ideas_sqlite(self, days):
        """
        Rimuove le idee grezze più vecchie da SQLite.
        
        Args:
            days: Numero di giorni
            
        Returns:
            Numero di idee rimosse
        """
        cursor = self.conn.cursor()
        
        try:
            # Calcola la data limite
            cutoff_date = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
            
            # Rimuovi le idee più vecchie
            cursor.execute("""
            DELETE FROM raw_ideas 
            WHERE date(created_at) < date(?)
            """, (cutoff_date,))
            
            count = cursor.rowcount
            self.conn.commit()
            
            logger.success(f"Rimosse {count} idee grezze vecchie da SQLite")
            return count
            
        except Exception as e:
            logger.error(f"Errore nella pulizia delle idee da SQLite: {str(e)}")
            return 0
    
    def close(self):
        """
        Chiude la connessione al database.
        """
        if self.db_type == "sqlite" and hasattr(self, "conn"):
            self.conn.close()
            logger.info("Connessione SQLite chiusa")


def main():
    """
    Funzione principale per l'archiviazione delle idee.
    """
    logger.info("Avvio processo di archiviazione idee")
    
    # Inizializza il database manager
    db_manager = DatabaseManager()
    
    try:
        # Trova il file più recente di idee processate
        processed_dir = os.path.join(DATA_DIR, "processed")
        if not os.path.exists(processed_dir):
            logger.error(f"Directory {processed_dir} non trovata")
            return
        
        processed_files = list(Path(processed_dir).glob("processed_ideas_*.json"))
        if not processed_files:
            logger.error("Nessun file di idee processate trovato")
            return
        
        # Ordina per data di modifica (più recente prima)
        latest_file = str(sorted(processed_files, key=lambda x: x.stat().st_mtime, reverse=True)[0])
        
        # Carica le idee processate
        with open(latest_file, "r", encoding="utf-8") as f:
            processed_ideas = json.load(f)
        
        logger.info(f"Caricate {len(processed_ideas)} idee processate da {latest_file}")
        
        # Archivia le idee grezze
        db_manager.store_raw_ideas(processed_ideas)
        
        # Archivia le idee analizzate
        db_manager.store_analyzed_ideas(processed_ideas)
        
        # Pulizia delle idee grezze vecchie
        db_manager.cleanup_old_raw_ideas()
        
        # Backup del database SQLite
        if db_manager.db_type == "sqlite":
            backup_file = os.path.join(DATA_DIR, f"backup_ideas_{datetime.datetime.now().strftime('%Y%m%d')}.db")
            os.system(f"copy {db_manager.db_path} {backup_file}")
            logger.info(f"Backup del database creato: {backup_file}")
        
        logger.success("Processo di archiviazione completato con successo")
        
    except Exception as e:
        logger.error(f"Errore durante l'archiviazione: {str(e)}")
    
    finally:
        # Chiudi la connessione al database
        db_manager.close()


if __name__ == "__main__":
    main()