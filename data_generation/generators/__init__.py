"""
Data Generators Package
=======================

Provides synthetic data generators for casino/gaming domain:
- SlotMachineGenerator: Slot machine telemetry and events
- TableGameGenerator: Table game transactions
- PlayerGenerator: Player profiles and loyalty data
- FinancialGenerator: Cage and financial transactions
- SecurityGenerator: Security and surveillance events
- ComplianceGenerator: CTR, SAR, W-2G compliance data
"""

from .base_generator import BaseGenerator
from .compliance_generator import ComplianceGenerator
from .financial_generator import FinancialGenerator
from .player_generator import PlayerGenerator
from .security_generator import SecurityGenerator
from .slot_machine_generator import SlotMachineGenerator
from .table_games_generator import TableGamesGenerator as TableGameGenerator

__all__ = [
    "BaseGenerator",
    "ComplianceGenerator",
    "FinancialGenerator",
    "PlayerGenerator",
    "SecurityGenerator",
    "SlotMachineGenerator",
    "TableGameGenerator",
]
