"""Check connector contracts without claiming real GX execution."""

import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
CONTEXT = ROOT / "validation" / "great_expectations"


@pytest.fixture
def datasources() -> dict:
    """Load the repository configuration."""
    return yaml.safe_load((CONTEXT / "great_expectations.yml").read_text("utf-8"))[
        "datasources"
    ]


@pytest.mark.parametrize("name", ["casino_bronze", "federal_bronze"])
def test_generated_parquet_destination(datasources: dict, name: str) -> None:
    """Optional generated output need not exist in a clean checkout."""
    connector = datasources[name]["data_connectors"][
        "default_inferred_data_connector_name"
    ]
    assert connector["class_name"] == "InferredAssetFilesystemDataConnector"
    assert (CONTEXT / connector["base_directory"]).resolve() == (
        ROOT / "data_generation" / "output"
    ).resolve()
    pattern = re.compile(connector["default_regex"]["pattern"])
    assert pattern.fullmatch("bronze_slot_telemetry.parquet")
    assert pattern.fullmatch("bronze_usda_crop_production.parquet")
    assert not pattern.fullmatch("slot_telemetry_sample.csv")


@pytest.mark.parametrize("name", ["casino_silver", "casino_gold", "federal_open_data"])
def test_unprovided_filesystem_inputs_are_runtime_only(
    datasources: dict, name: str
) -> None:
    """Do not invent curated data or a shared downloader destination."""
    assert set(datasources[name]["data_connectors"]) == {"runtime_data_connector"}


@pytest.mark.parametrize(
    ("name", "engine", "identifiers"),
    [
        ("casino_bronze", "SparkDFExecutionEngine", ["default_identifier_name"]),
        ("casino_silver", "SparkDFExecutionEngine", ["default_identifier_name"]),
        ("casino_gold", "SparkDFExecutionEngine", ["default_identifier_name"]),
        (
            "federal_bronze",
            "PandasExecutionEngine",
            ["default_identifier_name", "agency"],
        ),
        (
            "federal_open_data",
            "PandasExecutionEngine",
            ["default_identifier_name", "agency", "dataset"],
        ),
    ],
)
def test_runtime_contract_preserved(
    datasources: dict, name: str, engine: str, identifiers: list[str]
) -> None:
    """Retain execution engines and required runtime identifiers."""
    datasource = datasources[name]
    assert datasource["execution_engine"]["class_name"] == engine
    connector = datasource["data_connectors"]["runtime_data_connector"]
    assert connector["class_name"] == "RuntimeDataConnector"
    assert connector["batch_identifiers"] == identifiers
