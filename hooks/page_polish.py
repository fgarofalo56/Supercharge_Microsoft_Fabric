"""MkDocs post-page hook — three visual polish passes:

1. Code-block language badges
   pymdownx-superfences emits `<div class="highlight language-python">`.
   We add a `data-lang="python"` attribute that the CSS reads to render
   a small uppercase label in the top-right of every code block.

2. Page-type badge
   If the page frontmatter has `type: deep-dive` (or quick-start /
   runbook / reference / feature / tutorial / decision / compliance),
   we inject a small chip after the first <h1> so users see the
   content type at a glance.

3. Next-step cards at the bottom of every doc page
   Sourced from the mkdocs navigation: shows the Previous + Next
   sibling/parent links. Wraps in a `.next-steps` block.

Wire-in: this hook plus `hooks/unwrap_mermaid.py` both register `on_post_page`
handlers; mkdocs runs them in YAML order, so order in `mkdocs.yml` matters.
"""
from __future__ import annotations
import re

# ── 1. Code-block language badges ───────────────────────────────────
# Match the .highlight wrapper and pull the language class out. The
# wrapper class order varies — pymdownx-superfences may emit either
# `language-python highlight` or `highlight language-python` — so we
# match any class attribute that contains both tokens.
_HIGHLIGHT_OPEN_RE = re.compile(
    r'<div class="([^"]*\bhighlight\b[^"]*)"(?![^>]*data-lang=)',
)
_LANG_CLASS_RE = re.compile(r'\blanguage-([a-z0-9+\-]+)')


def _add_lang_attr(match: re.Match) -> str:
    classes = match.group(1)
    lang_match = _LANG_CLASS_RE.search(classes)
    if not lang_match:
        return match.group(0)  # no language → no badge
    lang = lang_match.group(1)
    # Friendly display names for common languages
    display = {
        "py": "python", "ps1": "powershell", "sh": "bash", "ts": "typescript",
        "js": "javascript", "yml": "yaml", "md": "markdown",
    }.get(lang, lang)
    return f'<div class="{classes}" data-lang="{display}"'


# ── 2. Page-type badge ──────────────────────────────────────────────
_VALID_TYPES = {
    "deep-dive", "quick-start", "runbook", "reference", "feature",
    "tutorial", "decision", "compliance",
}
_DISPLAY_LABELS = {
    "deep-dive":   "Deep Dive",
    "quick-start": "Quick Start",
    "runbook":     "Runbook",
    "reference":   "Reference",
    "feature":     "Feature",
    "tutorial":    "Tutorial",
    "decision":    "Decision",
    "compliance":  "Compliance",
}
_FIRST_H1_RE = re.compile(r"(<h1[^>]*>.*?)(</h1>)", re.DOTALL)


def _inject_page_type(html: str, page_type: str) -> str:
    label = _DISPLAY_LABELS.get(page_type, page_type.title())
    chip = (
        f' <span class="md-page-type" data-page-type="{page_type}">'
        f'{label}</span>'
    )

    def replace(match: re.Match) -> str:
        return match.group(1) + chip + match.group(2)

    return _FIRST_H1_RE.sub(replace, html, count=1)


# ── 3. Next-step cards ──────────────────────────────────────────────
_FOOTER_INSERT_RE = re.compile(
    r'(<hr class="md-footer">|<footer class="md-footer)',
)


def _build_next_steps(page) -> str | None:
    """Build the next-step card block for a page based on nav siblings."""
    prev = getattr(page, "previous_page", None)
    nxt = getattr(page, "next_page", None)
    if not prev and not nxt:
        return None

    cards: list[str] = []
    if prev is not None and getattr(prev, "url", None) and getattr(prev, "title", None):
        cards.append(
            f'<a class="next-step" href="{prev.url}">'
            f'<span class="next-step__label">← Previous</span>'
            f'<span class="next-step__title">{prev.title}</span>'
            f'<span class="next-step__arrow">Read more →</span>'
            f'</a>'
        )
    if nxt is not None and getattr(nxt, "url", None) and getattr(nxt, "title", None):
        cards.append(
            f'<a class="next-step" href="{nxt.url}">'
            f'<span class="next-step__label">Next →</span>'
            f'<span class="next-step__title">{nxt.title}</span>'
            f'<span class="next-step__arrow">Read more →</span>'
            f'</a>'
        )
    if not cards:
        return None

    return (
        '<div class="next-steps">'
        '<p class="next-steps__heading">Continue reading</p>'
        '<div class="next-steps__grid">'
        + "".join(cards) +
        '</div></div>'
    )


_ARTICLE_CLOSE_RE = re.compile(r'</article>')


def _inject_next_steps(html: str, page) -> str:
    block = _build_next_steps(page)
    if not block:
        return html
    # Insert before the closing </article> tag of the main content.
    return _ARTICLE_CLOSE_RE.sub(block + "</article>", html, count=1)


def on_post_page(output: str, page=None, config=None) -> str:
    # 1. Code-block badges — applied to every highlight wrapper that
    #    has a `language-*` class (regex matches both orderings).
    if "highlight" in output:
        output = _HIGHLIGHT_OPEN_RE.sub(_add_lang_attr, output)

    # 2. Page-type badge (frontmatter `type:` field)
    page_type = None
    if page and getattr(page, "meta", None):
        candidate = page.meta.get("type")
        if isinstance(candidate, str):
            candidate = candidate.strip().lower().replace(" ", "-")
            if candidate in _VALID_TYPES:
                page_type = candidate
    if page_type:
        output = _inject_page_type(output, page_type)

    # 3. Next-step cards (only for normal doc pages with siblings)
    if page is not None:
        output = _inject_next_steps(output, page)

    return output
