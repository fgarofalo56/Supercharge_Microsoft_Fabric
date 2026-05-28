"""
Multi-Region Retail Generator
=============================

Produces a small but realistic multi-region retail dataset for the
"Databricks Better Together with Fabric" tutorial.

Output tables:
    - customers       (one row per customer, region tag drives RLS demo)
    - products        (one row per SKU)
    - orders          (one row per order, region tag inherited from customer)
    - order_lines     (one row per line item)
    - returns         (subset of orders flagged as returned)

Regions used (drives every RLS / row-filtering example in the tutorial):
    US-EAST, US-WEST, EMEA, APAC
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import pandas as pd

from data_generation.generators.base_generator import BaseGenerator

REGIONS: tuple[str, ...] = ("US-EAST", "US-WEST", "EMEA", "APAC")

PRODUCT_CATEGORIES: tuple[str, ...] = (
    "Electronics",
    "Apparel",
    "Home",
    "Grocery",
    "Sports",
    "Books",
)

PAYMENT_METHODS: tuple[str, ...] = ("credit_card", "debit_card", "paypal", "gift_card")

ORDER_STATUSES: tuple[str, ...] = ("placed", "shipped", "delivered", "cancelled")


class BetterTogetherRetailGenerator(BaseGenerator):
    """Generates the full multi-region retail dataset used by tutorial 57."""

    def __init__(
        self,
        seed: int | None = 57,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        num_customers: int = 500,
        num_products: int = 120,
        avg_orders_per_customer: float = 4.0,
        avg_lines_per_order: float = 2.5,
        return_rate: float = 0.08,
    ):
        super().__init__(
            seed=seed,
            start_date=start_date or datetime(2025, 1, 1),
            end_date=end_date or datetime(2026, 4, 30),
        )
        self.num_customers = num_customers
        self.num_products = num_products
        self.avg_orders_per_customer = avg_orders_per_customer
        self.avg_lines_per_order = avg_lines_per_order
        self.return_rate = return_rate

        self._customers: pd.DataFrame | None = None
        self._products: pd.DataFrame | None = None

    # BaseGenerator demands a generate_record() — we override generate() instead,
    # so make this a no-op rather than raise (keeps the abstract contract happy).
    def generate_record(self) -> dict[str, Any]:
        raise NotImplementedError(
            "Use generate_all() — this generator emits multiple related tables."
        )

    def _gen_customers(self) -> pd.DataFrame:
        rows = []
        for i in range(self.num_customers):
            region = REGIONS[self.rng.integers(0, len(REGIONS))]
            rows.append(
                {
                    "customer_id": f"C{i + 1:06d}",
                    "first_name": self.faker.first_name(),
                    "last_name": self.faker.last_name(),
                    "email": self.faker.unique.email(),
                    "region": region,
                    "country": self._country_for_region(region),
                    "loyalty_tier": self.rng.choice(
                        ["bronze", "silver", "gold", "platinum"],
                        p=[0.55, 0.27, 0.13, 0.05],
                    ),
                    "created_at": self.faker.date_time_between(
                        start_date=self.start_date, end_date=self.end_date
                    ),
                }
            )
        return pd.DataFrame(rows)

    def _gen_products(self) -> pd.DataFrame:
        rows = []
        for i in range(self.num_products):
            cat = PRODUCT_CATEGORIES[self.rng.integers(0, len(PRODUCT_CATEGORIES))]
            unit_cost = round(float(self.rng.uniform(2.0, 400.0)), 2)
            margin = float(self.rng.uniform(1.15, 2.4))
            rows.append(
                {
                    "product_id": f"P{i + 1:05d}",
                    "sku": f"SKU-{cat[:3].upper()}-{i + 1:05d}",
                    "name": f"{cat} item {i + 1}",
                    "category": cat,
                    "unit_cost": unit_cost,
                    "unit_price": round(unit_cost * margin, 2),
                    "is_active": bool(self.rng.random() > 0.05),
                }
            )
        return pd.DataFrame(rows)

    def _gen_orders_and_lines(
        self,
        customers: pd.DataFrame,
        products: pd.DataFrame,
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        orders: list[dict[str, Any]] = []
        lines: list[dict[str, Any]] = []
        returns: list[dict[str, Any]] = []

        order_counter = 0
        line_counter = 0
        prod_ids = products["product_id"].to_list()
        prod_prices = dict(
            zip(products["product_id"], products["unit_price"], strict=False)
        )

        for _, cust in customers.iterrows():
            n_orders = max(0, int(self.rng.poisson(self.avg_orders_per_customer)))
            for _ in range(n_orders):
                order_counter += 1
                order_id = f"O{order_counter:08d}"
                order_ts = self.faker.date_time_between(
                    start_date=cust["created_at"], end_date=self.end_date
                )
                status = ORDER_STATUSES[self.rng.integers(0, len(ORDER_STATUSES))]
                n_lines = max(1, int(self.rng.poisson(self.avg_lines_per_order)))

                order_total = 0.0
                chosen_products = self.rng.choice(prod_ids, size=n_lines, replace=False)
                for pid in chosen_products:
                    line_counter += 1
                    qty = int(self.rng.integers(1, 5))
                    price = float(prod_prices[pid])
                    line_total = round(price * qty, 2)
                    order_total += line_total
                    lines.append(
                        {
                            "order_line_id": f"OL{line_counter:09d}",
                            "order_id": order_id,
                            "product_id": pid,
                            "quantity": qty,
                            "unit_price": price,
                            "line_total": line_total,
                        }
                    )

                orders.append(
                    {
                        "order_id": order_id,
                        "customer_id": cust["customer_id"],
                        "region": cust["region"],
                        "order_timestamp": order_ts,
                        "status": status,
                        "payment_method": PAYMENT_METHODS[
                            self.rng.integers(0, len(PAYMENT_METHODS))
                        ],
                        "order_total": round(order_total, 2),
                    }
                )

                if status == "delivered" and self.rng.random() < self.return_rate:
                    returns.append(
                        {
                            "return_id": f"R{order_counter:08d}",
                            "order_id": order_id,
                            "customer_id": cust["customer_id"],
                            "region": cust["region"],
                            "return_timestamp": order_ts
                            + timedelta(days=int(self.rng.integers(1, 30))),
                            "reason": self.rng.choice(
                                [
                                    "defective",
                                    "wrong_item",
                                    "no_longer_needed",
                                    "other",
                                ],
                                p=[0.35, 0.20, 0.30, 0.15],
                            ),
                            "refund_amount": round(order_total, 2),
                        }
                    )

        return (
            pd.DataFrame(orders),
            pd.DataFrame(lines),
            pd.DataFrame(returns),
        )

    @staticmethod
    def _country_for_region(region: str) -> str:
        return {
            "US-EAST": "USA",
            "US-WEST": "USA",
            "EMEA": "GBR",
            "APAC": "JPN",
        }[region]

    def generate_all(self) -> dict[str, pd.DataFrame]:
        """Generate every related table in a single deterministic pass."""
        self._customers = self._gen_customers()
        self._products = self._gen_products()
        orders, lines, returns = self._gen_orders_and_lines(
            self._customers, self._products
        )
        return {
            "customers": self._customers,
            "products": self._products,
            "orders": orders,
            "order_lines": lines,
            "returns": returns,
        }
