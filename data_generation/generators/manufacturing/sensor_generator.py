"""
Manufacturing Sensor Data Generator
====================================

Generates realistic IoT sensor telemetry for a discrete manufacturing plant:
- Sensor readings (vibration, temperature, current, pressure, RPM)
- Machine inventory (CNC, press, robot, conveyor)
- Work orders (preventive, corrective, predictive)

Includes degradation patterns that model gradual bearing wear, thermal drift,
and current draw increase before machine failure.

Compliance: IEC 62443 -- data contains no PII; OT network metadata only.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta
from typing import Any

import pandas as pd

from data_generation.generators.base_generator import BaseGenerator

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MACHINE_TYPES = ["CNC", "press", "robot", "conveyor"]
MACHINE_TYPE_WEIGHTS = [0.60, 0.15, 0.15, 0.10]

SENSOR_NAMES = ["vibration_mm_s", "temperature_c", "current_a", "pressure_bar", "rpm"]

# Normal operating ranges per sensor
SENSOR_RANGES: dict[str, dict[str, tuple[float, float]]] = {
    "CNC": {
        "vibration_mm_s": (0.5, 4.5),
        "temperature_c": (25, 60),
        "current_a": (8, 40),
        "pressure_bar": (4.0, 7.5),
        "rpm": (800, 12000),
    },
    "press": {
        "vibration_mm_s": (1.0, 5.0),
        "temperature_c": (30, 70),
        "current_a": (15, 50),
        "pressure_bar": (5.0, 9.0),
        "rpm": (0, 0),
    },
    "robot": {
        "vibration_mm_s": (0.3, 3.0),
        "temperature_c": (22, 50),
        "current_a": (5, 25),
        "pressure_bar": (3.0, 6.0),
        "rpm": (0, 0),
    },
    "conveyor": {
        "vibration_mm_s": (0.2, 2.5),
        "temperature_c": (20, 45),
        "current_a": (3, 15),
        "pressure_bar": (0, 0),
        "rpm": (100, 600),
    },
}

WORK_ORDER_TYPES = ["preventive", "corrective", "predictive"]
WORK_ORDER_WEIGHTS = [0.50, 0.30, 0.20]


class ManufacturingSensorGenerator(BaseGenerator):
    """Generate manufacturing sensor telemetry with degradation patterns.

    Args:
        seed: Random seed for reproducibility.
        num_machines: Total machines in the plant (default 200).
        start_date: Start of data generation window.
        end_date: End of data generation window.
        degradation_pct: Fraction of machines exhibiting degradation (0-1).
    """

    def __init__(
        self,
        seed: int | None = None,
        num_machines: int = 200,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        degradation_pct: float = 0.10,
    ):
        super().__init__(seed=seed, start_date=start_date, end_date=end_date)
        self.num_machines = num_machines
        self.degradation_pct = degradation_pct

        # Build machine inventory
        self.machines = self._build_machines()

        # Select machines that will show degradation
        n_degraded = max(1, int(num_machines * degradation_pct))
        self._degraded_ids = set(
            self.rng.choice(
                [m["machine_id"] for m in self.machines], size=n_degraded, replace=False
            )
        )

        # Track per-machine degradation progress (0.0 = healthy, 1.0 = failure)
        self._degradation_state: dict[str, float] = {
            mid: 0.0 for mid in self._degraded_ids
        }

        self._schema = {
            "sensor_id": "string",
            "machine_id": "string",
            "machine_type": "string",
            "timestamp": "datetime",
            "vibration_mm_s": "float",
            "temperature_c": "float",
            "current_a": "float",
            "pressure_bar": "float",
            "rpm": "float",
        }

    # ------------------------------------------------------------------
    # Machine inventory
    # ------------------------------------------------------------------

    def _build_machines(self) -> list[dict[str, Any]]:
        """Create machine inventory with type, install date, last maintenance."""
        machines: list[dict[str, Any]] = []
        for i in range(self.num_machines):
            mtype = str(self.rng.choice(MACHINE_TYPES, p=MACHINE_TYPE_WEIGHTS))
            prefix = mtype.upper()[:3]
            machine_id = f"{prefix}-{i + 1:04d}"
            install_dt = self.start_date - timedelta(
                days=int(self.rng.integers(180, 3650))
            )
            last_maint = self.start_date - timedelta(days=int(self.rng.integers(1, 90)))
            machines.append(
                {
                    "machine_id": machine_id,
                    "machine_type": mtype,
                    "install_dt": install_dt.isoformat(),
                    "last_maintenance_dt": last_maint.isoformat(),
                }
            )
        return machines

    # ------------------------------------------------------------------
    # Degradation model
    # ------------------------------------------------------------------

    def _apply_degradation(
        self,
        machine_id: str,
        base_vibration: float,
        base_temp: float,
        base_current: float,
    ) -> tuple[float, float, float]:
        """Apply gradual degradation to sensor values for flagged machines."""
        if machine_id not in self._degraded_ids:
            return base_vibration, base_temp, base_current

        progress = self._degradation_state[machine_id]
        # Advance degradation (each record ~ small time step)
        progress = min(1.0, progress + 0.002)
        self._degradation_state[machine_id] = progress

        # Vibration: linear then exponential near failure
        if progress < 0.8:
            vib_factor = 1.0 + progress * 1.5
        else:
            vib_factor = 1.0 + 1.2 + math.exp((progress - 0.8) * 10) * 0.5

        # Temperature: slow drift
        temp_offset = progress * 20.0

        # Current: gradual increase
        cur_factor = 1.0 + progress * 0.3

        return (
            base_vibration * vib_factor,
            base_temp + temp_offset,
            base_current * cur_factor,
        )

    # ------------------------------------------------------------------
    # Record generation
    # ------------------------------------------------------------------

    def generate_record(self) -> dict[str, Any]:
        """Generate a single sensor reading."""
        machine = self.machines[int(self.rng.integers(0, self.num_machines))]
        mtype = machine["machine_type"]
        machine_id = machine["machine_id"]
        ranges = SENSOR_RANGES[mtype]

        # Base values (normal operating range + noise)
        def _val(key: str) -> float:
            lo, hi = ranges[key]
            if lo == 0 and hi == 0:
                return 0.0
            mid = (lo + hi) / 2
            std = (hi - lo) / 6  # ~99.7% within range
            return float(self.rng.normal(mid, std))

        vibration = _val("vibration_mm_s")
        temperature = _val("temperature_c")
        current = _val("current_a")
        pressure = _val("pressure_bar")
        rpm = _val("rpm")

        # Apply degradation if applicable
        vibration, temperature, current = self._apply_degradation(
            machine_id, vibration, temperature, current
        )

        # Clamp to physical minimums
        vibration = max(0.0, vibration)
        temperature = max(-10.0, temperature)
        current = max(0.0, current)
        pressure = max(0.0, pressure)
        rpm = max(0.0, rpm)

        timestamp = self.random_datetime()
        sensor_id = f"{machine_id}-S{int(self.rng.integers(1, 6)):01d}"

        record = {
            "sensor_id": sensor_id,
            "machine_id": machine_id,
            "machine_type": mtype,
            "timestamp": timestamp.isoformat(),
            "vibration_mm_s": round(vibration, 3),
            "temperature_c": round(temperature, 2),
            "current_a": round(current, 2),
            "pressure_bar": round(pressure, 2),
            "rpm": round(rpm, 1),
        }
        return self.add_metadata_columns(record)

    # ------------------------------------------------------------------
    # Work order generation
    # ------------------------------------------------------------------

    def generate_work_orders(self, num_orders: int = 500) -> pd.DataFrame:
        """Generate maintenance work orders.

        Args:
            num_orders: Number of work orders to generate.

        Returns:
            DataFrame with work order records.
        """
        records: list[dict[str, Any]] = []
        for _ in range(num_orders):
            machine = self.machines[int(self.rng.integers(0, self.num_machines))]
            wo_type = str(self.rng.choice(WORK_ORDER_TYPES, p=WORK_ORDER_WEIGHTS))
            scheduled = self.random_datetime()
            duration_hrs = float(self.rng.uniform(0.5, 8.0))
            completed = scheduled + timedelta(hours=duration_hrs)

            records.append(
                {
                    "wo_id": self.generate_uuid(),
                    "machine_id": machine["machine_id"],
                    "machine_type": machine["machine_type"],
                    "wo_type": wo_type,
                    "scheduled_dt": scheduled.isoformat(),
                    "completed_dt": completed.isoformat()
                    if self.rng.random() > 0.1
                    else None,
                    "parts_cost": round(float(self.rng.uniform(50, 5000)), 2),
                    "labor_hrs": round(duration_hrs, 1),
                }
            )
        return pd.DataFrame(records)

    # ------------------------------------------------------------------
    # Machine inventory accessor
    # ------------------------------------------------------------------

    def get_machines(self) -> pd.DataFrame:
        """Return the machine inventory as a DataFrame."""
        return pd.DataFrame(self.machines)
