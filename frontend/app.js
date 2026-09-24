/**
 * FinNews AI – Frontend Application Logic
 * Integrates FastAPI REST Endpoints, Groq LLaMA 3.3-70B, NewsAPI, and Web Speech API
 */

const API_BASE = "";

const SCENARIO_META = {
  retail_investor: {
    name: "Retail Investor",
    icon: "📈",
    desc: "Summaries focus on stock market valuations, individual company fundamentals, and portfolio impacts without Wall Street slang."
  },
  student: {
    name: "Finance Student",
    icon: "🎓",
    desc: "Explains macroeconomic theory, interest rate mechanics, and central bank transmission channels with intuitive analogies."
  },
  professional: {
    name: "Busy Professional",
    icon: "⏱️",
    desc: "Provides a 60-second executive briefing focusing on CapEx allocations, free cash flow margins, and board-level risk factors."
  },
  volatility: {
    name: "High Volatility",
    icon: "⚡",
    desc: "Delivers rapid catalyst breakdowns, liquidation analysis, order book liquidity conditions, and near-term market risk levels."
  }
};

const MODE_META = {
  financial_news: "Prompt: Financial Simplification",
  market_event: "Prompt: Market Event Explanation",
  economic: "Prompt: Macro & Rates Overview",
  business: "Prompt: Business & CapEx Analysis",
  jargon_free: "Prompt: Jargon-Free Translation"
};

const state = {
  currentPersona: "retail_investor",
  currentMode: "financial_news",
  currentCategory: "all",
  searchQuery: "",
  articles: [],
  cardViews: {}, // article_id -> 'simplified' | 'original'
  isSpeaking: false,
  activeSpeechBtn: null
};

// DOM Elements
const newsGrid = document.getElementById("newsGrid");
const fetchSimplifyBtn = document.getElementById("fetchSimplifyBtn");
const mainSpinner = document.getElementById("mainSpinner");
const scenarioTabs = document.getElementById("scenarioTabs");
const categoryFilters = document.getElementById("categoryFilters");
const modeFilters = document.getElementById("modeFilters");
const searchInput = document.getElementById("searchInput");
const clearSearchBtn = document.getElementById("clearSearchBtn");
const refreshBtn = document.getElementById("refreshBtn");
const articleCountEl = document.getElementById("articleCount");
const activePersonaBadge = document.getElementById("activePersonaBadge");
const activeModeBadge = document.getElementById("activeModeBadge");
const scenarioBanner = document.getElementById("scenarioBanner");
const bannerIcon = document.getElementById("bannerIcon");
const bannerTitle = document.getElementById("bannerTitle");
const bannerDesc = document.getElementById("bannerDesc");

// Modals
const customModal = document.getElementById("customModal");
const customSimplifyBtn = document.getElementById("customSimplifyBtn");
const closeCustomModal = document.getElementById("closeCustomModal");
const cancelCustomBtn = document.getElementById("cancelCustomBtn");
const submitCustomBtn = document.getElementById("submitCustomBtn");
const customModeSelect = document.getElementById("customModeSelect");

const settingsModal = document.getElementById("settingsModal");
const settingsBtn = document.getElementById("settingsBtn");
const closeSettingsModal = document.getElementById("closeSettingsModal");
const closeSettingsBtn = document.getElementById("closeSettingsBtn");
const saveKeysBtn = document.getElementById("saveKeysBtn");
const groqKeyInput = document.getElementById("groqKeyInput");
const newsApiKeyInput = document.getElementById("newsApiKeyInput");

const bookmarksModal = document.getElementById("bookmarksModal");
const bookmarksBtn = document.getElementById("bookmarksBtn");
const closeBookmarksModal = document.getElementById("closeBookmarksModal");
const closeBookmarksBtn = document.getElementById("closeBookmarksBtn");
const bookmarksList = document.getElementById("bookmarksList");
const bookmarkCount = document.getElementById("bookmarkCount");

const jargonPopover = document.getElementById("jargonPopover");
const popoverTerm = document.getElementById("popoverTerm");
const popoverDefinition = document.getElementById("popoverDefinition");
const closePopoverBtn = document.getElementById("closePopoverBtn");

// Initialize App
let autoRefreshTimer = null;

document.addEventListener("DOMContentLoaded", () => {
  initApp();
  setupEventListeners();
});

async function initApp() {
  updateScenarioBanner();
  await checkHealth();
  await loadNews(true, true);
  await updateBookmarkCount();

  // Automated live polling every 60 seconds
  if (autoRefreshTimer) clearInterval(autoRefreshTimer);
  autoRefreshTimer = setInterval(() => {
    // Only background refresh when user is not actively searching
    if (!document.hidden && !state.searchQuery) {
      loadNews(false, true);
    }
  }, 60000);
}

// Relative time formatting helper
function formatTimeAgo(dateString) {
  if (!dateString) return "Live";
  const date = new Date(dateString);
  const now = new Date();
  const diffSec = Math.floor((now - date) / 1000);
  if (diffSec < 45) return "Just now";
  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;
  const diffDays = Math.floor(diffHr / 24);
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

// Event Listeners
function setupEventListeners() {
  // Scenario Tabs
  scenarioTabs.addEventListener("click", (e) => {
    const tab = e.target.closest(".scenario-tab");
    if (!tab) return;
    const persona = tab.dataset.persona;
    if (persona && persona !== state.currentPersona) {
      document.querySelectorAll(".scenario-tab").forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      state.currentPersona = persona;
      updateScenarioBanner();
      loadNews(false);
      showToast(`Switched perspective to ${SCENARIO_META[persona].name}`);
    }
  });

  // Category Pills
  categoryFilters.addEventListener("click", (e) => {
    const pill = e.target.closest(".cat-pill");
    if (!pill) return;
    document.querySelectorAll(".cat-pill").forEach(p => p.classList.remove("active"));
    pill.classList.add("active");
    state.currentCategory = pill.dataset.category;
    loadNews(true, true);
  });

  // Prompt Analysis Mode Pills
  if (modeFilters) {
    modeFilters.addEventListener("click", (e) => {
      const pill = e.target.closest(".mode-pill");
      if (!pill) return;
      document.querySelectorAll(".mode-pill").forEach(p => p.classList.remove("active"));
      pill.classList.add("active");
      state.currentMode = pill.dataset.mode;
      if (activeModeBadge) {
        activeModeBadge.textContent = MODE_META[state.currentMode] || `Prompt: ${state.currentMode}`;
      }
      showToast(`AI Prompt Mode: ${pill.textContent.trim()}`);
    });
  }

  // Hero Fetch & Simplify Button
  fetchSimplifyBtn.addEventListener("click", handleFetchAndSimplify);

  // Search Input with Debounce
  let searchTimeout;
  searchInput.addEventListener("input", (e) => {
    clearTimeout(searchTimeout);
    state.searchQuery = e.target.value.trim();
    clearSearchBtn.style.display = state.searchQuery ? "block" : "none";
    searchTimeout = setTimeout(() => {
      loadNews(true, true);
    }, 350);
  });

  clearSearchBtn.addEventListener("click", () => {
    searchInput.value = "";
    state.searchQuery = "";
    clearSearchBtn.style.display = "none";
    loadNews(true, true);
  });

  refreshBtn.addEventListener("click", () => {
    loadNews(true, true);
  });

  // Custom Article Modal
  customSimplifyBtn.addEventListener("click", () => {
    customModal.style.display = "flex";
  });
  closeCustomModal.addEventListener("click", () => customModal.style.display = "none");
  cancelCustomBtn.addEventListener("click", () => customModal.style.display = "none");
  submitCustomBtn.addEventListener("click", handleCustomArticleSubmit);

  // Settings Modal
  settingsBtn.addEventListener("click", () => {
    checkHealth();
    settingsModal.style.display = "flex";
  });
  closeSettingsModal.addEventListener("click", () => settingsModal.style.display = "none");
  closeSettingsBtn.addEventListener("click", () => settingsModal.style.display = "none");
  saveKeysBtn.addEventListener("click", handleSaveKeys);

  // Bookmarks Modal
  bookmarksBtn.addEventListener("click", showBookmarksModal);
  closeBookmarksModal.addEventListener("click", () => bookmarksModal.style.display = "none");
  closeBookmarksBtn.addEventListener("click", () => bookmarksModal.style.display = "none");

  // Jargon Popover Close
  closePopoverBtn.addEventListener("click", () => {
    jargonPopover.style.display = "none";
  });

  document.addEventListener("click", (e) => {
    if (!e.target.closest(".jargon-popover") && !e.target.closest(".jargon-chip")) {
      jargonPopover.style.display = "none";
    }
  });
}

function updateScenarioBanner() {
  const meta = SCENARIO_META[state.currentPersona];
  bannerIcon.textContent = meta.icon;
  bannerTitle.textContent = `${meta.name} Perspective Active:`;
  bannerDesc.textContent = meta.desc;
  activePersonaBadge.textContent = `Persona: ${meta.name}`;
}

// Health Check
async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE}/api/health`);
    const data = await res.json();
    
    // Header pills
    const aiText = document.getElementById("aiStatusText");
    const newsText = document.getElementById("newsStatusText");
    if (data.ai_engine.configured) {
      aiText.textContent = "Groq LLaMA 3.3 (Live)";
    } else {
      aiText.textContent = "Groq AI (Demo Mode)";
    }

    if (data.news_provider.configured) {
      newsText.textContent = "Live Multi-Wire (Active)";
    } else {
      newsText.textContent = "Financial Feed (Curated)";
    }

    // Modal diagnostics
    document.getElementById("diagGroqStatus").textContent = data.ai_engine.status;
    document.getElementById("diagNewsStatus").textContent = data.news_provider.status;
    document.getElementById("diagDbStatus").textContent = `Connected (${data.database.articles_count} articles stored)`;
  } catch (err) {
    console.error("Health check error:", err);
  }
}

// Load News Articles
async function loadNews(showSkeletons = false, forceRefresh = false) {
  const refreshIcon = document.getElementById("refreshIcon");
  const lastUpdatedEl = document.getElementById("lastUpdated");
  const liveStatusText = document.getElementById("liveStatusText");

  if (refreshIcon && forceRefresh) {
    refreshIcon.classList.add("spinning");
  }

  if (showSkeletons) {
    renderSkeletons();
  }

  try {
    const params = new URLSearchParams({
      category: state.currentCategory,
      persona: state.currentPersona,
      limit: 12
    });
    if (state.searchQuery) {
      params.append("query", state.searchQuery);
    }
    if (forceRefresh) {
      params.append("refresh", "true");
    }

    const res = await fetch(`${API_BASE}/api/news?${params.toString()}`);
    const data = await res.json();

    if (data.success && data.articles) {
      state.articles = data.articles;
      renderArticles(data.articles);
      articleCountEl.textContent = `${data.articles.length} financial articles`;
      
      const nowStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      if (lastUpdatedEl) {
        lastUpdatedEl.textContent = `Updated: ${nowStr}`;
      }
      if (liveStatusText && data.provider) {
        liveStatusText.textContent = data.provider.includes("NewsAPI") ? "LIVE • NEWSAPI" : "LIVE • REAL-TIME";
      }
      if (forceRefresh && showSkeletons) {
        showToast(`Refreshed live news (${data.articles.length} stories)`, "info");
      }
    } else {
      newsGrid.innerHTML = `<div class="empty-state"><p>No articles found for this filter.</p></div>`;
      articleCountEl.textContent = `0 articles`;
    }
  } catch (err) {
    console.error("Failed to load news:", err);
    newsGrid.innerHTML = `
      <div class="empty-state">
        <p>⚠️ Unable to connect to FinNews AI Backend. Ensure the FastAPI server is running on port 8000.</p>
        <button class="btn btn-outline" onclick="loadNews(true, true)">Retry</button>
      </div>`;
    articleCountEl.textContent = `Offline`;
  } finally {
    if (refreshIcon) {
      refreshIcon.classList.remove("spinning");
    }
  }
}

// 1-Click "Fetch & Simplify"
async function handleFetchAndSimplify() {
  fetchSimplifyBtn.disabled = true;
  mainSpinner.style.display = "inline-block";
  showToast("Fetching latest financial articles and generating LLaMA 3.3-70B summaries...");

  try {
    const params = new URLSearchParams({
      persona: state.currentPersona,
      mode: state.currentMode,
      category: state.currentCategory,
      limit: 6
    });

    const res = await fetch(`${API_BASE}/api/news/fetch-and-simplify?${params.toString()}`, {
      method: "POST"
    });
    const data = await res.json();

    if (data.success && data.articles) {
      state.articles = data.articles;
      renderArticles(data.articles);
      showToast(`Successfully simplified ${data.articles.length} articles!`);
    } else {
      showToast("Could not complete Fetch & Simplify.", "error");
    }
  } catch (err) {
    console.error("Fetch & Simplify error:", err);
    showToast("Error communicating with backend.", "error");
  } finally {
    fetchSimplifyBtn.disabled = false;
    mainSpinner.style.display = "none";
  }
}

// Render News Cards
function renderArticles(articles) {
  if (!articles || articles.length === 0) {
    newsGrid.innerHTML = `<div class="empty-state"><p>No news articles found.</p></div>`;
    return;
  }

  newsGrid.innerHTML = articles.map(art => {
    const summary = art.summary;
    const isBookmarked = art.is_bookmarked;
    const viewMode = state.cardViews[art.id] || "simplified";
    const hasSummary = Boolean(summary);

    // Format Sentiment Badge & Model Badge
    let sentimentBadge = "";
    let modelBadge = "";
    if (summary) {
      const sent = (summary.market_sentiment || "Neutral").toLowerCase();
      const scorePct = Math.round((summary.sentiment_score || 0.5) * 100);
      sentimentBadge = `
        <span class="sentiment-badge ${sent}">
          ${sent === 'bullish' ? '📈 Bullish' : sent === 'bearish' ? '📉 Bearish' : '⚖️ Neutral'} (${scorePct}%)
        </span>
      `;
      if (summary.model_used) {
        const displayModel = summary.model_used.includes("llama") ? "LLaMA 3.3-70B" : summary.model_used;
        modelBadge = `<span class="model-badge" title="Model: ${summary.model_used}">⚡ ${displayModel}</span>`;
      }
    }

    // Jargon Chips
    let jargonHtml = "";
    if (summary && summary.jargon_demystified && Object.keys(summary.jargon_demystified).length > 0) {
      const chips = Object.entries(summary.jargon_demystified).map(([term, def]) => {
        // Safe escaping for attributes
        const safeDef = def.replace(/"/g, '&quot;');
        return `<span class="jargon-chip" onclick="handleJargonClick(this, '${term}', '${safeDef}')">💡 ${term}</span>`;
      }).join("");
      jargonHtml = `
        <div class="section-block">
          <div class="section-title-sm">Demystified Jargon (Click for explanation):</div>
          <div class="jargon-chips">${chips}</div>
        </div>
      `;
    }

    // Takeaways
    let takeawaysHtml = "";
    if (summary && summary.key_takeaways && summary.key_takeaways.length > 0) {
      const items = summary.key_takeaways.map(t => `
        <li class="takeaway-item">
          <span class="takeaway-bullet">✓</span>
          <span>${t}</span>
        </li>
      `).join("");
      takeawaysHtml = `
        <div class="section-block">
          <div class="section-title-sm">Key Takeaways:</div>
          <ul class="takeaway-list">${items}</ul>
        </div>
      `;
    }

    // Executive summary & audio button
    let execHtml = "";
    if (summary) {
      const audioSafeText = encodeURIComponent(summary.executive_summary || "");
      const modeLabel = summary.mode ? summary.mode.replace('_', ' ') : "";
      execHtml = `
        <div class="exec-summary-box">
          <div class="exec-summary-header">
            <span style="display:flex; align-items:center; gap:8px;">
              <span>Executive Summary</span>
              ${modeLabel ? `<span class="mode-tag">${modeLabel}</span>` : ''}
            </span>
            <button class="tts-btn" onclick="toggleAudioSpeech('${art.id}', '${audioSafeText}', this)">
              🔊 Read Aloud
            </button>
          </div>
          <p>${summary.executive_summary}</p>
        </div>
        <div class="section-block">
          <div class="section-title-sm">What Happened:</div>
          <p class="text-muted" style="font-size:0.85rem;">${summary.what_happened}</p>
        </div>
        <div class="section-block">
          <div class="section-title-sm">Why It Matters:</div>
          <p class="text-muted" style="font-size:0.85rem;">${summary.why_it_matters}</p>
        </div>
      `;
    } else {
      execHtml = `
        <div class="empty-summary-prompt" style="padding: 20px 0; text-align: center;">
          <p class="text-muted" style="margin-bottom: 12px;">This article hasn't been simplified yet.</p>
          <button class="btn btn-primary btn-sm" onclick="simplifySingleArticle('${art.id}', this)">
            ⚡ Simplify with AI
          </button>
        </div>
      `;
    }

    const formattedDate = formatTimeAgo(art.published_at);

    return `
      <article class="news-card" id="card-${art.id}">
        <div class="card-image-wrap">
          <img class="card-image" src="${art.url_to_image || 'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=800&q=80'}" alt="${art.title}" loading="lazy" onerror="this.src='https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=800&q=80'">
          <div class="card-top-tags">
            <span class="source-tag">${art.source || 'Financial Wire'} • ${formattedDate}</span>
            <div style="display:flex; align-items:center; gap:6px;">
              ${modelBadge}
              <button class="bookmark-star-btn ${isBookmarked ? 'bookmarked' : ''}" onclick="toggleBookmark('${art.id}', this)" title="${isBookmarked ? 'Remove bookmark' : 'Bookmark article'}">
                ★
              </button>
            </div>
          </div>
        </div>

        <div class="card-body">
          <h4 class="card-title">${art.title}</h4>

          <!-- Mode switcher -->
          <div class="card-view-tabs">
            <button class="card-view-tab ${viewMode === 'simplified' ? 'active' : ''}" onclick="switchCardView('${art.id}', 'simplified')">
              ✨ FinNews AI Simplified
            </button>
            <button class="card-view-tab ${viewMode === 'original' ? 'active' : ''}" onclick="switchCardView('${art.id}', 'original')">
              📰 Original Source
            </button>
          </div>

          <!-- Simplified Content Pane -->
          <div class="simplified-content" id="simplified-${art.id}" style="display: ${viewMode === 'simplified' ? 'flex' : 'none'};">
            ${execHtml}
            ${takeawaysHtml}
            ${jargonHtml}
          </div>

          <!-- Original Content Pane -->
          <div class="original-content" id="original-${art.id}" style="display: ${viewMode === 'original' ? 'flex' : 'none'};">
            <p>${art.description || art.content || 'Full article text available at publisher website.'}</p>
            <a href="${art.url}" target="_blank" rel="noopener noreferrer" class="original-link">
              Read original article on ${art.source || 'external site'} ↗
            </a>
          </div>

          <div class="card-footer">
            ${sentimentBadge}
            ${!hasSummary ? `
              <button class="btn btn-outline btn-sm simplify-action-btn" onclick="simplifySingleArticle('${art.id}', this)">
                ⚡ Simplify
              </button>
            ` : `
              <button class="btn btn-ghost btn-sm" onclick="simplifySingleArticle('${art.id}', this, true)" title="Regenerate summary with current persona">
                🔄 Re-analyze
              </button>
            `}
          </div>
        </div>
      </article>
    `;
  }).join("");
}

// Switch between Simplified & Original tabs within a card
window.switchCardView = function(articleId, mode) {
  state.cardViews[articleId] = mode;
  const simp = document.getElementById(`simplified-${articleId}`);
  const orig = document.getElementById(`original-${articleId}`);
  const card = document.getElementById(`card-${articleId}`);
  if (!simp || !orig || !card) return;

  const tabs = card.querySelectorAll(".card-view-tab");
  if (mode === "simplified") {
    simp.style.display = "flex";
    orig.style.display = "none";
    tabs[0].classList.add("active");
    tabs[1].classList.remove("active");
  } else {
    simp.style.display = "none";
    orig.style.display = "flex";
    tabs[0].classList.remove("active");
    tabs[1].classList.add("active");
  }
};

// Simplify Single Article
window.simplifySingleArticle = async function(articleId, btnElement, forceRefresh = false) {
  if (btnElement) {
    btnElement.disabled = true;
    btnElement.innerHTML = `<span class="btn-spinner"></span> Simplifying...`;
  }

  try {
    const res = await fetch(`${API_BASE}/api/news/simplify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        article_id: articleId,
        persona: state.currentPersona,
        mode: state.currentMode,
        force_refresh: forceRefresh
      })
    });

    const data = await res.json();
    if (data.success && data.summary) {
      // Update article in state
      const target = state.articles.find(a => a.id === articleId);
      if (target) {
        target.summary = data.summary;
      }
      renderArticles(state.articles);
      showToast(`Article simplified for ${SCENARIO_META[state.currentPersona].name}!`);
    } else {
      showToast("Failed to simplify article.", "error");
    }
  } catch (err) {
    console.error("Single article simplify failed:", err);
    showToast("Error simplifying article.", "error");
  }
};

// Jargon Popover Click Handler
window.handleJargonClick = function(chipElement, term, definition) {
  const rect = chipElement.getBoundingClientRect();
  popoverTerm.textContent = term;
  popoverDefinition.textContent = definition;

  // Position relative to viewport
  const top = rect.bottom + window.scrollY + 8;
  const left = Math.min(rect.left + window.scrollX, window.innerWidth - 320);

  jargonPopover.style.top = `${top}px`;
  jargonPopover.style.left = `${left}px`;
  jargonPopover.style.display = "block";
};

// Text-to-Speech (TTS) Reader
window.toggleAudioSpeech = function(articleId, encodedText, btnElement) {
  const synth = window.speechSynthesis;
  if (!synth) {
    showToast("Web Speech API not supported in your browser.", "error");
    return;
  }

  // If already speaking this article, pause/cancel
  if (state.isSpeaking && state.activeSpeechBtn === btnElement) {
    synth.cancel();
    state.isSpeaking = false;
    btnElement.classList.remove("speaking");
    btnElement.innerHTML = "🔊 Read Aloud";
    return;
  }

  // If speaking another article, stop previous
  synth.cancel();
  if (state.activeSpeechBtn) {
    state.activeSpeechBtn.classList.remove("speaking");
    state.activeSpeechBtn.innerHTML = "🔊 Read Aloud";
  }

  const plainText = decodeURIComponent(encodedText);
  const utterance = new SpeechSynthesisUtterance(plainText);
  utterance.rate = 1.0;
  utterance.pitch = 1.0;

  utterance.onstart = () => {
    state.isSpeaking = true;
    state.activeSpeechBtn = btnElement;
    btnElement.classList.add("speaking");
    btnElement.innerHTML = "⏹ Stop Audio";
  };

  utterance.onend = utterance.onerror = () => {
    state.isSpeaking = false;
    btnElement.classList.remove("speaking");
    btnElement.innerHTML = "🔊 Read Aloud";
    state.activeSpeechBtn = null;
  };

  synth.speak(utterance);
};

// Toggle Bookmark
window.toggleBookmark = async function(articleId, btnElement) {
  try {
    const res = await fetch(`${API_BASE}/api/news/bookmark/${articleId}`, { method: "POST" });
    const data = await res.json();
    if (data.success) {
      if (btnElement) {
        btnElement.classList.toggle("bookmarked", data.is_bookmarked);
      }
      // Update state
      const target = state.articles.find(a => a.id === articleId);
      if (target) {
        target.is_bookmarked = data.is_bookmarked;
      }
      await updateBookmarkCount();
      showToast(data.message);
    }
  } catch (err) {
    console.error("Bookmark toggle failed:", err);
  }
};

// Update Bookmark Count Badge
async function updateBookmarkCount() {
  try {
    const res = await fetch(`${API_BASE}/api/news/bookmarks`);
    const data = await res.json();
    if (data.success) {
      bookmarkCount.textContent = data.count || 0;
    }
  } catch (e) {
    // Ignore
  }
}

// Show Bookmarks Modal
async function showBookmarksModal() {
  bookmarksModal.style.display = "flex";
  bookmarksList.innerHTML = `<p class="text-muted">Loading saved articles...</p>`;

  try {
    const res = await fetch(`${API_BASE}/api/news/bookmarks`);
    const data = await res.json();

    if (data.success && data.articles.length > 0) {
      bookmarksList.innerHTML = data.articles.map(art => `
        <div class="bookmark-item" style="padding:12px 0; border-bottom:1px solid var(--border-subtle); display:flex; justify-content:space-between; align-items:center;">
          <div>
            <strong style="color:var(--text-main); font-size:0.95rem;">${art.title}</strong>
            <p style="font-size:0.8rem; color:var(--text-dim); margin-top:4px;">${art.source} • ${art.category}</p>
          </div>
          <button class="btn btn-outline btn-sm" onclick="simplifySingleArticle('${art.id}'); bookmarksModal.style.display='none';">
            View / Simplify
          </button>
        </div>
      `).join("");
    } else {
      bookmarksList.innerHTML = `<p class="text-muted">No saved articles yet.</p>`;
    }
  } catch (err) {
    bookmarksList.innerHTML = `<p class="text-muted">Failed to load saved articles.</p>`;
  }
}

// Custom Article Submit
async function handleCustomArticleSubmit() {
  const titleInput = document.getElementById("customTitleInput");
  const contentInput = document.getElementById("customContentInput");
  const personaSelect = document.getElementById("customPersonaSelect");
  const modeSelect = document.getElementById("customModeSelect");

  const title = titleInput.value.trim();
  const content = contentInput.value.trim();
  const persona = personaSelect ? personaSelect.value : state.currentPersona;
  const mode = modeSelect ? modeSelect.value : state.currentMode;

  if (!title || !content) {
    showToast("Please provide both headline and content.", "error");
    return;
  }

  submitCustomBtn.disabled = true;
  submitCustomBtn.innerHTML = `<span class="btn-spinner"></span> Analyzing with Groq AI...`;

  try {
    const res = await fetch(`${API_BASE}/api/news/simplify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: title,
        content: content,
        persona: persona,
        mode: mode,
        source: "User Submission"
      })
    });

    const data = await res.json();
    if (data.success) {
      customModal.style.display = "none";
      titleInput.value = "";
      contentInput.value = "";
      showToast("Custom article successfully simplified!");
      // Reload news to show custom article at the top
      await loadNews(false);
    } else {
      showToast("Failed to process custom article.", "error");
    }
  } catch (err) {
    console.error("Custom article failed:", err);
    showToast("Error processing article.", "error");
  } finally {
    submitCustomBtn.disabled = false;
    submitCustomBtn.innerHTML = `<span>⚡ Simplify with FinNews AI</span>`;
  }
}

// Save API Keys
async function handleSaveKeys() {
  const groqKey = groqKeyInput.value.trim();
  const newsKey = newsApiKeyInput.value.trim();

  saveKeysBtn.disabled = true;
  saveKeysBtn.textContent = "Saving...";

  try {
    const res = await fetch(`${API_BASE}/api/health/keys`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        groq_api_key: groqKey || undefined,
        news_api_key: newsKey || undefined
      })
    });

    const data = await res.json();
    if (data.success) {
      showToast("API credentials updated successfully!");
      settingsModal.style.display = "none";
      groqKeyInput.value = "";
      newsApiKeyInput.value = "";
      await checkHealth();
    } else {
      showToast("Failed to save credentials.", "error");
    }
  } catch (err) {
    console.error("Save keys failed:", err);
    showToast("Error saving credentials.", "error");
  } finally {
    saveKeysBtn.disabled = false;
    saveKeysBtn.textContent = "Save Configuration";
  }
}

// Skeleton Loader
function renderSkeletons() {
  newsGrid.innerHTML = Array(6).fill(0).map(() => `
    <div class="skeleton-card shimmer">
      <div class="skeleton-image"></div>
      <div class="skeleton-body">
        <div class="skeleton-line title"></div>
        <div class="skeleton-line w-full"></div>
        <div class="skeleton-line w-75"></div>
        <div class="skeleton-line w-50"></div>
      </div>
    </div>
  `).join("");
}

// Toast Notifications
function showToast(message, type = "info") {
  const toastContainer = document.getElementById("toastContainer");
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <span>${type === 'error' ? '⚠️' : '✨'}</span>
    <span>${message}</span>
  `;

  toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(10px)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}
