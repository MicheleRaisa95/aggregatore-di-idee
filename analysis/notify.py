#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Notification System
Invia notifiche per le idee di business più promettenti tramite Telegram.
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any

# Telegram Bot
from telegram import Bot
from telegram.error import TelegramError

# Logging
from loguru import logger

# Configurazione
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.settings import NOTIFICATION_CONFIG, DATA_DIR
from database.store import DatabaseManager


class NotificationManager:
    """
    Gestisce l'invio di notifiche per le idee di business più promettenti.
    Attualmente supporta notifiche via Telegram.
    """
    
    def __init__(self, config=None):
        """
        Inizializza il notification manager con la configurazione specificata.
        
        Args:
            config: Configurazione delle notifiche
        """
        self.config = config or NOTIFICATION_CONFIG
        self.telegram_enabled = self.config.get("telegram", {}).get("enabled", False)
        self.min_score = self.config.get("telegram", {}).get("min_score_to_notify", 80)
        
        # Inizializza il bot Telegram se abilitato
        if self.telegram_enabled:
            self._init_telegram_bot()
        
        logger.info(f"Notification manager inizializzato")
    
    def _init_telegram_bot(self):
        """
        Inizializza il bot Telegram.
        """
        try:
            token = os.environ.get("TELEGRAM_BOT_TOKEN")
            self.chat_id = os.environ.get("TELEGRAM_CHAT_ID")
            
            if not token or not self.chat_id:
                logger.error("Credenziali Telegram mancanti. Imposta TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID")
                self.telegram_enabled = False
                return
            
            self.bot = Bot(token=token)
            logger.info("Bot Telegram inizializzato")
            
        except Exception as e:
            logger.error(f"Errore nell'inizializzazione del bot Telegram: {str(e)}")
            self.telegram_enabled = False
    
    def _format_idea_message(self, idea):
        """
        Formatta un'idea per l'invio come messaggio Telegram.
        
        Args:
            idea: Idea da formattare
            
        Returns:
            Messaggio formattato
        """
        analysis = idea.get("analysis", {})
        
        # Formatta i tag
        tags = analysis.get("tags", [])
        tags_str = " ".join([f"#{tag.replace(' ', '_')}" for tag in tags])
        
        # Crea il messaggio
        message = f"""🚀 *Nuova Idea Promettente!*

*{idea.get('title', 'Titolo non disponibile')}*

{analysis.get('summary', 'Nessun sommario disponibile')}

📊 *Score:* {analysis.get('score', 'N/A')}/100
🔍 *Difficoltà:* {analysis.get('difficulty', 'N/A')}
💼 *Potenziale di mercato:* {analysis.get('market_potential', 'N/A')}

💡 *Insight:* {analysis.get('insight', 'Nessun insight disponibile')}

🔗 [Fonte originale]({idea.get('url', '#')})

{tags_str}"""
        
        return message
    
    def send_telegram_notification(self, idea):
        """
        Invia una notifica Telegram per un'idea.
        
        Args:
            idea: Idea da notificare
            
        Returns:
            True se l'invio è riuscito, False altrimenti
        """
        if not self.telegram_enabled:
            logger.warning("Notifiche Telegram disabilitate")
            return False
        
        try:
            # Formatta il messaggio
            message = self._format_idea_message(idea)
            
            # Invia il messaggio
            self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode="Markdown",
                disable_web_page_preview=False
            )
            
            logger.success(f"Notifica inviata per: {idea.get('title', 'Idea senza titolo')}")
            return True
            
        except TelegramError as e:
            logger.error(f"Errore Telegram: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Errore nell'invio della notifica: {str(e)}")
            return False
    
    def notify_top_ideas(self, ideas=None, limit=5):
        """
        Notifica le idee più promettenti.
        
        Args:
            ideas: Lista di idee (opzionale, altrimenti le recupera dal database)
            limit: Numero massimo di idee da notificare
            
        Returns:
            Numero di notifiche inviate
        """
        # Se non sono state fornite idee, recuperale dal database
        if ideas is None:
            db_manager = DatabaseManager()
            ideas = db_manager.get_top_ideas(limit=limit, min_score=self.min_score)
            db_manager.close()
        
        if not ideas:
            logger.info("Nessuna idea da notificare")
            return 0
        
        # Filtra le idee con punteggio sufficiente
        high_score_ideas = [idea for idea in ideas 
                           if idea.get("analysis", {}).get("score", 0) >= self.min_score]
        
        if not high_score_ideas:
            logger.info(f"Nessuna idea con punteggio >= {self.min_score}")
            return 0
        
        # Limita il numero di notifiche
        ideas_to_notify = high_score_ideas[:limit]
        
        # Invia le notifiche
        sent_count = 0
        for idea in ideas_to_notify:
            if self.send_telegram_notification(idea):
                sent_count += 1
        
        logger.info(f"Inviate {sent_count}/{len(ideas_to_notify)} notifiche")
        return sent_count


def main():
    """
    Funzione principale per l'invio di notifiche.
    """
    logger.info("Avvio processo di notifica")
    
    # Inizializza il notification manager
    notifier = NotificationManager()
    
    try:
        # Trova il file più recente di idee rilevanti
        processed_dir = os.path.join(DATA_DIR, "processed")
        if not os.path.exists(processed_dir):
            logger.error(f"Directory {processed_dir} non trovata")
            return
        
        relevant_files = list(Path(processed_dir).glob("relevant_ideas_*.json"))
        if not relevant_files:
            logger.info("Nessun file di idee rilevanti trovato, uso il database")
            notifier.notify_top_ideas()
            return
        
        # Ordina per data di modifica (più recente prima)
        latest_file = str(sorted(relevant_files, key=lambda x: x.stat().st_mtime, reverse=True)[0])
        
        # Carica le idee rilevanti
        with open(latest_file, "r", encoding="utf-8") as f:
            relevant_ideas = json.load(f)
        
        logger.info(f"Caricate {len(relevant_ideas)} idee rilevanti da {latest_file}")
        
        # Invia notifiche
        notifier.notify_top_ideas(ideas=relevant_ideas)
        
        logger.success("Processo di notifica completato con successo")
        
    except Exception as e:
        logger.error(f"Errore durante l'invio delle notifiche: {str(e)}")


if __name__ == "__main__":
    main()