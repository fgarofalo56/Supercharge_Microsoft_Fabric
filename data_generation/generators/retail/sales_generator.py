"""
Retail POS Sales Generator
===========================

Generates realistic point-of-sale transaction data for a mid-market
omnichannel retailer (450 stores, 85K SKUs, 12M loyalty members).

Features:
- Realistic seasonality (holiday spikes, day-of-week patterns)
- Category mix with weighted distribution
- PCI-DSS compliant: card numbers are tokenized (never real PANs)
- Loyalty program linkage
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta
from typing import Any

import numpy as np

from data_generation.generators.base_generator import BaseGenerator

# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------

CATEGORIES = {
    "Grocery": {
        "subcategories": ["Dairy", "Bakery", "Produce", "Frozen", "Snacks", "Beverages"],
        "price_range": (1.50, 25.00),
        "weight": 0.35,
    },
    "Apparel": {
        "subcategories": ["Men", "Women", "Kids", "Accessories", "Footwear"],
        "price_range": (9.99, 149.99),
        "weight": 0.18,
    },
    "Electronics": {
        "subcategories": ["Phones", "Accessories", "Audio", "Computing", "Gaming"],
        "price_range": (4.99, 999.99),
        "weight": 0.12,
    },
    "Home & Garden": {
        "subcategories": ["Kitchen", "Bath", "Furniture", "Outdoor", "Decor"],
        "price_range": (3.99, 299.99),
        "weight": 0.15,
    },
    "Health & Beauty": {
        "subcategories": ["Skincare", "Haircare", "Supplements", "Personal Care"],
        "price_range": (2.99, 79.99),
        "weight": 0.12,
    },
    "Toys & Sports": {
        "subcategories": ["Toys", "Fitness", "Outdoor Sports", "Team Sports"],
        "price_range": (4.99, 199.99),
        "weight": 0.08,
    },
}

BRANDS = [
    "StoreBrand", "NaturePlus", "FreshCo", "PrimeLine", "ValueMax",
    "UrbanEdge", "TechNova", "HomeEssentials", "GreenLeaf", "ActiveLife",
    "QuickBite", "StyleFirst", "ProGear", "BrightStar", "PureBasics",
]

STORE_FORMATS = ["big-box", "express", "online"]
STORE_FORMAT_WEIGHTS = [0.50, 0.35, 0.15]

REGIONS = ["Northeast", "Southeast", "Midwest", "Southwest", "West", "Pacific"]

PAYMENT_METHODS = ["credit", "debit", "cash", "mobile_pay", "gift_card"]
PAYMENT_WEIGHTS = [0.35, 0.25, 0.20, 0.15, 0.05]

CUSTOMER_SEGMENTS = ["Platinum", "Gold", "Silver", "Bronze", "New"]
SEGMENT_WEIGHTS = [0.05, 0.15, 0.30, 0.30, 0.20]

# US federal holidays (month, day) for seasonality
HOLIDAY_DATES = [
    (1, 1), (2, 14), (5, 27), (7, 4), (9, 2),
    (10, 31), (11, 28), (12, 25), (12, 31),
]


class RetailSalesGenerator(BaseGenerator):
    """Generate synthetic POS transactions for a retail chain."""

    def __init__(
        self,
        num_stores: int = 450,
        num_skus: int = 5000,
        num_customers: int = 50000,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.num_stores = num_stores
        self.num_skus = num_skus
        self.num_customers = num_customers

        self._stores = self._build_stores()
        self._products = self._build_products()
        self._customers = self._build_customers()

        self._schema = {
            "txn_id": "string",
            "txn_timestamp": "timestamp",
            "store_id": "string",
            "sku": "string",
            "category": "string",
            "subcategory": "string",
            "brand": "string",
            "qty": "int",
            "unit_price": "double",
            "discount_pct": "double",
            "line_total": "double",
            "payment_method": "string",
            "card_token": "string",
            "card_last4": "string",
            "loyalty_id": "string",
            "customer_segment": "string",
            "store_format": "string",
            "region": "string",
        }

    # ------------------------------------------------------------------
    # Reference-data builders
    # ------------------------------------------------------------------

    def _build_stores(self) -> list[dict[str, str]]:
        stores = []
        for i in range(1, self.num_stores + 1):
            fmt = self.weighted_choice(STORE_FORMATS, STORE_FORMAT_WEIGHTS)
            region = self.rng.choice(REGIONS)
            stores.append({
                "store_id": f"STR-{i:04d}",
                "format": fmt,
                "region": region,
            })
        return stores

    def _build_products(self) -> list[dict[str, Any]]:
        products = []
        cat_names = list(CATEGORIES.keys())
        cat_weights = [CATEGORIES[c]["weight"] for c in cat_names]
        for i in range(1, self.num_skus + 1):
            cat = self.weighted_choice(cat_names, cat_weights)
            info = CATEGORIES[cat]
            subcat = self.rng.choice(info["subcategories"])
            lo, hi = info["price_range"]
            price = round(float(self.rng.uniform(lo, hi)), 2)
            cost = round(price * float(self.rng.uniform(0.40, 0.75)), 2)
            products.append({
                "sku": f"SKU-{i:06d}",
                "category": cat,
                "subcategory": subcat,
                "brand": self.rng.choice(BRANDS),
                "unit_price": price,
                "cost": cost,
            })
        return products

    def _build_customers(self) -> list[dict[str, Any]]:
        customers = []
        for i in range(1, self.num_customers + 1):
            segment = self.weighted_choice(CUSTOMER_SEGMENTS, SEGMENT_WEIGHTS)
            join_dt = self.faker.date_between(
                start_date="-5y", end_date="today"
            )
            customers.append({
                "customer_id": f"CUST-{i:07d}",
                "loyalty_id": f"LYL-{i:010d}",
                "segment": segment,
                "join_dt": str(join_dt),
                "lifetime_spend": round(float(self.rng.uniform(50, 25000)), 2),
            })
        return customers

    # ------------------------------------------------------------------
    # Seasonality helpers
    # ------------------------------------------------------------------

    def _seasonality_multiplier(self, dt: datetime) -> float:
        """Return a multiplier [0.7 .. 2.5] based on date seasonality."""
        base = 1.0
        # Day-of-week: weekends are busier
        if dt.weekday() >= 5:
            base *= 1.25
        # Holiday proximity
        for m, d in HOLIDAY_DATES:
            holiday = dt.replace(month=m, day=d)
            days_away = abs((dt - holiday).days)
            if days_away <= 7:
                base *= 1.4 + 1.1 * math.exp(-days_away / 2.0)
                break
        # Month-level seasonality (sinusoidal)
        month_factor = 1.0 + 0.15 * math.sin(2 * math.pi * (dt.month - 1) / 12.0)
        return round(base * month_factor, 4)

    # ------------------------------------------------------------------
    # Core generation
    # ------------------------------------------------------------------

    def generate_record(self) -> dict[str, Any]:
        """Generate a single POS transaction line item."""
        txn_dt = self.random_datetime()
        store = self.rng.choice(self._stores)
        product = self.rng.choice(self._products)

        # Quantity influenced by seasonality
        mult = self._seasonality_multiplier(txn_dt)
        qty = max(1, int(self.rng.poisson(1.8 * mult)))

        # Discount: 70% no discount, 20% small, 10% large
        disc_roll = float(self.rng.random())
        if disc_roll < 0.70:
            discount_pct = 0.0
        elif disc_roll < 0.90:
            discount_pct = round(float(self.rng.uniform(0.05, 0.20)), 2)
        else:
            discount_pct = round(float(self.rng.uniform(0.20, 0.50)), 2)

        unit_price = product["unit_price"]
        line_total = round(qty * unit_price * (1 - discount_pct), 2)

        # Payment
        payment = self.weighted_choice(PAYMENT_METHODS, PAYMENT_WEIGHTS)

        # Card token (PCI-DSS: no real PAN)
        if payment in ("credit", "debit"):
            card_token = f"tok_{self.generate_uuid().replace('-', '')[:24]}"
            card_last4 = f"{int(self.rng.integers(0, 10000)):04d}"
        else:
            card_token = None
            card_last4 = None

        # Loyalty — 75% of transactions have loyalty linkage
        if float(self.rng.random()) < 0.75:
            cust = self.rng.choice(self._customers)
            loyalty_id = cust["loyalty_id"]
            segment = cust["segment"]
        else:
            loyalty_id = None
            segment = None

        record = {
            "txn_id": f"TXN-{self.generate_uuid()[:12].upper()}",
            "txn_timestamp": txn_dt.isoformat(),
            "store_id": store["store_id"],
            "sku": product["sku"],
            "category": product["category"],
            "subcategory": product["subcategory"],
            "brand": product["brand"],
            "qty": qty,
            "unit_price": unit_price,
            "discount_pct": discount_pct,
            "line_total": line_total,
            "payment_method": payment,
            "card_token": card_token,
            "card_last4": card_last4,
            "loyalty_id": loyalty_id,
            "customer_segment": segment,
            "store_format": store["format"],
            "region": store["region"],
        }
        return self.add_metadata_columns(record)
