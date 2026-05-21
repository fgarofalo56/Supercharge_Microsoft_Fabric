/*
 * mermaid-init.js — make Mermaid work with mkdocs-material + pymdownx.superfences
 * and wire it to the MkDocs Material color scheme.
 *
 * Two problems this solves:
 *   1. pymdownx.superfences emits each Mermaid block as
 *      `<pre class="mermaid"><code>SOURCE</code></pre>`. Mermaid 10.x can't
 *      parse the inner `<code>` wrapper and renders the "Syntax error / bomb"
 *      icon. We unwrap to plain text before Mermaid runs.
 *   2. Mermaid doesn't re-render when the user toggles light/dark theme.
 *      We snapshot the source, then re-run on `data-md-color-scheme` change.
 */
(function () {
  if (typeof window === 'undefined') return;

  // Run as soon as both DOM is ready AND mermaid library is loaded.
  function whenReady(fn) {
    function check() {
      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', check);
        return;
      }
      if (typeof window.mermaid === 'undefined') {
        setTimeout(check, 50);
        return;
      }
      fn();
    }
    check();
  }

  function unwrapCodeWrappers() {
    document.querySelectorAll('pre.mermaid, div.mermaid, .mermaid').forEach(function (el) {
      const code = el.querySelector('code');
      if (code) {
        // textContent already decodes HTML entities (&lt; &gt; &amp;).
        el.textContent = code.textContent;
      }
    });
  }

  function snapshotSources() {
    document.querySelectorAll('pre.mermaid, div.mermaid, .mermaid').forEach(function (el) {
      if (!el.dataset.originalSource) {
        el.dataset.originalSource = el.textContent;
      }
    });
  }

  function themeVars(scheme) {
    return scheme === 'slate'
      ? {
          background: '#1f2937',
          primaryColor: '#3F51B5',
          primaryTextColor: '#f4f6fb',
          primaryBorderColor: '#5C6BC0',
          lineColor: '#94a3b8',
          secondaryColor: '#0078D4',
          tertiaryColor: '#1A237E',
          mainBkg: '#374151',
          secondBkg: '#1f2937',
          tertiaryBkg: '#1f2937',
          textColor: '#f4f6fb',
          nodeTextColor: '#f4f6fb',
          edgeLabelBackground: '#1f2937',
          clusterBkg: 'rgba(63, 81, 181, 0.15)',
          clusterBorder: '#5C6BC0',
        }
      : {
          primaryColor: '#3F51B5',
          primaryTextColor: '#0F172A',
          primaryBorderColor: '#5C6BC0',
          lineColor: '#475569',
          secondaryColor: '#0078D4',
          background: '#ffffff',
          mainBkg: '#F8FAFC',
        };
  }

  function runMermaid(scheme) {
    window.mermaid.initialize({
      startOnLoad: false,
      theme: scheme === 'slate' ? 'dark' : 'default',
      themeVariables: themeVars(scheme),
      securityLevel: 'loose',
    });
    try {
      window.mermaid.run({ querySelector: '.mermaid' });
    } catch (e) {
      try { window.mermaid.init(undefined, '.mermaid'); } catch (_) { /* ignore */ }
    }
  }

  function rerenderForScheme(scheme) {
    document.querySelectorAll('pre.mermaid, div.mermaid, .mermaid').forEach(function (el) {
      if (el.dataset.originalSource) {
        el.textContent = el.dataset.originalSource;
      }
      el.removeAttribute('data-processed');
    });
    runMermaid(scheme);
  }

  whenReady(function () {
    unwrapCodeWrappers();
    snapshotSources();
    const scheme = document.body.getAttribute('data-md-color-scheme') || 'default';
    runMermaid(scheme);

    // Re-render on theme toggle.
    const observer = new MutationObserver(function (mutations) {
      for (const m of mutations) {
        if (m.attributeName === 'data-md-color-scheme') {
          const next = document.body.getAttribute('data-md-color-scheme') || 'default';
          rerenderForScheme(next);
        }
      }
    });
    observer.observe(document.body, { attributes: true, attributeFilter: ['data-md-color-scheme'] });
  });
})();
