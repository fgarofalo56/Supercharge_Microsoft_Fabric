"""MkDocs hook: unwrap pymdownx-superfences' <code> wrapper inside <pre class="mermaid">.

pymdownx.superfences renders every ```mermaid``` block as:
    <pre class="mermaid"><code>SOURCE</code></pre>

Mermaid 10.x's parser does NOT strip the inner <code> tag and reports
"Syntax error in text — bomb icon" for every diagram. The recommended
runtime workaround (a JS init script that unwraps before Mermaid runs)
is timing-fragile because mermaid.min.js may auto-render before the
hook runs.

This hook fixes it deterministically at BUILD TIME — every page that
gets rendered into site/ has its <pre class="mermaid"><code>...</code></pre>
blocks rewritten to plain <pre class="mermaid">...</pre>, so Mermaid 10
parses correctly on first paint.

Wire in via mkdocs.yml:

    hooks:
      - hooks/unwrap_mermaid.py
"""
from __future__ import annotations
import re

# Match <pre class="mermaid"><code>BODY</code></pre> where BODY can span
# newlines. The class attribute may or may not be quoted, and may carry
# additional classes.
MERMAID_PRE_CODE = re.compile(
    r'<pre([^>]*?\bclass=(?:"[^"]*\bmermaid\b[^"]*"|'
    r'\'[^\']*\bmermaid\b[^\']*\'|mermaid)[^>]*)>'
    r'\s*<code[^>]*>(.*?)</code>\s*</pre>',
    re.DOTALL,
)


def on_post_page(output: str, page=None, config=None) -> str:
    """MkDocs post-page hook: rewrite mermaid pre/code blocks.

    Runs after Markdown -> HTML but before the minify plugin (alphabetic
    plugin order in mkdocs.yml). Even if minify runs after this, the
    regex tolerates both quoted and unquoted class attributes.
    """
    if "mermaid" not in output:
        return output
    return MERMAID_PRE_CODE.sub(_replace, output)


def _replace(match: re.Match) -> str:
    attrs = match.group(1)
    body = match.group(2)
    # Keep HTML entities intact — the browser decodes them at textContent
    # read time, which is exactly what Mermaid does. Decoding here would
    # put literal `<br/>` into the <pre>, and the browser would parse that
    # as a real HTML <br> tag, breaking the source mermaid sees.
    return f"<pre{attrs}>{body}</pre>"
