/**
 * Supercharge Microsoft Fabric — AI Copilot Chat Widget
 *
 * Floating chat button + expandable panel that connects to an Azure Function
 * backend powered by Azure OpenAI. Supports streaming responses, markdown
 * rendering, dark/light mode, and a dedicated full-page chat experience.
 *
 * Configuration:
 *   Set window.COPILOT_CONFIG.apiEndpoint before this script loads, or it
 *   defaults to "/api/chat" (works when the Azure Function is proxied).
 */
(function () {
  "use strict";

  /* ── Configuration ─────────────────────────────────────────────── */
  const CONFIG = Object.assign(
    {
      apiEndpoint: "https://fabric-copilot-docs.azurewebsites.net/api/chat",          // Azure Function URL
      maxHistory: 20,                     // conversation turns to keep
      rateLimitMs: 1500,                  // min ms between sends
      welcomeMessage:
        "Hi! I'm the **Supercharge Fabric Copilot**. Ask me anything about the codebase, tutorials, architecture, compliance rules, or troubleshooting. I have full context of this repository.",
    },
    window.COPILOT_CONFIG || {}
  );

  /* ── State ─────────────────────────────────────────────────────── */
  let chatHistory = [];
  let isOpen = false;
  let isStreaming = false;
  let lastSendTime = 0;

  /* ── Detect full-page mode ─────────────────────────────────────── */
  const isFullPage = !!document.getElementById("copilot-fullpage");

  /* ── Utility: simple markdown → HTML ───────────────────────────── */
  function md(text) {
    if (!text) return "";
    let html = text
      // code blocks (```lang ... ```)
      .replace(/```(\w*)\n([\s\S]*?)```/g, function (_, lang, code) {
        return '<pre><code class="language-' + (lang || "text") + '">' +
          escapeHtml(code.trim()) + "</code></pre>";
      })
      // inline code
      .replace(/`([^`]+)`/g, "<code>$1</code>")
      // bold
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      // italic
      .replace(/\*(.+?)\*/g, "<em>$1</em>")
      // links
      .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
      // unordered lists
      .replace(/^- (.+)$/gm, "<li>$1</li>")
      // wrap consecutive <li> in <ul>
      .replace(/((?:<li>.*<\/li>\n?)+)/g, "<ul>$1</ul>")
      // line breaks → paragraphs
      .replace(/\n{2,}/g, "</p><p>")
      .replace(/\n/g, "<br>");
    return "<p>" + html + "</p>";
  }

  function escapeHtml(str) {
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  /* ── Detect dark mode ──────────────────────────────────────────── */
  function isDark() {
    return document.body.getAttribute("data-md-color-scheme") === "slate";
  }

  /* ── Build DOM ─────────────────────────────────────────────────── */
  function buildWidget() {
    // Container
    const container = document.createElement("div");
    container.id = "copilot-container";
    container.innerHTML = `
      <!-- Floating button -->
      <button id="copilot-btn" aria-label="Open AI Copilot Chat" title="Ask the Fabric Copilot">
        <svg id="copilot-icon-chat" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
        <svg id="copilot-icon-close" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:none">
          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>

      <!-- Chat panel -->
      <div id="copilot-panel" class="copilot-hidden">
        <div id="copilot-header">
          <div id="copilot-header-left">
            <span id="copilot-logo">🤖</span>
            <span id="copilot-title">Fabric Copilot</span>
          </div>
          <div id="copilot-header-right">
            <button id="copilot-clear" title="Clear conversation" aria-label="Clear conversation">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
            </button>
            <button id="copilot-fullscreen" title="Open full-page chat" aria-label="Open full-page chat">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 3 21 3 21 9"/><polyline points="9 21 3 21 3 15"/><line x1="21" y1="3" x2="14" y2="10"/><line x1="3" y1="21" x2="10" y2="14"/></svg>
            </button>
          </div>
        </div>
        <div id="copilot-messages"></div>
        <form id="copilot-form">
          <div id="copilot-input-wrap">
            <textarea id="copilot-input" placeholder="Ask about Fabric, tutorials, code..." rows="1"></textarea>
            <button type="submit" id="copilot-send" aria-label="Send message">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
            </button>
          </div>
          <div id="copilot-footer">Powered by Azure OpenAI &middot; Context: this repository</div>
        </form>
      </div>
    `;

    if (isFullPage) {
      // In full-page mode, embed inside the target div
      const target = document.getElementById("copilot-fullpage");
      target.appendChild(container);
      container.classList.add("copilot-fullpage-mode");
      // Auto-open
      setTimeout(function () { togglePanel(true); }, 100);
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
  }

  /* ── Get base URL for MkDocs ───────────────────────────────────── */
  function getBaseUrl() {
    var base = document.querySelector('meta[name="base_url"]');
    if (base) return base.getAttribute("content");
    // fallback: look at canonical or just use /
    var link = document.querySelector('link[rel="canonical"]');
    if (link) {
      var url = new URL(link.getAttribute("href"));
      return url.pathname.replace(/[^/]*$/, "");
    }
    return "/";
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
      iconChat.style.display = "none";
      iconClose.style.display = "block";
      document.getElementById("copilot-input").focus();
    } else {
      panel.classList.remove("copilot-visible");
      panel.classList.add("copilot-hidden");
      iconChat.style.display = "block";
      iconClose.style.display = "none";
    }
  }

  /* ── Add message to chat ───────────────────────────────────────── */
  function addMessage(role, content, isStreaming) {
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

    if (isStreaming) {
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

    // Rate limit
    var now = Date.now();
    if (now - lastSendTime < CONFIG.rateLimitMs) return;
    lastSendTime = now;

    // Add user message
    addMessage("user", message);
    chatHistory.push({ role: "user", content: message });

    // Trim history
    if (chatHistory.length > CONFIG.maxHistory * 2) {
      chatHistory = chatHistory.slice(-CONFIG.maxHistory * 2);
    }

    // Clear input
    input.value = "";
    input.style.height = "auto";

    // Show typing indicator
    isStreaming = true;
    document.getElementById("copilot-send").disabled = true;
    input.disabled = true;
    addMessage("assistant", "Thinking...", true);

    // Send to backend
    sendToBackend(message);
  }

  /* ── Send message to Azure Function ────────────────────────────── */
  function sendToBackend(message) {
    var payload = {
      message: message,
      history: chatHistory.slice(0, -1), // exclude the message we just added
      pageContext: getPageContext(),
    };

    fetch(CONFIG.apiEndpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
      .then(function (response) {
        if (!response.ok) {
          throw new Error("HTTP " + response.status);
        }

        var contentType = response.headers.get("content-type") || "";

        // Streaming response (SSE-style via ndjson)
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
              // Each line is a JSON object with a "content" field
              chunk.split("\n").forEach(function (line) {
                line = line.trim();
                if (!line || line.startsWith(":")) return; // SSE comment/keepalive
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
                } catch (_) {
                  // non-JSON line, skip
                }
              });
              readChunk();
            });
          }
          readChunk();
        } else {
          // Non-streaming JSON response
          response.json().then(function (data) {
            var reply = data.reply || data.content || data.message || "Sorry, I couldn't generate a response.";
            updateStreamingMessage(reply);
            chatHistory.push({ role: "assistant", content: reply });
            finalizeStreaming();
          });
        }
      })
      .catch(function (err) {
        console.error("Copilot chat error:", err);
        updateStreamingMessage(
          "**Connection Error**\n\nCould not reach the Copilot backend. This typically means:\n\n" +
          "- The Azure Function isn't deployed yet\n" +
          "- The API endpoint URL needs to be configured\n\n" +
          "See `azure-functions/copilot-chat/` in the repo for setup instructions."
        );
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
    // Wait for DOM
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", buildWidget);
    } else {
      buildWidget();
    }
  }

  init();
})();
