/**
 * Supercharge Microsoft Fabric — AI Copilot Chat Widget
 *
 * Floating chat button + expandable panel that connects to an Azure Function
 * backend powered by Azure OpenAI. Supports streaming responses, markdown
 * rendering, dark/light mode, and a dedicated full-page chat experience.
 *
 * NEW: Client-side documentation search via MkDocs search index. When the
 * backend is unreachable, the widget falls back to local search and shows
 * clickable links to docs pages and GitHub source files.
 *
 * Configuration:
 *   Set window.COPILOT_CONFIG.apiEndpoint before this script loads, or it
 *   defaults to "/api/chat" (works when the Azure Function is proxied).
 */
(function () {
  "use strict";

  /* ── Configuration ─────────────────────────────────────────────── */
  var CONFIG = Object.assign(
    {
      apiEndpoint: "https://fabric-copilot-docs.azurewebsites.net/api/chat",
      maxHistory: 20,
      rateLimitMs: 1500,
      siteUrl: "https://fgarofalo56.github.io/Suppercharge_Microsoft_Fabric/",
      repoUrl: "https://github.com/fgarofalo56/Suppercharge_Microsoft_Fabric",
      repoBranch: "master",
      docsDir: "docs",
      welcomeMessage:
        "Hi! I'm the **Supercharge Fabric Copilot**. Ask me anything about the codebase, tutorials, architecture, compliance rules, or troubleshooting.\n\nI can **search the documentation** and provide direct links to relevant pages. Try asking about *\"Data Flow\"*, *\"medallion architecture\"*, or *\"compliance thresholds\"*.",
    },
    window.COPILOT_CONFIG || {}
  );

  /* ── State ─────────────────────────────────────────────────────── */
  var chatHistory = [];
  var isOpen = false;
  var isStreaming = false;
  var lastSendTime = 0;
  var searchIndex = null;
  var searchIndexLoading = false;
  var sendCount = 0;
  var sessionStart = Date.now();

  /* ── Client-side security ─────────────────────────────────────── */
  var MAX_MESSAGE_LENGTH = 2000;
  var MAX_SESSION_REQUESTS = 100;  // per browser session
  var INJECTION_PATTERNS = [
    /ignore\s+(all\s+)?(previous|prior|system)\s+(instructions?|prompts?|rules?)/i,
    /disregard\s+(all\s+)?(previous|system)\s+(instructions?|prompts?)/i,
    /forget\s+(all\s+)?(previous|your)\s+(instructions?|prompts?)/i,
    /override\s+(system|your)\s+(prompt|instructions?)/i,
    /you\s+are\s+now\s+(a|an|no\s+longer)/i,
    /pretend\s+(you\s+are|to\s+be)/i,
    /from\s+now\s+on\s+(you|ignore|disregard)/i,
    /\[system\]/i,
    /\[INST\]/i,
    /<\|im_start\|>/i,
    /(repeat|reveal|show|print)\s+(your|the)\s+(system\s+)?(prompt|instructions?)/i,
    /\bDAN\b/,
    /jailbreak/i,
    /developer\s+mode/i,
    /sudo\s+mode/i,
  ];

  function isInjectionAttempt(text) {
    for (var i = 0; i < INJECTION_PATTERNS.length; i++) {
      if (INJECTION_PATTERNS[i].test(text)) return true;
    }
    return false;
  }

  /* ── Detect full-page mode ─────────────────────────────────────── */
  var isFullPage = !!document.getElementById("copilot-fullpage");

  /* ── Utility: simple markdown → HTML ───────────────────────────── */
  function md(text) {
    if (!text) return "";

    // Split out fenced code blocks first to protect them
    var codeBlocks = [];
    var html = text.replace(/```(\w*)\n([\s\S]*?)```/g, function (_, lang, code) {
      var placeholder = "\x00CODE" + codeBlocks.length + "\x00";
      codeBlocks.push(
        '<pre><code class="language-' + (lang || "text") + '">' +
        escapeHtml(code.trim()) + "</code></pre>"
      );
      return placeholder;
    });

    // Inline formatting
    html = html
      .replace(/`([^`]+)`/g, "<code>$1</code>")
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replace(/\*(.+?)\*/g, "<em>$1</em>")
      .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');

    // Horizontal rules
    html = html.replace(/^---+$/gm, "<hr>");

    // Headers (h3, h2, h1)
    html = html.replace(/^### (.+)$/gm, "<h4>$1</h4>");
    html = html.replace(/^## (.+)$/gm, "<h3>$1</h3>");
    html = html.replace(/^# (.+)$/gm, "<h2>$1</h2>");

    // Process block-level lists by splitting into lines
    var lines = html.split("\n");
    var out = [];
    var inUl = false;
    var inOl = false;

    for (var i = 0; i < lines.length; i++) {
      var line = lines[i];
      var ulMatch = line.match(/^[-*] (.+)$/);
      var olMatch = line.match(/^\d+\.\s+(.+)$/);

      if (ulMatch) {
        if (!inUl) { if (inOl) { out.push("</ol>"); inOl = false; } out.push("<ul>"); inUl = true; }
        out.push("<li>" + ulMatch[1] + "</li>");
      } else if (olMatch) {
        if (!inOl) { if (inUl) { out.push("</ul>"); inUl = false; } out.push("<ol>"); inOl = true; }
        out.push("<li>" + olMatch[1] + "</li>");
      } else {
        if (inUl) { out.push("</ul>"); inUl = false; }
        if (inOl) { out.push("</ol>"); inOl = false; }
        out.push(line);
      }
    }
    if (inUl) out.push("</ul>");
    if (inOl) out.push("</ol>");

    html = out.join("\n");

    // Paragraphs — double newline = paragraph break, single = <br>
    // But skip <br> right after block elements
    html = html.replace(/\n{2,}/g, "</p><p>");
    html = html.replace(/\n/g, "<br>");
    // Clean up <br> adjacent to block elements
    html = html.replace(/<br>(<\/?(?:ul|ol|li|h[1-6]|hr|pre|blockquote)[\s>])/gi, "$1");
    html = html.replace(/(<\/(?:ul|ol|li|h[1-6]|hr|pre|blockquote)>)<br>/gi, "$1");

    html = "<p>" + html + "</p>";

    // Clean empty paragraphs and paragraphs wrapping block elements
    html = html.replace(/<p>\s*<\/p>/g, "");
    html = html.replace(/<p>(<(?:ul|ol|h[1-6]|hr|pre)[\s>])/gi, "$1");
    html = html.replace(/(<\/(?:ul|ol|h[1-6]|hr|pre)>)<\/p>/gi, "$1");

    // Restore code blocks
    for (var j = 0; j < codeBlocks.length; j++) {
      html = html.replace("\x00CODE" + j + "\x00", codeBlocks[j]);
    }

    return html;
  }

  function escapeHtml(str) {
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  /** Strip HTML tags and collapse whitespace for clean text snippets */
  function stripHtml(str) {
    return str.replace(/<[^>]*>/g, " ").replace(/\s{2,}/g, " ").trim();
  }

  /* ── Search Index ─────────────────────────────────────────────── */

  function getBaseUrl() {
    var base = document.querySelector('meta[name="base_url"]');
    if (base) return base.getAttribute("content");
    var link = document.querySelector('link[rel="canonical"]');
    if (link) {
      var url = new URL(link.getAttribute("href"));
      return url.pathname.replace(/[^/]*$/, "");
    }
    return "/Suppercharge_Microsoft_Fabric/";
  }

  function loadSearchIndex(callback) {
    if (searchIndex) { callback(searchIndex); return; }
    if (searchIndexLoading) {
      // Retry after a moment
      setTimeout(function () { loadSearchIndex(callback); }, 200);
      return;
    }
    searchIndexLoading = true;
    var base = getBaseUrl();
    fetch(base + "search/search_index.json")
      .then(function (r) { return r.json(); })
      .then(function (data) {
        searchIndex = data;
        searchIndexLoading = false;
        callback(data);
      })
      .catch(function () {
        searchIndexLoading = false;
        callback(null);
      });
  }

  /**
   * Search the MkDocs index for matching documents.
   * Returns top results with title, snippet, docs URL, and GitHub URL.
   */
  function searchDocs(query, maxResults) {
    maxResults = maxResults || 8;
    if (!searchIndex || !searchIndex.docs) return [];

    var terms = query.toLowerCase().split(/\s+/).filter(function (t) { return t.length > 1; });
    if (terms.length === 0) return [];

    var scored = [];
    searchIndex.docs.forEach(function (doc) {
      var title = (doc.title || "").toLowerCase();
      var text = (doc.text || "").toLowerCase();
      var location = doc.location || "";
      var score = 0;

      terms.forEach(function (term) {
        // Title matches score higher
        if (title.indexOf(term) !== -1) score += 10;
        // Exact word boundary match in title
        if (new RegExp("\\b" + term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + "\\b").test(title)) score += 5;
        // Text body matches
        var bodyMatches = (text.match(new RegExp(term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), "gi")) || []).length;
        score += Math.min(bodyMatches, 5);
      });

      // Skip very low scores and anchor-only entries (sections within a page)
      if (score > 0 && location) {
        // Extract a snippet around the first match
        var snippet = "";
        for (var i = 0; i < terms.length; i++) {
          var idx = text.indexOf(terms[i]);
          if (idx !== -1) {
            var start = Math.max(0, idx - 60);
            var end = Math.min(text.length, idx + 120);
            snippet = (start > 0 ? "..." : "") + stripHtml(doc.text.substring(start, end)) + (end < text.length ? "..." : "");
            break;
          }
        }
        if (!snippet && doc.text) {
          snippet = stripHtml(doc.text.substring(0, 150)) + (doc.text.length > 150 ? "..." : "");
        }

        scored.push({
          title: doc.title || "Untitled",
          location: location,
          snippet: snippet,
          score: score,
        });
      }
    });

    // Sort by score descending
    scored.sort(function (a, b) { return b.score - a.score; });

    // Deduplicate by base page (remove anchor fragments, keep highest score)
    var seen = {};
    var deduped = [];
    scored.forEach(function (item) {
      var basePage = item.location.split("#")[0];
      if (!seen[basePage]) {
        seen[basePage] = true;
        deduped.push(item);
      }
    });

    return deduped.slice(0, maxResults);
  }

  /**
   * Build docs URL from a search index location.
   */
  function buildDocsUrl(location) {
    return CONFIG.siteUrl + location;
  }

  /**
   * Build GitHub source URL from a search index location.
   */
  function buildGitHubUrl(location) {
    // location is like "PREREQUISITES/" or "features/fabric-iq/"
    // Map to docs source path
    var path = location.replace(/\/$/, "");
    if (!path) path = "index";
    // Most MkDocs pages map to docs/PAGE.md or docs/PAGE/index.md
    // We'll link to the folder; GitHub shows the README/index
    return CONFIG.repoUrl + "/blob/" + CONFIG.repoBranch + "/" + CONFIG.docsDir + "/" + path + ".md";
  }

  /**
   * Format search results as a chat-friendly HTML string.
   */
  function formatSearchResults(results, query) {
    if (results.length === 0) {
      return "I couldn't find any documentation pages matching **\"" + escapeHtml(query) + "\"**. Try different keywords or browse the [documentation home](" + CONFIG.siteUrl + ").";
    }

    var msg = 'I found **' + results.length + ' page' + (results.length > 1 ? 's' : '') + '** matching **"' + escapeHtml(query) + '"**:\n\n';

    results.forEach(function (r, i) {
      var docsUrl = buildDocsUrl(r.location);
      var ghUrl = buildGitHubUrl(r.location);
      msg += '**' + (i + 1) + '. ' + escapeHtml(r.title) + '**\n';
      if (r.snippet) {
        // Truncate snippet for chat
        var snip = r.snippet.length > 120 ? r.snippet.substring(0, 120) + "..." : r.snippet;
        msg += escapeHtml(snip) + '\n';
      }
      msg += '[📄 View in Docs](' + docsUrl + ') · [💻 View on GitHub](' + ghUrl + ')\n\n';
    });

    msg += "---\n*Click any link above to jump directly to that page.*";
    return msg;
  }

  /* ── Build DOM ─────────────────────────────────────────────────── */
  function buildWidget() {
    var container = document.createElement("div");
    container.id = "copilot-container";
    container.innerHTML =
      '<button id="copilot-btn" aria-label="Open AI Copilot Chat" title="Ask the Fabric Copilot">' +
        '<svg id="copilot-icon-chat" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
          '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>' +
        '</svg>' +
        '<svg id="copilot-icon-close" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:none">' +
          '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>' +
        '</svg>' +
      '</button>' +
      '<div id="copilot-panel" class="copilot-hidden">' +
        '<div id="copilot-resize-handle" title="Drag to resize"></div>' +
        '<div id="copilot-header">' +
          '<div id="copilot-header-left">' +
            '<span id="copilot-logo">🤖</span>' +
            '<span id="copilot-title">Fabric Copilot</span>' +
          '</div>' +
          '<div id="copilot-header-right">' +
            '<button id="copilot-clear" title="Clear conversation" aria-label="Clear conversation">' +
              '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>' +
            '</button>' +
            '<button id="copilot-fullscreen" title="Open full-page chat" aria-label="Open full-page chat">' +
              '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 3 21 3 21 9"/><polyline points="9 21 3 21 3 15"/><line x1="21" y1="3" x2="14" y2="10"/><line x1="3" y1="21" x2="10" y2="14"/></svg>' +
            '</button>' +
          '</div>' +
        '</div>' +
        '<div id="copilot-messages"></div>' +
        '<form id="copilot-form">' +
          '<div id="copilot-input-wrap">' +
            '<textarea id="copilot-input" placeholder="Ask about Fabric, tutorials, code..." rows="1"></textarea>' +
            '<button type="submit" id="copilot-send" aria-label="Send message">' +
              '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>' +
            '</button>' +
          '</div>' +
          '<div id="copilot-footer">Powered by Azure OpenAI · <a href="' + CONFIG.siteUrl + '" target="_blank" style="color:inherit;text-decoration:underline;">Documentation</a></div>' +
        '</form>' +
      '</div>';

    if (isFullPage) {
      var target = document.getElementById("copilot-fullpage");
      target.appendChild(container);
      container.classList.add("copilot-fullpage-mode");
      togglePanel(true);
    } else {
      document.body.appendChild(container);
    }

    // Event listeners
    document.getElementById("copilot-btn").addEventListener("click", function () { togglePanel(); });
    document.getElementById("copilot-form").addEventListener("submit", onSubmit);
    document.getElementById("copilot-clear").addEventListener("click", clearChat);
    document.getElementById("copilot-fullscreen").addEventListener("click", function () {
      window.open(getBaseUrl() + "chat/", "_blank");
    });

    // Auto-resize textarea
    var input = document.getElementById("copilot-input");
    input.addEventListener("input", function () {
      this.style.height = "auto";
      this.style.height = Math.min(this.scrollHeight, 120) + "px";
    });
    input.addEventListener("keydown", function (e) {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        document.getElementById("copilot-form").dispatchEvent(new Event("submit"));
      }
    });

    // Show welcome message
    addMessage("assistant", CONFIG.welcomeMessage);

    // Preload search index in background
    loadSearchIndex(function () {});

    // ── Resize logic ──────────────────────────────────────────────
    if (!isFullPage) {
      var resizeHandle = document.getElementById("copilot-resize-handle");
      var panel = document.getElementById("copilot-panel");
      var startX, startY, startW, startH;

      resizeHandle.addEventListener("mousedown", function (e) {
        e.preventDefault();
        startX = e.clientX;
        startY = e.clientY;
        startW = panel.offsetWidth;
        startH = panel.offsetHeight;
        document.addEventListener("mousemove", onResizeMove);
        document.addEventListener("mouseup", onResizeUp);
        panel.style.transition = "none";
      });

      function onResizeMove(e) {
        var newW = Math.max(320, startW - (e.clientX - startX));
        var newH = Math.max(300, startH - (e.clientY - startY));
        panel.style.width = newW + "px";
        panel.style.maxHeight = newH + "px";
      }

      function onResizeUp() {
        document.removeEventListener("mousemove", onResizeMove);
        document.removeEventListener("mouseup", onResizeUp);
        panel.style.transition = "";
      }
    }
  }

  /* ── Toggle panel ──────────────────────────────────────────────── */
  function togglePanel(forceOpen) {
    var panel = document.getElementById("copilot-panel");
    var iconChat = document.getElementById("copilot-icon-chat");
    var iconClose = document.getElementById("copilot-icon-close");

    isOpen = forceOpen !== undefined ? forceOpen : !isOpen;
    if (isOpen) {
      panel.classList.remove("copilot-hidden");
      panel.classList.add("copilot-visible");
      if (iconChat) iconChat.style.display = "none";
      if (iconClose) iconClose.style.display = "block";
      document.getElementById("copilot-input").focus();
    } else {
      panel.classList.remove("copilot-visible");
      panel.classList.add("copilot-hidden");
      if (iconChat) iconChat.style.display = "block";
      if (iconClose) iconClose.style.display = "none";
    }
  }

  /* ── Add message to chat ───────────────────────────────────────── */
  function addMessage(role, content, streaming) {
    var messages = document.getElementById("copilot-messages");
    var div = document.createElement("div");
    div.className = "copilot-msg copilot-msg-" + role;

    var avatar = document.createElement("div");
    avatar.className = "copilot-avatar";
    avatar.textContent = role === "user" ? "👤" : "🤖";

    var bubble = document.createElement("div");
    bubble.className = "copilot-bubble";
    bubble.innerHTML = md(content);

    div.appendChild(avatar);
    div.appendChild(bubble);
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;

    if (streaming) {
      div.id = "copilot-streaming";
    }

    return bubble;
  }

  /* ── Update streaming message ──────────────────────────────────── */
  function updateStreamingMessage(content) {
    var el = document.querySelector("#copilot-streaming .copilot-bubble");
    if (el) {
      el.innerHTML = md(content);
      var messages = document.getElementById("copilot-messages");
      messages.scrollTop = messages.scrollHeight;
    }
  }

  /* ── Finalize streaming ────────────────────────────────────────── */
  function finalizeStreaming() {
    var el = document.getElementById("copilot-streaming");
    if (el) el.removeAttribute("id");
    isStreaming = false;
    document.getElementById("copilot-send").disabled = false;
    document.getElementById("copilot-input").disabled = false;
    document.getElementById("copilot-input").focus();
  }

  /* ── Get current page context ──────────────────────────────────── */
  function getPageContext() {
    return {
      url: window.location.href,
      title: document.title,
      path: window.location.pathname,
    };
  }

  /* ── Submit handler ────────────────────────────────────────────── */
  function onSubmit(e) {
    e.preventDefault();
    var input = document.getElementById("copilot-input");
    var message = input.value.trim();
    if (!message || isStreaming) return;

    var now = Date.now();
    if (now - lastSendTime < CONFIG.rateLimitMs) return;
    lastSendTime = now;

    // ── Client-side security checks ──────────────────────────────
    // Enforce max message length
    if (message.length > MAX_MESSAGE_LENGTH) {
      message = message.substring(0, MAX_MESSAGE_LENGTH);
    }

    // Session request cap (prevents runaway usage from a single tab)
    sendCount++;
    if (sendCount > MAX_SESSION_REQUESTS) {
      addMessage("assistant", "You've reached the session limit. Please refresh the page to continue.");
      return;
    }

    // Client-side injection detection (defense in depth — server also checks)
    if (isInjectionAttempt(message)) {
      addMessage("user", message);
      addMessage("assistant", "I can only help with Microsoft Fabric topics from this repository. Try asking about tutorials, architecture, compliance rules, or troubleshooting.");
      input.value = "";
      input.style.height = "auto";
      return;
    }

    addMessage("user", message);
    chatHistory.push({ role: "user", content: message });

    if (chatHistory.length > CONFIG.maxHistory * 2) {
      chatHistory = chatHistory.slice(-CONFIG.maxHistory * 2);
    }

    input.value = "";
    input.style.height = "auto";

    isStreaming = true;
    document.getElementById("copilot-send").disabled = true;
    input.disabled = true;
    addMessage("assistant", "Searching documentation...", true);

    sendToBackend(message);
  }

  /* ── Send message to Azure Function (with search fallback) ─────── */
  function sendToBackend(message) {
    var payload = {
      message: message,
      history: chatHistory.slice(0, -1),
      pageContext: getPageContext(),
    };

    // Set a short timeout for the backend check
    var controller = new AbortController();
    var timeoutId = setTimeout(function () { controller.abort(); }, 5000);

    fetch(CONFIG.apiEndpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: controller.signal,
    })
      .then(function (response) {
        clearTimeout(timeoutId);
        if (!response.ok) throw new Error("HTTP " + response.status);

        var contentType = response.headers.get("content-type") || "";

        if (contentType.includes("text/event-stream") || contentType.includes("application/x-ndjson")) {
          var reader = response.body.getReader();
          var decoder = new TextDecoder();
          var accumulated = "";

          function readChunk() {
            reader.read().then(function (result) {
              if (result.done) {
                chatHistory.push({ role: "assistant", content: accumulated });
                finalizeStreaming();
                return;
              }
              var chunk = decoder.decode(result.value, { stream: true });
              chunk.split("\n").forEach(function (line) {
                line = line.trim();
                if (!line || line.startsWith(":")) return;
                if (line.startsWith("data: ")) line = line.substring(6);
                if (line === "[DONE]") return;
                try {
                  var data = JSON.parse(line);
                  if (data.content) {
                    accumulated += data.content;
                    updateStreamingMessage(accumulated);
                  }
                  if (data.error) {
                    accumulated = "**Error:** " + data.error;
                    updateStreamingMessage(accumulated);
                  }
                } catch (_) {}
              });
              readChunk();
            });
          }
          readChunk();
        } else {
          response.json().then(function (data) {
            var reply = data.reply || data.content || data.message || "Sorry, I couldn't generate a response.";
            updateStreamingMessage(reply);
            chatHistory.push({ role: "assistant", content: reply });
            finalizeStreaming();
          });
        }
      })
      .catch(function () {
        clearTimeout(timeoutId);
        // Backend unreachable — fall back to local documentation search
        fallbackToLocalSearch(message);
      });
  }

  /* ── Local search fallback ────────────────────────────────────── */
  function fallbackToLocalSearch(query) {
    loadSearchIndex(function (index) {
      if (!index) {
        updateStreamingMessage(
          "**Offline Mode**\n\nThe AI backend isn't available and I couldn't load the search index. " +
          "You can browse the [documentation](" + CONFIG.siteUrl + ") directly or use the search bar above."
        );
        chatHistory.push({ role: "assistant", content: "Offline — search index unavailable." });
        finalizeStreaming();
        return;
      }

      var results = searchDocs(query);
      var reply = formatSearchResults(results, query);
      updateStreamingMessage(reply);
      chatHistory.push({ role: "assistant", content: reply });
      finalizeStreaming();
    });
  }

  /* ── Clear chat ────────────────────────────────────────────────── */
  function clearChat() {
    chatHistory = [];
    var messages = document.getElementById("copilot-messages");
    messages.innerHTML = "";
    addMessage("assistant", CONFIG.welcomeMessage);
  }

  /* ── Initialize ────────────────────────────────────────────────── */
  function init() {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", buildWidget);
    } else {
      buildWidget();
    }
  }

  init();
})();
