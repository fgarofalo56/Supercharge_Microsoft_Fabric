"""Regression checks for navigation and published sample documentation."""

import csv
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def test_parent_navigation() -> None:
    """Parent labels resolve to existing parent pages, never themselves."""
    checked = 0
    errors: list[str] = []
    labels = {
        "Best Practices",
        "Security Index",
        "Parent",
        "Compliance Templates",
        "Compliance Overview",
    }
    for directory in (DOCS / "best-practices", DOCS / "compliance-templates"):
        for page in directory.rglob("*.md"):
            for label, target in re.findall(
                r"\[([^\]]+)\]\(([^)]+)\)", page.read_text(encoding="utf-8")
            ):
                label = label.removeprefix("📚 ")
                if label not in labels:
                    continue
                destination = (page.parent / target.split("#", 1)[0]).resolve()
                valid = destination.is_file() and destination != page.resolve()
                if label in {"Best Practices", "Security Index"}:
                    valid &= destination == (DOCS / "best-practices.md").resolve()
                if not valid:
                    errors.append(f"{page.relative_to(DOCS)}: [{label}]({target})")
                checked += 1
    assert not errors, "Invalid parent links:\n" + "\n".join(errors)
    assert checked >= 30


@pytest.mark.parametrize("published", [False, True])
def test_generator_samples(published: bool) -> None:
    """Both copies describe shipped CSV counts and source-directory paths."""
    page = ROOT / (
        "docs/data_generation/README.md" if published else "data_generation/README.md"
    )
    text = page.read_text(encoding="utf-8")
    rows = re.findall(r"^\| [^|]+ \| (\d+) \| CSV \| `([^`]+)` \|$", text, re.MULTILINE)
    assert len(rows) == 4
    working_directory = ROOT / "data_generation"
    for count, relative in rows:
        with (working_directory / relative).open(
            encoding="utf-8", newline=""
        ) as stream:
            reader = csv.reader(stream)
            header = next(reader)
            records = list(reader)
        assert len(records) == int(count)
        assert all(len(row) == len(header) for row in records)
    section = text.split("### Using Sample Data", 1)[1].split("### ", 1)[0]
    assert "data_generation directory" in section
    match = re.search(r'pd\.read_csv\("([^"]+)"\)', section)
    assert match and (working_directory / match.group(1)).is_file()
    assert "Schema definitions are available in `schemas/`" in text


@pytest.mark.parametrize(
    "relative",
    ["README.md", "TEST_PLAN.md", "notebooks/setup/01_load_sample_data.py"],
)
def test_tutorial_57_repository_references(relative: str) -> None:
    """Host commands and GitHub links resolve after relocation."""
    tutorial = DOCS / "tutorials/57-databricks-better-together"
    text = (tutorial / relative).read_text(encoding="utf-8")
    for old_path in (
        "tutorials/57-databricks-better-together/",
        "sample-data/57-better-together/",
    ):
        assert not re.search(r"(?<!docs/)" + re.escape(old_path), text)
    references = re.findall(
        r"docs/(?:tutorials/57-databricks-better-together|"
        r"sample-data/57-better-together)/[\w./*-]+",
        text,
    )
    assert references
    for reference in references:
        assert list(ROOT.glob(reference)), f"Missing documented path: {reference}"


@pytest.mark.parametrize("published", [False, True])
def test_generator_tutorial_links(published: bool) -> None:
    """Each README resolves tutorial links from its own location."""
    page = (DOCS if published else ROOT) / "data_generation/README.md"
    links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", page.read_text(encoding="utf-8"))
    tutorial_links = [link for link in links if "tutorials/" in link]
    assert tutorial_links
    for link in tutorial_links:
        assert (page.parent / link).exists(), f"Missing tutorial link: {link}"


@pytest.mark.parametrize(
    ("relative", "label", "target"),
    [
        ("disaster-recovery.md", "📚 Docs", "index.md"),
        ("features/prompt-engineering-fabric.md", "📚 Features Index", "index.md"),
    ],
)
def test_section_index_links(relative: str, label: str, target: str) -> None:
    """Index navigation leads to the parent index, not the current page."""
    page = DOCS / relative
    assert f"[{label}]({target})" in page.read_text(encoding="utf-8")
    destination = (page.parent / target).resolve()
    assert destination.is_file() and destination != page.resolve()


def test_root_readme_sample_counts() -> None:
    """The root README describes the actual shipped CSV datasets."""
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    rows = re.findall(r"^\| [^|]+ \| (\d+) \| CSV \| `([^`]+)` \|$", text, re.MULTILINE)
    assert len(rows) == 4
    for count, relative in rows:
        with (ROOT / relative).open(encoding="utf-8", newline="") as stream:
            reader = csv.reader(stream)
            header = next(reader)
            records = list(reader)
        assert len(records) == int(count), relative
        assert all(len(row) == len(header) for row in records), relative


def test_react_app_documented_location() -> None:
    """Deployment instructions identify the directory containing the app."""
    page = DOCS / "sample-apps/react-graphql-consumer/README.md"
    match = re.search(
        r"App location:\*\*\s+`([^`]+)`", page.read_text(encoding="utf-8")
    )
    assert match
    assert (ROOT / match.group(1) / "package.json").is_file()


def test_published_gx_contracts() -> None:
    """Published compatibility and input contracts match the source."""
    source = (ROOT / "validation/great_expectations/README.md").read_text(
        encoding="utf-8"
    )
    published = (DOCS / "validation/great_expectations/README.md").read_text(
        encoding="utf-8"
    )
    for start, end in [
        ("### Prerequisites", "### Running Validations"),
        ("### Python Integration", "### Custom Validation"),
    ]:
        assert (
            source.split(start, 1)[1].split(end, 1)[0]
            == published.split(start, 1)[1].split(end, 1)[0]
        )
    assert (
        'pd.read_csv("docs/sample-data/bronze/slot_telemetry_sample.csv")' in published
    )
