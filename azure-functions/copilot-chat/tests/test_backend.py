"""Unit tests for the Copilot chat backend.

Run with:  pytest azure-functions/copilot-chat/tests/ -v

These tests exercise the pure/deterministic logic (PII redaction, term
scoring, snippet extraction, grounding formatting, fingerprinting) and
mock the network boundary (MS Learn MCP, GitHub, Table Storage) so they
run offline and fast.
"""

from __future__ import annotations

import os
import sys

import pytest

# Make the backend modules importable regardless of pytest's rootdir.
BACKEND = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.abspath(BACKEND))

import feedback  # noqa: E402
import github_issue  # noqa: E402
import repo_grounding  # noqa: E402


# ── feedback.redact_pii ─────────────────────────────────────────
class TestRedactPii:
    @pytest.mark.parametrize(
        "text,raw,placeholder",
        [
            ("mail jane.doe@contoso.com", "jane.doe@contoso.com", "[email]"),
            ("ssn 123-45-6789", "123-45-6789", "[ssn]"),
            ("ssn 123456789", "123456789", "[ssn]"),
            ("card 4111 1111 1111 1111", "4111 1111 1111 1111", "[card]"),
            ("call (555) 123-4567", "555", "[phone]"),
            ("host 10.0.0.42 down", "10.0.0.42", "[ip]"),
        ],
    )
    def test_redacts(self, text, raw, placeholder):
        out = feedback.redact_pii(text)
        assert raw not in out
        assert placeholder in out

    def test_plain_text_untouched(self):
        msg = "How do I set up Direct Lake with medallion architecture?"
        assert feedback.redact_pii(msg) == msg

    def test_empty_and_none_safe(self):
        assert feedback.redact_pii("") == ""


# ── feedback._hash_session ──────────────────────────────────────
class TestHashSession:
    def test_deterministic(self):
        assert feedback._hash_session("abc") == feedback._hash_session("abc")

    def test_hides_raw(self):
        assert "abc" not in feedback._hash_session("abc")

    def test_empty_safe(self):
        assert feedback._hash_session("") == ""

    def test_distinct(self):
        assert feedback._hash_session("a") != feedback._hash_session("b")


# ── feedback.record_feedback (validation + dedupe, storage mocked) ──
class TestRecordFeedback:
    def test_rejects_invalid_rating(self):
        out = feedback.record_feedback(rating="sideways")
        assert out["stored"] is False
        assert "error" in out

    def test_dedupes_identical_event(self, monkeypatch):
        monkeypatch.setattr(feedback, "_store_table", lambda e: True)
        feedback._dedupe.clear()
        kwargs = dict(
            rating="up",
            comment="",
            user_message="q",
            assistant_reply="a",
            page_path="/x/",
            session_id="s1",
        )
        first = feedback.record_feedback(**kwargs)
        second = feedback.record_feedback(**kwargs)
        assert first.get("deduped") is not True
        assert second.get("deduped") is True

    def test_redacts_before_storage(self, monkeypatch):
        captured = {}
        monkeypatch.setattr(
            feedback, "_store_table", lambda e: captured.update(e) or True
        )
        feedback._dedupe.clear()
        feedback.record_feedback(
            rating="down",
            comment="reach me at jane@contoso.com",
            user_message="my ssn 123-45-6789",
            assistant_reply="answer",
            page_path="/x/",
            session_id="raw-session-token",
        )
        assert "jane@contoso.com" not in captured["comment"]
        assert "123-45-6789" not in captured["user_message"]
        assert "raw-session-token" not in captured["session_id"]


# ── repo_grounding._terms / _score / _snippet ───────────────────
class TestTerms:
    def test_lowercases_and_strips_stopwords(self):
        terms = repo_grounding._terms("How do I configure Direct Lake?")
        assert "direct" in terms
        assert "lake" in terms
        # stopwords removed
        assert "how" not in terms
        assert "do" not in terms


class TestScore:
    def test_title_hit_beats_body_only(self):
        terms = ["lakehouse"]
        title_hit = repo_grounding._score(terms, "Lakehouse guide", "some text")
        body_only = repo_grounding._score(terms, "Guide", "lakehouse text")
        assert title_hit > body_only

    def test_no_match_scores_zero(self):
        assert repo_grounding._score(["zzz"], "Direct Lake", "medallion") == 0.0


class TestSnippet:
    def test_strips_html(self):
        out = repo_grounding._snippet("<p>Direct <b>Lake</b> mode</p>", ["direct"])
        assert "<" not in out and ">" not in out
        assert "Direct" in out

    def test_centres_on_first_term(self):
        text = "padding " * 100 + "DIRECTLAKE" + " tail" * 100
        out = repo_grounding._snippet(text, ["directlake"], width=200)
        assert "DIRECTLAKE" in out
        assert out.startswith("…")  # leading ellipsis because match is deep


class TestFormatGroundingContext:
    def test_renders_sources(self):
        chunks = [
            {
                "source": "docs",
                "title": "Direct Lake",
                "url": "https://x/direct-lake/",
                "text": "Direct Lake reads Delta.",
                "score": 12.0,
            }
        ]
        out = repo_grounding.format_grounding_context(chunks)
        assert "Direct Lake" in out
        assert "Direct Lake reads Delta." in out

    def test_empty_chunks(self):
        assert repo_grounding.format_grounding_context([]) == ""


# ── github_issue._fingerprint + dedupe ──────────────────────────
class TestGithubIssue:
    def test_fingerprint_normalises_whitespace_case(self):
        a = github_issue._fingerprint("  Direct   Lake ")
        b = github_issue._fingerprint("direct lake")
        assert a == b

    def test_no_token_noop(self, monkeypatch):
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("GITHUB_REPO", raising=False)
        assert github_issue.file_content_gap("q", []) is None

    def test_dedupes_repeat_question(self, monkeypatch):
        monkeypatch.setenv("GITHUB_TOKEN", "x")
        monkeypatch.setenv("GITHUB_REPO", "o/r")
        github_issue._dedupe.clear()

        class _Resp:
            status_code = 201

            def json(self):
                return {"html_url": "https://github.com/o/r/issues/1"}

        class _Client:
            def __init__(self, **kw):
                self.kw = kw

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def post(self, *a, **kw):
                return _Resp()

        monkeypatch.setattr(github_issue.httpx, "Client", _Client)
        first = github_issue.file_content_gap("unique question?", [])
        second = github_issue.file_content_gap("unique question?", [])
        assert first == "https://github.com/o/r/issues/1"
        assert second is None  # deduped
