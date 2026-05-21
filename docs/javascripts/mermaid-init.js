/*
 * mermaid-init.js — wire Mermaid's theme to MkDocs Material's color scheme.
 *
 * The mkdocs-material superfences extension renders <div class="mermaid">
 * blocks but doesn't re-render them when the user toggles light/dark mode.
 * This script:
 *   1. On first load, picks the theme based on `data-md-color-scheme`.
 *   2. On scheme change (MutationObserver), re-runs Mermaid with the new
 *      theme so dark-mode users see a real dark diagram (not a light
 *      diagram inverted via CSS filter).
 */
(function () {
  if (typeof window === 'undefined' || typeof window.mermaid === 'undefined') {
    // Mermaid lib hasn't loaded yet — defer.
    document.addEventListener('DOMContentLoaded', initWhenReady);
    return;
  }
  initWhenReady();

  function initWhenReady() {
    if (typeof window.mermaid === 'undefined') {
      setTimeout(initWhenReady, 100);
      return;
    }
    const scheme = document.body.getAttribute('data-md-color-scheme') || 'default';
    window.mermaid.initialize({
      startOnLoad: true,
      theme: scheme === 'slate' ? 'dark' : 'default',
      themeVariables: scheme === 'slate'
        ? {
            // Tuned to mkdocs-material slate palette
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
          },
    });

    // Re-render when the user toggles the theme.
    const observer = new MutationObserver(function (mutations) {
      for (const m of mutations) {
        if (m.attributeName === 'data-md-color-scheme') {
          const next = document.body.getAttribute('data-md-color-scheme') || 'default';
          // Reset rendered diagrams so they re-init with the new theme.
          document.querySelectorAll('.mermaid').forEach(function (el) {
            // Preserve the original source if Mermaid removed it after first render.
            if (el.dataset.originalSource) {
              el.innerHTML = el.dataset.originalSource;
            } else if (el.querySelector('svg')) {
              // Already rendered — nothing to recover; skip.
              return;
            }
            el.removeAttribute('data-processed');
          });
          window.mermaid.initialize({
            startOnLoad: false,
            theme: next === 'slate' ? 'dark' : 'default',
          });
          try {
            window.mermaid.run({ querySelector: '.mermaid' });
          } catch (e) { /* mermaid v10+ uses .run, older uses .init */
            try { window.mermaid.init(undefined, '.mermaid'); } catch (_) {}
          }
        }
      }
    });
    observer.observe(document.body, { attributes: true, attributeFilter: ['data-md-color-scheme'] });

    // Snapshot original source on first sight so we can re-render later.
    document.querySelectorAll('.mermaid').forEach(function (el) {
      if (!el.dataset.originalSource) {
        el.dataset.originalSource = el.innerHTML;
      }
    });
  }
})();
