#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Reddit Scraper
Raccoglie idee di business da subreddit specifici utilizzando l'API ufficiale di Reddit tramite PRAW.
"""

import os
import time
import json
import praw
import backoff
from loguru import logger
from typing import List, Dict, Any
from datetime import datetime, timedelta


class RedditScraper:
    """
    Scraper per raccogliere idee di business da subreddit specifici.
    Utilizza PRAW per interagire con l'API di Reddit in modo sicuro e rispettoso dei rate limit.
    """
    
    def __init__(self, subreddits: List[str], time_filter: str = "week", 
                 limit: int = 100, min_score: int = 10):
        """
        Inizializza lo scraper di Reddit.
        
        Args:
            subreddits: Lista di subreddit da cui raccogliere idee
            time_filter: Filtro temporale (hour, day, week, month, year, all)
            limit: Numero massimo di post da raccogliere per subreddit
            min_score: Punteggio minimo (upvotes) per considerare un post
        """
        self.subreddits = subreddits
        self.time_filter = time_filter
        self.limit = limit
        self.min_score = min_score
        
        # Inizializza il client Reddit
        try:
            self.reddit = praw.Reddit(
                client_id=os.environ.get("REDDIT_CLIENT_ID"),
                client_secret=os.environ.get("REDDIT_CLIENT_SECRET"),
                user_agent=os.environ.get("REDDIT_USER_AGENT", "IdeaAggregator/1.0")
            )
            logger.info(f"Reddit client inizializzato con successo")
        except Exception as e:
            logger.error(f"Errore nell'inizializzazione del client Reddit: {str(e)}")
            raise
    
    @backoff.on_exception(backoff.expo, 
                          (praw.exceptions.PRAWException, Exception),
                          max_tries=3)
    def _fetch_subreddit_posts(self, subreddit_name: str) -> List[Dict[str, Any]]:
        """
        Raccoglie i post da un subreddit specifico con gestione degli errori e retry.
        
        Args:
            subreddit_name: Nome del subreddit
            
        Returns:
            Lista di post raccolti
        """
        logger.info(f"Raccolta post da r/{subreddit_name}")
        posts = []
        
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            
            # Ottieni i post in base al filtro temporale
            if self.time_filter == "all":
                submissions = subreddit.top(limit=self.limit)
            else:
                submissions = subreddit.top(time_filter=self.time_filter, limit=self.limit)
            
            for post in submissions:
                # Salta i post con punteggio troppo basso
                if post.score < self.min_score:
                    continue
                    
                # Estrai il testo completo (post + commenti principali)
                post_text = post.selftext if hasattr(post, 'selftext') else ""
                
                # Raccogli i commenti principali (solo i primi 5 più votati)
                top_comments = ""
                post.comment_sort = "top"
                post.comments.replace_more(limit=0)  # Non caricare commenti aggiuntivi
                for i, comment in enumerate(post.comments[:5]):
                    if hasattr(comment, 'body') and comment.score > 5:
                        top_comments += f"\n---\nCommento {i+1}: {comment.body}"
                
                # Crea l'oggetto post
                post_data = {
                    "title": post.title,
                    "description": post_text + top_comments if post_text else top_comments,
                    "url": f"https://www.reddit.com{post.permalink}",
                    "score": post.score,
                    "created_utc": datetime.fromtimestamp(post.created_utc).isoformat(),
                    "author": str(post.author) if post.author else "[deleted]",
                    "subreddit": subreddit_name,
                    "num_comments": post.num_comments
                }
                
                posts.append(post_data)
                
                # Rispetta i rate limit
                time.sleep(0.5)
                
            logger.success(f"Raccolti {len(posts)} post da r/{subreddit_name}")
            return posts
            
        except Exception as e:
            logger.error(f"Errore durante la raccolta da r/{subreddit_name}: {str(e)}")
            raise
    
    def run(self) -> List[Dict[str, Any]]:
        """
        Esegue lo scraper su tutti i subreddit configurati.
        
        Returns:
            Lista di idee raccolte da tutti i subreddit
        """
        all_posts = []
        
        for subreddit in self.subreddits:
            try:
                posts = self._fetch_subreddit_posts(subreddit)
                all_posts.extend(posts)
                # Pausa tra subreddit per rispettare i rate limit
                time.sleep(2)
            except Exception as e:
                logger.error(f"Impossibile raccogliere post da r/{subreddit}: {str(e)}")
                continue
        
        logger.info(f"Scraping Reddit completato. Raccolti {len(all_posts)} post totali")
        return all_posts


# Test dello scraper se eseguito direttamente
if __name__ == "__main__":
    # Configurazione di test
    test_subreddits = ["SomeoneShouldMake", "SaaS"]
    
    # Inizializza e esegui lo scraper
    scraper = RedditScraper(
        subreddits=test_subreddits,
        time_filter="month",
        limit=10,
        min_score=5
    )
    
    results = scraper.run()
    
    # Stampa i risultati
    print(f"Raccolti {len(results)} post")
    for i, post in enumerate(results[:3], 1):
        print(f"\n--- Post {i} ---")
        print(f"Titolo: {post['title']}")
        print(f"URL: {post['url']}")
        print(f"Punteggio: {post['score']}")