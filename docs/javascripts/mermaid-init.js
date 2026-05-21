/* Initialize Mermaid — runs with startOnLoad so it auto-processes
 * .mermaid blocks on DOMContentLoaded. The pymdownx <code> wrapper is
 * stripped at build time by hooks/unwrap_mermaid.py, so Mermaid only
 * sees the clean <pre class="mermaid">SOURCE</pre> shape it expects.
 */
(function () {
  function init() {
    if (typeof window.mermaid === 'undefined') {
      setTimeout(init, 30);
      return;
    }
    const scheme = (document.body && document.body.getAttribute('data-md-color-scheme')) || 'default';
    window.mermaid.initialize({
      startOnLoad: false,
      theme: scheme === 'slate' ? 'dark' : 'default',
      securityLevel: 'loose',
    });
    function runIt() {
      try { window.mermaid.run({ querySelector: '.mermaid' }); }
      catch (_) { try { window.mermaid.init(undefined, '.mermaid'); } catch (_) {} }
    }
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', runIt);
    } else {
      runIt();
    }
  }
  init();
})();
