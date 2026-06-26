(function () {
  'use strict';

  const STATE = {
    sessionId: null,
    history: [],
    theme: localStorage.getItem('tp-theme') || 'light',
    isWaiting: false,
    typingTimer: null,
    typingIndex: 0,
    factTimer: null,
    factShowTimer: null,
    factIndex: 0,
  };

  const TYPING_MESSAGES = [
    'Analizando tu consulta',
    'Buscando opciones de viaje',
    'Consultando destinos',
    'Planificando itinerario',
    'Organizando actividades',
    'Casi listo',
  ];

  const SPAIN_FACTS = [
    '¿Sabías que el español es el segundo idioma más hablado del mundo, con más de 500 millones de hablantes nativos?',
    '¿Sabías que Cuenca tiene rascacielos medievales colgados sobre el borde de un barranco?',
    '¿Sabías que el desierto de Tabernas en Almería es el único desierto real de Europa?',
    '¿Sabías que España tiene más bares por habitante que ningún otro país de la Unión Europea?',
    '¿Sabías que La Sagrada Família lleva más de 140 años en construcción y aún no ha terminado?',
    '¿Sabías que el flamenco es Patrimonio Cultural Inmaterial de la Humanidad desde 2010?',
    '¿Sabías que España tiene la red de Alta Velocidad ferroviaria más extensa de Europa?',
    '¿Sabías que la paella nació en Valencia y la original lleva conejo y pollo, no marisco?',
    '¿Sabías que el Camino de Santiago tiene más de 1.200 años de historia y cruza toda Europa?',
    '¿Sabías que Toledo fue capital de España antes que Madrid, durante la época visigoda?',
    '¿Sabías que España es el tercer país más visitado del mundo, con casi 90 millones de turistas al año?',
    '¿Sabías que el País Vasco tiene más estrellas Michelin por habitante que ningún otro lugar del planeta?',
    '¿Sabías que el acueducto de Segovia lleva en pie más de 2.000 años sin usar argamasa?',
    '¿Sabías que Sevilla es la ciudad más calurosa de la Europa continental, con picos de 47\xBAC?',
    '¿Sabías que las cuevas de Altamira tienen pinturas rupestres de hace más de 36.000 años?',
    '¿Sabías que la Alhambra de Granada es el monumento más visitado de España con más de 2 millones de visitas?',
    '¿Sabías que en la Tomatina de Buñol se lanzan cada agosto más de 150.000 kg de tomates?',
    '¿Sabías que el Museo del Prado es uno de los 10 museos de arte más importantes del mundo?',
    '¿Sabías que Granada fue el último reino moro en caer en 1492, el mismo año que Colón llegó a América?',
    '¿Sabías que España tiene más de 50 sitios declarados Patrimonio Mundial por la UNESCO?',
  ];

  const GREETINGS = {
    morning: 'Buenos d\u00edas',
    afternoon: 'Buenas tardes',
    evening: 'Buenas noches',
  };

  /* ─── Conversation Storage ─── */
  const ConversationStorage = {
    STORAGE_KEY: 'travelplanner_history',
    MAX_SESSIONS: 10,
    
    saveConversation(sessionId, destination, messages) {
      if (!sessionId || !messages.length) return;

      const existing = this.loadConversations().filter(c => c.sessionId !== sessionId);

      const session = {
        sessionId: sessionId,
        destination: destination || 'Sin destino',
        createdAt: Date.now(),
        messages: messages.map(m => ({
          role: m.role,
          text: m.text,
          time: m.time
        }))
      };

      existing.unshift(session);
      existing.splice(this.MAX_SESSIONS);

      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(existing));
    },
    
    loadConversations() {
      const data = localStorage.getItem(this.STORAGE_KEY);
      return data ? JSON.parse(data) : [];
    },
    
    deleteConversation(sessionId) {
      const conversations = this.loadConversations();
      const filtered = conversations.filter(c => c.sessionId !== sessionId);
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(filtered));
    }
  };

  /* ─── DOM refs ─── */
  const $ = (s) => document.querySelector(s);
  const $$ = (s) => document.querySelectorAll(s);

  const el = {
    messages: $('#messages'),
    welcome: $('#welcome'),
    input: $('#input'),
    sendBtn: $('#sendBtn'),
    typing: $('#typingIndicator'),
    typingText: $('#typingText'),
    resetBtn: $('#resetBtn'),
    homeBtn: $('#homeBtn'),
    homeBrand: $('#homeBrand'),
    menuToggle: $('#menuToggle'),
    sidebar: $('#sidebar'),
    overlay: $('#overlay'),
    toast: $('#toast'),
    greeting: $('#greeting'),
    currentDest: $('#currentDest'),
    themeToggle: $('#themeToggle'),
    darkModeToggle: $('#darkModeToggle'),
    statusText: $('#statusText'),
    chatView: $('#chatView'),
    historyView: $('#historyView'),
    settingsView: $('#settingsView'),
    historyList: $('#historyList'),
    chips: $('#chips'),
    ragView: $('#ragView'),
    ragStats: $('#ragStats'),
    statChunks: $('#statChunks'),
    statDocs: $('#statDocs'),
    ollamaDot: $('#ollamaDot'),
    ollamaLabel: $('#ollamaLabel'),
    dropzone: $('#dropzone'),
    fileInput: $('#fileInput'),
    docCategory: $('#docCategory'),
    docCity: $('#docCity'),
    uploadBtn: $('#uploadBtn'),
    uploadProgress: $('#uploadProgress'),
    uploadProgressBar: $('#uploadProgressBar'),
    uploadProgressText: $('#uploadProgressText'),
    docList: $('#docList'),
    docSearch: $('#docSearch'),
    refreshDocsBtn: $('#refreshDocsBtn'),
    reindexBtn: $('#reindexBtn'),
    testQuery: $('#testQuery'),
    testSearchBtn: $('#testSearchBtn'),
    testResults: $('#testResults'),
  };

  /* ─── Init ─── */
  function init() {
    setTheme(STATE.theme);
    setGreeting();
    setupSidebarNav();
    setupThemeToggle();
    setupInput();
    setupButtons();
    setupChips();
    setupRAG();
    startSession();
    
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') {
        ModalManager.closeAllModals();
      }
    });
  }

  /* ─── Greeting ─── */
  function setGreeting() {
    const h = new Date().getHours();
    let key = 'afternoon';
    if (h < 12) key = 'morning';
    else if (h >= 20) key = 'evening';
    el.greeting.textContent = GREETINGS[key];
  }

  /* ─── Theme ─── */
  function setTheme(theme) {
    STATE.theme = theme;
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('tp-theme', theme);
    if (el.darkModeToggle) el.darkModeToggle.checked = theme === 'dark';
  }

  function toggleTheme() {
    setTheme(STATE.theme === 'light' ? 'dark' : 'light');
  }

  function setupThemeToggle() {
    el.themeToggle.addEventListener('click', toggleTheme);
    el.darkModeToggle.addEventListener('change', function () {
      setTheme(this.checked ? 'dark' : 'light');
    });
  }

  /* ─── Sidebar Nav ─── */
  function setupSidebarNav() {
    $$('.sidebar__item[data-modal]').forEach(function (item) {
      item.addEventListener('click', function () {
        const modalId = this.dataset.modal;
        ModalManager.openModal(modalId);
        closeSidebar();
      });
    });

    el.menuToggle.addEventListener('click', toggleSidebar);
    el.overlay.addEventListener('click', closeSidebar);
  }

  function toggleSidebar() { el.sidebar.classList.toggle('open'); el.overlay.classList.toggle('open'); }
  function closeSidebar() { el.sidebar.classList.remove('open'); el.overlay.classList.remove('open'); }

  /* ─── Modal Manager ─── */
  const ModalManager = {
    openModal(modalId) {
      const backdrop = document.getElementById(modalId);
      if (!backdrop) return;
      backdrop.removeAttribute('hidden');
      backdrop.style.display = 'flex';
      backdrop.style.opacity = '0';
      
      setTimeout(() => {
        backdrop.style.transition = 'opacity 0.2s ease';
        backdrop.style.opacity = '1';
      }, 10);
      
      const closeBtn = backdrop.querySelector('.modal-close');
      if (closeBtn) {
        closeBtn.addEventListener('click', () => this.closeModal(modalId), { once: true });
      }
      backdrop.addEventListener('click', (e) => {
        if (e.target === backdrop) this.closeModal(modalId);
      }, { once: true });
      
      const handleEsc = (e) => {
        if (e.key === 'Escape') {
          this.closeModal(modalId);
          document.removeEventListener('keydown', handleEsc);
        }
      };
      document.addEventListener('keydown', handleEsc);
      
      if (modalId === 'modal-history') renderHistory();
      if (modalId === 'modal-rag') refreshRAG();
    },
    
    closeModal(modalId) {
      const backdrop = document.getElementById(modalId);
      if (!backdrop) return;
      const content = backdrop.querySelector('.modal-content');
      if (content) {
        content.classList.add('closing');
        setTimeout(() => {
          backdrop.setAttribute('hidden', '');
          backdrop.style.display = 'none';
          content.classList.remove('closing');
        }, 200);
      } else {
        backdrop.setAttribute('hidden', '');
        backdrop.style.display = 'none';
      }
    },
    
    closeAllModals() {
      const modals = $$('.modal-backdrop:not([hidden])');
      modals.forEach((m) => this.closeModal(m.id));
    }
  };

  function showView(view) {
    if (view === 'history') renderHistory();
    if (view === 'rag') refreshRAG();
  }

  /* ─── Session ─── */
  async function startSession() {
    try {
      const res = await fetch('/session/create', { method: 'POST' });
      if (!res.ok) throw new Error('HTTP ' + res.status);
      const data = await res.json();
      STATE.sessionId = data.session_id;
      el.statusText.textContent = 'Conectado';
    } catch (e) {
      el.statusText.textContent = 'Sin conexi\u00f3n';
    }
  }

  /* ─── Reset ─── */
  async function resetSession() {
    if (STATE.sessionId && STATE.history.length > 0) {
      ConversationStorage.saveConversation(
        STATE.sessionId,
        el.currentDest.textContent || 'Sin destino',
        STATE.history
      );
    }
    
    if (STATE.sessionId) {
      try { await fetch('/session/' + STATE.sessionId + '/reset', { method: 'POST' }); } catch (e) { /* ignore */ }
    }
    el.messages.innerHTML = '';
    STATE.history = [];
    STATE.sessionId = null;
    stopTyping();
    el.currentDest.textContent = '';
    await startSession();

    const welcomeHTML =
      '<div class="welcome__logo"><img src="/ui/travelimg.jpg" alt="TravelPlanner"></div>' +
      '<h1 class="welcome__title">Nueva conversaci\u00f3n</h1>' +
      '<p class="welcome__desc">Cu\u00e9ntame a d\u00f3nde quieres viajar</p>';
    const div = document.createElement('div');
    div.className = 'welcome';
    div.id = 'welcome';
    div.style.animation = 'none';
    div.innerHTML = welcomeHTML;
    el.messages.appendChild(div);
    el.currentDest.textContent = '';
  }

  /* ─── Send ─── */
  async function sendMessage() {
    const text = el.input.value.trim();
    if (!text || STATE.isWaiting) return;

    STATE.isWaiting = true;
    el.sendBtn.disabled = true;
    removeWelcome();
    appendMessage('user', text);
    el.input.value = '';
    el.input.style.height = 'auto';
    startTyping();

    if (!STATE.sessionId) await startSession();

    if (!STATE.sessionId) {
      stopTyping();
      appendMessage('bot', 'No se pudo conectar con el servidor. Verifica que est\u00e9 corriendo.');
      STATE.isWaiting = false;
      el.sendBtn.disabled = false;
      return;
    }

    try {
      const res = await fetch('/chat/' + STATE.sessionId, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text }),
      });

      if (!res.ok) throw new Error('HTTP ' + res.status);

      const contentType = res.headers.get('content-type') || '';
      if (contentType.includes('text/event-stream')) {
        await consumeStream(res, text);
      } else {
        const data = await res.json();
        stopTyping();
        const reply = data.response || 'El servidor no devolvi\u00f3 una respuesta v\u00e1lida.';
        appendMessage('bot', reply);
        updateDestFromResponse(text, reply);
      }
    } catch (err) {
      stopTyping();
      appendMessage('bot', 'Error de conexi\u00f3n. Aseg\u00farate de que el servidor est\u00e9 corriendo en el puerto 8000.');
    }

    STATE.isWaiting = false;
    el.sendBtn.disabled = false;
    el.input.focus();
  }

  /* \u2500\u2500\u2500 Stream consumer \u2500\u2500\u2500 */
  async function consumeStream(res, userText) {
    var reader = res.body.getReader();
    var decoder = new TextDecoder();
    var buffer = '';
    var fullText = '';
    var msgDiv = null;
    var firstToken = true;

    try {
      while (true) {
        var chunk = await reader.read();
        if (chunk.done) break;

        buffer += decoder.decode(chunk.value, { stream: true });
        var lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (var i = 0; i < lines.length; i++) {
          var line = lines[i];
          if (!line.startsWith('data: ')) continue;
          var raw = line.slice(6).trim();
          if (raw === '[DONE]') continue;

          var token;
          try { token = JSON.parse(raw).token; } catch (e) { continue; }
          if (!token) continue;

          if (firstToken) {
            stopTyping();
            firstToken = false;
            msgDiv = createBotMessageDiv();
          }

          fullText += token;
          if (msgDiv) {
            msgDiv.innerHTML = renderMarkdown(fullText);
            el.messages.scrollTop = el.messages.scrollHeight;
          }
        }
      }
    } catch (e) { /* network error mid-stream */ }

    if (firstToken) stopTyping();

    if (msgDiv) {
      msgDiv.innerHTML = renderMarkdown(fullText);
      var timeEl = document.createElement('span');
      timeEl.className = 'msg__time';
      timeEl.textContent = formatTime(new Date());
      msgDiv.appendChild(timeEl);
      el.messages.scrollTop = el.messages.scrollHeight;
    }

    if (fullText) {
      STATE.history.push({ role: 'bot', text: fullText, time: Date.now() });
      updateDestFromResponse(userText, fullText);
    }
  }

  function createBotMessageDiv() {
    var div = document.createElement('div');
    div.className = 'msg msg--bot';
    el.messages.appendChild(div);
    el.messages.scrollTop = el.messages.scrollHeight;
    return div;
  }

  /* ─── Extract dest from text ─── */
  function extractDest(text) {
    const match = text.match(/(?:viajar\s+a|visit(?:ar)?\s+|ir\s+a|a\s+)([A-Za-z\u00c0-\u024f]+(?:\s+[A-Za-z\u00c0-\u024f]+)?)/i);
    return match ? match[1].trim() : null;
  }

  function updateDestFromResponse(inputText, responseText) {
    const dest = extractDest(inputText || '');
    if (dest) {
      el.currentDest.textContent = dest.charAt(0).toUpperCase() + dest.slice(1);
    } else {
      const match = responseText.match(/##\s+(.+?)\s*\u2014/);
      if (match) el.currentDest.textContent = match[1].trim();
    }
  }

  /* ─── Append message ─── */
  function appendMessage(role, text) {
    const div = document.createElement('div');
    div.className = 'msg msg--' + role;

    if (role === 'bot') {
      div.innerHTML = renderMarkdown(text);
    } else {
      div.textContent = text;
    }

    const time = document.createElement('span');
    time.className = 'msg__time';
    time.textContent = formatTime(new Date());
    div.appendChild(time);

    el.messages.appendChild(div);
    el.messages.scrollTop = el.messages.scrollHeight;

    STATE.history.push({ role: role, text: text, time: Date.now() });
  }

  /* ─── Markdown render ─── */
  function renderMarkdown(text) {
    var html = text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');

    html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
    html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
    html = html.replace(/^# (.+)$/gm, '<h2>$1</h2>');

    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');

    html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
    html = html.replace(/(<li>[\s\S]*?<\/li>(\s*<li>[\s\S]*?<\/li>)*)/g, function (m) {
      return '<ul>' + m + '</ul>';
    });

    html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');
    html = html.replace(/(<li>[\s\S]*?<\/li>(\s*<li>[\s\S]*?<\/li>)*)/g, function (m) {
      return '<ol>' + m + '</ol>';
    });

    html = html.replace(/D\u00eda \d+/g, function (m) {
      return '<br><strong>' + m + '</strong>';
    });

    html = html.replace(/\n/g, '<br>');
    html = html.replace(/(<br>)+<\/ul>/g, '</ul>');
    html = html.replace(/(<br>)+<\/ol>/g, '</ol>');
    html = html.replace(/<\/ul><br>/g, '</ul>');
    html = html.replace(/<\/ol><br>/g, '</ol>');
    html = html.replace(/<br><ul>/g, '<ul>');
    html = html.replace(/<br><ol>/g, '<ol>');
    html = html.replace(/<br>(<h[1-3]>)/g, '$1');
    html = html.replace(/(<h[1-3]>)/g, '<br>$1');
    html = html.replace(/<br><br>/g, '<br>');
    html = html.replace(/^<br>/, '');
    html = html.replace(/<br>$/, '');

    return html;
  }

  /* ─── Time formatting ─── */
  function formatTime(date) {
    return date.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });
  }

  function formatDate(date) {
    return date.toLocaleDateString('es-ES', { day: 'numeric', month: 'short' });
  }

  /* ─── Typing ─── */
  function startTyping() {
    STATE.typingIndex = 0;
    STATE.factIndex = Math.floor(Math.random() * SPAIN_FACTS.length);
    el.typing.classList.add('active');
    el.typingText.textContent = TYPING_MESSAGES[0] + '...';

    STATE.typingTimer = setInterval(function () {
      STATE.typingIndex = (STATE.typingIndex + 1) % TYPING_MESSAGES.length;
      el.typingText.textContent = TYPING_MESSAGES[STATE.typingIndex] + '...';
    }, 2500);

    STATE.factShowTimer = setTimeout(function () {
      showFact();
      STATE.factTimer = setInterval(showFact, 9000);
    }, 2200);
  }

  function showFact() {
    var factCard = document.getElementById('typingFact');
    var factText = document.getElementById('typingFactText');
    if (!factCard || !factText) return;

    STATE.factIndex = (STATE.factIndex + 1) % SPAIN_FACTS.length;

    if (factCard.hasAttribute('hidden')) {
      factText.textContent = SPAIN_FACTS[STATE.factIndex];
      factCard.removeAttribute('hidden');
    } else {
      factCard.style.opacity = '0';
      factCard.style.transform = 'translateY(8px)';
      setTimeout(function () {
        factText.textContent = SPAIN_FACTS[STATE.factIndex];
        factCard.style.opacity = '1';
        factCard.style.transform = 'translateY(0)';
      }, 460);
    }
  }

  function stopTyping() {
    el.typing.classList.remove('active');
    clearInterval(STATE.typingTimer);
    STATE.typingTimer = null;
    clearTimeout(STATE.factShowTimer);
    STATE.factShowTimer = null;
    clearInterval(STATE.factTimer);
    STATE.factTimer = null;
    var factCard = document.getElementById('typingFact');
    if (factCard) factCard.setAttribute('hidden', '');
  }

  /* ─── Welcome ─── */
  function removeWelcome() {
    if (el.welcome) {
      el.welcome.remove();
      el.welcome = null;
    }
  }

  /* ─── Input ─── */
  function setupInput() {
    el.input.addEventListener('input', function () {
      this.style.height = 'auto';
      this.style.height = Math.min(this.scrollHeight, 100) + 'px';
      el.sendBtn.disabled = this.value.trim().length === 0 || STATE.isWaiting;
    });

    el.input.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });

    el.sendBtn.addEventListener('click', sendMessage);
  }

  /* ─── Buttons ─── */
  async function goHome() {
    if (STATE.sessionId && STATE.history.length > 0) {
      ConversationStorage.saveConversation(
        STATE.sessionId,
        el.currentDest.textContent || 'Sin destino',
        STATE.history
      );
    }
    if (STATE.sessionId) {
      try { await fetch('/session/' + STATE.sessionId + '/reset', { method: 'POST' }); } catch (e) {}
    }
    window.location.reload();
  }

  function setupButtons() {
    el.resetBtn.addEventListener('click', resetSession);
    el.homeBtn.addEventListener('click', goHome);
    el.homeBrand.addEventListener('click', function () { goHome(); closeSidebar(); });
    el.homeBrand.addEventListener('keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') { goHome(); closeSidebar(); } });
    
    window.addEventListener('beforeunload', function () {
      if (STATE.sessionId && STATE.history.length > 0) {
        ConversationStorage.saveConversation(
          STATE.sessionId,
          el.currentDest.textContent || 'Sin destino',
          STATE.history
        );
      }
    });
  }

  /* ─── Chips ─── */
  function setupChips() {
    el.chips.addEventListener('click', function (e) {
      var chip = e.target.closest('.chip');
      if (!chip) return;
      var text = chip.getAttribute('data-text');
      if (text) {
        el.input.value = text;
        sendMessage();
      }
    });
  }

  /* ─── History ─── */
  function renderHistory() {
    el.historyList.innerHTML = '';
    const conversations = ConversationStorage.loadConversations();
    
    if (!conversations.length) {
      el.historyList.innerHTML = '<div class="history__empty">' +
        '<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" opacity="0.3">' +
        '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>' +
        '<p>A\u00fan no hay sesiones guardadas</p></div>';
      return;
    }

    conversations.slice(0, 10).forEach(function (session) {
      var div = document.createElement('div');
      div.className = 'history__item';
      div.style.cursor = 'pointer';

      var date = new Date(session.createdAt);
      var timeStr = formatDate(date) + ' ' + date.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });

      var deleteBtn = document.createElement('button');
      deleteBtn.className = 'history__item-delete';
      deleteBtn.title = 'Eliminar conversaci\u00F3n';
      deleteBtn.innerHTML = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4h6v2"/></svg>';
      deleteBtn.addEventListener('click', function (e) {
        e.stopPropagation();
        deleteSession(session.sessionId);
      });

      div.innerHTML =
        '<span class="history__item-icon">' +
        '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>' +
        '</span>' +
        '<div class="history__item-info">' +
        '<div class="history__item-title">' + esc(session.destination) + '</div>' +
        '<div class="history__item-meta">' + timeStr + ' \u00B7 ' + session.messages.length + ' mensajes</div>' +
        '</div>';

      div.appendChild(deleteBtn);

      div.addEventListener('click', function () {
        loadConversationSession(session);
        ModalManager.closeModal('modal-history');
      });

      el.historyList.appendChild(div);
    });
  }

  async function deleteSession(sessionId) {
    try {
      await fetch('/session/' + sessionId, { method: 'DELETE' });
    } catch (e) { /* si la sesión ya no existe en el servidor, ignorar */ }
    ConversationStorage.deleteConversation(sessionId);
    // Evitar que beforeunload vuelva a guardar esta sesión si es la activa
    if (STATE.sessionId === sessionId) {
      STATE.history = [];
      STATE.sessionId = null;
    }
    renderHistory();
    showToast('Conversación eliminada');
  }

  function loadConversationSession(session) {
    el.messages.innerHTML = '';
    STATE.history = [];
    stopTyping();
    
    session.messages.forEach(function (msg) {
      appendMessage(msg.role, msg.text);
    });
    
    el.currentDest.textContent = session.destination;
    STATE.sessionId = session.sessionId;
    
    el.messages.scrollTop = el.messages.scrollHeight;
  }

  /* ─── RAG Admin ─── */
  function setupRAG() {
    el.dropzone.addEventListener('click', function () { el.fileInput.click(); });
    el.dropzone.addEventListener('dragover', function (e) { e.preventDefault(); el.dropzone.classList.add('ragadmin__dropzone--active'); });
    el.dropzone.addEventListener('dragleave', function () { el.dropzone.classList.remove('ragadmin__dropzone--active'); });
    el.dropzone.addEventListener('drop', function (e) { e.preventDefault(); el.dropzone.classList.remove('ragadmin__dropzone--active'); if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]); });
    el.fileInput.addEventListener('change', function () { if (el.fileInput.files.length) handleFile(el.fileInput.files[0]); });
    el.uploadBtn.addEventListener('click', uploadDocument);
    el.refreshDocsBtn.addEventListener('click', refreshRAG);
    el.reindexBtn.addEventListener('click', reindexAll);
    el.docSearch.addEventListener('input', filterDocs);
    el.testSearchBtn.addEventListener('click', testSearch);
    el.testQuery.addEventListener('keydown', function (e) { if (e.key === 'Enter') testSearch(); });
    checkOllamaHealth();
    setInterval(checkOllamaHealth, 30000);
  }

  async function checkOllamaHealth() {
    var dot = el.ollamaDot;
    var label = el.ollamaLabel;
    if (!dot) return;
    try {
      var res = await fetch('/health/ollama');
      if (!res.ok) throw new Error('HTTP ' + res.status);
      var data = await res.json();
      if (data.status === 'connected') {
        dot.className = 'ragadmin__stat-indicator ragadmin__stat-indicator--ok';
        label.textContent = 'Ollama conectado';
      } else {
        dot.className = 'ragadmin__stat-indicator ragadmin__stat-indicator--err';
        label.textContent = 'Ollama no disponible';
      }
    } catch (e) {
      dot.className = 'ragadmin__stat-indicator ragadmin__stat-indicator--err';
      label.textContent = 'Ollama no disponible';
    }
  }

  var _pendingFile = null;

  function handleFile(file) {
    var allowed = ['.pdf', '.txt', '.md', '.csv'];
    var ext = file.name.slice(file.name.lastIndexOf('.')).toLowerCase();
    if (allowed.indexOf(ext) === -1) { showToast('Formato no permitido: ' + ext); return; }
    _pendingFile = file;
    el.uploadBtn.disabled = false;
    el.dropzone.querySelector('p').textContent = file.name;
    el.dropzone.querySelector('.ragadmin__dropzone-hint').textContent = (file.size / 1024).toFixed(1) + ' KB';
  }

  async function uploadDocument() {
    if (!_pendingFile) return;
    el.uploadBtn.disabled = true;
    el.uploadProgress.hidden = false;

    var form = new FormData();
    form.append('file', _pendingFile);
    form.append('category', el.docCategory.value);
    form.append('city', el.docCity.value || '');

    try {
      var res = await fetch('/rag/upload', { method: 'POST', body: form });
      if (!res.ok) throw new Error('HTTP ' + res.status);
      var upData = await res.json();
      el.uploadProgressText.textContent = 'Indexado (' + (upData.chunks || '?') + ' chunks)';
      showToast('Documento subido e indexado');
      _pendingFile = null;
      el.uploadBtn.disabled = true;
      el.dropzone.querySelector('p').textContent = 'Arrastra un archivo aqu\u00ED o haz clic para seleccionar';
      el.dropzone.querySelector('.ragadmin__dropzone-hint').textContent = 'PDF, TXT, MD, CSV';
      refreshRAG();
    } catch (e) {
      showToast('Error al subir: ' + e.message);
    } finally {
      el.uploadProgress.hidden = true;
    }
  }

  async function refreshRAG() {
    el.ragView.hidden = false;
    loadStats();
    loadDocuments();
  }

  async function loadStats() {
    try {
      var res = await fetch('/rag/stats');
      if (!res.ok) throw new Error('HTTP ' + res.status);
      var data = await res.json();
      el.statChunks.textContent = data.total_chunks || 0;
      el.statDocs.textContent = (data.documents && data.documents.length) || 0;
    } catch (e) {
      el.statChunks.textContent = '?';
      el.statDocs.textContent = '?';
    }
  }

  async function loadDocuments() {
    try {
      var res = await fetch('/rag/documents');
      if (!res.ok) throw new Error('HTTP ' + res.status);
      var data = await res.json();
      renderDocuments(data.documents || []);
    } catch (e) {
      el.docList.innerHTML = '<p class="ragadmin__empty">Error cargando documentos</p>';
    }
  }

  function renderDocuments(docs) {
    if (!docs.length) {
      el.docList.innerHTML = '<p class="ragadmin__empty">No hay documentos indexados</p>';
      return;
    }
    var html = '';
    var filter = el.docSearch.value.toLowerCase();
    docs.forEach(function (d) {
      if (filter && d.name.toLowerCase().indexOf(filter) === -1) return;
      html +=
        '<div class="ragadmin__doc-item" data-path="' + d.path + '">' +
        '<div class="ragadmin__doc-info">' +
        '<span class="ragadmin__doc-name">' + esc(d.name) + '</span>' +
        '<span class="ragadmin__doc-meta">' + esc(d.category) + (d.city ? ' \u00B7 ' + esc(d.city) : '') + ' \u00B7 ' + (d.size / 1024).toFixed(1) + ' KB</span>' +
        '</div>' +
        '<button class="ragadmin__doc-delete" onclick="deleteDoc(\'' + d.path.replace(/'/g, "\\'") + '\')">Eliminar</button>' +
        '</div>';
    });
    if (!html) html = '<p class="ragadmin__empty">Sin resultados</p>';
    el.docList.innerHTML = html;
  }

  function filterDocs() { loadDocuments(); }

  window.deleteDoc = async function (path) {
    if (!confirm('\u00BFEliminar ' + path + '?')) return;
    try {
      var res = await fetch('/rag/document?path=' + encodeURIComponent(path), { method: 'DELETE' });
      if (!res.ok) throw new Error('HTTP ' + res.status);
      showToast('Documento eliminado');
      refreshRAG();
    } catch (e) {
      showToast('Error: ' + e.message);
    }
  };

  async function reindexAll() {
    el.reindexBtn.disabled = true;
    el.reindexBtn.textContent = 'Indexando...';
    try {
      var res = await fetch('/rag/reindex', { method: 'POST' });
      if (!res.ok) throw new Error('HTTP ' + res.status);
      var data = await res.json();
      showToast('Indexaci\u00F3n completa: ' + (data.chunks || 0) + ' chunks');
      refreshRAG();
    } catch (e) {
      showToast('Error: ' + e.message);
    } finally {
      el.reindexBtn.disabled = false;
      el.reindexBtn.textContent = 'Reindexar todo';
    }
  }

  async function testSearch() {
    var q = el.testQuery.value.trim();
    if (!q) return;
    el.testResults.innerHTML = '<p class="ragadmin__empty">Buscando...</p>';
    try {
      var res = await fetch('/rag/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: 'query=' + encodeURIComponent(q) + '&k=5',
      });
      if (!res.ok) throw new Error('HTTP ' + res.status);
      var data = await res.json();
      var results = data.results || [];
      if (!results.length) {
        el.testResults.innerHTML = '<p class="ragadmin__empty">Sin resultados</p>';
        return;
      }
      var html = results.map(function (r, i) {
        var cat = (r.metadata && r.metadata.categoria) || '';
        var score = r.score != null ? ' (' + r.score.toFixed(2) + ')' : '';
        return '<div class="ragadmin__test-item"><strong>#' + (i + 1) + score + '</strong> ' + esc(r.content.slice(0, 300)) + '<div class="ragadmin__doc-meta">' + esc(cat) + '</div></div>';
      }).join('');
      el.testResults.innerHTML = html;
    } catch (e) {
      el.testResults.innerHTML = '<p class="ragadmin__empty">Error: ' + e.message + '</p>';
    }
  }

  function esc(s) {
    var d = document.createElement('div');
    d.appendChild(document.createTextNode(s));
    return d.innerHTML;
  }

  /* ─── Toast ─── */
  function showToast(msg) {
    el.toast.textContent = msg;
    el.toast.classList.add('show');
    setTimeout(function () { el.toast.classList.remove('show'); }, 2500);
  }

  /* ─── Boot ─── */
  document.addEventListener('DOMContentLoaded', init);

})();
