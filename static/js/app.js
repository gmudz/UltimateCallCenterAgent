/**
 * AI Sales Copilot — Frontend Application
 * Real-time WebSocket client for the agent dashboard.
 */

// ---- State ----
let ws = null;
let isConnected = false;
let isDemoRunning = false;
let segmentCount = 0;
let battleCardsShown = new Set();
let currentSpeaker = 'client';
let callStartTime = null;
let timerInterval = null;
let callData = { clientType: null, objections: [], violations: [], segments: 0, clientName: '' };

// ---- Speech Recognition State ----
let recognition = null;
let isMicActive = false;
let audioContext = null;
let analyser = null;
let micStream = null;

function initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        console.warn('Web Speech API not supported');
        const micBtn = document.getElementById('micBtn');
        if (micBtn) {
            micBtn.style.opacity = '0.4';
            micBtn.title = 'غير مدعوم في هذا المتصفح — استخدم Chrome';
        }
        return;
    }

    recognition = new SpeechRecognition();
    recognition.lang = 'ar-SA';
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;

    let finalTranscript = '';
    let silenceTimer = null;

    recognition.onresult = (event) => {
        let interim = '';
        finalTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
                finalTranscript += transcript;
            } else {
                interim += transcript;
            }
        }

        // Show interim text
        const interimEl = document.getElementById('micInterim');
        if (interimEl) interimEl.textContent = interim || '';

        // Send final transcript
        if (finalTranscript.trim().length > 3) {
            clearTimeout(silenceTimer);
            sendSpeechText(finalTranscript.trim());
            if (interimEl) interimEl.textContent = '';
        }
    };

    recognition.onerror = (event) => {
        console.warn('Speech error:', event.error);
        if (event.error === 'no-speech') return; // Normal — just silence
        if (event.error === 'aborted') return;
        if (event.error === 'not-allowed') {
            showToast('❌ الميكروفون ممنوع — اسمح بالوصول من إعدادات المتصفح');
            stopMic();
        }
    };

    recognition.onend = () => {
        // Auto-restart if mic is still active
        if (isMicActive) {
            try { recognition.start(); } catch (e) { }
        }
    };
}

function toggleMic() {
    if (isMicActive) {
        stopMic();
    } else {
        startMic();
    }
}

async function startMic() {
    if (!recognition) initSpeechRecognition();
    if (!recognition) {
        showToast('❌ المتصفح لا يدعم التعرف على الصوت — استخدم Chrome');
        return;
    }

    try {
        // Get microphone access for audio level visualization
        micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const source = audioContext.createMediaStreamSource(micStream);
        analyser = audioContext.createAnalyser();
        analyser.fftSize = 256;
        source.connect(analyser);
        visualizeAudioLevel();
    } catch (e) {
        console.warn('Audio visualizer failed:', e);
    }

    try {
        recognition.start();
        isMicActive = true;

        // UI updates
        const micBtn = document.getElementById('micBtn');
        micBtn.classList.add('active');
        document.getElementById('micIcon').textContent = '🔴';
        document.getElementById('micLabel').textContent = 'إيقاف الميكروفون';
        document.getElementById('micStatus').style.display = 'flex';

        if (!callStartTime) startTimer();
        showToast('🎙️ الميكروفون شغال — تحدث الآن');
    } catch (e) {
        showToast('❌ فشل تشغيل الميكروفون');
        console.error(e);
    }
}

function stopMic() {
    isMicActive = false;
    if (recognition) {
        try { recognition.stop(); } catch (e) { }
    }
    if (micStream) {
        micStream.getTracks().forEach(t => t.stop());
        micStream = null;
    }
    if (audioContext) {
        audioContext.close();
        audioContext = null;
    }

    // UI updates
    const micBtn = document.getElementById('micBtn');
    micBtn.classList.remove('active');
    document.getElementById('micIcon').textContent = '🎙️';
    document.getElementById('micLabel').textContent = 'تشغيل الميكروفون';
    document.getElementById('micStatus').style.display = 'none';
    document.getElementById('micInterim').textContent = '';
    document.getElementById('micLevel').style.width = '0%';
}

function visualizeAudioLevel() {
    if (!analyser || !isMicActive) return;
    const data = new Uint8Array(analyser.frequencyBinCount);
    analyser.getByteFrequencyData(data);
    const avg = data.reduce((a, b) => a + b, 0) / data.length;
    const level = Math.min(100, (avg / 128) * 100);
    document.getElementById('micLevel').style.width = level + '%';
    requestAnimationFrame(visualizeAudioLevel);
}

function sendSpeechText(text) {
    if (!ws || !isConnected) return;
    ws.send(JSON.stringify({ action: 'process_text', speaker: currentSpeaker, text }));
    if (!callStartTime) startTimer();
}

// ---- Init ----
document.addEventListener('DOMContentLoaded', () => {
    connectWebSocket();
    loadMarketData();
    loadCurrentUser();
    document.getElementById('speedControl').addEventListener('input', e => {
        document.getElementById('speedLabel').textContent = e.target.value + 'x';
    });
});

// ---- Auth ----
async function loadCurrentUser() {
    try {
        const res = await fetch('/api/me');
        if (res.status === 401) return;
        const data = await res.json();
        if (data.user) {
            const el = document.getElementById('currentUserName');
            if (el) el.textContent = data.user.display_name;
            // Show admin-only links
            if (data.user.role === 'admin') {
                const usersLink = document.getElementById('usersLink');
                if (usersLink) usersLink.style.display = '';
            } else {
                // Hide admin links for agents
                const adminLink = document.getElementById('adminLink');
                if (adminLink) adminLink.style.display = 'none';
                const usersLink = document.getElementById('usersLink');
                if (usersLink) usersLink.style.display = 'none';
            }
        }
    } catch (e) { }
}

async function logoutUser() {
    await fetch('/api/logout', { method: 'POST' });
    window.location.href = '/login';
}

// ---- WebSocket ----
function connectWebSocket() {
    const protocol = location.protocol === 'https:' ? 'wss' : 'ws';
    ws = new WebSocket(`${protocol}://${location.host}/ws/call/agent-001`);
    ws.onopen = () => { isConnected = true; updateStatus('متصل', 'connected'); };
    ws.onclose = () => { isConnected = false; updateStatus('غير متصل', 'disconnected'); setTimeout(connectWebSocket, 3000); };
    ws.onerror = () => { updateStatus('خطأ في الاتصال', 'disconnected'); };
    ws.onmessage = (event) => { handleMessage(JSON.parse(event.data)); };
}

function handleMessage(data) {
    switch (data.type) {
        case 'connected': loadScenarios(data.scenarios); break;
        case 'demo_started': onDemoStarted(); break;
        case 'demo_stopped': onDemoStopped(); break;
        case 'analysis': processAnalysis(data); break;
        case 'call_ended': onCallEnded(data); break;
        case 'knowledge_results': displayKnowledgeResults(data.results); break;
        case 'feedback_received': showToast('تم تسجيل التقييم ✓'); break;
    }
}

// ---- Status ----
function updateStatus(text, state) {
    document.getElementById('statusText').textContent = text;
    const dot = document.getElementById('statusDot');
    dot.className = 'status-dot';
    if (state === 'disconnected') dot.classList.add('disconnected');
    else if (state === 'active') dot.classList.add('active');
}

// ---- Call Timer ----
function startTimer() {
    callStartTime = Date.now();
    document.getElementById('callTimer').classList.add('active');
    timerInterval = setInterval(() => {
        const elapsed = Math.floor((Date.now() - callStartTime) / 1000);
        const m = String(Math.floor(elapsed / 60)).padStart(2, '0');
        const s = String(elapsed % 60).padStart(2, '0');
        document.getElementById('timerDisplay').textContent = `${m}:${s}`;
    }, 1000);
}

function stopTimer() {
    clearInterval(timerInterval);
    document.getElementById('callTimer').classList.remove('active');
}

function getCallDuration() {
    if (!callStartTime) return '00:00';
    const elapsed = Math.floor((Date.now() - callStartTime) / 1000);
    const m = String(Math.floor(elapsed / 60)).padStart(2, '0');
    const s = String(elapsed % 60).padStart(2, '0');
    return `${m}:${s}`;
}

// ---- Scenarios ----
function loadScenarios(scenarios) {
    const select = document.getElementById('scenarioSelect');
    select.innerHTML = '<option value="">— اختر سيناريو المكالمة —</option>';
    if (!scenarios) return;
    scenarios.forEach(s => {
        const opt = document.createElement('option');
        opt.value = s.id;
        const typeLabel = { emotional: 'عاطفي', analyst: 'محلل', leader: 'قائد', nice: 'لطيف' }[s.client_type] || s.client_type;
        opt.textContent = `${s.client_name} — ${typeLabel} (${s.dialect})`;
        select.appendChild(opt);
    });
    // Auto-select from URL params (from training page)
    const params = new URLSearchParams(window.location.search);
    const preselect = params.get('scenario');
    if (preselect) {
        select.value = preselect;
        if (params.get('mode') === 'training') {
            showToast('🎓 وضع التدريب — اضغط بدء المحاكاة للبدء');
        }
    }
}

// ---- Demo Controls ----
function startDemo() {
    const scenarioId = document.getElementById('scenarioSelect').value;
    if (!scenarioId) { showToast('اختر سيناريو أولاً'); return; }
    if (!isConnected) { showToast('غير متصل بالخادم'); return; }
    const speed = parseFloat(document.getElementById('speedControl').value);
    resetDashboard();
    ws.send(JSON.stringify({ action: 'start_demo', scenario_id: scenarioId, speed }));
}

function stopDemo() {
    if (ws && isConnected) ws.send(JSON.stringify({ action: 'stop_demo' }));
}

function onDemoStarted() {
    isDemoRunning = true;
    document.getElementById('startBtn').style.display = 'none';
    document.getElementById('stopBtn').style.display = 'inline-flex';
    updateStatus('مكالمة جارية...', 'active');
    showThinking(true);
    startTimer();
    callData = { clientType: null, objections: [], violations: [], segments: 0, clientName: '' };
}

function onDemoStopped() {
    isDemoRunning = false;
    document.getElementById('startBtn').style.display = 'inline-flex';
    document.getElementById('stopBtn').style.display = 'none';
    updateStatus('متصل', 'connected');
    showThinking(false);
    stopTimer();
}

function onCallEnded(data) {
    const duration = getCallDuration();
    onDemoStopped();
    if (data.compliance_score) updateComplianceScore(data.compliance_score);
    document.getElementById('progressBar').style.width = '100%';
    showToast('انتهت المكالمة — ' + (data.total_segments || segmentCount) + ' رسالة');
    // Show summary after a brief delay
    setTimeout(() => showCallSummary(data, duration), 800);
}

function resetDashboard() {
    segmentCount = 0;
    battleCardsShown.clear();
    callData = { clientType: null, objections: [], violations: [], segments: 0, clientName: '' };
    document.getElementById('transcriptFeed').innerHTML = '';
    document.getElementById('clientProfileContent').innerHTML = `
    <div class="empty-state"><div class="empty-state-icon">👤</div>
    <div class="empty-state-text">جارٍ تحليل شخصية العميل...</div></div>`;
    document.getElementById('battleCardsContent').innerHTML = '';
    document.getElementById('violationsList').innerHTML = '';
    document.getElementById('ragContent').innerHTML = '<div class="empty-state"><div class="empty-state-icon">🧠</div><div class="empty-state-text">ابحث أو ستظهر النتائج تلقائياً</div></div>';
    document.getElementById('segmentCount').textContent = '0 رسالة';
    document.getElementById('battleCardCount').textContent = '0';
    document.getElementById('complianceScore').textContent = '100';
    document.getElementById('complianceLabel').textContent = 'ممتاز';
    document.getElementById('progressBar').style.width = '0%';
    document.getElementById('timerDisplay').textContent = '00:00';
    callStartTime = null;
}

// ---- Manual Input ----
function setSpeaker(speaker) {
    currentSpeaker = speaker;
    document.getElementById('speakerClient').className = speaker === 'client' ? 'active' : '';
    document.getElementById('speakerAgent').className = speaker === 'agent' ? 'active' : '';
}

function sendManualText() {
    const input = document.getElementById('manualInput');
    const text = input.value.trim();
    if (!text) return;
    if (!isConnected) { showToast('غير متصل بالخادم'); return; }
    if (!callStartTime) startTimer(); // Start timer on first manual message
    ws.send(JSON.stringify({ action: 'process_text', speaker: currentSpeaker, text: text }));
    input.value = '';
}

// ---- Knowledge Search ----
function searchKnowledge() {
    const input = document.getElementById('knowledgeSearch');
    const query = input.value.trim();
    if (!query) return;
    if (!isConnected) { showToast('غير متصل بالخادم'); return; }
    ws.send(JSON.stringify({ action: 'search_knowledge', query: query }));
}

function displayKnowledgeResults(results) {
    updateRAGResults(results);
}

// ---- Process Analysis ----
function processAnalysis(data) {
    showThinking(false);
    addTranscriptMessage(data.speaker, data.text, data.client_name);
    segmentCount++;
    callData.segments = segmentCount;
    if (data.client_name) callData.clientName = data.client_name;
    document.getElementById('segmentCount').textContent = segmentCount + ' رسالة';
    if (data.progress) document.getElementById('progressBar').style.width = data.progress + '%';

    if (data.classification && data.classification.type !== 'unknown') {
        updateClientProfile(data.classification);
        callData.clientType = data.classification;
    }
    if (data.objections && data.objections.length > 0) {
        data.objections.forEach(obj => {
            addBattleCard(obj);
            if (!callData.objections.find(o => o.card.id === obj.card.id)) callData.objections.push(obj);
        });
    }
    if (data.opportunities && data.opportunities.length > 0) {
        data.opportunities.forEach(opp => addOpportunityCard(opp));
    }
    if (data.violations && data.violations.length > 0) {
        data.violations.forEach(v => { addViolation(v); callData.violations.push(v); });
    }
    if (data.compliance_score) updateComplianceScore(data.compliance_score);
    if (data.rag_results && data.rag_results.length > 0) updateRAGResults(data.rag_results);
    if (data.suggestions) renderSuggestions(data.suggestions);
    if (data.agent_score) renderAgentScore(data.agent_score);
    if (data.competitor) renderCompetitorCard(data.competitor);
    if (!data.is_last && isDemoRunning) setTimeout(() => showThinking(true), 500);
}

// ---- Agent Performance Score ----
function renderAgentScore(score) {
    let el = document.getElementById('agentScoreBadge');
    if (!el) {
        el = document.createElement('div');
        el.id = 'agentScoreBadge';
        el.style.cssText = 'position:fixed;top:0.5rem;left:50%;transform:translateX(-50%);z-index:100;display:flex;align-items:center;gap:0.5rem;padding:0.4rem 1rem;border-radius:20px;font-size:0.8rem;font-weight:700;backdrop-filter:blur(12px);border:1px solid var(--border-glass);transition:all 0.3s ease;';
        document.body.appendChild(el);
    }
    el.style.background = score.grade.color + '22';
    el.style.color = score.grade.color;
    el.style.borderColor = score.grade.color + '44';
    el.innerHTML = `<span style="font-size:1.1rem">${score.grade.letter}</span> <span>${score.percentage}% — ${score.grade.label_ar}</span> <span style="font-size:0.7rem;opacity:0.7">(${score.criteria_met}/${score.total_criteria})</span>`;

    // Show achievement toast
    if (score.new_achievements && score.new_achievements.length > 0) {
        score.new_achievements.forEach(a => {
            showToast(`${a.icon} +${a.points} ${a.label_ar}`);
        });
    }
}

// ---- Competitor Intelligence Card ----
function renderCompetitorCard(comp) {
    if (!comp.detected) return;
    const container = document.getElementById('coachingContent');
    const card = document.createElement('div');
    card.className = 'suggestion-card critical';
    card.style.borderRightColor = '#ef4444';
    card.style.background = 'rgba(239,68,68,0.06)';

    if (comp.has_details) {
        let compTable = '<table style="width:100%;font-size:0.72rem;border-collapse:collapse;margin:0.4rem 0">';
        compTable += '<tr style="color:var(--text-muted)"><th style="text-align:right;padding:0.2rem">المقارنة</th><th style="text-align:right;padding:0.2rem">هم</th><th style="text-align:right;padding:0.2rem">نحن</th></tr>';
        comp.comparisons.forEach(c => {
            compTable += `<tr><td style="padding:0.2rem;font-weight:600">${c.aspect}</td><td style="padding:0.2rem;color:var(--accent-red)">${c.them}</td><td style="padding:0.2rem;color:var(--accent-green)">${c.us}</td></tr>`;
        });
        compTable += '</table>';

        card.innerHTML = `
        <div class="suggestion-card-header">
            <div class="suggestion-card-title">🏢 ${comp.logo} العميل ذكر ${comp.competitor_name}!</div>
            <span style="font-size:0.6rem;padding:0.15rem 0.4rem;background:rgba(239,68,68,0.2);color:var(--accent-red);border-radius:10px">استخبارات تنافسية</span>
        </div>
        ${compTable}
        <div style="margin-top:0.3rem">
            ${comp.killing_points.map(p => `<div style="font-size:0.75rem;margin-bottom:0.25rem;padding:0.3rem;background:rgba(16,185,129,0.06);border-radius:4px">⚡ ${p}</div>`).join('')}
        </div>`;
    } else {
        card.innerHTML = `
        <div class="suggestion-card-header">
            <div class="suggestion-card-title">🏢 العميل ذكر منافس: ${comp.competitor_name}</div>
        </div>
        <div class="suggestion-card-text">${comp.generic_response}</div>`;
    }
    container.insertBefore(card, container.firstChild);
}

// ---- Smart Suggestions Rendering ----
function renderSuggestions(suggestions) {
    // Stage indicator
    if (suggestions.stage && suggestions.stage.id) {
        const stageEl = document.getElementById('stageIndicator');
        stageEl.style.display = 'flex';
        document.getElementById('stageIcon').textContent = suggestions.stage.icon || '📋';
        document.getElementById('stageName').textContent = suggestions.stage.name_ar;
        document.getElementById('stageGoal').textContent = suggestions.stage.goal || '';
    }

    // Mood badge
    if (suggestions.mood && suggestions.mood.mood && suggestions.mood.mood !== 'neutral') {
        const moodEl = document.getElementById('moodBadge');
        moodEl.style.display = 'inline-flex';
        moodEl.className = 'mood-badge';
        moodEl.style.background = suggestions.mood.color + '22';
        moodEl.style.color = suggestions.mood.color;
        moodEl.textContent = 'حالة العميل: ' + suggestions.mood.label_ar;
    }

    const container = document.getElementById('coachingContent');
    container.innerHTML = '';

    // ★ Gemini AI Response (highest priority) ★
    if (suggestions.gemini_response) {
        const gem = suggestions.gemini_response;
        const uid = 'gemini-' + Date.now();
        const card = document.createElement('div');
        card.className = 'suggestion-card critical';
        card.style.borderRight = '3px solid #8b5cf6';
        card.style.background = 'linear-gradient(135deg, rgba(99,102,241,0.08), rgba(139,92,246,0.05))';
        card.innerHTML = `
      <div class="suggestion-card-header">
        <div class="suggestion-card-title" style="color:#a78bfa;font-size:0.85rem">✨ اقتراح Gemini AI</div>
        <span style="font-size:0.6rem;padding:0.15rem 0.5rem;background:linear-gradient(135deg,rgba(99,102,241,0.3),rgba(139,92,246,0.3));color:#c4b5fd;border-radius:10px">gemini-2.0-flash</span>
      </div>
      <div class="suggestion-script" id="${uid}" style="font-size:0.85rem;line-height:1.8;border-color:rgba(139,92,246,0.2)">
        <button class="copy-btn" onclick="copyScript('${uid}',this)">📋 نسخ</button>
        ${gem.text}
      </div>`;
        container.appendChild(card);
    }

    // Situational alert (highest priority)
    if (suggestions.situational) {
        const sit = suggestions.situational;
        const card = document.createElement('div');
        card.className = `suggestion-card ${sit.priority || 'high'}`;
        card.innerHTML = `
      <div class="suggestion-card-header">
        <div class="suggestion-card-title">${sit.title_ar}</div>
        <span style="font-size:0.65rem;color:var(--text-muted)">${sit.category_ar}</span>
      </div>
      <div class="suggestion-card-text">
        ${sit.suggestions.map(s => `<div style="margin-bottom:0.3rem">${s}</div>`).join('')}
      </div>`;
        container.appendChild(card);
    }

    // Objection script from best employees
    if (suggestions.objection_script) {
        const obj = suggestions.objection_script;
        const uid = 'script-' + Date.now();
        const card = document.createElement('div');
        card.className = 'suggestion-card critical';
        card.innerHTML = `
      <div class="suggestion-card-header">
        <div class="suggestion-card-title">${obj.icon} رد أفضل موظف</div>
        <span style="font-size:0.6rem;padding:0.15rem 0.4rem;background:rgba(16,185,129,0.2);color:var(--accent-green);border-radius:10px">سكربت جاهز</span>
      </div>
      <div class="suggestion-script" id="${uid}">
        <button class="copy-btn" onclick="copyScript('${uid}',this)">📋 نسخ</button>
        ${obj.script}
      </div>
      ${obj.key_points ? `<div class="suggestion-key-points">${obj.key_points.map(p => `<span class="key-point-tag">✓ ${p}</span>`).join('')}</div>` : ''}
      ${obj.tone ? `<div style="font-size:0.65rem;color:var(--text-muted);margin-top:0.3rem">🎭 النبرة: ${obj.tone}</div>` : ''}`;
        container.appendChild(card);
    }

    // ★ RAG-Powered Answers from training files ★
    if (suggestions.rag_answers && suggestions.rag_answers.length > 0) {
        suggestions.rag_answers.forEach(answer => {
            const uid = 'rag-' + Date.now() + Math.random().toString(36).substr(2, 4);
            const card = document.createElement('div');
            const isCritical = answer.priority === 'critical';
            const isHigh = answer.priority === 'high';
            card.className = `suggestion-card ${isCritical ? 'critical' : (isHigh ? 'high' : '')}`;
            card.style.borderRightColor = isCritical ? 'var(--accent-green)' : (isHigh ? 'var(--accent-amber)' : 'var(--accent-purple)');

            const sourceTag = answer.source ?
                `<span style="font-size:0.6rem;padding:0.1rem 0.4rem;background:rgba(139,92,246,0.15);color:var(--accent-purple);border-radius:10px;margin-right:0.3rem">📁 ${answer.source}</span>` : '';

            card.innerHTML = `
          <div class="suggestion-card-header">
            <div class="suggestion-card-title">${answer.icon || '📄'} ${answer.title_ar || 'اقتراح من ملفات التدريب'}</div>
            ${sourceTag}
          </div>
          <div class="suggestion-script" id="${uid}">
            <button class="copy-btn" onclick="copyScript('${uid}',this)">📋 نسخ</button>
            ${answer.text}
          </div>`;
            container.appendChild(card);
        });
    }

    // Closing techniques
    if (suggestions.closing && suggestions.closing.length > 0) {
        suggestions.closing.forEach(closing => {
            const uid = 'close-' + Date.now() + Math.random().toString(36).substr(2, 4);
            const card = document.createElement('div');
            card.className = 'closing-card';
            card.innerHTML = `
        <div class="closing-card-title">🎯 ${closing.title_ar}</div>
        <div class="suggestion-script" id="${uid}">
          <button class="copy-btn" onclick="copyScript('${uid}',this)">📋 نسخ</button>
          ${closing.text}
        </div>
        <div style="font-size:0.65rem;color:var(--text-muted);margin-top:0.2rem">📌 ${closing.description || ''}</div>`;
            container.appendChild(card);
        });
    }

    // General stage suggestions (best practices)
    if (suggestions.suggestions && suggestions.suggestions.length > 0) {
        suggestions.suggestions.forEach(tip => {
            if (tip.type === 'suggested_phrase' && tip.copyable) {
                const uid = 'tip-' + Date.now() + Math.random().toString(36).substr(2, 4);
                const card = document.createElement('div');
                card.className = 'suggestion-card';
                card.innerHTML = `
          <div class="suggestion-card-header">
            <div class="suggestion-card-title">${tip.icon} ${tip.category_ar}</div>
          </div>
          <div class="suggestion-script" id="${uid}">
            <button class="copy-btn" onclick="copyScript('${uid}',this)">📋 نسخ</button>
            ${tip.text}
          </div>`;
                container.appendChild(card);
            } else if (tip.type === 'best_practice') {
                const card = document.createElement('div');
                card.className = 'suggestion-card';
                card.style.borderRightColor = 'var(--accent-cyan)';
                card.innerHTML = `<div class="suggestion-card-text">${tip.icon} ${tip.text}</div>`;
                container.appendChild(card);
            }
        });
    }
}

function copyScript(id, btn) {
    const el = document.getElementById(id);
    if (!el) return;
    const text = el.textContent.replace('📋 نسخ', '').trim();
    navigator.clipboard.writeText(text).then(() => {
        btn.textContent = '✓ تم النسخ';
        btn.classList.add('copied');
        setTimeout(() => { btn.textContent = '📋 نسخ'; btn.classList.remove('copied'); }, 2000);
    });
}

// ---- Transcript ----
function addTranscriptMessage(speaker, text, clientName) {
    const feed = document.getElementById('transcriptFeed');
    const empty = feed.querySelector('.empty-state');
    if (empty) empty.remove();
    const isClient = speaker === 'client';
    const msg = document.createElement('div');
    msg.className = 'transcript-msg';
    msg.innerHTML = `
    <div class="msg-avatar ${isClient ? 'client' : 'agent'}">${isClient ? '👤' : '🎧'}</div>
    <div class="msg-content">
      <div class="msg-speaker">
        <span>${isClient ? (clientName || 'العميل') : 'الموظف'}</span>
        <span style="color:var(--text-muted);font-size:0.6rem">${new Date().toLocaleTimeString('ar-SA', { hour: '2-digit', minute: '2-digit' })}</span>
      </div>
      <div class="msg-text">${text}</div>
    </div>`;
    feed.appendChild(msg);
    feed.scrollTop = feed.scrollHeight;
}

// ---- Client Profile ----
function updateClientProfile(classification) {
    const container = document.getElementById('clientProfileContent');
    const badge = document.getElementById('clientTypeBadge');
    const typeColors = { emotional: 'var(--accent-pink)', analyst: 'var(--accent-cyan)', leader: 'var(--accent-amber)', nice: 'var(--accent-green)' };
    const color = typeColors[classification.type] || 'var(--accent-blue)';
    badge.textContent = classification.icon + ' ' + classification.type_ar;
    badge.style.background = color + '22';
    badge.style.color = color;

    let tacticsHTML = '';
    if (classification.strategy && classification.strategy.tactics) {
        tacticsHTML = '<ul class="strategy-list">' + classification.strategy.tactics.map(t => `<li class="strategy-item">${t}</li>`).join('') + '</ul>';
    }
    let scoresHTML = '<div class="scores-grid">';
    if (classification.scores) {
        for (const [type, score] of Object.entries(classification.scores)) {
            const label = { emotional: 'عاطفي', analyst: 'محلل', leader: 'قائد', nice: 'لطيف' }[type] || type;
            scoresHTML += `<div class="score-bar-item"><div class="score-bar-label"><span>${label}</span><span>${Math.round(score * 100)}%</span></div><div class="score-bar-track"><div class="score-bar-fill ${type}" style="width:${score * 100}%"></div></div></div>`;
        }
    }
    scoresHTML += '</div>';

    // Sentiment gauge
    const sentiment = classification.confidence > 0.5 ? classification.confidence * 100 : 50;
    const sentimentHTML = `
    <div class="sentiment-gauge">
      <span class="sentiment-label">سلبي</span>
      <div class="sentiment-bar-track"><div class="sentiment-bar-indicator" style="right:${sentiment}%"></div></div>
      <span class="sentiment-label">إيجابي</span>
    </div>`;

    container.innerHTML = `
    <div class="profile-type">
      <div class="profile-type-icon">${classification.icon}</div>
      <div class="profile-type-info">
        <h4>${classification.type_ar}</h4>
        <p>ثقة التصنيف: ${Math.round(classification.confidence * 100)}%</p>
        <div class="confidence-bar"><div class="confidence-fill" style="width:${classification.confidence * 100}%"></div></div>
      </div>
    </div>
    ${scoresHTML}
    ${sentimentHTML}
    ${classification.strategy ? `<p style="font-size:0.8rem;color:var(--accent-cyan);margin:0.6rem 0 0.4rem;font-weight:600">الاستراتيجية: ${classification.strategy.ar}</p>` : ''}
    ${tacticsHTML}`;
}

// ---- Battle Cards ----
function addBattleCard(objection) {
    const card = objection.card;
    if (battleCardsShown.has(card.id)) return;
    battleCardsShown.add(card.id);
    const container = document.getElementById('battleCardsContent');
    const empty = container.querySelector('.empty-state');
    if (empty) empty.remove();
    const el = document.createElement('div');
    el.className = `battle-card ${card.severity}`;
    el.innerHTML = `
    <div class="battle-card-header">
      <div class="battle-card-title">${card.icon} ${card.title_ar}</div>
      <span class="card-badge" style="background:${card.severity === 'high' ? 'rgba(239,68,68,0.2);color:var(--accent-red)' : card.severity === 'medium' ? 'rgba(245,158,11,0.2);color:var(--accent-amber)' : 'rgba(99,102,241,0.2);color:var(--accent-blue)'}">${card.severity === 'high' ? 'عالي' : card.severity === 'medium' ? 'متوسط' : 'منخفض'}</span>
    </div>
    <div class="battle-card-points">
      ${card.response_points.map(p => `<div class="battle-point"><span class="battle-point-icon">${p.icon}</span><div class="battle-point-text"><strong>${p.point}:</strong> ${p.detail}</div></div>`).join('')}
    </div>
    <div class="battle-card-actions">
      <button class="feedback-btn" onclick="sendFeedback('${card.id}','up',this)">👍 مفيد</button>
      <button class="feedback-btn" onclick="sendFeedback('${card.id}','down',this)">👎 غير مفيد</button>
    </div>`;
    container.insertBefore(el, container.firstChild);
    document.getElementById('battleCardCount').textContent = battleCardsShown.size;
}

// ---- 3M Opportunity ----
function addOpportunityCard(opp) {
    const container = document.getElementById('battleCardsContent');
    const empty = container.querySelector('.empty-state');
    if (empty) empty.remove();
    const el = document.createElement('div');
    el.className = 'opportunity-card';
    el.innerHTML = `
    <div class="opp-header">${opp.market.icon} فرصة 3M — ${opp.market.name_ar}</div>
    <div class="opp-3m">
      <div class="opp-3m-item"><div class="opp-3m-label">المحرك</div><div class="opp-3m-value">${opp.mover.icon}<br><span style="font-size:0.7rem">${opp.mover.event_ar.substring(0, 20)}</span></div></div>
      <div class="opp-3m-item"><div class="opp-3m-label">السوق</div><div class="opp-3m-value">${opp.market.icon}<br><span style="font-size:0.7rem">${opp.market.name_ar}</span></div></div>
      <div class="opp-3m-item"><div class="opp-3m-label">الحركة المتوقعة</div><div class="opp-3m-value" style="color:var(--accent-green)">${opp.movement.expected_points} نقطة</div></div>
    </div>
    <div class="opp-pitch">${opp.pitch_ar}</div>`;
    container.insertBefore(el, container.firstChild);
}

// ---- Compliance ----
function updateComplianceScore(score) {
    const el = document.getElementById('complianceScore');
    el.textContent = score.score;
    el.style.background = score.score >= 90 ? 'var(--gradient-main)' : score.score >= 70 ? 'linear-gradient(135deg,#f59e0b,#eab308)' : 'linear-gradient(135deg,#ef4444,#dc2626)';
    el.style.webkitBackgroundClip = 'text';
    el.style.webkitTextFillColor = 'transparent';
    document.getElementById('complianceLabel').textContent = score.status.label_ar;
    document.getElementById('complianceLabel').style.color = score.status.color;
}

function addViolation(v) {
    const container = document.getElementById('violationsList');
    const el = document.createElement('div');
    el.className = `violation-item ${v.severity}`;
    el.innerHTML = `<span>${v.severity === 'critical' ? '🔴' : '🟡'}</span><div><strong>${v.title_ar}</strong><br><span style="color:var(--text-muted);font-size:0.75rem">${v.description_ar}</span></div>`;
    container.insertBefore(el, container.firstChild);
}

// ---- RAG Results ----
function updateRAGResults(results) {
    const container = document.getElementById('ragContent');
    container.innerHTML = '';
    const typeLabels = { company_info: 'معلومات الشركة', term: 'مصطلح', competitor: 'مقارنة', faq: 'سؤال شائع', license: 'ترخيص', security: 'أمان' };
    results.forEach(r => {
        const el = document.createElement('div');
        el.className = 'rag-item';
        const type = r.document?.metadata?.type || 'info';
        el.innerHTML = `<div class="rag-item-type">${typeLabels[type] || type}</div><div>${r.document?.text || ''}</div>`;
        container.appendChild(el);
    });
}

// ---- Market Data ----
async function loadMarketData() {
    try {
        const res = await fetch('/api/market-data');
        const data = await res.json();
        renderMarketData(data.instruments);
    } catch (e) { console.error('Market data error:', e); }
}

function renderMarketData(instruments) {
    const container = document.getElementById('marketDataContent');
    container.innerHTML = '';
    for (const [symbol, inst] of Object.entries(instruments)) {
        if (!inst.popular) continue;
        const el = document.createElement('div');
        el.className = 'market-item';
        const isPos = inst.change_pct >= 0;
        el.onclick = () => load3MForAsset(symbol);
        el.innerHTML = `
      <div class="market-item-info"><span class="market-item-icon">${inst.icon}</span><div><div class="market-item-name">${inst.name_ar}</div><div class="market-item-symbol">${inst.symbol}</div></div></div>
      <div class="market-item-price"><div class="market-item-value">${inst.price.toLocaleString()}</div><div class="market-item-change ${isPos ? 'positive' : 'negative'}">${isPos ? '▲' : '▼'} ${Math.abs(inst.change_pct).toFixed(2)}%</div></div>`;
        container.appendChild(el);
    }
}

async function load3MForAsset(symbol) {
    try {
        const res = await fetch(`/api/3m/${symbol}`);
        const opp = await res.json();
        if (!opp.error) addOpportunityCard(opp);
        showToast(`🎯 تم حساب فرصة 3M لـ ${symbol}`);
    } catch (e) { console.error(e); }
}

// ---- Call Summary ----
function showCallSummary(data, duration) {
    const overlay = document.getElementById('callSummaryOverlay');
    const statsEl = document.getElementById('summaryStats');
    const detailsEl = document.getElementById('summaryDetails');
    const compScore = data.compliance_score?.score ?? 100;

    document.getElementById('summarySubtitle').textContent = callData.clientName ? `تقرير مكالمة مع ${callData.clientName}` : 'تقرير تحليلي للمكالمة';

    statsEl.innerHTML = `
    <div class="summary-stat"><div class="summary-stat-value" style="color:var(--accent-blue)">${duration}</div><div class="summary-stat-label">مدة المكالمة</div></div>
    <div class="summary-stat"><div class="summary-stat-value" style="color:var(--accent-cyan)">${segmentCount}</div><div class="summary-stat-label">عدد الرسائل</div></div>
    <div class="summary-stat"><div class="summary-stat-value" style="color:var(--accent-amber)">${battleCardsShown.size}</div><div class="summary-stat-label">اعتراضات مكتشفة</div></div>
    <div class="summary-stat"><div class="summary-stat-value" style="color:${compScore >= 90 ? 'var(--accent-green)' : compScore >= 70 ? 'var(--accent-amber)' : 'var(--accent-red)'}"><span>${compScore}%</span></div><div class="summary-stat-label">درجة الامتثال</div></div>`;

    let details = '';
    // Client type
    if (callData.clientType) {
        details += `<div class="summary-section"><h4>👤 نوع العميل</h4><div class="summary-recommendation">${callData.clientType.icon} <strong>${callData.clientType.type_ar}</strong> — ثقة ${Math.round(callData.clientType.confidence * 100)}%${callData.clientType.strategy ? '<br>الاستراتيجية: ' + callData.clientType.strategy.ar : ''}</div></div>`;
    }
    // Objections
    if (callData.objections.length > 0) {
        details += `<div class="summary-section"><h4>⚔️ الاعتراضات المكتشفة</h4>${callData.objections.map(o => `<div class="summary-recommendation">${o.card.icon} ${o.card.title_ar}</div>`).join('')}</div>`;
    }
    // Violations
    if (callData.violations.length > 0) {
        details += `<div class="summary-section"><h4>⚠️ مخالفات الامتثال</h4>${callData.violations.map(v => `<div class="summary-recommendation" style="border-right-color:${v.severity === 'critical' ? 'var(--accent-red)' : 'var(--accent-amber)'}">${v.title_ar}</div>`).join('')}</div>`;
    }
    // Recommendations
    details += `<div class="summary-section"><h4>💡 توصيات المتابعة</h4>
    <div class="summary-recommendation">📞 جدولة مكالمة متابعة خلال 24 ساعة</div>
    <div class="summary-recommendation">📧 إرسال ملخص المحادثة للعميل عبر WhatsApp أو البريد</div>
    ${callData.clientType?.type === 'nice' ? '<div class="summary-recommendation">⏰ العميل اللطيف يحتاج متابعة مستمرة — لا تتركه أكثر من يومين</div>' : ''}
    ${callData.clientType?.type === 'analyst' ? '<div class="summary-recommendation">📊 أرسل جدول مقارنة تفصيلي مع المنافسين الذين ذكرهم</div>' : ''}
  </div>`;

    // Performance Report
    if (data.performance_report) {
        const perf = data.performance_report;
        details += `<div class="summary-section"><h4>📊 تقرير أداء الموظف</h4>
        <div style="text-align:center;padding:0.5rem">
            <div style="font-size:2rem;font-weight:800;color:${perf.grade.color}">${perf.grade.letter}</div>
            <div style="font-size:0.85rem;color:${perf.grade.color}">${perf.grade.label_ar}</div>
            <div style="font-size:0.75rem;color:var(--text-muted);margin-top:0.2rem">${perf.percentage}% (${perf.score}/${perf.max_score} نقطة)</div>
        </div>`;
        // Achieved criteria
        if (perf.achieved && perf.achieved.length > 0) {
            details += '<div style="margin-top:0.5rem">';
            perf.achieved.forEach(a => {
                details += `<div class="summary-recommendation" style="border-right-color:var(--accent-green)">${a.icon} ${a.label_ar} <span style="float:left;color:var(--accent-green)">+${a.weight}</span></div>`;
            });
            details += '</div>';
        }
        // Missed criteria
        if (perf.missed && perf.missed.length > 0) {
            details += '<div style="margin-top:0.5rem"><div style="font-size:0.75rem;color:var(--text-muted);margin-bottom:0.3rem">❌ لم يتحقق:</div>';
            perf.missed.forEach(m => {
                details += `<div class="summary-recommendation" style="border-right-color:var(--accent-red);opacity:0.7">${m.icon} ${m.label_ar}</div>`;
            });
            details += '</div>';
        }
        // Tips
        if (perf.tips && perf.tips.length > 0) {
            details += '<div style="margin-top:0.5rem"><div style="font-size:0.75rem;color:var(--accent-amber);margin-bottom:0.3rem">💡 نصائح للتحسين:</div>';
            perf.tips.forEach(tip => {
                details += `<div class="summary-recommendation" style="border-right-color:var(--accent-amber)">${tip}</div>`;
            });
            details += '</div>';
        }
        details += '</div>';
    }

    detailsEl.innerHTML = details;
    overlay.classList.add('active');
}

function closeSummary() {
    document.getElementById('callSummaryOverlay').classList.remove('active');
}

// ---- Feedback ----
function sendFeedback(cardId, vote, btn) {
    if (ws && isConnected) ws.send(JSON.stringify({ action: 'feedback', card_id: cardId, vote }));
    const parent = btn.parentElement;
    parent.querySelectorAll('.feedback-btn').forEach(b => b.className = 'feedback-btn');
    btn.classList.add(vote === 'up' ? 'voted-up' : 'voted-down');
}

// ---- Thinking Indicator ----
function showThinking(show) {
    document.getElementById('thinkingIndicator').className = 'thinking-indicator' + (show ? ' active' : '');
}

// ---- Toast ----
function showToast(message) {
    let toast = document.getElementById('toast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'toast';
        toast.style.cssText = `position:fixed;bottom:2rem;left:50%;transform:translateX(-50%) translateY(100px);background:var(--bg-card);backdrop-filter:blur(12px);border:1px solid var(--border-glass);border-radius:var(--radius-sm);padding:0.7rem 1.5rem;font-size:0.85rem;color:var(--text-primary);z-index:9999;transition:transform 0.4s cubic-bezier(0.34,1.56,0.64,1);box-shadow:var(--shadow-lg);`;
        document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.style.transform = 'translateX(-50%) translateY(0)';
    setTimeout(() => { toast.style.transform = 'translateX(-50%) translateY(100px)'; }, 3000);
}

// Refresh market data every 30s
setInterval(loadMarketData, 30000);
