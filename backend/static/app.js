/* Linda chat UI — polls the backend for live task steps. No build step. */
(function () {
  "use strict";

  var messagesEl = document.getElementById("messages");
  var stepsEl = document.getElementById("steps");
  var stepsCol = document.getElementById("stepsCol");
  var stepsBtn = document.getElementById("stepsBtn");
  var stepsClose = document.getElementById("stepsClose");
  var backdrop = document.getElementById("sheetBackdrop");
  var statusPill = document.getElementById("statusPill");
  var approvalCard = document.getElementById("approvalCard");
  var approvalDetail = document.getElementById("approvalDetail");
  var inputEl = document.getElementById("input");
  var sendBtn = document.getElementById("sendBtn");
  var stopBtn = document.getElementById("stopBtn");
  var micBtn = document.getElementById("micBtn");
  var listenHint = document.getElementById("listenHint");
  var form = document.getElementById("composer");

  // Settings modal
  var settingsModal = document.getElementById("settingsModal");
  var settingsBtn = document.getElementById("settingsBtn");
  var settingsClose = document.getElementById("settingsClose");
  var settingsSave = document.getElementById("settingsSave");
  var settingsMsg = document.getElementById("settingsMsg");
  var setProvider = document.getElementById("setProvider");
  var setOllamaModel = document.getElementById("setOllamaModel");
  var setGeminiKey = document.getElementById("setGeminiKey");
  var setGeminiModel = document.getElementById("setGeminiModel");
  var setApproval = document.getElementById("setApproval");
  var setBrowser = document.getElementById("setBrowser");
  var setMaxSteps = document.getElementById("setMaxSteps");
  var setApiToken = document.getElementById("setApiToken");
  var setAutoSpeak = document.getElementById("setAutoSpeak");
  // No messaging fields here (v0.7): WhatsApp/Instagram auto-reply is
  // controlled by talking to Linda in chat; tokens live in .env only.

  // Health modal
  var healthModal = document.getElementById("healthModal");
  var healthBtn = document.getElementById("healthBtn");
  var healthClose = document.getElementById("healthClose");
  var healthRefresh = document.getElementById("healthRefresh");
  var healthList = document.getElementById("healthList");
  var healthMsg = document.getElementById("healthMsg");

  // Chats modal (side chats)
  var chatsBtn = document.getElementById("chatsBtn");
  var newChatBtn = document.getElementById("newChatBtn");
  var chatsModal = document.getElementById("chatsModal");
  var chatsClose = document.getElementById("chatsClose");
  var chatsList = document.getElementById("chatsList");
  var newChatBtn2 = document.getElementById("newChatBtn2");

  var toastEl = document.getElementById("toast");
  var toastTimer = null;

  // ---- Server API token (cloud servers only) ----
  // When the server has API_TOKEN set in .env, every API call needs the
  // Bearer token. It lives in this browser only (localStorage) and is
  // sent nowhere except this server. On a laptop server (no token set)
  // this does nothing at all — no prompt, no header.
  var TOKEN_KEY = "linda_api_token";
  var tokenAsked = false;
  function getToken() { try { return localStorage.getItem(TOKEN_KEY) || ""; } catch (e) { return ""; } }
  function setToken(t) { try { localStorage.setItem(TOKEN_KEY, t || ""); } catch (e) {} }

  function apiFetch(url, options) {
    options = options || {};
    var headers = {};
    var k;
    for (k in options.headers) headers[k] = options.headers[k];
    var token = getToken();
    if (token) headers["Authorization"] = "Bearer " + token;
    options.headers = headers;
    return fetch(url, options).then(function (resp) {
      if (resp.status === 401 && !tokenAsked) {
        tokenAsked = true; // one prompt max per page load
        var t = window.prompt("This server needs an API token (set as API_TOKEN in the server's .env). Enter the token:");
        if (t && t.trim()) {
          setToken(t.trim());
          return apiFetch(url, options); // retry once with the new token
        }
      }
      return resp;
    });
  }

  var currentTaskId = null;
  var pollTimer = null;
  var renderedSteps = 0;
  var agentBubble = null;
  var agentStepLine = null;
  var healthAutoShown = false;
  var currentConversationId = null; // side chat currently open
  var conversations = []; // all side chats, most recently active first

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function scrollChat() {
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function showToast(text, isError) {
    toastEl.textContent = text;
    toastEl.className = "toast" + (isError ? " toast-error" : "");
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(function () {
      toastEl.classList.add("hidden");
    }, 3500);
  }

  function addBubble(role, html, isError) {
    var msg = document.createElement("div");
    msg.className = "msg " + role;
    var bubble = document.createElement("div");
    bubble.className = "bubble" + (isError ? " error" : "");
    bubble.innerHTML = html;
    msg.appendChild(bubble);
    // Agent messages get a speaker button (hidden until the reply is final).
    if (role === "agent") attachSpeakButton(msg, bubble);
    messagesEl.appendChild(msg);
    scrollChat();
    return bubble;
  }

  // ---- Voice: mic input + spoken replies (fully client-side, free) ----
  // Speech recognition + synthesis run in the browser itself — no API
  // key, no server cost, no backend change. Everything is wrapped in
  // feature checks: browsers without these APIs just don't get the
  // buttons (or get a clean hint), and the app works exactly as before.
  var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  var ttsSupported = ("speechSynthesis" in window) && ("SpeechSynthesisUtterance" in window);
  var AUTO_SPEAK_KEY = "linda_auto_speak";
  var recognition = null;
  var listening = false;
  var recogRestarting = false;
  var recogLangTriedHi = false;
  var speakingBtn = null; // the .speak-btn currently reading aloud

  function autoSpeakEnabled() {
    try { return localStorage.getItem(AUTO_SPEAK_KEY) === "1"; } catch (e) { return false; }
  }
  function setAutoSpeakEnabled(on) {
    try { localStorage.setItem(AUTO_SPEAK_KEY, on ? "1" : "0"); } catch (e) {}
  }

  // --- Mic input (SpeechRecognition) ---
  function setListeningUI(on) {
    listening = on;
    micBtn.classList.toggle("listening", on);
    listenHint.classList.toggle("hidden", !on);
    inputEl.placeholder = on ? "Listening…" : "Tell Linda what to do…";
  }

  function startListening() {
    if (!SpeechRecognition) {
      showToast("Voice input doesn't work in this browser — try Chrome (phone or laptop).", true);
      return;
    }
    if (listening) { stopListening(); return; }
    stopSpeaking(); // don't talk over the user
    try {
      recognition = new SpeechRecognition();
    } catch (e) {
      showToast("Couldn't start voice input.", true);
      return;
    }
    // en-IN first: it handles English + Hinglish well. If this device
    // has no en-IN recognizer, onerror retries once with hi-IN.
    recognition.lang = "en-IN";
    recognition.interimResults = true;
    recognition.continuous = false; // one utterance: stops when you pause
    recognition.maxAlternatives = 1;
    recogLangTriedHi = false;
    recogRestarting = false;
    var baseText = inputEl.value.trim();

    recognition.onresult = function (event) {
      var interim = "", finalText = "";
      for (var i = event.resultIndex; i < event.results.length; i++) {
        if (event.results[i].isFinal) finalText += event.results[i][0].transcript;
        else interim += event.results[i][0].transcript;
      }
      var text = (finalText || interim).trim();
      if (!text) return;
      // Live transcript lands in the composer for editing — never
      // auto-sent; the user presses send (just like Muse here).
      inputEl.value = baseText ? baseText + " " + text : text;
      inputEl.dispatchEvent(new Event("input"));
    };

    recognition.onerror = function (event) {
      if (event.error === "not-allowed" || event.error === "service-not-allowed") {
        showToast("Mic permission denied — allow the mic for this site in your browser settings.", true);
      } else if (event.error === "language-not-supported" && !recogLangTriedHi) {
        recogLangTriedHi = true;
        recogRestarting = true; // onend of the failed session must not reset the UI
        try {
          recognition.lang = "hi-IN";
          recognition.start();
          return;
        } catch (e) { recogRestarting = false; }
      } else if (event.error !== "no-speech" && event.error !== "aborted") {
        showToast("Voice input ran into a problem — try again.", true);
      }
      // no-speech: the user stayed silent; just stop quietly.
      setListeningUI(false);
    };

    recognition.onend = function () {
      if (recogRestarting) { recogRestarting = false; return; }
      setListeningUI(false);
      recognition = null;
      inputEl.focus();
    };

    try {
      recognition.start();
      setListeningUI(true);
    } catch (e) {
      showToast("Couldn't start voice input.", true);
    }
  }

  function stopListening() {
    if (recognition) { try { recognition.stop(); } catch (e) {} }
    setListeningUI(false);
  }

  // --- Spoken replies (speechSynthesis) ---
  function pickVoice() {
    if (!ttsSupported) return null;
    var voices = [];
    try { voices = window.speechSynthesis.getVoices() || []; } catch (e) { return null; }
    if (!voices.length) return null; // voices load async; default voice is fine
    var i, v;
    for (i = 0; i < voices.length; i++) {
      v = voices[i];
      if (v.lang && v.lang.toLowerCase().indexOf("en-in") === 0) return v;
    }
    for (i = 0; i < voices.length; i++) {
      v = voices[i];
      if (v.lang && v.lang.toLowerCase().indexOf("en") === 0 && v.default) return v;
    }
    for (i = 0; i < voices.length; i++) {
      v = voices[i];
      if (v.lang && v.lang.toLowerCase().indexOf("en") === 0) return v;
    }
    return null;
  }

  function cleanForSpeech(text) {
    return String(text || "")
      .replace(/```[\s\S]*?```/g, " ")  // code blocks: skipped, not read aloud
      .replace(/`([^`]*)`/g, "$1")
      .replace(/[*_#>-]/g, " ")
      .replace(/https?:\/\/\S+/g, " ")
      .replace(/\s+/g, " ")
      .trim();
  }

  function clearSpeakingBtn() {
    if (speakingBtn) speakingBtn.classList.remove("speaking");
    speakingBtn = null;
  }

  function stopSpeaking() {
    if (!ttsSupported) return;
    try { window.speechSynthesis.cancel(); } catch (e) {}
    clearSpeakingBtn();
  }

  function speakText(text, btn) {
    if (!ttsSupported) return;
    stopSpeaking();
    var clean = cleanForSpeech(text);
    if (!clean) return;
    // Chunk into sentences so long replies don't hit the browser's
    // per-utterance limits and Stop works promptly.
    var chunks = clean.match(/[^.!?\n]+[.!?]+|[^.!?\n]+$/g) || [clean];
    var voice = pickVoice();
    var synth = window.speechSynthesis;
    speakingBtn = btn || null;
    if (speakingBtn) speakingBtn.classList.add("speaking");
    var last = chunks[chunks.length - 1];
    chunks.forEach(function (chunk) {
      chunk = chunk.trim();
      if (!chunk) return;
      var u = new SpeechSynthesisUtterance(chunk);
      if (voice) u.voice = voice;
      u.lang = (voice && voice.lang) || "en-IN";
      u.rate = 0.95;
      if (chunk === last) {
        u.onend = function () { clearSpeakingBtn(); };
        u.onerror = function () { clearSpeakingBtn(); };
      }
      synth.speak(u);
    });
  }

  // Speaker glyph — custom hand-drawn icon (v0.5): a speaker cone with
  // equalizer bars, painted with the shared #voiceGrad gradient. Same
  // path as mobile_app/assets/icons/speaker.svg.
  var SPEAKER_SVG = '<svg class="voice-icon" viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path fill="url(#voiceGrad)" d="M3.2 10.1 a1.3 1.3 0 0 1 1.3-1.3 h1.9 l4.9-3.9 a1.1 1.1 0 0 1 1.7.9 v12.4 a1.1 1.1 0 0 1 -1.7.9 l-4.9-3.9 H4.5 a1.3 1.3 0 0 1 -1.3-1.3 z"/><rect x="15" y="9.8" width="1.9" height="4.4" rx=".95" fill="url(#voiceGrad)"/><rect x="17.9" y="7.6" width="1.9" height="8.8" rx=".95" fill="url(#voiceGrad)"/><rect x="20.8" y="9.8" width="1.9" height="4.4" rx=".95" fill="url(#voiceGrad)"/></svg>';

  // Stop button icon (custom rounded square, white on the red button).
  // The button's content is swapped to "…" while the stop request is
  // in flight, then restored — so the markup lives here, not in HTML.
  var STOP_ICON = '<svg class="voice-icon" viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><rect x="7.2" y="7.2" width="9.6" height="9.6" rx="2.6" fill="#fff"/></svg>';

  function attachSpeakButton(msgEl, bubbleEl) {
    if (!ttsSupported) return null;
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "speak-btn hidden";
    btn.innerHTML = SPEAKER_SVG;
    btn.title = "Listen";
    btn.setAttribute("aria-label", "Read aloud");
    btn.addEventListener("click", function () {
      if (btn.classList.contains("speaking")) { stopSpeaking(); return; }
      var text = bubbleEl.dataset.speakText || bubbleEl.innerText || "";
      speakText(text, btn);
    });
    msgEl.appendChild(btn);
    return btn;
  }

  // v0.8.3: the header has no model subtitle anymore (brain info
  // lives in the Status panel) — only the online/offline pill.
  function setStatus(online) {
    statusPill.textContent = online ? "● online" : "● offline";
    statusPill.className = "pill " + (online ? "pill-on" : "pill-off");
  }

  // ---- Health / status line ----
  function refreshHealth() {
    apiFetch("/health")
      .then(function (r) { return r.json(); })
      .then(function (h) {
        setStatus(true);
      })
      .catch(function () {
        setStatus(false);
      });
  }

  // ---- Modals ----
  function openModal(modal) { modal.classList.remove("hidden"); }
  function closeModal(modal) { modal.classList.add("hidden"); }
  function closeAllModals() {
    closeModal(settingsModal);
    closeModal(healthModal);
  }
  [settingsModal, healthModal].forEach(function (modal) {
    modal.addEventListener("click", function (e) {
      if (e.target === modal) closeModal(modal);
    });
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") closeAllModals();
  });

  // ---- Settings ----
  function loadSettings() {
    settingsMsg.classList.add("hidden");
    setGeminiKey.value = "";
    setApiToken.value = getToken();
    setAutoSpeak.checked = autoSpeakEnabled(); // browser-only preference
    apiFetch("/settings")
      .then(function (r) { return r.json(); })
      .then(function (s) {
        setProvider.value = s.model_provider || "ollama";
        setOllamaModel.value = s.ollama_model || "";
        setGeminiModel.value = s.gemini_model || "";
        setApproval.value = s.approval_mode || "auto";
        setBrowser.value = s.browser_headless ? "headless" : "visible";
        setMaxSteps.value = s.max_agent_steps || 15;
        setGeminiKey.placeholder = s.gemini_key_set
          ? ("Key set: " + (s.gemini_api_key_masked || "••••••••"))
          : "No key set yet";
      })
      .catch(function () {
        settingsMsg.textContent = "Couldn't load Settings — is the server running?";
        settingsMsg.className = "form-msg error";
      });
  }

  function saveSettings() {
    // Server API token lives in this browser only — never sent to /settings.
    setToken(setApiToken.value.trim());
    var payload = {
      model_provider: setProvider.value,
      ollama_model: setOllamaModel.value.trim(),
      gemini_model: setGeminiModel.value.trim(),
      approval_mode: setApproval.value,
      browser_headless: setBrowser.value === "headless",
      max_agent_steps: parseInt(setMaxSteps.value, 10),
    };
    // Only send the key if the user typed a new one — otherwise the
    // stored key stays untouched.
    var newKey = setGeminiKey.value.trim();
    if (newKey) payload.gemini_api_key = newKey;

    settingsSave.disabled = true;
    settingsSave.textContent = "Saving…";
    apiFetch("/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
      .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, d: d }; }); })
      .then(function (res) {
        if (!res.ok) throw new Error((res.d && res.d.detail) || "Couldn't save.");
        settingsMsg.textContent = res.d.message || "Settings saved.";
        settingsMsg.className = "form-msg ok";
        setGeminiKey.value = "";
        setGeminiKey.placeholder = res.d.settings && res.d.settings.gemini_key_set
          ? ("Key set: " + (res.d.settings.gemini_api_key_masked || "••••••••"))
          : "No key set yet";
        refreshHealth();
        showToast("Settings saved — applied without a restart.");
        setTimeout(function () { closeModal(settingsModal); }, 900);
      })
      .catch(function (err) {
        settingsMsg.textContent = err.message || "Couldn't save Settings.";
        settingsMsg.className = "form-msg error";
      })
      .finally(function () {
        settingsSave.disabled = false;
        settingsSave.textContent = "Save settings";
      });
  }

  settingsBtn.addEventListener("click", function () {
    loadSettings();
    openModal(settingsModal);
  });
  settingsClose.addEventListener("click", function () { closeModal(settingsModal); });
  settingsSave.addEventListener("click", saveSettings);

  // Auto-speak is a browser-only preference (like the API token) — it
  // saves to localStorage immediately, not via the server Save button.
  setAutoSpeak.addEventListener("change", function () {
    setAutoSpeakEnabled(setAutoSpeak.checked);
    if (!setAutoSpeak.checked) stopSpeaking();
  });

  // Mic button: tap to talk, tap again (or pause) to stop.
  micBtn.addEventListener("click", startListening);

  // ---- Status / health panel ----
  function renderHealth(data) {
    if (!data || !data.checks) {
      healthList.innerHTML = '<p class="steps-empty">Status check failed.</p>';
      return;
    }
    var html = "";
    // Health icons are small custom SVGs (v0.5) — filled circle + white
    // glyph: green check, red cross, grey dash. Same paths as the
    // check/error/skip icons in mobile_app/assets/icons/.
    var HEALTH_ICONS = {
      ok: '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><circle cx="12" cy="12" r="9.2" fill="#16A34A"/><path d="M7.9 12.4 l2.7 2.7 L16.5 9.1" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
      fail: '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><circle cx="12" cy="12" r="9.2" fill="#DC2626"/><path d="M8.4 8.4 L15.6 15.6 M15.6 8.4 L8.4 15.6" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round"/></svg>',
      skip: '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><circle cx="12" cy="12" r="9.2" fill="#94A3C8"/><path d="M8 12 h8" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round"/></svg>'
    };
    data.checks.forEach(function (c) {
      var icon = HEALTH_ICONS[c.status] || HEALTH_ICONS.skip;
      html += "<div class='health-row " + c.status + "'>" +
        "<div class='health-head'><span class='health-icon'>" + icon + "</span>" +
        escapeHtml(c.label) + "</div>";
      if (c.detail) html += "<div class='health-detail'>" + escapeHtml(c.detail) + "</div>";
      if (c.status === "fail" && c.hint) {
        html += "<div class='health-hint'>Fix: " + escapeHtml(c.hint) + "</div>";
      }
      html += "</div>";
    });
    healthList.innerHTML = html;
    healthMsg.textContent = data.all_ok
      ? "Everything looks good — Linda is ready."
      : "Some checks failed — each one shows its fix below.";
    healthMsg.className = "form-msg " + (data.all_ok ? "ok" : "error");
    // The Status button keeps its icon + "Status" label; only the warn
    // class changes (amber border + amber pulse icon via CSS).
    healthBtn.classList.toggle("warn", !data.all_ok);
  }

  function loadHealth(autoShow) {
    healthList.innerHTML = '<p class="steps-empty">Checking…</p>';
    healthMsg.classList.add("hidden");
    apiFetch("/health/detailed")
      .then(function (r) { return r.json(); })
      .then(function (data) {
        renderHealth(data);
        // First run: if something is broken, show the panel on its own
        // so the user sees what to fix instead of a silent failure.
        if (autoShow && !data.all_ok && !healthAutoShown) {
          healthAutoShown = true;
          openModal(healthModal);
        }
      })
      .catch(function () {
        healthList.innerHTML = '<p class="steps-empty">Status check failed — is the server running?</p>';
      });
  }

  healthBtn.addEventListener("click", function () {
    loadHealth(false);
    openModal(healthModal);
  });
  healthClose.addEventListener("click", function () { closeModal(healthModal); });
  healthRefresh.addEventListener("click", function () { loadHealth(false); });

  // ---- Steps rendering ----
  function renderSteps(steps) {
    if (!steps || steps.length === 0) return;
    if (renderedSteps === 0) stepsEl.innerHTML = "";
    for (var i = renderedSteps; i < steps.length; i++) {
      var s = steps[i];
      var div = document.createElement("div");
      div.className = "step";
      var head = "<div class='step-head'><span class='n'>#" + escapeHtml(s.n) +
        "</span>" + escapeHtml(s.action) + "</div>";
      var thought = s.thought
        ? "<div class='step-thought'>" + escapeHtml(s.thought) + "</div>" : "";
      var result = s.result
        ? "<div class='step-result'>" + escapeHtml(s.result) + "</div>" : "";
      div.innerHTML = head + thought + result;
      stepsEl.appendChild(div);
    }
    renderedSteps = steps.length;
    stepsEl.scrollTop = stepsEl.scrollHeight;

    // Latest step also shows inline in the agent bubble (handy on phones).
    if (agentStepLine && steps.length > 0) {
      var last = steps[steps.length - 1];
      agentStepLine.textContent = "Step " + last.n + ": " + last.action;
    }
  }

  // ---- Task polling ----
  function finishTaskUI(task) {
    stopPolling();
    if (agentBubble) {
      var text;
      if (task.status === "done") {
        text = task.result || "Done.";
      } else if (task.status === "stopped") {
        text = task.result || "Task stopped.";
      } else {
        text = "Error: " + (task.error || "something went wrong.");
      }
      agentBubble.innerHTML = "<p>" + escapeHtml(text).replace(/\n/g, "<br>") + "</p>";
      if (task.status === "error") agentBubble.classList.add("error");
      // Final reply: enable its speaker button, and read it aloud if
      // auto-speak is on (done replies only — not errors).
      agentBubble.dataset.speakText = text;
      var speakBtn = agentBubble.parentElement.querySelector(".speak-btn");
      if (speakBtn) speakBtn.classList.remove("hidden");
      if (task.status === "done" && autoSpeakEnabled()) speakText(text, speakBtn);
    }
    agentBubble = null;
    agentStepLine = null;
    currentTaskId = null; // Free the composer for the next message.
    sendBtn.disabled = false;
    stopBtn.classList.add("hidden");
    stopBtn.disabled = false;
    stopBtn.innerHTML = STOP_ICON;
    inputEl.focus();
    // If this task asked for messaging credentials, show the secure box.
    checkMessagingPending();
    // The chat's title/order may have changed — refresh the list.
    loadConversations();
  }

  function pollTask() {
    if (!currentTaskId) return;
    apiFetch("/tasks/" + currentTaskId)
      .then(function (r) { return r.json(); })
      .then(function (task) {
        renderSteps(task.steps);

        if (task.pending_approval) {
          approvalDetail.textContent =
            task.pending_approval.action + " — " + task.pending_approval.detail;
          approvalCard.classList.remove("hidden");
        } else {
          approvalCard.classList.add("hidden");
        }

        if (task.status === "done" || task.status === "error" || task.status === "stopped") {
          finishTaskUI(task);
        }
      })
      .catch(function () {
        // Transient network hiccup — keep polling.
      });
  }

  function startPolling() {
    stopPolling();
    pollTimer = setInterval(pollTask, 900);
    pollTask();
  }

  function stopPolling() {
    if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
  }

  // ---- Stop a running task ----
  stopBtn.addEventListener("click", function () {
    stopSpeaking(); // a running reply stops talking too
    if (!currentTaskId) return;
    stopBtn.disabled = true;
    stopBtn.innerHTML = "…";
    apiFetch("/tasks/" + currentTaskId + "/stop", { method: "POST" })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        if (d && d.message) showToast(d.message);
      })
      .catch(function () {
        stopBtn.disabled = false;
        stopBtn.innerHTML = STOP_ICON;
        showToast("The stop request didn't reach the server — try again.", true);
      });
  });

  // ---- Send a message ----
  function sendMessage(text) {
    text = (text || "").trim();
    if (!text || currentTaskId) return;
    stopSpeaking(); // a new message silences the previous reply

    addBubble("user", "<p>" + escapeHtml(text).replace(/\n/g, "<br>") + "</p>");
    agentBubble = addBubble(
      "agent",
      '<span class="spinner"></span>Working…<div class="step-line"></div>'
    );
    agentStepLine = agentBubble.querySelector(".step-line");
    renderedSteps = 0;
    stepsEl.innerHTML = "";
    sendBtn.disabled = true;
    stopBtn.classList.remove("hidden");

    apiFetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: text,
        conversation_id: currentConversationId,
      }),
    })
      .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, d: d }; }); })
      .then(function (res) {
        if (!res.ok || !res.d.task_id) {
          throw new Error((res.d && res.d.detail) || "Couldn't start the task.");
        }
        if (res.d.conversation_id) currentConversationId = res.d.conversation_id;
        currentTaskId = res.d.task_id;
        startPolling();
      })
      .catch(function (err) {
        stopPolling();
        currentTaskId = null;
        if (agentBubble) {
          var errText = "Error: " + (err.message || "couldn't reach the server. Is it running?");
          agentBubble.innerHTML = "<p>" + escapeHtml(errText) + "</p>";
          agentBubble.classList.add("error");
          agentBubble.dataset.speakText = errText;
          var errSpeakBtn = agentBubble.parentElement.querySelector(".speak-btn");
          if (errSpeakBtn) errSpeakBtn.classList.remove("hidden");
        }
        agentBubble = null;
        sendBtn.disabled = false;
        stopBtn.classList.add("hidden");
      });
  }

  // ---- Side chats (conversations) ----
  // Each chat has its own transcript on the server, so closing the app
  // and reopening it shows the same chat (v0.9), and the Chats list
  // switches between separate conversations. The static welcome
  // bubble stays on top; restored messages render below it, oldest
  // first. Agent replies get a working speaker button, just like
  // fresh ones. Error replies keep their red bubble (the server saves
  // them as "Error: ..."). Switching is blocked while a task runs —
  // the reply always lands in the chat it was sent from.
  var TRASH_ICON = '<svg class="btn-icon" viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><path d="M5.2 6.4 H18.8 M9.2 6.4 V4.6 a1.4 1.4 0 0 1 1.4 -1.4 h2.8 a1.4 1.4 0 0 1 1.4 1.4 V6.4 M6.6 6.4 L7.4 19.2 a1.6 1.6 0 0 0 1.6 1.4 h6 a1.6 1.6 0 0 0 1.6 -1.4 L17.4 6.4 M10 10.2 V16.6 M14 10.2 V16.6" fill="none" stroke="url(#voiceGrad)" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>';

  function clearChatBubbles() {
    // Keep the static welcome bubble (first child); drop the rest.
    while (messagesEl.children.length > 1) {
      messagesEl.removeChild(messagesEl.lastChild);
    }
    shownSecureCards = {};
    agentBubble = null;
    agentStepLine = null;
  }

  function renderHistoryMessages(messages) {
    messages.forEach(function (m) {
      if (m.role !== "user" && m.role !== "agent") return;
      var text = m.text || "";
      var isError = m.role === "agent" && text.indexOf("Error: ") === 0;
      var bubble = addBubble(
        m.role,
        "<p>" + escapeHtml(text).replace(/\n/g, "<br>") + "</p>",
        isError
      );
      if (m.role === "agent") {
        bubble.dataset.speakText = text;
        var speakBtn = bubble.parentElement.querySelector(".speak-btn");
        if (speakBtn) speakBtn.classList.remove("hidden");
      }
    });
    scrollChat();
  }

  function loadChatHistory(conversationId) {
    var url = "/chat/history" +
      (conversationId ? "?conversation_id=" + conversationId : "");
    return apiFetch(url)
      .then(function (r) { return r.json(); })
      .then(function (d) {
        if (d && d.conversation_id) currentConversationId = d.conversation_id;
        renderHistoryMessages((d && d.messages) || []);
      })
      .catch(function () {
        // Server down or history unavailable — the chat just starts
        // fresh with the welcome bubble; nothing to show the user.
      });
  }

  function formatChatDate(iso) {
    try {
      var d = new Date(iso);
      return d.toLocaleDateString(undefined, { day: "numeric", month: "short" }) +
        ", " + d.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });
    } catch (e) { return ""; }
  }

  function renderChatsList() {
    chatsList.innerHTML = "";
    if (!conversations.length) {
      chatsList.innerHTML = '<p class="steps-empty">No chats yet — start a new one.</p>';
      return;
    }
    conversations.forEach(function (c) {
      var row = document.createElement("div");
      row.className = "chat-item" + (c.id === currentConversationId ? " active" : "");
      var main = document.createElement("button");
      main.type = "button";
      main.className = "chat-item-main";
      main.innerHTML =
        '<span class="chat-item-title">' + escapeHtml(c.title || "New chat") + "</span>" +
        '<span class="chat-item-meta">' + escapeHtml(formatChatDate(c.updated_at)) +
        (c.message_count ? " · " + c.message_count + " messages" : "") + "</span>";
      main.addEventListener("click", function () { openConversation(c.id); });
      var del = document.createElement("button");
      del.type = "button";
      del.className = "chat-del-btn";
      del.title = "Delete chat";
      del.setAttribute("aria-label", "Delete chat");
      del.innerHTML = TRASH_ICON;
      del.addEventListener("click", function (ev) {
        ev.stopPropagation();
        deleteConversation(c.id, c.title);
      });
      row.appendChild(main);
      row.appendChild(del);
      chatsList.appendChild(row);
    });
  }

  function loadConversations() {
    return apiFetch("/conversations")
      .then(function (r) { return r.json(); })
      .then(function (d) {
        conversations = (d && d.conversations) || [];
        renderChatsList();
        return conversations;
      })
      .catch(function () { return conversations; });
  }

  function openConversation(id) {
    if (currentTaskId) {
      showToast("Wait for the current task to finish, or stop it first.", true);
      return;
    }
    currentConversationId = id;
    clearChatBubbles();
    closeModal(chatsModal);
    renderChatsList();
    loadChatHistory(id);
    inputEl.focus();
  }

  function newConversation() {
    if (currentTaskId) {
      showToast("Wait for the current task to finish, or stop it first.", true);
      return;
    }
    apiFetch("/conversations", { method: "POST" })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        return loadConversations().then(function () {
          openConversation(d.id);
        });
      })
      .catch(function () {
        showToast("Couldn't create a new chat — is the server running?", true);
      });
  }

  function deleteConversation(id, title) {
    if (currentTaskId && id === currentConversationId) {
      showToast("Wait for the current task to finish, or stop it first.", true);
      return;
    }
    if (!window.confirm('Delete chat "' + (title || "New chat") + '"? Its messages will be gone.')) return;
    apiFetch("/conversations/" + id, { method: "DELETE" })
      .then(function (r) { return r.json(); })
      .then(function () { return loadConversations(); })
      .then(function () {
        if (id === currentConversationId) {
          if (conversations.length) {
            openConversation(conversations[0].id);
          } else {
            newConversation();
          }
        } else {
          renderChatsList();
        }
      })
      .catch(function () {
        showToast("Couldn't delete the chat — try again.", true);
      });
  }

  function initConversations() {
    loadConversations().then(function () {
      if (conversations.length) {
        currentConversationId = conversations[0].id;
        renderChatsList();
        loadChatHistory(currentConversationId);
      } else {
        // First run ever — the server creates the first chat on demand.
        loadChatHistory(null).then(loadConversations);
      }
    });
  }

  chatsBtn.addEventListener("click", function () {
    loadConversations();
    openModal(chatsModal);
  });
  chatsClose.addEventListener("click", function () { closeModal(chatsModal); });
  newChatBtn.addEventListener("click", newConversation);
  newChatBtn2.addEventListener("click", newConversation);

  // Composer grows as you type (up to 120px). The grow logic lives in
  // one place so typing and sending can never disagree about height.
  function autosizeComposer() {
    inputEl.style.height = "auto";
    inputEl.style.height = Math.min(inputEl.scrollHeight, 120) + "px";
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    var text = inputEl.value;
    inputEl.value = "";
    // Snap back to a single line IMMEDIATELY on send: drop the inline
    // height entirely (back to the rows="1" default) instead of leaving
    // a stale two-line height behind after the programmatic clear.
    inputEl.style.removeProperty("height");
    sendMessage(text);
  });

  // Enter sends, Shift+Enter makes a new line. Textarea grows as you type.
  inputEl.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      form.requestSubmit();
    }
  });
  inputEl.addEventListener("input", autosizeComposer);

  // ---- Approval buttons (ask mode only) ----
  function decide(approve) {
    if (!currentTaskId) return;
    apiFetch("/tasks/" + currentTaskId + "/approve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ approve: approve }),
    }).catch(function () { /* polling will surface any problem */ });
    approvalCard.classList.add("hidden");
  }
  document.getElementById("approveYes").addEventListener("click", function () { decide(true); });
  document.getElementById("approveNo").addEventListener("click", function () { decide(false); });

  // ---- Secure credential box (v0.7) ----
  // When the user enables WhatsApp/Instagram auto-reply in chat and a
  // token/ID is missing, the server records a pending request and this
  // renders a masked input card in the chat flow. The token is pasted
  // here once — never as a plain chat message — saved to .env, and
  // auto-reply starts. Values are never logged or shown back.
  var SECURE_FIELD_META = {
    whatsapp: {
      token: { label: "WhatsApp access token", hint: "Meta dashboard → WhatsApp → API Setup → permanent token (create it via a System User). Steps: MESSAGING_SETUP.md Part A." },
      target_id: { label: "WhatsApp phone number ID", hint: "Find it in Meta dashboard → WhatsApp → API Setup." },
      verify_token: { label: "Verify token", hint: "Make up any secret string (e.g. linda-verify-12345) — enter the same string when verifying the webhook in the Meta dashboard." },
      app_secret: { label: "App secret (optional)", hint: "Meta app → Settings → Basic → App Secret. Used to check webhook signatures — optional, it works without it.", optional: true }
    },
    instagram: {
      token: { label: "Instagram access token (Page token)", hint: "Access token of the linked Facebook Page. Steps: MESSAGING_SETUP.md Part B." },
      target_id: { label: "Facebook Page ID", hint: "ID of the Facebook Page linked to Instagram." },
      verify_token: { label: "Verify token", hint: "Make up any secret string — enter the same string when verifying the webhook in the Meta dashboard." },
      app_secret: { label: "App secret (optional)", hint: "Meta app → Settings → Basic → App Secret. Used to check webhook signatures.", optional: true }
    }
  };
  var SECURE_FIELD_ORDER = ["token", "target_id", "verify_token", "app_secret"];
  var shownSecureCards = {}; // key -> card element (one card per request)
  var dismissedSecureCards = {}; // key -> true (hidden for this session)

  var LOCK_ICON = '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path d="M7.5 10.5 V7.8 a4.5 4.5 0 0 1 9 0 v2.7" fill="none" stroke="url(#voiceGrad)" stroke-width="1.8" stroke-linecap="round"/><rect x="5" y="10.5" width="14" height="9.5" rx="3" fill="url(#voiceGrad)"/><circle cx="12" cy="14.6" r="1.4" fill="#fff"/></svg>';
  var CLOSE_ICON = '<svg viewBox="0 0 24 24" width="14" height="14" aria-hidden="true"><path d="M6.8 6.8 L17.2 17.2 M17.2 6.8 L6.8 17.2" fill="none" stroke="url(#voiceGrad)" stroke-width="2.1" stroke-linecap="round"/></svg>';

  function secureCardKey(platform, fields) {
    return platform + ":" + fields.slice().sort().join(",");
  }

  function checkMessagingPending() {
    apiFetch("/messaging/pending")
      .then(function (r) { return r.json(); })
      .then(function (d) {
        var pending = (d && d.pending) || [];
        pending.forEach(function (req) {
          var key = secureCardKey(req.platform, req.fields);
          if (shownSecureCards[key] || dismissedSecureCards[key]) return;
          renderSecureCard(req.platform, req.fields, key);
        });
      })
      .catch(function () { /* server down — try again after the next task */ });
  }

  function renderSecureCard(platform, fields, key) {
    var meta = SECURE_FIELD_META[platform] || {};
    var name = platform === "whatsapp" ? "WhatsApp" : "Instagram";
    var ordered = SECURE_FIELD_ORDER.filter(function (f) { return fields.indexOf(f) !== -1; });
    if (ordered.length === 0) return;

    var card = document.createElement("div");
    card.className = "secure-card";
    var head = document.createElement("div");
    head.className = "secure-card-head";
    head.innerHTML = LOCK_ICON + '<span class="secure-card-title">' + escapeHtml(name) + ' setup — secure box</span>';
    var closeBtn = document.createElement("button");
    closeBtn.className = "secure-card-close";
    closeBtn.setAttribute("aria-label", "Close");
    closeBtn.innerHTML = CLOSE_ICON;
    closeBtn.addEventListener("click", function () {
      dismissedSecureCards[key] = true;
      delete shownSecureCards[key];
      card.remove();
    });
    head.appendChild(closeBtn);
    card.appendChild(head);

    var note = document.createElement("p");
    note.className = "secure-card-note";
    note.textContent = "Paste the token here — this is not a chat message, and the token will never be shown (it stays masked). Auto-reply starts as soon as you save.";
    card.appendChild(note);

    var inputs = {};
    ordered.forEach(function (field) {
      var m = meta[field] || { label: field };
      var wrap = document.createElement("label");
      wrap.className = "field";
      var lab = document.createElement("span");
      lab.className = "field-label";
      lab.textContent = m.label;
      var input = document.createElement("input");
      input.type = (field === "target_id") ? "text" : "password";
      input.autocomplete = "off";
      input.placeholder = m.optional ? "Optional — you can leave it blank" : "";
      var hint = document.createElement("span");
      hint.className = "field-hint";
      hint.textContent = m.hint || "";
      wrap.appendChild(lab);
      wrap.appendChild(input);
      wrap.appendChild(hint);
      card.appendChild(wrap);
      inputs[field] = input;
    });

    var msg = document.createElement("div");
    msg.className = "form-msg hidden secure-card-msg";
    card.appendChild(msg);

    var saveBtn = document.createElement("button");
    saveBtn.className = "btn btn-yes";
    saveBtn.style.width = "100%";
    saveBtn.textContent = "Save — turn on auto-reply";
    saveBtn.addEventListener("click", function () {
      var values = {};
      ordered.forEach(function (field) {
        var v = inputs[field].value.trim();
        if (v) values[field] = v;
      });
      if (Object.keys(values).length === 0) {
        msg.textContent = "Enter something first — all fields are empty.";
        msg.className = "form-msg error secure-card-msg";
        return;
      }
      saveBtn.disabled = true;
      saveBtn.textContent = "Saving…";
      msg.classList.add("hidden");
      apiFetch("/messaging/credentials", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ platform: platform, values: values })
      })
        .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, d: d }; }); })
        .then(function (res) {
          if (!res.ok) throw new Error((res.d && res.d.detail) || "Couldn't save.");
          // Clear the inputs (values must not linger in the DOM) and
          // show the server's message in place of the form.
          ordered.forEach(function (field) { inputs[field].value = ""; });
          delete shownSecureCards[key];
          card.innerHTML = "";
          var done = document.createElement("p");
          done.className = "secure-card-done";
          done.textContent = (res.d && res.d.message) || "Saved.";
          card.appendChild(done);
          showToast("Credentials saved.");
          // Anything still missing gets a fresh card.
          setTimeout(checkMessagingPending, 600);
        })
        .catch(function (err) {
          msg.textContent = err.message || "Couldn't save.";
          msg.className = "form-msg error secure-card-msg";
          saveBtn.disabled = false;
          saveBtn.textContent = "Save — turn on auto-reply";
        });
    });
    card.appendChild(saveBtn);

    messagesEl.appendChild(card);
    shownSecureCards[key] = card;
    scrollChat();
  }

  // (v0.5: the demo suggestion chips were removed — the composer sits
  // clean at the bottom. The demo prompts still live in DEMO_GUIDE.md.)

  // ---- Steps bottom sheet (phones) ----
  function openSheet() {
    stepsCol.classList.add("open");
    backdrop.classList.remove("hidden");
  }
  function closeSheet() {
    stepsCol.classList.remove("open");
    backdrop.classList.add("hidden");
  }
  stepsBtn.addEventListener("click", openSheet);
  stepsClose.addEventListener("click", closeSheet);
  backdrop.addEventListener("click", closeSheet);

  // ---- PWA: register the service worker ----
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", function () {
      navigator.serviceWorker.register("/sw.js").catch(function () {
        /* Offline caching is a bonus; the app works without it. */
      });
    });
  }

  refreshHealth();
  setInterval(refreshHealth, 30000);
  loadHealth(true); // Auto-show the Status panel on first run if broken.
  initConversations(); // side chats: open the most recent chat + its history.
  checkMessagingPending(); // Show the secure box if a setup is waiting.
  // The static welcome bubble gets its speaker button too.
  (function () {
    var welcome = messagesEl.querySelector(".msg.agent .bubble");
    if (welcome) {
      welcome.dataset.speakText = welcome.innerText || "";
      var btn = attachSpeakButton(welcome.parentElement, welcome);
      if (btn) btn.classList.remove("hidden");
    }
  })();
  inputEl.focus();
})();

