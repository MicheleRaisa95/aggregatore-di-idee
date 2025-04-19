# Guida Dettagliata all'Implementazione dell'Aggregatore di Idee Business

Questa guida fornisce istruzioni dettagliate per implementare ogni componente del sistema di aggregazione di idee business, con esempi di codice e spiegazioni approfondite.

## Indice
1. [Implementazione degli Scraper](#1-implementazione-degli-scraper)
2. [Configurazione dell'Analisi LLM](#2-configurazione-dellanalisi-llm)
3. [Setup del Database](#3-setup-del-database)
4. [Sviluppo del Frontend](#4-sviluppo-del-frontend)
5. [Automazione con GitHub Actions](#5-automazione-con-github-actions)

## 1. Implementazione degli Scraper

### 1.1 Scraper Reddit

Il file `scrapers/reddit.py` è già implementato. Ecco come personalizzarlo:

```python
# Modifica i parametri nel file config/settings.py
SCRAPER_CONFIG = {
    "Reddit": {
        "enabled": True,
        "params": {
            # Aggiungi o rimuovi subreddit in base alle tue esigenze
            "subreddits": ["SaaS", "microsaas", "SomeoneShouldMake", "Entrepreneur", "startups", "sidehustle"],
            "time_filter": "week",  # Puoi cambiare in "day", "month", ecc.
            "limit": 100,  # Numero massimo di post da raccogliere
            "min_score": 10  # Punteggio minimo per considerare un post
        }
    }
}
```

### 1.2 Implementazione di un Nuovo Scraper

Per aggiungere un nuovo scraper (es. ProductHunt), crea un file `scrapers/producthunt.py`:

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ProductHunt Scraper
Raccoglie idee di business da ProductHunt utilizzando web scraping.
"""

import os
import time
import json
import requests
from bs4 import BeautifulSoup
from loguru import logger
from typing import List, Dict, Any
from datetime import datetime
from fake_useragent import UserAgent
from retrying import retry


class ProductHuntScraper:
    """
    Scraper per raccogliere idee di business da ProductHunt.
    Utilizza BeautifulSoup per il parsing HTML e implementa rate limiting e retry.
    """
    
    def __init__(self, pages_to_scrape: int = 3, min_upvotes: int = 5, rate_limit: float = 1.5):
        """
        Inizializza lo scraper di ProductHunt.
        
        Args:
            pages_to_scrape: Numero di pagine da scrapare
            min_upvotes: Numero minimo di upvotes per considerare un prodotto
            rate_limit: Secondi di attesa tra le richieste
        """
        self.pages_to_scrape = pages_to_scrape
        self.min_upvotes = min_upvotes
        self.rate_limit = rate_limit
        self.user_agent = UserAgent()
        self.base_url = "https://www.producthunt.com"
        
        logger.info(f"ProductHunt scraper inizializzato: {pages_to_scrape} pagine, min {min_upvotes} upvotes")
    
    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def _fetch_page(self, url: str) -> str:
        """
        Scarica una pagina con retry in caso di errore.
        
        Args:
            url: URL della pagina da scaricare
            
        Returns:
            Contenuto HTML della pagina
        """
        headers = {"User-Agent": self.user_agent.random}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    
    def scrape(self) -> List[Dict[str, Any]]:
        """
        Esegue lo scraping di ProductHunt.
        
        Returns:
            Lista di prodotti trovati
        """
        products = []
        
        try:
            for page in range(1, self.pages_to_scrape + 1):
                url = f"{self.base_url}/?page={page}"
                logger.info(f"Scraping ProductHunt pagina {page}/{self.pages_to_scrape}")
                
                html = self._fetch_page(url)
                soup = BeautifulSoup(html, "lxml")
                
                # Trova i prodotti nella pagina
                product_cards = soup.select(".styles_item__Dk_nz")
                
                for card in product_cards:
                    try:
                        # Estrai informazioni del prodotto
                        title_elem = card.select_one(".styles_title__jWi91")
                        desc_elem = card.select_one(".styles_tagline__pQ_7U")
                        votes_elem = card.select_one(".styles_voteButtonWrap__NLsAE span")
                        link_elem = card.select_one("a[href^='/posts/']")
                        
                        if not all([title_elem, desc_elem, votes_elem, link_elem]):
                            continue
                        
                        title = title_elem.text.strip()
                        description = desc_elem.text.strip()
                        votes = int(votes_elem.text.strip())
                        relative_url = link_elem["href"]
                        product_url = f"{self.base_url}{relative_url}"
                        
                        # Controlla se il prodotto ha abbastanza upvotes
                        if votes < self.min_upvotes:
                            continue
                        
                        # Crea il dizionario del prodotto
                        product = {
                            "title": title,
                            "description": description,
                            "upvotes": votes,
                            "url": product_url,
                            "source": "ProductHunt",
                            "collected_at": datetime.now().isoformat()
                        }
                        
                        products.append(product)
                        logger.debug(f"Prodotto trovato: {title} ({votes} upvotes)")
                    
                    except Exception as e:
                        logger.warning(f"Errore nell'estrazione di un prodotto: {str(e)}")
                
                # Rispetta il rate limit
                time.sleep(self.rate_limit)
            
            logger.info(f"Scraping ProductHunt completato: {len(products)} prodotti trovati")
        
        except Exception as e:
            logger.error(f"Errore durante lo scraping di ProductHunt: {str(e)}")
        
        return products
```

Aggiorna poi `scrapers/main.py` per includere il nuovo scraper:

```python
# Aggiungi l'import
from scrapers.producthunt import ProductHuntScraper

# Nel metodo main o dove vengono eseguiti gli scraper
def run_scrapers():
    results = []
    
    # Esegui lo scraper ProductHunt se abilitato
    if SCRAPER_CONFIG["ProductHunt"]["enabled"]:
        params = SCRAPER_CONFIG["ProductHunt"]["params"]
        scraper = ProductHuntScraper(
            pages_to_scrape=params.get("pages_to_scrape", 3),
            min_upvotes=params.get("min_upvotes", 5),
            rate_limit=params.get("rate_limit", 1.5)
        )
        products = scraper.scrape()
        normalized_products = [normalize_data(p, "ProductHunt") for p in products]
        results.extend(normalized_products)
    
    # Altri scraper...
    
    return results
```

## 2. Configurazione dell'Analisi LLM

### 2.1 Configurazione di Ollama

Per utilizzare Ollama localmente:

1. Scarica e installa Ollama dal sito ufficiale: [https://ollama.ai/download](https://ollama.ai/download)
2. Avvia Ollama e scarica un modello adatto all'analisi di testo:

```bash
# Per Windows, apri PowerShell e esegui
ollama pull llama2

# Oppure per un modello più leggero
ollama pull mistral
```

### 2.2 Personalizzazione dei Prompt LLM

Modifica il file `analysis/process.py` per personalizzare i prompt utilizzati per l'analisi:

```python
def generate_analysis_prompt(idea):
    """
    Genera il prompt per l'analisi di un'idea.
    
    Args:
        idea: Dizionario contenente i dati dell'idea
        
    Returns:
        Prompt formattato per l'LLM
    """
    return f"""
    Analizza la seguente idea di business e fornisci una valutazione strutturata:
    
    TITOLO: {idea['title']}
    DESCRIZIONE: {idea['description']}
    FONTE: {idea['source']}
    
    Rispondi con un JSON nel seguente formato:
    {{"analysis": "Analisi dettagliata dell'idea",
     "score": "Punteggio da 0.0 a 1.0 basato su fattibilità, innovazione e potenziale di mercato",
     "pros": ["Lista dei punti di forza"],
     "cons": ["Lista dei punti deboli"],
     "tags": ["Lista di tag/categorie pertinenti"]}}
    """
```

### 2.3 Ottimizzazione del Batch Processing

Per migliorare l'efficienza dell'analisi LLM, implementa il batch processing:

```python
def process_ideas_in_batches(ideas, batch_size=10):
    """
    Processa le idee in batch per ottimizzare l'analisi LLM.
    
    Args:
        ideas: Lista di idee da processare
        batch_size: Dimensione di ogni batch
        
    Returns:
        Lista di idee processate con analisi LLM
    """
    processed_ideas = []
    total_batches = (len(ideas) + batch_size - 1) // batch_size
    
    for i in range(0, len(ideas), batch_size):
        batch = ideas[i:i+batch_size]
        batch_num = (i // batch_size) + 1
        
        logger.info(f"Processando batch {batch_num}/{total_batches} ({len(batch)} idee)")
        
        # Processa ogni idea nel batch
        for idea in batch:
            processed_idea = process_single_idea(idea)
            if processed_idea:
                processed_ideas.append(processed_idea)
        
        # Breve pausa tra i batch per non sovraccaricare l'LLM
        if batch_num < total_batches:
            time.sleep(1)
    
    return processed_ideas
```

## 3. Setup del Database

### 3.1 Configurazione di Supabase

1. Crea un account gratuito su [Supabase](https://supabase.com/)
2. Crea un nuovo progetto
3. Nella sezione SQL Editor, esegui il seguente script per creare la tabella delle idee:

```sql
-- Crea la tabella principale per le idee
CREATE TABLE public.ideas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    description TEXT,
    source TEXT NOT NULL,
    source_url TEXT,
    upvotes INTEGER,
    score FLOAT,
    analysis TEXT,
    pros TEXT[],
    cons TEXT[],
    tags TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Crea indici per migliorare le performance
CREATE INDEX idx_ideas_score ON public.ideas(score DESC);
CREATE INDEX idx_ideas_source ON public.ideas(source);
CREATE INDEX idx_ideas_created_at ON public.ideas(created_at DESC);

-- Crea una tabella per le interazioni degli utenti
CREATE TABLE public.user_interactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id),
    idea_id UUID REFERENCES public.ideas(id),
    interaction_type TEXT NOT NULL, -- 'favorite', 'view', 'hide'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Crea un indice per le interazioni
CREATE INDEX idx_user_interactions ON public.user_interactions(user_id, idea_id);

-- Abilita RLS (Row Level Security)
ALTER TABLE public.ideas ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_interactions ENABLE ROW LEVEL SECURITY;

-- Crea policy per permettere a tutti di leggere le idee
CREATE POLICY "Ideas are viewable by everyone" 
    ON public.ideas FOR SELECT USING (true);

-- Crea policy per permettere agli utenti autenticati di interagire
CREATE POLICY "Users can manage their own interactions" 
    ON public.user_interactions 
    USING (auth.uid() = user_id);
```

4. Ottieni l'URL e la chiave API dal pannello di controllo (Settings > API)
5. Aggiungi queste informazioni al file `.env`:

```
SUPABASE_URL=https://tuo-progetto.supabase.co
SUPABASE_KEY=tua-chiave-api
```

### 3.2 Implementazione dell'Archiviazione Dati

Modifica il file `database/store.py` per ottimizzare l'archiviazione:

```python
def store_ideas_batch(ideas, batch_size=50):
    """
    Archivia un batch di idee nel database.
    
    Args:
        ideas: Lista di idee da archiviare
        batch_size: Dimensione di ogni batch
    """
    total_ideas = len(ideas)
    total_batches = (total_ideas + batch_size - 1) // batch_size
    
    for i in range(0, total_ideas, batch_size):
        batch = ideas[i:i+batch_size]
        batch_num = (i // batch_size) + 1
        
        logger.info(f"Archiviando batch {batch_num}/{total_batches} ({len(batch)} idee)")
        
        try:
            # Per Supabase
            if self.db_type == "supabase":
                # Prepara i dati per l'inserimento
                data = [{
                    "title": idea["title"],
                    "description": idea["description"],
                    "source": idea["source"],
                    "source_url": idea.get("url", ""),
                    "upvotes": idea.get("upvotes", 0),
                    "score": idea.get("score", 0.0),
                    "analysis": idea.get("analysis", ""),
                    "pros": idea.get("pros", []),
                    "cons": idea.get("cons", []),
                    "tags": idea.get("tags", [])
                } for idea in batch]
                
                # Inserisci i dati con upsert (aggiorna se esiste già)
                result = self.supabase.table("ideas").upsert(
                    data, 
                    on_conflict="source,source_url"
                ).execute()
                
                if hasattr(result, "error") and result.error:
                    logger.error(f"Errore nell'archiviazione su Supabase: {result.error}")
                else:
                    logger.info(f"Batch {batch_num} archiviato con successo su Supabase")
            
            # Per SQLite
            else:
                # Implementazione per SQLite...
        
        except Exception as e:
            logger.error(f"Errore nell'archiviazione del batch {batch_num}: {str(e)}")
        
        # Breve pausa tra i batch
        if batch_num < total_batches:
            time.sleep(0.5)
```

## 4. Sviluppo del Frontend

### 4.1 Implementazione della Dashboard

Modifica il file `frontend/js/app.js` per implementare la dashboard interattiva:

```javascript
// Configurazione Vue.js
const app = Vue.createApp({
  data() {
    return {
      ideas: [],
      filteredIdeas: [],
      isLoading: true,
      error: null,
      searchQuery: '',
      currentFilter: 'all',
      sortOption: 'score',
      isAuthenticated: false,
      user: null,
      favorites: [],
      showLoginModal: false,
      loginEmail: '',
      loginPassword: '',
      registerEmail: '',
      registerPassword: '',
      authError: null
    }
  },
  
  computed: {
    // Idee filtrate e ordinate
    displayedIdeas() {
      // Filtra in base alla ricerca
      let result = this.ideas.filter(idea => {
        const searchLower = this.searchQuery.toLowerCase();
        return (
          idea.title.toLowerCase().includes(searchLower) ||
          idea.description.toLowerCase().includes(searchLower) ||
          (idea.tags && idea.tags.some(tag => tag.toLowerCase().includes(searchLower)))
        );
      });
      
      // Filtra per categoria
      if (this.currentFilter !== 'all') {
        result = result.filter(idea => {
          return idea.tags && idea.tags.includes(this.currentFilter);
        });
      }
      
      // Ordina le idee
      result.sort((a, b) => {
        if (this.sortOption === 'score') {
          return b.score - a.score;
        } else if (this.sortOption === 'date') {
          return new Date(b.created_at) - new Date(a.created_at);
        } else if (this.sortOption === 'upvotes') {
          return b.upvotes - a.upvotes;
        }
        return 0;
      });
      
      return result;
    },
    
    // Categorie uniche per i filtri
    uniqueCategories() {
      const categories = new Set();
      this.ideas.forEach(idea => {
        if (idea.tags) {
          idea.tags.forEach(tag => categories.add(tag));
        }
      });
      return Array.from(categories).sort();
    }
  },
  
  methods: {
    // Carica le idee dal database
    async loadIdeas() {
      this.isLoading = true;
      this.error = null;
      
      try {
        // Per Supabase
        const { data, error } = await supabase
          .from('ideas')
          .select('*')
          .order('score', { ascending: false });
        
        if (error) throw error;
        
        this.ideas = data;
        this.isLoading = false;
      } catch (err) {
        console.error('Errore nel caricamento delle idee:', err);
        this.error = 'Impossibile caricare le idee. Riprova più tardi.';
        this.isLoading = false;
      }
    },
    
    // Gestione autenticazione
    async login() {
      this.authError = null;
      
      try {
        const { user, error } = await supabase.auth.signIn({
          email: this.loginEmail,
          password: this.loginPassword
        });
        
        if (error) throw error;
        
        this.user = user;
        this.isAuthenticated = true;
        this.showLoginModal = false;
        this.loadFavorites();
      } catch (err) {
        this.authError = err.message || 'Errore durante il login';
      }
    },
    
    // Altre funzioni...
  },
  
  mounted() {
    // Carica le idee all'avvio
    this.loadIdeas();
    
    // Controlla se l'utente è già autenticato
    const user = supabase.auth.user();
    if (user) {
      this.user = user;
      this.isAuthenticated = true;
      this.loadFavorites();
    }
  }
});

// Monta l'app
app.mount('#app');
```

### 4.2 Implementazione del CSS

Modifica il file `frontend/css/style.css` per migliorare l'aspetto della dashboard:

```css
:root {
  --primary-color: #4361ee;
  --secondary-color: #3f37c9;
  --accent-color: #4cc9f0;
  --text-color: #333;
  --light-bg: #f8f9fa;
  --card-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  color: var(--text-color);
  background-color: var(--light-bg);
  line-height: 1.6;
}

/* Card delle idee */
.idea-card {
  border-radius: 8px;
  box-shadow: var(--card-shadow);
  transition: transform 0.2s, box-shadow 0.2s;
  overflow: hidden;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.idea-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1);
}

.idea-card .card-header {
  background-color: var(--primary-color);
  color: white;
  padding: 1rem;
}

.idea-card .card-body {
  flex: 1;
  padding: 1.5rem;
}

.idea-card .card-footer {
  padding: 1rem;
  background-color: rgba(0, 0, 0, 0.03);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* Tag e badge */
.tag {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  border-radius: 50px;
  background-color: var(--accent-color);
  color: white;
  font-size: 0.75rem;
  margin-right: 0.5rem;
  margin-bottom: 0.5rem;
}

.score-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 3rem;
  height: 3rem;
  border-radius: 50%;
  background-color: var(--primary-color);
  color: white;
  font-weight: bold;
  font-size: 1.2rem;
}

/* Animazioni e transizioni */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

/* Responsive */
@media (max-width: 768px) {
  .idea-card {
    margin-bottom: 1.5rem;
  }
  
  .filters-container {
    flex-direction: column;
  }
  
  .filters-container > div {
    margin-bottom: 1rem;
  }
}
```

## 5. Automazione con GitHub Actions

### 5.1 Configurazione del Workflow Completo

Modifica il file `.github/workflows/scraper_workflow.yml` per implementare un workflow completo:

```yaml
name: Idea Scraper Workflow

on:
  schedule:
    # Esegui ogni giorno alle 2:00 UTC
    - cron: '0 2 * * *'
  workflow_dispatch: # Permette l'esecuzione manuale

jobs:
  scrape_and_analyze:
    runs-on: ubuntu-latest
    timeout-minutes: 30 # Limita il tempo di esecuzione
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      
      - name: Run scrapers
        run: python scrapers/main.py
        env:
          REDDIT_CLIENT_ID: ${{ secrets.REDDIT_CLIENT_ID }}
          REDDIT_CLIENT_SECRET: ${{ secrets.REDDIT_CLIENT_SECRET }}
          REDDIT_USER_AGENT: ${{ secrets.REDDIT_USER_AGENT }}
      
      - name: Set up Ollama
        run: |
          # Scarica e installa Ollama
          curl -fsSL https://ollama.ai/install.sh | sh
          # Scarica il modello
          ollama pull mistral:7b-instruct-v0.2-q4_K_M
      
      - name: Process and analyze data
        run: python analysis/process.py
      
      - name: Store results in database
        run: python database/store.py
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
      
      - name: Send notifications
        run: python analysis/notify.py
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
      
      - name: Generate static data for GitHub Pages
        run: |
          mkdir -p docs/data
          python -c "import json; import sqlite3; conn = sqlite3.connect('data/ideas.db'); cursor = conn.cursor(); cursor.execute('SELECT * FROM ideas ORDER BY score DESC LIMIT 500'); columns = [col[0] for col in cursor.description]; data = [dict(zip(columns, row)) for row in cursor.fetchall()]; json.dump(data, open('docs/data/ideas.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)"
      
      - name: Copy frontend to docs
        run: |
          cp -r frontend/* docs/
          # Aggiorna il percorso API nel file app.js
          sed -i 's|const API_ENDPOINT = .*|const API_ENDPOINT = "./data/ideas.json";|g' docs/js/app.js
      
      - name: Commit and push changes
        run: |
          git config --global user.name 'GitHub Actions'
          git config --global user.email 'actions@github.com'
          git add docs/
          git commit -m "Update data and frontend $(date +'%Y-%m-%d')" || echo "No changes to commit"
          git push
```

### 5.2 Configurazione delle Notifiche Telegram

Implementa il file `analysis/notify.py` per inviare notifiche delle idee migliori:

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
from config.settings import NOTIFICATION_CONFIG, DATA_DIR

# Configurazione Telegram
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def load_processed_ideas():
    """
    Carica le idee processate dal file JSON più recente.
    
    Returns:
        Lista di idee processate
    ""