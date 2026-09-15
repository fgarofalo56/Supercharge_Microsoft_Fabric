# Synapse pipelines to Fabric: migration and cutover

[Back to Tutorial 41](README.md)

> **Reviewed:** 2026-09-11. The Synapse pipeline migration experience is **preview**. This procedure is not evidence of a cloud migration executed in this repository.

## Prerequisites

Use a source Synapse workspace and a nonproduction Fabric workspace. Confirm permissions, capacity, connection credentials, and network access. Obtain workload-owner approval before production cutover.

Complete the [assessment](01_assessment.py) and [schema conversion](02_schema_conversion.py) where applicable. Preserve source definitions and record linked services, parameters, triggers, retry policies, dependencies, and the last committed ingestion watermark. Exclude secrets from evidence.

## Prepare dependencies

Migrate notebooks and Spark job definitions first. Validate their environments, lakehouse bindings, parameters, identities, and output locations independently. Missing target Spark items can leave migrated activities unmapped or deactivated.

Create and test Fabric connections. Do not assume Synapse integration runtime settings or credentials transfer unchanged; consult the activity and connectivity comparison below.

## Assess and migrate a pilot

1. In Synapse Studio, open **Integrate**, select **Migrate to Fabric (Preview)**, then **Get started**.
2. Export the assessment CSV and inspect activity-level findings.
3. Start with **Ready** pipelines. Remediate **Needs review** items and reassess. Keep **Coming soon** items on the source or design a replacement; refactor **Not compatible** items before migration.
4. Select a destination Fabric workspace and map each linked service to a tested Fabric connection.
5. Select **Confirm**, then inspect the migrated pipelines. Microsoft documents a source-workspace prefix on their names.
6. Check every child pipeline, notebook, Spark job, parameter, and failure branch. Activities using unmapped connections remain **deactivated** until configured and reactivated.

Migrated triggers are **disabled by default**. Leave production schedules disabled during validation. Review scheduling, timezone, event filters, parameters, concurrency, and missed-run behavior explicitly.

If the preview is unavailable, evaluate the documented PowerShell upgrader against its own supported-functionality list, or rebuild unsupported activities manually. Neither route is a universal JSON import. A successful conversion is not runtime validation.

## Verify before cutover

Use isolated destinations and the same bounded source interval for comparison. Never run both orchestrators against shared production output during a parallel test.

| Check | Evidence and acceptance |
| --- | --- |
| Connections | Sanitized mapping and run IDs; intended identities reach all required endpoints. |
| Activity coverage | Source-to-target inventory; no required activity is missing or unintentionally deactivated. |
| Data parity | Counts, key uniqueness, null checks, and business aggregates match agreed tolerances. |
| Incremental processing | Watermarks and processed keys demonstrate no gaps or duplicate committed results on rerun. |
| Failure handling | Controlled failure exercises retries, timeouts, failure branches, and notifications. |
| Empty and boundary input | Empty batches and interval boundaries do not advance the watermark beyond committed input. |
| Performance | Duration and capacity observations meet the agreed processing window. |

For a casino medallion pilot, reconcile raw Bronze ingestion, Silver deduplication, and Gold business totals separately. Keep Bronze append-only; implement replay detection and downstream deduplication rather than overwriting raw evidence.

## Cutover and rollback

1. Obtain owner sign-off on validation evidence, the change window, and rollback criteria.
2. Disable source triggers, drain in-flight Synapse runs, and record the final committed watermark.
3. Configure Fabric from that verified checkpoint and enable only approved target triggers.
4. Observe a complete processing cycle and reconcile outputs before expanding the migration.
5. If reconciliation fails, disable Fabric triggers and drain active runs. Identify committed writes before selecting a recovery watermark.
6. Reconcile partial or duplicate output using the tested workload recovery procedure, then resume Synapse from the verified checkpoint. Do not blindly restart both orchestrators.

Retain source definitions and rollback access for the agreed observation period. Decommission only after owner approval of reconciliation, operational ownership, retention, and recovery readiness.

## Official references

- [Synapse pipeline upgrade experience (preview)](https://learn.microsoft.com/azure/data-factory/how-to-upgrade-your-azure-synapse-analytics-pipelines-to-fabric-data-factory)
- [Synapse data and pipeline migration](https://learn.microsoft.com/fabric/data-engineering/migrate-synapse-data-pipelines)
- [PowerShell upgrader and supported functionality](https://learn.microsoft.com/fabric/data-factory/migrate-pipelines-powershell-upgrade-module-for-azure-data-factory-to-fabric)
- [Fabric and Azure Data Factory comparison](https://learn.microsoft.com/fabric/data-factory/compare-fabric-data-factory-and-azure-data-factory)
