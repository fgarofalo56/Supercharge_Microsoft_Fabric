/*
 * mermaid-theme.js — toggle Mermaid theme when MkDocs Material color
 * scheme changes. Relies on Material's NATIVE mermaid integration.
 *
 * Material for MkDocs ships its own loader for Mermaid that reads
 * `<pre class="mermaid">` blocks correctly (no <code> wrapper issue)
 * and re-renders on instant navigation. We DO NOT load the mermaid
 * CDN ourselves — Material does. We only need to swap the theme when
 * the user toggles dark/light.
 */
(function () {
  if (typeof window === 'undefined') return;

  function applyTheme(scheme) {
    if (typeof window.mermaid === 'undefined') return;
    window.mermaid.initialize({
      startOnLoad: false,
      theme: scheme === 'slate' ? 'dark' : 'default',
      securityLevel: 'loose',
    });
    document.querySelectorAll('.mermaid').forEach(function (el) {
      if (el.dataset.originalSource) el.textContent = el.dataset.originalSource;
      el.removeAttribute('data-processed');
    });
    try { window.mermaid.run({ querySelector: '.mermaid' }); } catch (_) {}
  }

  // Snapshot sources so we can re-render on theme change.
  function snapshot() {
    document.querySelectorAll('.mermaid').forEach(function (el) {
      if (!el.dataset.originalSource && !el.querySelector('svg')) {
        el.dataset.originalSource = el.textContent;
      }
    });
  }

  // On theme toggle, re-init mermaid with the new color palette.
  const observer = new MutationObserver(function (mutations) {
    for (const m of mutations) {
      if (m.attributeName === 'data-md-color-scheme') {
        applyTheme(document.body.getAttribute('data-md-color-scheme') || 'default');
      }
    }
  });
  if (document.body) {
    observer.observe(document.body, { attributes: true, attributeFilter: ['data-md-color-scheme'] });
    setTimeout(snapshot, 1500);
  } else {
    document.addEventListener('DOMContentLoaded', function () {
      observer.observe(document.body, { attributes: true, attributeFilter: ['data-md-color-scheme'] });
      setTimeout(snapshot, 1500);
    });
  }
})();
