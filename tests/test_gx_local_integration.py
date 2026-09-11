"""Real legacy-GX Pandas checks; excludes Spark and repository checkpoints."""

from copy import deepcopy
from pathlib import Path

import pandas as pd
import pytest
import yaml

CONTEXT = Path(__file__).resolve().parents[1] / "validation" / "great_expectations"


@pytest.fixture
def gx_context():
    """Create a legacy context with usage reporting disabled."""
    gx = pytest.importorskip("great_expectations")
    if not gx.__version__.startswith("0.18."):
        pytest.skip("Requires isolated GX 0.18 environment")
    from great_expectations.data_context.types.base import (
        DataContextConfig,
        InMemoryStoreBackendDefaults,
    )

    config = DataContextConfig(
        store_backend_defaults=InMemoryStoreBackendDefaults(),
        anonymous_usage_statistics={"enabled": False},
    )
    return gx.get_context(mode="ephemeral", project_config=config)


def datasource_config(name: str) -> dict:
    """Copy the actual repository datasource definition."""
    config = yaml.safe_load((CONTEXT / "great_expectations.yml").read_text("utf-8"))
    return deepcopy(config["datasources"][name])


@pytest.mark.parametrize("name", ["casino_pandas", "federal_bronze"])
def test_filesystem_discovery_and_validation(gx_context, tmp_path: Path, name: str):
    """Discover and validate shipped CSV or temporary Parquet fixture data."""
    from great_expectations.core.batch import BatchRequest

    config = datasource_config(name)
    connector_name = "default_inferred_data_connector_name"
    connector = config["data_connectors"][connector_name]
    if name == "casino_pandas":
        directory = (CONTEXT / connector["base_directory"]).resolve()
        asset = "slot_telemetry_sample"
        expected_rows = len(pd.read_csv(directory / f"{asset}.csv"))
    else:
        directory = tmp_path
        asset = "bronze_usda_crop_production"
        pd.DataFrame({"record_id": [1, 2]}).to_parquet(directory / f"{asset}.parquet")
        expected_rows = 2
    connector["base_directory"] = str(directory)
    source = gx_context.add_datasource(name=name, **config)
    available = source.get_available_data_asset_names()[connector_name]
    assets = [entry[0] if isinstance(entry, tuple) else entry for entry in available]
    assert asset in assets
    gx_context.add_or_update_expectation_suite(expectation_suite_name="audit_rows")
    validator = gx_context.get_validator(
        batch_request=BatchRequest(
            datasource_name=name,
            data_connector_name=connector_name,
            data_asset_name=asset,
        ),
        expectation_suite_name="audit_rows",
    )
    assert validator.expect_table_row_count_to_equal(expected_rows).success
    assert validator.validate().success


def test_federal_runtime_checkpoint(gx_context):
    """Execute a new in-memory checkpoint, not a checked-in template."""
    from great_expectations.checkpoint import SimpleCheckpoint
    from great_expectations.core.batch import RuntimeBatchRequest

    name = "federal_open_data"
    gx_context.add_datasource(name=name, **datasource_config(name))
    request = RuntimeBatchRequest(
        datasource_name=name,
        data_connector_name="runtime_data_connector",
        data_asset_name="audit_fixture",
        runtime_parameters={"batch_data": pd.DataFrame({"record_id": [1, 2]})},
        batch_identifiers={
            "default_identifier_name": "audit",
            "agency": "usda",
            "dataset": "fixture",
        },
    )
    gx_context.add_or_update_expectation_suite(expectation_suite_name="audit_runtime")
    validator = gx_context.get_validator(
        batch_request=request, expectation_suite_name="audit_runtime"
    )
    validator.expect_column_values_to_not_be_null("record_id")
    validator.save_expectation_suite(discard_failed_expectations=False)
    checkpoint = SimpleCheckpoint(name="audit_runtime", data_context=gx_context)
    result = checkpoint.run(
        validations=[
            {"batch_request": request, "expectation_suite_name": "audit_runtime"}
        ]
    )
    assert result.success
    assert len(result.run_results) == 1
