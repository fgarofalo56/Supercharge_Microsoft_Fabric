/**
 * Supercharge Microsoft Fabric — AI Copilot Chat Widget (Enhanced)
 *
 * Floating chat button + expandable panel that connects to an Azure Function
 * backend powered by Azure OpenAI. Supports ndjson streaming with progressive
 * rendering, XSS-hardened markdown (tables, task lists, blockquotes, citations,
 * code blocks with syntax highlighting), panel resize, full-page mode toggle,
 * and SHA-256 token generation via SubtleCrypto.
 *
 * Configuration:
 *   Set window.COPILOT_CONFIG before this script loads, or it
 *   defaults to sensible values for the Supercharge Fabric site.
 */
(function () {
  "use strict";

  /* ── Configuration ─────────────────────────────────────────────── */
  var CONFIG = Object.assign(
    {
      apiEndpoint: "https://fabric-copilot-docs-ldai.azurewebsites.net/api/chat",
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
  var highlightLoaded = false;
  var highlightLoading = false;

  /* ── Client-side security ─────────────────────────────────────── */
  var MAX_MESSAGE_LENGTH = 2000;
  var MAX_SESSION_REQUESTS = 100;
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

  /* ── HTML escaping (XSS prevention) ────────────────────────────── */
  function escapeHtml(str) {
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function stripHtml(str) {
    return str.replace(/<[^>]*>/g, " ").replace(/\s{2,}/g, " ").trim();
  }

  /* ── SHA-256 token via SubtleCrypto ────────────────────────────── */
  function generateToken(input) {
    if (!window.crypto || !window.crypto.subtle) {
      return Promise.resolve("");
    }
    var data = new TextEncoder().encode(input);
    return window.crypto.subtle.digest("SHA-256", data).then(function (buf) {
      var arr = new Uint8Array(buf);
      var hex = "";
      for (var i = 0; i < arr.length; i++) {
        hex += ("0" + arr[i].toString(16)).slice(-2);
      }
      return hex;
    });
  }

  /* ── Highlight.js lazy loading ─────────────────────────────────── */
  function loadHighlightJs(callback) {
    if (highlightLoaded) {
      if (callback) callback();
      return;
    }
    if (highlightLoading) {
      setTimeout(function () { loadHighlightJs(callback); }, 100);
      return;
    }
    highlightLoading = true;

    var link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github.min.css";
    document.head.appendChild(link);

    var darkLink = document.createElement("link");
    darkLink.rel = "stylesheet";
    darkLink.href = "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css";
    darkLink.media = "(prefers-color-scheme: dark)";
    document.head.appendChild(darkLink);

    var script = document.createElement("script");
    script.src = "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js";
    script.onload = function () {
      highlightLoaded = true;
      highlightLoading = false;
      if (callback) callback();
    };
    script.onerror = function () {
      highlightLoading = false;
      if (callback) callback();
    };
    document.head.appendChild(script);
  }

  function highlightAllBlocks() {
    if (!highlightLoaded || !window.hljs) return;
    var blocks = document.querySelectorAll("#copilot-messages pre code[class*='language-']");
    for (var i = 0; i < blocks.length; i++) {
      if (!blocks[i].dataset.highlighted) {
        window.hljs.highlightElement(blocks[i]);
        blocks[i].dataset.highlighted = "true";
      }
    }
  }

  /* ── XSS-hardened markdown renderer ────────────────────────────── */
  function md(text) {
    if (!text) return "";

    var codeBlocks = [];
    var citations = {};

    // Extract fenced code blocks first
    var html = text.replace(/```(\w*)\n([\s\S]*?)```/g, function (_, lang, code) {
      var idx = codeBlocks.length;
      var langClass = lang ? "language-" + escapeHtml(lang) : "language-text";
      var langLabel = lang || "text";
      codeBlocks.push(
        '<div class="copilot-code-block">' +
          '<div class="copilot-code-header">' +
            '<span class="copilot-code-lang">' + escapeHtml(langLabel) + '</span>' +
            '<button class="copilot-copy-btn" onclick="window._copilotCopy(this)" title="Copy code">Copy</button>' +
          '</div>' +
          '<pre><code class="' + langClass + '">' +
          escapeHtml(code.trim()) + '</code></pre>' +
        '</div>'
      );
      return "\x00CODE" + idx + "\x00";
    });

    // Extract citation definitions [^n]: text
    html = html.replace(/^\[\^(\d+)\]:\s*(.+)$/gm, function (_, num, citText) {
      citations[num] = escapeHtml(citText.trim());
      return "";
    });

    // Citation references [^n] → superscript
    html = html.replace(/\[\^(\d+)\]/g, function (_, num) {
      return '<sup class="copilot-cite-ref" data-cite="' + escapeHtml(num) + '">[' + escapeHtml(num) + ']</sup>';
    });

    // Inline code (must come before other inline processing)
    html = html.replace(/`([^`]+)`/g, function (_, code) {
      return "<code>" + escapeHtml(code) + "</code>";
    });

    // Bold & italic
    html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    html = html.replace(/\*(.+?)\*/g, "<em>$1</em>");

    // Links — escape href to prevent javascript: XSS
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, function (_, linkText, href) {
      var safeHref = escapeHtml(href.trim());
      if (/^javascript:/i.test(href.trim())) return escapeHtml(linkText);
      return '<a href="' + safeHref + '" target="_blank" rel="noopener noreferrer">' + linkText + '</a>';
    });

    // Horizontal rules
    html = html.replace(/^---+$/gm, "<hr>");

    // Headers
    html = html.replace(/^#### (.+)$/gm, "<h5>$1</h5>");
    html = html.replace(/^### (.+)$/gm, "<h4>$1</h4>");
    html = html.replace(/^## (.+)$/gm, "<h3>$1</h3>");
    html = html.replace(/^# (.+)$/gm, "<h2>$1</h2>");

    // Tables
    html = html.replace(/^(\|.+\|)\n(\|[-| :]+\|)\n((?:\|.+\|\n?)+)/gm, function (_, headerRow, sepRow, bodyRows) {
      var headers = headerRow.split("|").filter(function (c) { return c.trim() !== ""; });
      var aligns = sepRow.split("|").filter(function (c) { return c.trim() !== ""; }).map(function (c) {
        c = c.trim();
        if (c.startsWith(":") && c.endsWith(":")) return "center";
        if (c.endsWith(":")) return "right";
        return "left";
      });
      var rows = bodyRows.trim().split("\n").map(function (row) {
        return row.split("|").filter(function (c) { return c.trim() !== ""; });
      });

      var table = '<div class="copilot-table-wrap"><table><thead><tr>';
      headers.forEach(function (h, i) {
        table += '<th style="text-align:' + (aligns[i] || "left") + '">' + escapeHtml(h.trim()) + '</th>';
      });
      table += '</tr></thead><tbody>';
      rows.forEach(function (row) {
        table += '<tr>';
        row.forEach(function (cell, i) {
          table += '<td style="text-align:' + (aligns[i] || "left") + '">' + escapeHtml(cell.trim()) + '</td>';
        });
        table += '</tr>';
      });
      table += '</tbody></table></div>';
      return table;
    });

    // Block-level processing: lists, task lists, blockquotes
    var lines = html.split("\n");
    var out = [];
    var inUl = false;
    var inOl = false;
    var inBlockquote = false;

    for (var i = 0; i < lines.length; i++) {
      var line = lines[i];

      // Task list items: - [x] or - [ ]
      var taskMatch = line.match(/^[-*] \[([ xX])\] (.+)$/);
      if (taskMatch) {
        if (!inUl) {
          if (inOl) { out.push("</ol>"); inOl = false; }
          if (inBlockquote) { out.push("</blockquote>"); inBlockquote = false; }
          out.push('<ul class="copilot-task-list">');
          inUl = true;
        }
        var checked = taskMatch[1] !== " " ? ' checked disabled' : ' disabled';
        out.push('<li class="copilot-task-item"><input type="checkbox"' + checked + '> ' + taskMatch[2] + '</li>');
        continue;
      }

      // Unordered list
      var ulMatch = line.match(/^[-*] (.+)$/);
      if (ulMatch) {
        if (!inUl) {
          if (inOl) { out.push("</ol>"); inOl = false; }
          if (inBlockquote) { out.push("</blockquote>"); inBlockquote = false; }
          out.push("<ul>");
          inUl = true;
        }
        out.push("<li>" + ulMatch[1] + "</li>");
        continue;
      }

      // Ordered list
      var olMatch = line.match(/^\d+\.\s+(.+)$/);
      if (olMatch) {
        if (!inOl) {
          if (inUl) { out.push("</ul>"); inUl = false; }
          if (inBlockquote) { out.push("</blockquote>"); inBlockquote = false; }
          out.push("<ol>");
          inOl = true;
        }
        out.push("<li>" + olMatch[1] + "</li>");
        continue;
      }

      // Blockquotes
      var bqMatch = line.match(/^>\s?(.*)$/);
      if (bqMatch) {
        if (inUl) { out.push("</ul>"); inUl = false; }
        if (inOl) { out.push("</ol>"); inOl = false; }
        if (!inBlockquote) {
          out.push("<blockquote>");
          inBlockquote = true;
        }
        out.push(bqMatch[1]);
        continue;
      }

      // Close open blocks
      if (inUl) { out.push("</ul>"); inUl = false; }
      if (inOl) { out.push("</ol>"); inOl = false; }
      if (inBlockquote) { out.push("</blockquote>"); inBlockquote = false; }
      out.push(line);
    }
    if (inUl) out.push("</ul>");
    if (inOl) out.push("</ol>");
    if (inBlockquote) out.push("</blockquote>");

    html = out.join("\n");

    // Paragraphs
    html = html.replace(/\n{2,}/g, "</p><p>");
    html = html.replace(/\n/g, "<br>");
    html = html.replace(/<br>(<\/?(?:ul|ol|li|h[1-6]|hr|pre|blockquote|div|table)[\s>])/gi, "$1");
    html = html.replace(/(<\/(?:ul|ol|li|h[1-6]|hr|pre|blockquote|div|table)>)<br>/gi, "$1");

    html = "<p>" + html + "</p>";

    // Clean empty paragraphs and paragraphs wrapping block elements
    html = html.replace(/<p>\s*<\/p>/g, "");
    html = html.replace(/<p>(<(?:ul|ol|h[1-6]|hr|pre|div|blockquote|table)[\s>])/gi, "$1");
    html = html.replace(/(<\/(?:ul|ol|h[1-6]|hr|pre|div|blockquote|table)>)<\/p>/gi, "$1");

    // Restore code blocks
    for (var j = 0; j < codeBlocks.length; j++) {
      html = html.replace("\x00CODE" + j + "\x00", codeBlocks[j]);
    }

    // Build citation footer if any citations were found
    var citeKeys = Object.keys(citations);
    if (citeKeys.length > 0) {
      html += '<div class="copilot-citations-footer"><div class="copilot-citations-title">Sources</div>';
      citeKeys.forEach(function (key) {
        html += '<div class="copilot-citation-card" data-cite="' + escapeHtml(key) + '">' +
          '<span class="copilot-citation-num">[' + escapeHtml(key) + ']</span> ' +
          '<span class="copilot-citation-text">' + citations[key] + '</span>' +
        '</div>';
      });
      html += '</div>';
    }

    return html;
  }

  // Global copy handler for code blocks
  window._copilotCopy = function (btn) {
    var codeEl = btn.closest(".copilot-code-block").querySelector("code");
    if (!codeEl) return;
    var text = codeEl.textContent;
    navigator.clipboard.writeText(text).then(function () {
      btn.textContent = "Copied!";
      setTimeout(function () { btn.textContent = "Copy"; }, 2000);
    }).catch(function () {
      btn.textContent = "Failed";
      setTimeout(function () { btn.textContent = "Copy"; }, 2000);
    });
  };

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
        if (title.indexOf(term) !== -1) score += 10;
        if (new RegExp("\\b" + term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "\\b").test(title)) score += 5;
        var bodyMatches = (text.match(new RegExp(term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "gi")) || []).length;
        score += Math.min(bodyMatches, 5);
      });

      if (score > 0 && location) {
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

        scored.push({ title: doc.title || "Untitled", location: location, snippet: snippet, score: score });
      }
    });

    scored.sort(function (a, b) { return b.score - a.score; });

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

  function buildDocsUrl(location) {
    return CONFIG.siteUrl + location;
  }

  function buildGitHubUrl(location) {
    var path = location.replace(/\/$/, "");
    if (!path) path = "index";
    return CONFIG.repoUrl + "/blob/" + CONFIG.repoBranch + "/" + CONFIG.docsDir + "/" + path + ".md";
  }

  function formatSearchResults(results, query) {
    if (results.length === 0) {
      return "I couldn't find any documentation pages matching **\"" + escapeHtml(query) + "\"**. Try different keywords or browse the [documentation](" + CONFIG.siteUrl + ").";
    }

    var msg = 'I found **' + results.length + ' page' + (results.length > 1 ? 's' : '') + '** matching **"' + escapeHtml(query) + '"**:\n\n';

    results.forEach(function (r, i) {
      var docsUrl = buildDocsUrl(r.location);
      var ghUrl = buildGitHubUrl(r.location);
      msg += '**' + (i + 1) + '. ' + escapeHtml(r.title) + '**\n';
      if (r.snippet) {
        var snip = r.snippet.length > 120 ? r.snippet.substring(0, 120) + "..." : r.snippet;
        msg += escapeHtml(snip) + '\n';
      }
      msg += '[View in Docs](' + docsUrl + ') · [View on GitHub](' + ghUrl + ')\n\n';
    });

    msg += "---\n*Click any link above to jump directly to that page.*";
    return msg;
  }

  /* ── Build DOM ─────────────────────────────────────────────────── */
  function buildWidget() {
    var container = document.createElement("div");
    container.id = "copilot-container";
    container.innerHTML =
      '<button id="copilot-btn" class="copilot-fab" aria-label="Open AI Copilot Chat" title="Ask the Fabric Copilot">' +
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
            '<span id="copilot-logo">&#x1F916;</span>' +
            '<span id="copilot-title">Fabric Copilot</span>' +
          '</div>' +
          '<div id="copilot-header-right">' +
            '<button id="copilot-clear" title="Clear conversation" aria-label="Clear conversation">' +
              '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>' +
            '</button>' +
            '<button id="copilot-fullpage-toggle" title="Toggle full-page mode" aria-label="Toggle full-page mode">' +
              '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 3 21 3 21 9"/><polyline points="9 21 3 21 3 15"/><line x1="21" y1="3" x2="14" y2="10"/><line x1="3" y1="21" x2="10" y2="14"/></svg>' +
            '</button>' +
            '<button id="copilot-fullscreen" title="Open full-page chat" aria-label="Open full-page chat">' +
              '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>' +
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
          '<div id="copilot-footer">Powered by Azure OpenAI &middot; <a href="' + escapeHtml(CONFIG.siteUrl) + '" target="_blank" style="color:inherit;text-decoration:underline;">Documentation</a></div>' +
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

    // Full-page mode toggle (inline expand)
    document.getElementById("copilot-fullpage-toggle").addEventListener("click", function () {
      var panel = document.getElementById("copilot-panel");
      panel.classList.toggle("copilot-fullpage-inline");
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

    // Preload search index and highlight.js in background
    loadSearchIndex(function () {});
    loadHighlightJs(function () {});

    // ── Resize drag logic ─────────────────────────────────────────
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
        document.body.style.userSelect = "none";
      });

      function onResizeMove(e) {
        var newW = Math.max(320, Math.min(window.innerWidth * 0.75, startW - (e.clientX - startX)));
        var newH = Math.max(300, startH - (e.clientY - startY));
        panel.style.width = newW + "px";
        panel.style.maxHeight = newH + "px";
      }

      function onResizeUp() {
        document.removeEventListener("mousemove", onResizeMove);
        document.removeEventListener("mouseup", onResizeUp);
        panel.style.transition = "";
        document.body.style.userSelect = "";
      }

      // Touch support for resize
      resizeHandle.addEventListener("touchstart", function (e) {
        var touch = e.touches[0];
        startX = touch.clientX;
        startY = touch.clientY;
        startW = panel.offsetWidth;
        startH = panel.offsetHeight;
        document.addEventListener("touchmove", onTouchResize, { passive: false });
        document.addEventListener("touchend", onTouchResizeEnd);
        panel.style.transition = "none";
      }, { passive: true });

      function onTouchResize(e) {
        e.preventDefault();
        var touch = e.touches[0];
        var newW = Math.max(320, Math.min(window.innerWidth * 0.75, startW - (touch.clientX - startX)));
        var newH = Math.max(300, startH - (touch.clientY - startY));
        panel.style.width = newW + "px";
        panel.style.maxHeight = newH + "px";
      }

      function onTouchResizeEnd() {
        document.removeEventListener("touchmove", onTouchResize);
        document.removeEventListener("touchend", onTouchResizeEnd);
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

    highlightAllBlocks();
    return bubble;
  }

  /* ── Update streaming message ──────────────────────────────────── */
  function updateStreamingMessage(content) {
    var el = document.querySelector("#copilot-streaming .copilot-bubble");
    if (el) {
      el.innerHTML = md(content);
      var messages = document.getElementById("copilot-messages");
      messages.scrollTop = messages.scrollHeight;
      highlightAllBlocks();
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
    highlightAllBlocks();
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

    if (message.length > MAX_MESSAGE_LENGTH) {
      message = message.substring(0, MAX_MESSAGE_LENGTH);
    }

    sendCount++;
    if (sendCount > MAX_SESSION_REQUESTS) {
      addMessage("assistant", "You've reached the session limit. Please refresh the page to continue.");
      return;
    }

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

  /* ── Send message to Azure Function (ndjson streaming) ─────────── */
  function sendToBackend(message) {
    var tokenInput = sessionStart + ":" + message.substring(0, 32);
    generateToken(tokenInput).then(function (token) {
      var payload = {
        message: message,
        history: chatHistory.slice(0, -1),
        pageContext: getPageContext(),
      };
      if (token) {
        payload.token = token;
      }

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
            var buffer = "";

            function readChunk() {
              reader.read().then(function (result) {
                if (result.done) {
                  chatHistory.push({ role: "assistant", content: accumulated });
                  finalizeStreaming();
                  return;
                }
                buffer += decoder.decode(result.value, { stream: true });
                var lines = buffer.split("\n");
                buffer = lines.pop();

                lines.forEach(function (line) {
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
              // If the answer was grounded from Microsoft Learn (i.e., the
              // topic isn't covered in the repo yet), append a small note
              // so the user knows where the citations came from.
              if (data.groundedFromMsLearn) {
                reply +=
                  "\n\n*ⓘ Answer grounded from Microsoft Learn — this topic isn't in the repo yet. " +
                  "A content-gap issue was filed automatically.*";
              }
              updateStreamingMessage(reply);
              chatHistory.push({ role: "assistant", content: reply });
              finalizeStreaming();
            });
          }
        })
        .catch(function () {
          clearTimeout(timeoutId);
          fallbackToLocalSearch(message);
        });
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
