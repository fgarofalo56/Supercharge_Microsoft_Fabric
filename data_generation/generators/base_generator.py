"""
Base Generator Class
====================

Abstract base class for all data generators providing common functionality:
- Seed management for reproducibility
- Output format handling (DataFrame, Parquet, JSON)
- Batch generation
- Progress tracking
"""

import hashlib
import uuid
from abc import ABC, abstractmethod
from collections.abc import Iterator
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from faker import Faker
from tqdm import tqdm


class BaseGenerator(ABC):
    """Abstract base class for data generators."""

    def __init__(
        self,
        seed: int | None = None,
        locale: str = "en_US",
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ):
        """
        Initialize the generator.

        Args:
            seed: Random seed for reproducibility (non-negative integer)
            locale: Faker locale
            start_date: Start date for generated data
            end_date: End date for generated data

        Raises:
            ValueError: If seed is negative or start_date > end_date
        """
        if seed is not None and seed < 0:
            raise ValueError(f"seed must be non-negative, got {seed}")

        self.seed = seed or 42
        self.locale = locale
        self.start_date = start_date or datetime.now() - timedelta(days=30)
        self.end_date = end_date or datetime.now()

        if self.start_date > self.end_date:
            raise ValueError(
                f"start_date ({self.start_date}) must be before "
                f"end_date ({self.end_date})"
            )

        # Initialize random generators
        self.faker = Faker(locale)
        Faker.seed(self.seed)
        self.rng = np.random.default_rng(self.seed)

        # Schema definition (to be overridden by subclasses)
        self._schema: dict[str, str] = {}

    @property
    def schema(self) -> dict[str, str]:
        """Return the schema definition for this generator."""
        return self._schema

    @abstractmethod
    def generate_record(self) -> dict[str, Any]:
        """Generate a single record. Must be implemented by subclasses."""
        pass

    def generate(
        self,
        num_records: int,
        show_progress: bool = True,
    ) -> pd.DataFrame:
        """
        Generate multiple records.

        Args:
            num_records: Number of records to generate (must be positive)
            show_progress: Show progress bar

        Returns:
            DataFrame containing generated records

        Raises:
            ValueError: If num_records is not a positive integer
        """
        if not isinstance(num_records, int) or num_records <= 0:
            raise ValueError(
                f"num_records must be a positive integer, got {num_records}"
            )

        records = []
        iterator = range(num_records)

        if show_progress:
            iterator = tqdm(iterator, desc=f"Generating {self.__class__.__name__}")

        for _ in iterator:
            records.append(self.generate_record())

        return pd.DataFrame(records)

    def generate_batches(
        self,
        num_records: int,
        batch_size: int = 10000,
        show_progress: bool = True,
    ) -> Iterator[pd.DataFrame]:
        """
        Generate records in batches (memory efficient).

        Args:
            num_records: Total number of records (must be positive)
            batch_size: Records per batch (must be positive)
            show_progress: Show progress bar

        Yields:
            DataFrame batches

        Raises:
            ValueError: If num_records or batch_size is not positive
        """
        if not isinstance(num_records, int) or num_records <= 0:
            raise ValueError(
                f"num_records must be a positive integer, got {num_records}"
            )
        if not isinstance(batch_size, int) or batch_size <= 0:
            raise ValueError(f"batch_size must be a positive integer, got {batch_size}")

        remaining = num_records
        batch_num = 0

        while remaining > 0:
            current_batch = min(batch_size, remaining)
            if show_progress:
                print(f"Generating batch {batch_num + 1} ({current_batch} records)...")

            yield self.generate(current_batch, show_progress=False)
            remaining -= current_batch
            batch_num += 1

    def to_parquet(
        self,
        df: pd.DataFrame,
        output_path: str | Path,
        partition_cols: list[str] | None = None,
    ) -> None:
        """
        Save DataFrame to Parquet format.

        Args:
            df: DataFrame to save
            output_path: Output file or directory path
            partition_cols: Columns to partition by

        Raises:
            OSError: If the output path is not writable
        """
        output_path = Path(output_path)
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise OSError(
                f"Cannot create output directory {output_path.parent}: {e}"
            ) from e

        try:
            if partition_cols:
                df.to_parquet(
                    output_path,
                    partition_cols=partition_cols,
                    engine="pyarrow",
                    index=False,
                )
            else:
                df.to_parquet(output_path, engine="pyarrow", index=False)
        except Exception as e:
            raise OSError(f"Failed to write Parquet to {output_path}: {e}") from e

    def to_json(
        self,
        df: pd.DataFrame,
        output_path: str | Path,
        orient: str = "records",
        lines: bool = True,
    ) -> None:
        """
        Save DataFrame to JSON format.

        Args:
            df: DataFrame to save
            output_path: Output file path
            orient: JSON orientation
            lines: Write as JSON lines

        Raises:
            OSError: If the output path is not writable
        """
        output_path = Path(output_path)
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise OSError(
                f"Cannot create output directory {output_path.parent}: {e}"
            ) from e

        try:
            df.to_json(output_path, orient=orient, lines=lines, date_format="iso")
        except Exception as e:
            raise OSError(f"Failed to write JSON to {output_path}: {e}") from e

    # ==========================================================================
    # Helper Methods
    # ==========================================================================

    def random_datetime(
        self,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> datetime:
        """Generate a random datetime within range."""
        start = start or self.start_date
        end = end or self.end_date
        delta = end - start
        random_seconds = int(self.rng.integers(0, int(delta.total_seconds())))
        return start + timedelta(seconds=random_seconds)

    def generate_uuid(self) -> str:
        """Generate a UUID."""
        return str(uuid.uuid4())

    def hash_value(self, value: str, salt: str = "") -> str:
        """Generate SHA-256 hash of a value."""
        return hashlib.sha256(f"{salt}{value}".encode()).hexdigest()

    def mask_ssn(self, ssn: str | None) -> str:
        """Mask SSN showing only last 4 digits.

        Raises:
            ValueError: If ssn is None or has fewer than 4 characters
        """
        if not ssn or len(ssn) < 4:
            raise ValueError(f"SSN must be at least 4 characters, got {ssn!r}")
        return f"XXX-XX-{ssn[-4:]}"

    def mask_card_number(self, card_number: str) -> str:
        """Mask card number showing only last 4 digits."""
        return f"****-****-****-{card_number[-4:]}"

    def weighted_choice(
        self,
        choices: list[Any],
        weights: list[float],
    ) -> Any:
        """Make a weighted random choice.

        Raises:
            ValueError: If choices/weights are empty or weights don't sum to ~1.0
        """
        if not choices or not weights:
            raise ValueError("choices and weights must be non-empty")
        if len(choices) != len(weights):
            raise ValueError(
                f"choices ({len(choices)}) and weights ({len(weights)}) "
                f"must have the same length"
            )
        weight_sum = sum(weights)
        if not (0.99 <= weight_sum <= 1.01):
            raise ValueError(f"weights must sum to ~1.0, got {weight_sum:.4f}")
        return self.rng.choice(choices, p=weights)

    def add_metadata_columns(self, record: dict[str, Any]) -> dict[str, Any]:
        """Add standard metadata columns to a record."""
        record["_ingested_at"] = datetime.now().isoformat()
        record["_source"] = self.__class__.__name__
        record["_batch_id"] = self.generate_uuid()[:8]
        return record
