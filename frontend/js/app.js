/**
 * Aggregatore di Idee Business - Frontend Application
 * 
 * Applicazione Vue.js per visualizzare e interagire con le idee di business raccolte
 * dal sistema di aggregazione automatica.
 */

// Inizializzazione dell'app Vue
const { createApp, ref, computed, onMounted, watch } = Vue;

const app = createApp({
  setup() {
    // Stato dell'applicazione
    const ideas = ref([]);
    const loading = ref(true);
    const error = ref(null);
    const searchQuery = ref('');
    const currentFilter = ref('all');
    const currentSort = ref('score');
    const currentPage = ref(1);
    const itemsPerPage = ref(9);
    const selectedIdea = ref(null);
    const isAuthenticated = ref(false);
    const userFavorites = ref([]);
    
    // Stato per i modali
    const loginEmail = ref('');
    const loginPassword = ref('');
    const userComment = ref('');
    const userRating = ref(0);
    
    // Modali Bootstrap
    let ideaDetailsModal = null;
    let loginModal = null;
    
    // Inizializzazione dei modali dopo il mount del componente
    onMounted(() => {
      ideaDetailsModal = new bootstrap.Modal(document.getElementById('ideaDetailsModal'));
      loginModal = new bootstrap.Modal(document.getElementById('loginModal'));
      
      // Carica i dati
      fetchIdeas();
      
      // Controlla se l'utente è già autenticato
      checkAuthentication();
      
      // Carica i preferiti dell'utente
      if (isAuthenticated.value) {
        loadUserFavorites();
      }
    });
    
    // Computed properties
    const filteredIdeas = computed(() => {
      let result = [...ideas.value];
      
      // Applica la ricerca
      if (searchQuery.value) {
        const query = searchQuery.value.toLowerCase();
        result = result.filter(idea => 
          idea.title.toLowerCase().includes(query) || 
          idea.analysis.summary.toLowerCase().includes(query) ||
          idea.analysis.tags.some(tag => tag.toLowerCase().includes(query))
        );
      }
      
      // Applica i filtri
      switch (currentFilter.value) {
        case 'high_potential':
          result = result.filter(idea => idea.analysis.score >= 80);
          break;
        case 'low_difficulty':
          result = result.filter(idea => idea.analysis.difficulty === 'low');
          break;
        case 'large_market':
          result = result.filter(idea => idea.analysis.market_potential === 'large');
          break;
      }
      
      // Applica l'ordinamento
      switch (currentSort.value) {
        case 'score':
          result.sort((a, b) => b.analysis.score - a.analysis.score);
          break;
        case 'date':
          result.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
          break;
        case 'source':
          result.sort((a, b) => a.source.localeCompare(b.source));
          break;
      }
      
      return result;
    });
    
    // Paginazione
    const paginatedIdeas = computed(() => {
      const startIndex = (currentPage.value - 1) * itemsPerPage.value;
      const endIndex = startIndex + itemsPerPage.value;
      return filteredIdeas.value.slice(startIndex, endIndex);
    });
    
    const totalPages = computed(() => {
      return Math.ceil(filteredIdeas.value.length / itemsPerPage.value);
    });
    
    const paginationRange = computed(() => {
      const range = [];
      const maxVisiblePages = 5;
      
      if (totalPages.value <= maxVisiblePages) {
        // Mostra tutte le pagine
        for (let i = 1; i <= totalPages.value; i++) {
          range.push(i);
        }
      } else {
        // Logica per mostrare un sottoinsieme di pagine
        let startPage = Math.max(1, currentPage.value - 2);
        let endPage = Math.min(totalPages.value, startPage + maxVisiblePages - 1);
        
        if (endPage - startPage < maxVisiblePages - 1) {
          startPage = Math.max(1, endPage - maxVisiblePages + 1);
        }
        
        for (let i = startPage; i <= endPage; i++) {
          range.push(i);
        }
      }
      
      return range;
    });
    
    // Metodi
    const fetchIdeas = async () => {
      loading.value = true;
      error.value = null;
      
      try {
        // In un'implementazione reale, questa sarebbe una chiamata API
        // Per ora, utilizziamo dati di esempio
        const response = await fetch('data/ideas.json');
        if (!response.ok) {
          throw new Error('Errore nel caricamento delle idee');
        }
        
        const data = await response.json();
        ideas.value = data.map(idea => ({
          ...idea,
          isFavorite: userFavorites.value.includes(idea.id)
        }));
        
      } catch (err) {
        console.error('Errore:', err);
        error.value = err.message;
        
        // Dati di fallback per demo
        ideas.value = generateMockIdeas();
      } finally {
        loading.value = false;
      }
    };
    
    const showIdeaDetails = (idea) => {
      selectedIdea.value = idea;
      userComment.value = '';
      userRating.value = 0;
      ideaDetailsModal.show();
    };
    
    const showLoginModal = () => {
      loginEmail.value = '';
      loginPassword.value = '';
      loginModal.show();
    };
    
    const showRegisterForm = () => {
      // In un'implementazione reale, mostrerebbe il form di registrazione
      alert('Funzionalità di registrazione non implementata in questa demo');
    };
    
    const login = () => {
      // In un'implementazione reale, questa sarebbe una chiamata API
      if (loginEmail.value && loginPassword.value) {
        isAuthenticated.value = true;
        loginModal.hide();
        loadUserFavorites();
      }
    };
    
    const logout = () => {
      isAuthenticated.value = false;
      userFavorites.value = [];
    };
    
    const checkAuthentication = () => {
      // In un'implementazione reale, verificherebbe il token di autenticazione
      const token = localStorage.getItem('authToken');
      isAuthenticated.value = !!token;
    };
    
    const loadUserFavorites = () => {
      // In un'implementazione reale, questa sarebbe una chiamata API
      const storedFavorites = localStorage.getItem('userFavorites');
      if (storedFavorites) {
        userFavorites.value = JSON.parse(storedFavorites);
        
        // Aggiorna lo stato dei preferiti nelle idee
        ideas.value.forEach(idea => {
          idea.isFavorite = userFavorites.value.includes(idea.id);
        });
      }
    };
    
    const toggleFavorite = (idea) => {
      if (!isAuthenticated.value) {
        showLoginModal();
        return;
      }
      
      idea.isFavorite = !idea.isFavorite;
      
      if (idea.isFavorite) {
        userFavorites.value.push(idea.id);
      } else {
        userFavorites.value = userFavorites.value.filter(id => id !== idea.id);
      }
      
      // Salva i preferiti
      localStorage.setItem('userFavorites', JSON.stringify(userFavorites.value));
    };
    
    const shareIdea = (idea) => {
      // In un'implementazione reale, utilizzerebbe l'API Web Share
      if (navigator.share) {
        navigator.share({
          title: idea.title,
          text: idea.analysis.summary,
          url: idea.url
        });
      } else {
        // Fallback
        alert(`Condividi: ${idea.title}\n${idea.url}`);
      }
    };
    
    const rateIdea = (rating) => {
      userRating.value = rating;
    };
    
    const submitFeedback = () => {
      // In un'implementazione reale, questa sarebbe una chiamata API
      alert(`Feedback inviato! Valutazione: ${userRating.value}/5`);
      ideaDetailsModal.hide();
    };
    
    const changePage = (page) => {
      if (page >= 1 && page <= totalPages.value) {
        currentPage.value = page;
        window.scrollTo(0, 0);
      }
    };
    
    // Utility functions
    const formatSource = (source) => {
      return source || 'Fonte sconosciuta';
    };
    
    const formatDate = (dateString) => {
      if (!dateString) return 'Data sconosciuta';
      
      const date = new Date(dateString);
      return date.toLocaleDateString('it-IT', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
    };
    
    const getScoreBadgeClass = (score) => {
      if (score >= 80) return 'bg-success';
      if (score >= 60) return 'bg-primary';
      if (score >= 40) return 'bg-warning';
      return 'bg-danger';
    };
    
    const getScoreProgressClass = (score) => {
      if (score >= 80) return 'bg-success';
      if (score >= 60) return 'bg-primary';
      if (score >= 40) return 'bg-warning';
      return 'bg-danger';
    };
    
    // Genera dati di esempio per la demo
    const generateMockIdeas = () => {
      const mockIdeas = [
        {
          id: 1,
          title: "Piattaforma di micro-learning per professionisti",
          description: "Un'app che offre lezioni di 5 minuti su competenze professionali specifiche, con certificazioni riconosciute dalle aziende.",
          url: "https://example.com/idea1",
          source: "ProductHunt",
          timestamp: "2023-09-15T10:30:00Z",
          analysis: {
            score: 85,
            tags: ["EdTech", "Microlearning", "B2B"],
            summary: "Piattaforma di micro-corsi professionali con certificazioni aziendali integrate.",
            difficulty: "medium",
            market_potential: "large",
            insight: "Il mercato della formazione professionale continua è in forte crescita. Questa idea risponde alla necessità di apprendimento continuo con un formato adatto ai professionisti con poco tempo disponibile."
          },
          isFavorite: false
        },
        {
          id: 2,
          title: "Marketplace per eccedenze alimentari dei ristoranti",
          description: "App che permette ai ristoranti di vendere a prezzo ridotto il cibo invenduto a fine giornata, riducendo gli sprechi alimentari.",
          url: "https://example.com/idea2",
          source: "Reddit",
          timestamp: "2023-09-14T18:45:00Z",
          analysis: {
            score: 78,
            tags: ["FoodTech", "Sostenibilità", "Marketplace"],
            summary: "App per ridurre lo spreco alimentare nei ristoranti vendendo le eccedenze a prezzo ridotto.",
            difficulty: "medium",
            market_potential: "moderate",
            insight: "Combina sostenibilità e risparmio economico, due trend in crescita. Esistono già competitor, ma il mercato è ancora frammentato e c'è spazio per soluzioni innovative."
          },
          isFavorite: false
        },
        {
          id: 3,
          title: "Assistente AI per la gestione delle spese aziendali",
          description: "Software che automatizza la categorizzazione e l'approvazione delle spese aziendali utilizzando l'intelligenza artificiale.",
          url: "https://example.com/idea3",
          source: "HackerNews",
          timestamp: "2023-09-13T09:15:00Z",
          analysis: {
            score: 92,
            tags: ["FinTech", "AI", "B2B"],
            summary: "Software di gestione spese aziendali potenziato da AI per automatizzare l'intero processo.",
            difficulty: "high",
            market_potential: "large",
            insight: "La gestione delle spese è un punto dolente per molte aziende. L'automazione tramite AI può ridurre significativamente i costi amministrativi e migliorare la compliance."
          },
          isFavorite: false
        },
        {
          id: 4,
          title: "Piattaforma per noleggio attrezzature tra privati",
          description: "Marketplace che permette ai privati di noleggiare attrezzature poco utilizzate (trapani, tosaerba, ecc.) ad altri nella propria zona.",
          url: "https://example.com/idea4",
          source: "SomeoneShouldMake",
          timestamp: "2023-09-12T14:20:00Z",
          analysis: {
            score: 72,
            tags: ["Sharing Economy", "P2P", "Sostenibilità"],
            summary: "Marketplace P2P per il noleggio di attrezzature tra privati nella stessa area geografica.",
            difficulty: "medium",
            market_potential: "moderate",
            insight: "Sfrutta il trend della sharing economy e della sostenibilità. La sfida principale sarà la logistica e l'assicurazione degli oggetti."
          },
          isFavorite: false
        },
        {
          id: 5,
          title: "App per la gestione della salute mentale dei dipendenti",
          description: "Piattaforma B2B che offre strumenti di monitoraggio e supporto per la salute mentale dei dipendenti, con analisi anonimizzate per i datori di lavoro.",
          url: "https://example.com/idea5",
          source: "ProductHunt",
          timestamp: "2023-09-11T11:05:00Z",
          analysis: {
            score: 88,
            tags: ["HealthTech", "HR", "B2B"],
            summary: "Piattaforma per monitorare e supportare la salute mentale dei dipendenti con analytics per le aziende.",
            difficulty: "high",
            market_potential: "large",
            insight: "Il benessere mentale è diventato una priorità per molte aziende, specialmente dopo la pandemia. Questa soluzione offre un approccio data-driven mantenendo la privacy dei dipendenti."
          },
          isFavorite: false
        },
        {
          id: 6,
          title: "Servizio di abbonamento per riparazioni domestiche",
          description: "Abbonamento mensile che offre accesso illimitato a riparazioni domestiche di base (idraulica, elettricità, ecc.) per un prezzo fisso.",
          url: "https://example.com/idea6",
          source: "HuntScreens",
          timestamp: "2023-09-10T16:30:00Z",
          analysis: {
            score: 65,
            tags: ["Subscription", "Home Services", "B2C"],
            summary: "Servizio in abbonamento per riparazioni domestiche a prezzo fisso mensile.",
            difficulty: "high",
            market_potential: "moderate",
            insight: "Il modello subscription è attraente per i consumatori, ma la sfida sarà gestire i costi variabili delle riparazioni mantenendo la redditività."
          },
          isFavorite: false
        },
        {
          id: 7,
          title: "Piattaforma di micro-investimenti in startup locali",
          description: "App che permette di investire piccole somme in startup e piccole imprese locali, democratizzando l'accesso agli investimenti di venture capital.",
          url: "https://example.com/idea7",
          source: "Aquaire",
          timestamp: "2023-09-09T13:45:00Z",
          analysis: {
            score: 82,
            tags: ["FinTech", "Crowdfunding", "Local"],
            summary: "Piattaforma per micro-investimenti in startup e imprese locali accessibile a tutti.",
            difficulty: "high",
            market_potential: "large",
            insight: "Combina il trend del supporto alle economie locali con la democratizzazione degli investimenti. Le sfide principali saranno normative e di educazione finanziaria degli utenti."
          },
          isFavorite: false
        },
        {
          id: 8,
          title: "Assistente AI per la scrittura di contenuti tecnici",
          description: "Tool specializzato nella generazione e revisione di contenuti tecnici (documentazione software, manuali, specifiche tecniche) con AI.",
          url: "https://example.com/idea8",
          source: "HackerNews",
          timestamp: "2023-09-08T10:10:00Z",
          analysis: {
            score: 76,
            tags: ["AI", "Content", "B2B"],
            summary: "Tool AI specializzato nella creazione e revisione di documentazione tecnica e contenuti specialistici.",
            difficulty: "medium",
            market_potential: "moderate",
            insight: "La documentazione tecnica è spesso un collo di bottiglia nello sviluppo software. Un tool specializzato potrebbe differenziarsi dai generatori di contenuti generici."
          },
          isFavorite: false
        },
        {
          id: 9,
          title: "Marketplace per servizi di sostenibilità aziendale",
          description: "Piattaforma che connette aziende con consulenti e servizi specializzati in sostenibilità ambientale e reporting ESG.",
          url: "https://example.com/idea9",
          source: "ProductHunt",
          timestamp: "2023-09-07T15:20:00Z",
          analysis: {
            score: 79,
            tags: ["Sostenibilità", "B2B", "Marketplace"],
            summary: "Marketplace B2B che connette aziende con esperti di sostenibilità e servizi ESG.",
            difficulty: "medium",
            market_potential: "large",
            insight: "Con l'aumento delle normative ESG, molte aziende cercano supporto per adeguarsi. Un marketplace centralizzato potrebbe semplificare l'accesso a questi servizi."
          },
          isFavorite: false
        },
        {
          id: 10,
          title: "App per la gestione collaborativa dei condomini",
          description: "Piattaforma che semplifica la comunicazione e la gestione dei condomini, con funzionalità per votazioni, segnalazioni e gestione delle spese comuni.",
          url: "https://example.com/idea10",
          source: "SomeoneShouldMake",
          timestamp: "2023-09-06T09:30:00Z",
          analysis: {
            score: 68,
            tags: ["PropTech", "Community", "B2C"],
            summary: "App per semplificare la gestione e comunicazione nei condomini con funzionalità collaborative.",
            difficulty: "low",
            market_potential: "moderate",
            insight: "La gestione condominiale è spesso inefficiente e fonte di conflitti. Una soluzione digitale potrebbe migliorare significativamente l'esperienza, ma potrebbe essere difficile monetizzare."
          },
          isFavorite: false
        }
      ];
      
      return mockIdeas;
    };
    
    // Resetta la pagina quando cambiano i filtri o la ricerca
    watch([searchQuery, currentFilter, currentSort], () => {
      currentPage.value = 1;
    });
    
    return {
      // Stato
      ideas,
      loading,
      error,
      searchQuery,
      currentFilter,
      currentSort,
      currentPage,
      selectedIdea,
      isAuthenticated,
      loginEmail,
      loginPassword,
      userComment,
      
      // Computed
      filteredIdeas: paginatedIdeas,
      totalPages,
      paginationRange,
      
      // Metodi
      showIdeaDetails,
      showLoginModal,
      showRegisterForm,
      login,
      logout,
      toggleFavorite,
      shareIdea,
      rateIdea,
      submitFeedback,
      changePage,
      formatSource,
      formatDate,
      getScoreBadgeClass,
      getScoreProgressClass
    };
  }
});

app.mount('#app');