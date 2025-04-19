# Aggregatore di Idee Business a Budget Zero

Questo progetto implementa un sistema automatizzato per raccogliere, analizzare e presentare idee di business da diverse fonti online, utilizzando esclusivamente strumenti gratuiti e open source.

## 🎯 Obiettivo del Progetto

Sviluppare un sistema che raccolga idee di business/prodotto da diverse fonti online, le analizzi attraverso un LLM, e presenti quelle più promettenti in una dashboard accessibile, tutto a costo zero.

## 🏗️ Architettura del Sistema

Il sistema è composto da quattro componenti principali:

### 🤖 Componente 1: Raccolta Dati
- **Tecnologia**: GitHub Actions + Python
- **Funzionalità**: Script di scraping per ProductHunt, Reddit, HackerNews, Hunt Screens, Aquaire.com
- **Caratteristiche**: Gestione resiliente con retry, rate limiting, normalizzazione dati

### 🧠 Componente 2: Analisi LLM
- **Tecnologia**: Ollama/LocalAI + Python
- **Funzionalità**: Analisi delle idee raccolte tramite modelli LLM open-source
- **Caratteristiche**: Deduplicazione, batch processing, prompt ottimizzati

### 💾 Componente 3: Storage
- **Tecnologia**: Supabase (piano gratuito) o SQLite + GitHub
- **Funzionalità**: Archiviazione delle idee raccolte e analizzate
- **Caratteristiche**: Schema ottimizzato, backup automatici, indici efficaci

### 🖥️ Componente 4: Frontend & Interazione
- **Tecnologia**: GitHub Pages + Vue.js
- **Funzionalità**: Visualizzazione e interazione con le idee raccolte
- **Caratteristiche**: SPA statica, autenticazione, dashboard interattiva, notifiche Telegram

## 📂 Struttura del Progetto

```
.
├── .github/workflows/       # Workflow GitHub Actions
├── scrapers/               # Script di scraping per le diverse fonti
├── analysis/               # Script per l'analisi LLM
├── database/               # Schema e script per il database
├── frontend/               # Codice frontend
├── config/                 # File di configurazione
└── docs/                   # Documentazione aggiuntiva
```

## 🚀 Setup e Deployment

1. Clona il repository
2. Configura le credenziali necessarie come segreti GitHub
3. Personalizza i file di configurazione in base alle tue esigenze
4. Attiva GitHub Actions per avviare il workflow di raccolta dati
5. Configura GitHub Pages per il deployment del frontend

## 📊 Funzionalità Principali

- Raccolta automatizzata di idee da diverse fonti
- Analisi e scoring delle idee tramite LLM
- Archiviazione efficiente dei dati
- Dashboard interattiva per esplorare le idee
- Notifiche per nuove idee promettenti

## ⚠️ Considerazioni su Privacy e Legalità

- Il sistema è progettato per rispettare i ToS delle piattaforme target
- Implementa rate limiting etico per non sovraccaricare le fonti
- Conforme al GDPR per i dati utente

## 🔧 Manutenzione e Troubleshooting

Consulta la documentazione nella cartella `docs/` per guide dettagliate su:
- Risoluzione problemi comuni
- Personalizzazione del sistema
- Best practices per l'estensione delle funzionalità