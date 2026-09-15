"""
Streamlit Casino Slot Performance Dashboard
============================================
Connects to a Microsoft Fabric SQL endpoint via pyodbc and renders
executive-level KPIs, slot performance breakdowns, and revenue trend
charts using Plotly.

Prerequisites
-------------
- ODBC Driver 18 for SQL Server installed on the host
- Service principal with access to the Fabric SQL endpoint
- Environment variables: FABRIC_SQL_ENDPOINT, FABRIC_DATABASE,
  AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID
"""

from __future__ import annotations

import os
from datetime import date, timedelta
from typing import Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

FABRIC_SQL_ENDPOINT: str = os.getenv("FABRIC_SQL_ENDPOINT", "")
FABRIC_DATABASE: str = os.getenv("FABRIC_DATABASE", "")
AZURE_CLIENT_ID: str = os.getenv("AZURE_CLIENT_ID", "")
AZURE_CLIENT_SECRET: str = os.getenv("AZURE_CLIENT_SECRET", "")
AZURE_TENANT_ID: str = os.getenv("AZURE_TENANT_ID", "")

TOKEN_URL_TEMPLATE: str = (
    "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
)
FABRIC_SCOPE: str = "https://database.windows.net/.default"


# ---------------------------------------------------------------------------
# Authentication helpers
# ---------------------------------------------------------------------------


def _get_access_token() -> str:
    """Acquire an OAuth2 access token using client credentials flow."""
    import urllib.request
    import urllib.parse
    import json

    token_url = TOKEN_URL_TEMPLATE.format(tenant=AZURE_TENANT_ID)
    payload = urllib.parse.urlencode(
        {
            "grant_type": "client_credentials",
            "client_id": AZURE_CLIENT_ID,
            "client_secret": AZURE_CLIENT_SECRET,
            "scope": FABRIC_SCOPE,
        }
    ).encode()

    req = urllib.request.Request(token_url, data=payload)
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = json.loads(resp.read().decode())
    return body["access_token"]


def _build_connection_string() -> str:
    """Build a pyodbc connection string for Fabric SQL endpoint."""
    token = _get_access_token()
    return (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={FABRIC_SQL_ENDPOINT};"
        f"DATABASE={FABRIC_DATABASE};"
        f"Encrypt=yes;TrustServerCertificate=no;"
        f"Authentication=ActiveDirectoryAccessToken;"
        f"AccessToken={token};"
    )


# ---------------------------------------------------------------------------
# Data-access layer (cached)
# ---------------------------------------------------------------------------


def _get_connection():
    """Return a pyodbc connection to the Fabric SQL endpoint."""
    import pyodbc

    try:
        conn = pyodbc.connect(_build_connection_string(), timeout=30)
        return conn
    except pyodbc.Error as exc:
        st.error(
            f"Failed to connect to Fabric SQL endpoint: {exc}\n\n"
            "Verify FABRIC_SQL_ENDPOINT, FABRIC_DATABASE, and service-principal "
            "credentials in your .env file."
        )
        st.stop()


@st.cache_data(ttl=300, show_spinner="Querying Fabric...")
def fetch_slot_performance(
    start_date: str,
    end_date: str,
    casino: Optional[str] = None,
    denomination: Optional[str] = None,
) -> pd.DataFrame:
    """Return slot-machine performance rows for the given filters."""
    query = """
        SELECT
            machine_id,
            casino_name,
            denomination,
            play_date,
            coin_in,
            coin_out,
            jackpot_amount,
            theoretical_hold_pct,
            actual_hold_pct,
            games_played
        FROM gold_slot_performance
        WHERE play_date BETWEEN ? AND ?
    """
    params: list = [start_date, end_date]

    if casino:
        query += " AND casino_name = ?"
        params.append(casino)
    if denomination:
        query += " AND denomination = ?"
        params.append(denomination)

    query += " ORDER BY play_date DESC"

    conn = _get_connection()
    try:
        return pd.read_sql(query, conn, params=params)
    finally:
        conn.close()


@st.cache_data(ttl=300, show_spinner="Querying Fabric...")
def fetch_revenue_trends(start_date: str, end_date: str) -> pd.DataFrame:
    """Return daily revenue aggregation for trend analysis."""
    query = """
        SELECT
            play_date,
            casino_name,
            SUM(coin_in)          AS total_coin_in,
            SUM(coin_out)         AS total_coin_out,
            SUM(coin_in - coin_out) AS net_revenue,
            COUNT(DISTINCT machine_id) AS active_machines,
            SUM(games_played)     AS total_games
        FROM gold_slot_performance
        WHERE play_date BETWEEN ? AND ?
        GROUP BY play_date, casino_name
        ORDER BY play_date
    """
    conn = _get_connection()
    try:
        return pd.read_sql(query, conn, params=[start_date, end_date])
    finally:
        conn.close()


@st.cache_data(ttl=600, show_spinner="Loading filter options...")
def fetch_filter_options() -> dict:
    """Return distinct casino names and denominations for sidebar filters."""
    conn = _get_connection()
    try:
        casinos = pd.read_sql(
            "SELECT DISTINCT casino_name FROM gold_slot_performance ORDER BY 1",
            conn,
        )
        denominations = pd.read_sql(
            "SELECT DISTINCT denomination FROM gold_slot_performance ORDER BY 1",
            conn,
        )
        return {
            "casinos": casinos["casino_name"].tolist(),
            "denominations": denominations["denomination"].tolist(),
        }
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------


def _kpi_card(label: str, value: str, delta: Optional[str] = None) -> None:
    """Render a single KPI metric card."""
    st.metric(label=label, value=value, delta=delta)


def _validate_env() -> bool:
    """Return True when all required env vars are present."""
    missing = [
        name
        for name in (
            "FABRIC_SQL_ENDPOINT",
            "FABRIC_DATABASE",
            "AZURE_CLIENT_ID",
            "AZURE_CLIENT_SECRET",
            "AZURE_TENANT_ID",
        )
        if not os.getenv(name)
    ]
    if missing:
        st.error(
            "Missing required environment variables: "
            + ", ".join(f"`{v}`" for v in missing)
        )
        st.info("Copy `.env.example` to `.env` and fill in the values.")
        return False
    return True


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------


def page_executive_dashboard(df: pd.DataFrame) -> None:
    """Executive-level KPI summary."""
    st.header("Executive Dashboard")

    if df.empty:
        st.warning("No data for the selected filters.")
        return

    total_coin_in = df["coin_in"].sum()
    total_coin_out = df["coin_out"].sum()
    net_revenue = total_coin_in - total_coin_out
    avg_hold = df["actual_hold_pct"].mean() if "actual_hold_pct" in df.columns else 0
    total_games = df["games_played"].sum() if "games_played" in df.columns else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        _kpi_card("Total Coin-In", f"${total_coin_in:,.0f}")
    with col2:
        _kpi_card("Total Coin-Out", f"${total_coin_out:,.0f}")
    with col3:
        _kpi_card("Net Revenue", f"${net_revenue:,.0f}")
    with col4:
        _kpi_card("Avg Hold %", f"{avg_hold:.2f}%")

    st.divider()

    col_left, col_right = st.columns(2)

    with col_left:
        rev_by_casino = (
            df.groupby("casino_name")
            .agg(revenue=("coin_in", "sum"))
            .reset_index()
        )
        fig_pie = px.pie(
            rev_by_casino,
            names="casino_name",
            values="revenue",
            title="Revenue Share by Casino",
            hole=0.4,
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_right:
        rev_by_denom = (
            df.groupby("denomination")
            .agg(revenue=("coin_in", "sum"))
            .reset_index()
        )
        fig_bar = px.bar(
            rev_by_denom,
            x="denomination",
            y="revenue",
            title="Revenue by Denomination",
            labels={"revenue": "Coin-In ($)", "denomination": "Denomination"},
            color="denomination",
        )
        st.plotly_chart(fig_bar, use_container_width=True)


def page_slot_performance(df: pd.DataFrame) -> None:
    """Interactive slot-machine performance explorer."""
    st.header("Slot Performance")

    if df.empty:
        st.warning("No data for the selected filters.")
        return

    fig = px.scatter(
        df,
        x="theoretical_hold_pct",
        y="actual_hold_pct",
        color="denomination",
        size="coin_in",
        hover_data=["machine_id", "casino_name"],
        title="Theoretical vs Actual Hold %",
        labels={
            "theoretical_hold_pct": "Theoretical Hold %",
            "actual_hold_pct": "Actual Hold %",
        },
    )
    fig.add_trace(
        go.Scatter(
            x=[0, df["theoretical_hold_pct"].max()],
            y=[0, df["theoretical_hold_pct"].max()],
            mode="lines",
            name="Parity Line",
            line={"dash": "dash", "color": "gray"},
        )
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Raw Data")
    st.dataframe(df, use_container_width=True, height=400)


def page_revenue_trends(start: str, end: str) -> None:
    """Time-series revenue trend analysis."""
    st.header("Revenue Trends")

    trend_df = fetch_revenue_trends(start, end)
    if trend_df.empty:
        st.warning("No trend data for the selected date range.")
        return

    fig_line = px.line(
        trend_df,
        x="play_date",
        y="net_revenue",
        color="casino_name",
        title="Daily Net Revenue by Casino",
        labels={"net_revenue": "Net Revenue ($)", "play_date": "Date"},
    )
    st.plotly_chart(fig_line, use_container_width=True)

    fig_area = px.area(
        trend_df,
        x="play_date",
        y="total_games",
        color="casino_name",
        title="Daily Games Played",
        labels={"total_games": "Games Played", "play_date": "Date"},
    )
    st.plotly_chart(fig_area, use_container_width=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    st.set_page_config(
        page_title="Casino Slot Performance - Fabric Consumer",
        page_icon=":slot_machine:",
        layout="wide",
    )
    st.title("Casino Slot Performance Dashboard")
    st.caption("Powered by Microsoft Fabric SQL Endpoint")

    if not _validate_env():
        return

    # -- Sidebar filters ---------------------------------------------------
    st.sidebar.header("Filters")

    options = fetch_filter_options()

    date_range = st.sidebar.date_input(
        "Date Range",
        value=(date.today() - timedelta(days=30), date.today()),
        max_value=date.today(),
    )
    start_str = str(date_range[0]) if isinstance(date_range, tuple) else str(date_range)
    end_str = str(date_range[1]) if isinstance(date_range, tuple) and len(date_range) > 1 else start_str

    casino = st.sidebar.selectbox(
        "Casino", options=["All"] + options["casinos"]
    )
    denomination = st.sidebar.selectbox(
        "Denomination", options=["All"] + options["denominations"]
    )

    selected_casino = None if casino == "All" else casino
    selected_denom = None if denomination == "All" else denomination

    # -- Fetch data --------------------------------------------------------
    df = fetch_slot_performance(
        start_str, end_str, selected_casino, selected_denom
    )

    # -- Page navigation ---------------------------------------------------
    page = st.sidebar.radio(
        "Page",
        options=["Executive Dashboard", "Slot Performance", "Revenue Trends"],
    )

    if page == "Executive Dashboard":
        page_executive_dashboard(df)
    elif page == "Slot Performance":
        page_slot_performance(df)
    else:
        page_revenue_trends(start_str, end_str)


if __name__ == "__main__":
    main()
