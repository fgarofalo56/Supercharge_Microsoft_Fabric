"""Check runner input paths without executing Great Expectations suites."""

import ast
from pathlib import Path


def test_gx_runner_sample_inputs_exist() -> None:
    """Every configured sample and expectation suite must exist after moves."""
    root = Path(__file__).resolve().parents[1]
    runner = root / "validation" / "great_expectations" / "run_all_suites.py"
    tree = ast.parse(runner.read_text(encoding="utf-8"))
    names = {"ROOT", "EXPECT_DIR", "SAMPLE", "PAIRS"}
    assignments = {
        target.id: node.value
        for node in tree.body
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name) and target.id in names
    }

    def path_value(node: ast.expr) -> Path | str:
        if isinstance(node, ast.Name) and node.id == "ROOT":
            return runner.parent
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.Attribute) and node.attr == "parent":
            return Path(path_value(node.value)).parent
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            return Path(path_value(node.left)) / path_value(node.right)
        raise AssertionError(f"Unsupported path expression: {ast.dump(node)}")

    namespace = {
        "SAMPLE": Path(path_value(assignments["SAMPLE"])),
        "EXPECT_DIR": Path(path_value(assignments["EXPECT_DIR"])),
        "PAIRS": ast.literal_eval(assignments["PAIRS"]),
    }

    for csv_name, suite_name in namespace["PAIRS"]:
        sample = namespace["SAMPLE"] / csv_name
        suite = namespace["EXPECT_DIR"] / f"{suite_name}.json"
        assert sample.is_file(), f"Missing runner sample: {sample}"
        assert suite.is_file(), f"Missing expectation suite: {suite}"


def test_gx_pandas_connector_discovers_shipped_samples() -> None:
    """Resolve the filesystem connector relative to the GX context root."""
    import re

    import yaml

    root = Path(__file__).resolve().parents[1]
    context = root / "validation" / "great_expectations"
    config = yaml.safe_load(
        (context / "great_expectations.yml").read_text(encoding="utf-8")
    )
    connector = config["datasources"]["casino_pandas"]["data_connectors"][
        "default_inferred_data_connector_name"
    ]
    directory = (context / connector["base_directory"]).resolve()
    expected = root / "docs" / "sample-data" / "bronze"
    assert directory == expected.resolve()
    pattern = re.compile(connector["default_regex"]["pattern"])
    discovered = {
        path.name
        for path in directory.iterdir()
        if path.is_file() and pattern.fullmatch(path.name)
    }
    shipped = {path.name for path in expected.glob("*.csv")}
    assert shipped, "No shipped CSV samples were checked"
    assert discovered == shipped


def test_moved_report_deployment_triggers() -> None:
    """Report edits must still trigger deployment after relocation."""
    root = Path(__file__).resolve().parents[1]
    workflow = (root / ".github/workflows/deploy-fabric.yml").read_text(
        encoding="utf-8"
    )
    for directory in ("semantic-model", "report-definitions"):
        path = f"docs/reports/{directory}"
        assert (root / path).is_dir()
        assert f"'{path}/**'" in workflow, f"Missing deployment trigger: {path}"


def test_codeowners_moved_directory_rules() -> None:
    """Explicit ownership rules must follow relocated directories."""
    root = Path(__file__).resolve().parents[1]
    owners = (root / ".github/CODEOWNERS").read_text(encoding="utf-8")
    rules = {line.split()[0] for line in owners.splitlines() if line.startswith("/")}
    for directory in ("sample-data", "reports", "tutorials", "poc-agenda"):
        assert (root / "docs" / directory).is_dir()
        assert f"/docs/{directory}/" in rules
        assert f"/{directory}/" not in rules


def test_readme_relocated_links_exist() -> None:
    """Check Markdown and HTML links into relocated documentation folders."""
    import re

    root = Path(__file__).resolve().parents[1]
    text = (root / "README.md").read_text(encoding="utf-8")
    links = re.findall(r'\]\(([^)]+)\)|href="([^"]+)"', text)
    moved = ("tutorials/", "reports/", "sample-data/", "poc-agenda/")
    checked = 0
    for markdown_link, html_link in links:
        target = (markdown_link or html_link).split("#", 1)[0]
        assert not target.startswith(moved), f"Stale README link: {target}"
        if target.startswith(tuple(f"docs/{directory}" for directory in moved)):
            assert (root / target).exists(), f"Missing README target: {target}"
            checked += 1
    assert checked > 0, "No relocated README links were checked"


def test_readme_sample_loading_example() -> None:
    """Load the README's sample CSV and resolve its schema directory."""
    import re

    import pandas as pd

    root = Path(__file__).resolve().parents[1]
    text = (root / "README.md").read_text(encoding="utf-8")
    match = re.search(r"pd\.read_csv\('([^']+)'\)", text)
    assert match is not None, "README must demonstrate loading a shipped CSV"
    data = pd.read_csv(root / match.group(1))
    assert not data.empty
    schema_match = re.search(r"^ls (\S*schemas/)$", text, re.MULTILINE)
    assert schema_match is not None
    schema_directory = root / schema_match.group(1)
    assert schema_directory.is_dir()
    assert any(schema_directory.glob("*.json"))


def test_gx_readme_sample_loading_example() -> None:
    """Load the shipped CSV named in the local GX documentation example."""
    import re

    import pandas as pd

    root = Path(__file__).resolve().parents[1]
    text = (root / "validation/great_expectations/README.md").read_text(
        encoding="utf-8"
    )
    section = text.split("### Python Integration", 1)[1].split("### ", 1)[0]
    assert "Run this example from the repository root." in section
    match = re.search(r'pd\.read_csv\("([^"]+)"\)', section)
    assert match is not None, "Local GX example must load a shipped CSV"
    data = pd.read_csv(root / match.group(1))
    assert not data.empty
    assert "event_id" in data.columns


def test_generator_readme_samples() -> None:
    """Check documented sample counts and load the generator README example."""
    import csv
    import re

    import pandas as pd

    directory = Path(__file__).resolve().parents[1] / "data_generation"
    text = (directory / "README.md").read_text(encoding="utf-8")
    rows = re.findall(r"^\| [^|]+ \| (\d+) \| CSV \| `([^`]+)` \|$", text, re.MULTILINE)
    assert len(rows) == 4
    for count, relative_path in rows:
        path = directory / relative_path
        with path.open(encoding="utf-8", newline="") as stream:
            reader = csv.reader(stream)
            header = next(reader)
            records = list(reader)
        assert len(records) == int(count), relative_path
        assert all(len(row) == len(header) for row in records), relative_path
    section = text.split("### Using Sample Data", 1)[1].split("### ", 1)[0]
    match = re.search(r'pd\.read_csv\("([^"]+)"\)', section)
    assert match is not None
    assert not pd.read_csv(directory / match.group(1)).empty
    assert (directory / "schemas").is_dir()
    assert "../sample-data/" not in text


def test_repository_path_checks_run_on_pull_requests() -> None:
    """Keep relocation checks in an unconditional job for documentation PRs."""
    import yaml

    root = Path(__file__).resolve().parents[1]
    workflow = yaml.safe_load(
        (root / ".github/workflows/run-tests.yml").read_text(encoding="utf-8")
    )
    # PyYAML uses YAML 1.1, which treats the unquoted Actions key `on` as True.
    triggers = workflow.get("on", workflow.get(True))
    assert "pull_request" in triggers
    job = workflow["jobs"]["changes"]
    assert "if" not in job
    steps = job["steps"]
    check = next(
        step
        for step in steps
        if step.get("name") == "Validate repository paths and README sample"
    )
    assert "if" not in check
    assert (
        "python -m pytest tests/test_sample_data_paths.py --noconftest -q"
        in check["run"]
    )
