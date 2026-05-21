"""
Multi-Source CDC Event Simulator
=================================

Unified Change Data Capture (CDC) event generator that simulates events from
multiple database source types for Microsoft Fabric Eventstreams demos:

  - SQL Server (on-premises, Debezium-style LSN-based CDC)
  - Azure SQL Database (Fabric Mirroring / Change Feed)
  - Azure Cosmos DB (Change Feed Processor)
  - IBM DB2 (InfoSphere CDC / ASN Capture)
  - Oracle (LogMiner / GoldenGate)

Each source produces realistic server names, database names, table names,
before/after images, and connector metadata drawn from the casino/gaming domain.
"""

import random
import uuid
from datetime import datetime, timezone

UTC = timezone.utc  # `datetime.UTC` constant is Python 3.11+ only; alias for 3.10 compat
from typing import Any

import numpy as np

from ..base_generator import BaseGenerator

# ---------------------------------------------------------------------------
# Source configuration registry
# ---------------------------------------------------------------------------

SOURCE_CONFIG: dict[str, dict[str, Any]] = {
    "sql_server": {
        "source_type_enum": "SQL_SERVER",
        "server_names": [
            "sql-prod-east-01",
            "sql-prod-east-02",
            "sql-casino-ops-01",
            "sql-finance-prod-01",
            "sql-compliance-01",
            "sql-player-mgmt-01",
        ],
        "database_names": [
            "CasinoOperations",
            "PlayerManagement",
            "FinancialReporting",
            "ComplianceAudit",
            "SlotFloorMgmt",
        ],
        "schema_name": "dbo",
        "table_names": [
            "Transactions",
            "Players",
            "SlotEvents",
            "TableGameHands",
            "JackpotAwards",
            "CashierTransactions",
            "PlayerRatings",
            "MachineMeters",
            "SecurityIncidents",
            "CtrFilings",
        ],
        "connectors": ["DEBEZIUM", "FABRIC_MIRRORING"],
        "latency_range": (50, 2000),
        "pk_style": "integer",
        "has_lsn": True,
        "has_scn": False,
        "has_partition_key": False,
    },
    "azure_sql": {
        "source_type_enum": "AZURE_SQL",
        "server_names": [
            "casino-azuresql.database.windows.net",
            "player-db-prod.database.windows.net",
            "analytics-dwh.database.windows.net",
            "reporting-db.database.windows.net",
        ],
        "database_names": [
            "PlayerDB",
            "CasinoAnalytics",
            "LoyaltyProgram",
            "OperationsDB",
        ],
        "schema_name": "dbo",
        "table_names": [
            "Orders",
            "Products",
            "CustomerActivity",
            "PlayerSessions",
            "RewardPoints",
            "GamingActivity",
            "MarketingCampaigns",
            "ChipInventory",
        ],
        "connectors": ["FABRIC_MIRRORING", "CHANGE_FEED"],
        "latency_range": (10, 500),
        "pk_style": "uuid",
        "has_lsn": False,
        "has_scn": False,
        "has_partition_key": False,
    },
    "cosmos_db": {
        "source_type_enum": "COSMOS_DB",
        "server_names": [
            "casino-cosmos-db.documents.azure.com",
            "player-activity-cosmos.documents.azure.com",
            "realtime-events-cosmos.documents.azure.com",
        ],
        "database_names": [
            "CasinoOperations",
            "PlayerProfiles",
            "LiveEvents",
        ],
        "schema_name": None,
        "table_names": [
            "PlayerActivity",
            "SlotEvents",
            "Transactions",
            "SessionData",
            "Notifications",
            "BettingHistory",
        ],
        "connectors": ["CHANGE_FEED", "FABRIC_MIRRORING"],
        "latency_range": (10, 200),
        "pk_style": "uuid",
        "has_lsn": False,
        "has_scn": False,
        "has_partition_key": True,
        "partition_key_templates": [
            "/playerId/P{id}",
            "/casinoId/C{id}",
            "/machineId/M{id}",
            "/sessionId/S{id}",
        ],
    },
    "ibm_db2": {
        "source_type_enum": "IBM_DB2",
        "server_names": [
            "db2-mainframe-01",
            "db2-luw-prod-01",
            "zos-db2-casino-01",
            "ibm-db2-legacy-01",
        ],
        "database_names": [
            "CASINODB",
            "LEGACYOPS",
            "FINANCEDB",
            "PLAYERDB",
        ],
        "schema_name": "CASINO",
        "table_names": [
            "LEGACY_TRANSACTIONS",
            "PLAYER_HISTORY",
            "MACHINE_CONFIG",
            "CAGE_OPERATIONS",
            "GAMING_SESSIONS",
            "PAYROLL_DATA",
            "AUDIT_LOG",
        ],
        "connectors": ["INFOSPHERE_CDC"],
        "latency_range": (500, 5000),
        "pk_style": "integer",
        "has_lsn": False,
        "has_scn": False,
        "has_partition_key": False,
    },
    "oracle": {
        "source_type_enum": "ORACLE",
        "server_names": [
            "oracle-prod-01.casino.local",
            "oracle-rac-node1.casino.local",
            "oracle-rac-node2.casino.local",
            "oracle-finance-01.casino.local",
        ],
        "database_names": [
            "CASINOPRD",
            "FINPRD",
            "HRPRD",
            "RPTPRD",
        ],
        "schema_name": "CASINO",
        "table_names": [
            "SLOT_TRANSACTIONS",
            "TABLE_GAME_HANDS",
            "CAGE_OPERATIONS",
            "PLAYER_ACCOUNTS",
            "JACKPOT_EVENTS",
            "COMPLIANCE_EVENTS",
            "CHIP_TRANSFERS",
            "SHIFT_REPORTS",
        ],
        "connectors": ["GOLDEN_GATE", "LOGMINER"],
        "latency_range": (100, 3000),
        "pk_style": "integer",
        "has_lsn": False,
        "has_scn": True,
        "has_partition_key": False,
    },
}

# Operations and their weights: INSERT/UPDATE/DELETE/READ → 40/35/15/10
_OPERATIONS = ["INSERT", "UPDATE", "DELETE", "READ"]
_OPERATION_WEIGHTS = [0.40, 0.35, 0.15, 0.10]

# Casino-domain field pools for before/after images
_AMOUNT_STATUSES = ["PENDING", "APPROVED", "SETTLED", "REVERSED", "VOIDED"]
_GAME_STATUSES = ["ACTIVE", "INACTIVE", "SUSPENDED", "MAINTENANCE", "CLOSED"]
_PLAYER_TIERS = ["Bronze", "Silver", "Gold", "Platinum", "Diamond"]
_TRANSACTION_TYPES = [
    "COIN_IN",
    "COIN_OUT",
    "JACKPOT",
    "TICKET_OUT",
    "CASH_IN",
    "CASH_OUT",
]
_PAYMENT_METHODS = ["CASH", "CHIP", "VOUCHER", "CREDIT_CARD", "CHECK", "WIRE"]


class MultiSourceSimulator(BaseGenerator):
    """
    Unified CDC event simulator for multiple database source types.

    Generates realistic CDC event payloads including operation type, before/after
    images with casino-domain fields, connector metadata, and source-specific
    identifiers (LSN for SQL Server, SCN for Oracle, partition key for Cosmos DB).
    """

    def __init__(
        self,
        seed: int | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ):
        """
        Initialize the multi-source CDC simulator.

        Args:
            seed: Random seed for reproducibility
            start_date: Start of the simulated event time window
            end_date: End of the simulated event time window
        """
        super().__init__(
            seed=seed,
            start_date=start_date,
            end_date=end_date,
        )

        self._sequence_counter: int = 0

        self._schema: dict[str, str] = {
            "event_id": "string",
            "source_type": "string",
            "operation": "string",
            "timestamp": "string",
            "server_name": "string",
            "database_name": "string",
            "schema_name": "string",
            "table_name": "string",
            "primary_key": "string",
            "before_image": "object",
            "after_image": "object",
            "transaction_id": "string",
            "lsn": "string",
            "scn": "string",
            "partition_key": "string",
            "sequence_number": "integer",
            "connector_name": "string",
            "latency_ms": "integer",
            "schema_version": "string",
            "load_time": "string",
        }

    # ------------------------------------------------------------------
    # Abstract method implementation
    # ------------------------------------------------------------------

    def generate_record(self, source_type: str = "sql_server") -> dict[str, Any]:  # type: ignore[override]
        """
        Generate a single CDC event for the specified source type.

        Args:
            source_type: One of "sql_server", "azure_sql", "cosmos_db",
                         "ibm_db2", "oracle". Defaults to "sql_server".

        Returns:
            Dictionary representing one CDC event record.
        """
        if source_type not in SOURCE_CONFIG:
            raise ValueError(
                f"Unknown source_type '{source_type}'. "
                f"Valid options: {list(SOURCE_CONFIG.keys())}"
            )

        cfg = SOURCE_CONFIG[source_type]
        operation = self.weighted_choice(_OPERATIONS, _OPERATION_WEIGHTS)
        event_ts = self.random_datetime()

        # Primary key
        if cfg["pk_style"] == "uuid":
            primary_key = str(uuid.uuid4())
        else:
            primary_key = str(self.rng.integers(100_000, 9_999_999))

        # Before / after images
        before_image = self._build_image(operation, "before")
        after_image = self._build_image(operation, "after")

        # Transaction ID (null ~10% of time to simulate non-transactional reads)
        txn_id: str | None
        if operation == "READ" or self.rng.random() < 0.10:
            txn_id = None
        else:
            txn_id = "TXN-" + uuid.uuid4().hex[:12].upper()

        # Source-specific identifiers
        lsn: str | None = None
        scn: str | None = None
        partition_key: str | None = None

        if cfg["has_lsn"]:
            lsn = self._generate_lsn()
        if cfg["has_scn"]:
            scn = self._generate_scn()
        if cfg["has_partition_key"]:
            partition_key = self._generate_partition_key(cfg)

        # Sequence number (thread-safe increment)
        self._sequence_counter += 1

        latency_ms = int(
            self.rng.integers(cfg["latency_range"][0], cfg["latency_range"][1])
        )

        record: dict[str, Any] = {
            "event_id": str(uuid.uuid4()),
            "source_type": cfg["source_type_enum"],
            "operation": operation,
            "timestamp": event_ts.isoformat(),
            "server_name": random.choice(cfg["server_names"]),  # nosec B311 - synthetic data only
            "database_name": random.choice(cfg["database_names"]),  # nosec B311 - synthetic data only
            "schema_name": cfg["schema_name"],
            "table_name": random.choice(cfg["table_names"]),  # nosec B311 - synthetic data only
            "primary_key": primary_key,
            "before_image": before_image,
            "after_image": after_image,
            "transaction_id": txn_id,
            "lsn": lsn,
            "scn": scn,
            "partition_key": partition_key,
            "sequence_number": self._sequence_counter,
            "connector_name": random.choice(cfg["connectors"]),  # nosec B311 - synthetic data only
            "latency_ms": latency_ms,
            "schema_version": "1.0.0",
            "load_time": datetime.now(UTC).isoformat(),
        }
        return record

    def generate_batch(  # type: ignore[override]
        self,
        count: int = 1000,
        source_type: str = "sql_server",
    ) -> list[dict[str, Any]]:
        """
        Generate a list of CDC events from a single source type.

        Args:
            count: Number of events to generate.
            source_type: Source database type (see SOURCE_CONFIG keys).

        Returns:
            List of CDC event dictionaries.
        """
        return [self.generate_record(source_type=source_type) for _ in range(count)]

    def generate_mixed_batch(self, count: int = 1000) -> list[dict[str, Any]]:
        """
        Generate a list of CDC events drawn randomly from all source types.

        Source type is selected uniformly at random for each event, producing
        a realistic multi-source stream for Eventstreams ingestion demos.

        Args:
            count: Total number of events to generate.

        Returns:
            List of CDC event dictionaries with mixed source types.
        """
        source_types = list(SOURCE_CONFIG.keys())
        return [
            self.generate_record(source_type=random.choice(source_types))  # nosec B311 - synthetic data only
            for _ in range(count)
        ]

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_image(self, operation: str, side: str) -> dict[str, Any] | None:
        """
        Build a before or after image dict with 3-5 casino-domain fields.

        Rules:
            - INSERT  → before=None,  after=populated
            - DELETE  → before=populated, after=None
            - UPDATE  → before=populated (old values), after=populated (new values)
            - READ    → before=None,  after=populated (snapshot)

        Args:
            operation: CDC operation string.
            side: "before" or "after".

        Returns:
            Dict with casino-domain fields, or None when not applicable.
        """
        needs_before = operation in ("UPDATE", "DELETE")
        needs_after = operation in ("INSERT", "UPDATE", "READ")

        if side == "before" and not needs_before:
            return None
        if side == "after" and not needs_after:
            return None

        return self._generate_casino_image()

    def _generate_casino_image(self) -> dict[str, Any]:
        """Return a realistic casino-domain field dict (3-5 fields)."""
        # Full pool of possible fields; we'll pick a subset
        pool: dict[str, Any] = {
            "player_id": "P" + str(self.rng.integers(100_000, 999_999)),
            "amount": round(float(self.rng.uniform(1.0, 50_000.0)), 2),
            "status": random.choice(_AMOUNT_STATUSES),  # nosec B311 - synthetic data only
            "game_status": random.choice(_GAME_STATUSES),  # nosec B311 - synthetic data only
            "player_tier": random.choice(_PLAYER_TIERS),  # nosec B311 - synthetic data only
            "transaction_type": random.choice(_TRANSACTION_TYPES),  # nosec B311 - synthetic data only
            "payment_method": random.choice(_PAYMENT_METHODS),  # nosec B311 - synthetic data only
            "machine_id": "M" + str(self.rng.integers(1_000, 9_999)),
            "cage_id": "CAGE-" + str(self.rng.integers(1, 20)),
            "shift": random.choice(["DAY", "SWING", "GRAVE"]),  # nosec B311 - synthetic data only
            "denomination": random.choice([0.01, 0.05, 0.25, 1.00, 5.00, 25.00]),  # nosec B311 - synthetic data only
            "win_amount": round(float(self.rng.uniform(0.0, 100_000.0)), 2),
            "session_id": "SES-" + uuid.uuid4().hex[:8].upper(),
            "modified_by": random.choice(["system", "cashier", "pit_boss", "audit"]),  # nosec B311 - synthetic data only
        }

        # Pick 3 to 5 fields
        num_fields = self.rng.integers(3, 6)
        selected_keys = random.sample(list(pool.keys()), k=int(num_fields))  # nosec B311 - synthetic data only
        return {k: pool[k] for k in selected_keys}

    def _generate_lsn(self) -> str:
        """
        Generate a SQL Server-style Log Sequence Number.

        Format: XXXXXXXX:XXXXXXXX:XXXX (hex segments).
        """
        seg1 = format(self.rng.integers(0x00000001, 0x0000FFFF), "08x")
        seg2 = format(self.rng.integers(0x00000001, 0x0000FFFF), "08x")
        seg3 = format(self.rng.integers(0x0001, 0x00FF), "04x")
        return f"{seg1}:{seg2}:{seg3}"

    def _generate_scn(self) -> str:
        """Generate an Oracle-style System Change Number (large integer string)."""
        return str(self.rng.integers(10_000_000_000, 99_999_999_999, dtype=np.int64))

    def _generate_partition_key(self, cfg: dict[str, Any]) -> str:
        """Generate a Cosmos DB-style partition key path with a realistic value."""
        template: str = random.choice(cfg["partition_key_templates"])  # nosec B311 - synthetic data only
        numeric_id = str(self.rng.integers(10_000, 999_999))
        return template.format(id=numeric_id)
