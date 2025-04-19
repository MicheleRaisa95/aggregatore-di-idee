# Tutorial: Implementazione dell'Aggregatore di Idee Business a Budget Zero

Questo tutorial ti guiderà passo dopo passo nell'implementazione completa del sistema di aggregazione di idee business, utilizzando esclusivamente strumenti gratuiti e open source.

## Indice
1. [Preparazione dell'ambiente](#1-preparazione-dellambiente)
2. [Configurazione degli scraper](#2-configurazione-degli-scraper)
3. [Implementazione dell'analisi LLM](#3-implementazione-dellanalisi-llm)
4. [Configurazione del database](#4-configurazione-del-database)
5. [Deployment del frontend](#5-deployment-del-frontend)
6. [Configurazione di GitHub Actions](#6-configurazione-di-github-actions)
7. [Test e monitoraggio](#7-test-e-monitoraggio)

## 1. Preparazione dell'ambiente

### 1.1 Requisiti di sistema
- Python 3.10 o superiore
- Git
- Account GitHub
- Ollama (per LLM locale) o LocalAI

### 1.2 Installazione delle dipendenze

```bash
# Clona il repository (se non l'hai già fatto)
git clone <url-del-tuo-repository>
cd progetto-se4freto

# Crea e attiva un ambiente virtuale (opzionale ma consigliato)
python -m venv venv
# Su Windows
venv\Scripts\activate
# Su macOS/Linux
source venv/bin/activate

# Installa le dipendenze
pip install -r requirements.txt
```

### 1.3 Struttura delle directory

Assicurati che la struttura del progetto sia la seguente:

```
.
├── .github/workflows/       # Workflow GitHub Actions
├── scrapers/               # Script di scraping
├── analysis/               # Script per l'analisi LLM
├── database/               # Schema e script per il database
├── frontend/               # Codice frontend
├── config/                 # File di configurazione
├── data/                   # Directory per i dati raccolti (creata automaticamente)
└── docs/                   # Documentazione aggiuntiva
```

## 2. Configurazione degli scraper

### 2.1 Configurazione delle API keys

Per Reddit, dovrai creare un'applicazione su Reddit per ottenere le credenziali API:

1. Vai su [Reddit Developer](https://www.reddit.com/prefs/apps)
2. Crea una nuova applicazione di tipo "script"
3. Prendi nota di client_id e client_secret

Crea un file `.env` nella root del progetto con le seguenti variabili:

```
REDDIT_CLIENT_ID=il_tuo_client_id
REDDIT_CLIENT_SECRET=il_tuo_client_secret
REDDIT_USER_AGENT=IdeaAggregator/1.0
```

### 2.2 Personalizzazione degli scraper

Modifica il file `config/settings.py` per personalizzare i parametri degli scraper:

```python
# Esempio: modifica i subreddit da monitorare
SCRAPER_CONFIG = {
    "Reddit": {
        "enabled": True,
        "params": {
            "subreddits": ["SaaS", "microsaas", "SomeoneShouldMake", "startups"],
            "time_filter": "week",
            "limit": 100,
            "min_score": 10
        }
    },
    # Altri scraper...
}
```

### 2.3 Test degli scraper

Esegui un test degli scraper per verificare che funzionino correttamente:

```bash
python scrapers/main.py
```

I dati raccolti verranno salvati nella directory `data/raw/`.

## 3. Implementazione dell'analisi LLM

### 3.1 Installazione di Ollama

1. Scarica e installa [Ollama](https://ollama.ai/download) per il tuo sistema operativo
2. Esegui il seguente comando per scaricare un modello adatto (ad esempio Llama2):

```bash
ollama pull llama2
```

### 3.2 Configurazione dell'analisi LLM

Modifica il file `config/settings.py` per configurare i parametri LLM:

```python
LLM_CONFIG = {
    "model": "llama2",  # o altro modello disponibile su Ollama
    "endpoint": "http://localhost:11434/api/generate",  # Endpoint Ollama predefinito
    "temperature": 0.7,
    "max_tokens": 500,
    "batch_size": 10,  # Numero di idee da processare in batch
    "deduplication": {
        "enabled": True,
        "threshold": 80  # Soglia di similarità (0-100)
    }
}
```

### 3.3 Test dell'analisi LLM

Assicurati che Ollama sia in esecuzione, poi esegui:

```bash
python analysis/process.py
```

I risultati dell'analisi verranno salvati nella directory `data/processed/`.

## 4. Configurazione del database

### 4.1 Opzione 1: Supabase (Piano gratuito)

1. Crea un account gratuito su [Supabase](https://supabase.com/)
2. Crea un nuovo progetto
3. Ottieni l'URL e la chiave API dal pannello di controllo
4. Aggiungi queste informazioni al file `.env`:

```
SUPABASE_URL=https://tuo-progetto.supabase.co
SUPABASE_KEY=tua-chiave-api
```

5. Crea la tabella necessaria eseguendo la seguente query SQL nell'editor SQL di Supabase:

```sql
CREATE TABLE ideas (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  title TEXT NOT NULL,
  description TEXT,
  source TEXT NOT NULL,
  source_url TEXT,
  score FLOAT,
  analysis TEXT,
  tags TEXT[],
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indice per ricerche più veloci
CREATE INDEX idx_ideas_score ON ideas(score DESC);
CREATE INDEX idx_ideas_source ON ideas(source);
```

### 4.2 Opzione 2: SQLite (Locale)

Se preferisci utilizzare SQLite, modifica `config/settings.py`:

```python
DB_CONFIG = {
    "type": "sqlite",
    "path": os.path.join(DATA_DIR, "ideas.db")
}
```

Il database SQLite verrà creato automaticamente quando esegui:

```bash
python database/store.py
```

## 5. Deployment del frontend

### 5.1 Configurazione del frontend

Modifica il file `frontend/js/app.js` per configurare l'endpoint API:

```javascript
// Per Supabase
const supabaseUrl = 'https://tuo-progetto.supabase.co';
const supabaseKey = 'tua-chiave-api-pubblica';
const supabase = createClient(supabaseUrl, supabaseKey);

// Oppure per API locale/GitHub Pages
const API_ENDPOINT = 'https://tuo-username.github.io/tuo-repository/data/ideas.json';
```

### 5.2 Test locale del frontend

Per testare il frontend localmente:

```bash
python -m http.server 8000 --directory frontend
```

Visita `http://localhost:8000` nel tuo browser.

### 5.3 Deployment su GitHub Pages

1. Assicurati che il repository sia pubblico
2. Vai su Settings > Pages
3. Seleziona la branch `main` e la cartella `/docs` o `/frontend`
4. Clicca su Save

In alternativa, puoi configurare un workflow GitHub Actions per il deployment automatico.

## 6. Configurazione di GitHub Actions

### 6.1 Configurazione dei segreti GitHub

1. Vai su Settings > Secrets and variables > Actions
2. Aggiungi i seguenti segreti:
   - `REDDIT_CLIENT_ID`
   - `REDDIT_CLIENT_SECRET`
   - `REDDIT_USER_AGENT`
   - `SUPABASE_URL` (se usi Supabase)
   - `SUPABASE_KEY` (se usi Supabase)
   - `TELEGRAM_BOT_TOKEN` (per le notifiche)
   - `TELEGRAM_CHAT_ID` (per le notifiche)

### 6.2 Personalizzazione del workflow

Il file `.github/workflows/scraper_workflow.yml` è già configurato per eseguire gli scraper, l'analisi e l'archiviazione ogni giorno. Puoi modificare la pianificazione cambiando la configurazione cron:

```yaml
on:
  schedule:
    # Esegui ogni giorno alle 2:00 UTC
    - cron: '0 2 * * *'
```

### 6.3 Attivazione del workflow

1. Commit e push di tutte le modifiche
2. Vai su Actions nel repository GitHub
3. Seleziona il workflow "Idea Scraper Workflow"
4. Clicca su "Run workflow" per eseguirlo manualmente la prima volta

## 7. Test e monitoraggio

### 7.1 Verifica del funzionamento

Dopo l'esecuzione del workflow, verifica che:

1. I dati siano stati raccolti correttamente (controlla i file nella directory `data/raw/`)
2. L'analisi LLM sia stata eseguita (controlla i file nella directory `data/processed/`)
3. I dati siano stati archiviati nel database (controlla Supabase o il file SQLite)
4. Il frontend visualizzi correttamente le idee

### 7.2 Configurazione delle notifiche Telegram

1. Crea un bot Telegram usando [BotFather](https://t.me/botfather)
2. Ottieni il token del bot
3. Crea un gruppo o un canale e aggiungi il bot
4. Ottieni l'ID del chat
5. Aggiungi queste informazioni ai segreti GitHub

### 7.3 Personalizzazione delle notifiche

Modifica il file `analysis/notify.py` per personalizzare il formato e i criteri delle notifiche:

```python
# Esempio: invia notifiche solo per idee con score > 0.8
ideas_to_notify = [idea for idea in processed_ideas if idea.get('score', 0) > 0.8]
```

## Conclusione

Complimenti! Hai implementato con successo un sistema completo di aggregazione di idee business a budget zero. Il sistema ora raccoglierà automaticamente idee da diverse fonti, le analizzerà tramite LLM, le archivierà nel database e le presenterà nel frontend.

Per estendere ulteriormente il sistema, puoi:

- Aggiungere nuovi scraper per altre fonti
- Migliorare i prompt LLM per un'analisi più accurata
- Implementare funzionalità aggiuntive nel frontend (filtri, ordinamento, ecc.)
- Configurare un sistema di feedback per migliorare l'analisi nel tempo

Ricorda di monitorare regolarmente i log e le esecuzioni del workflow per assicurarti che tutto funzioni correttamente.