import React from "react";
import { useQuery } from "@apollo/client";
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  CircularProgress,
  Alert,
} from "@mui/material";
import { GET_KPI_SUMMARY, GET_SLOT_PERFORMANCE } from "../queries";

// ---------------------------------------------------------------------------
// KPI card
// ---------------------------------------------------------------------------

interface KpiCardProps {
  title: string;
  value: string;
  subtitle?: string;
}

function KpiCard({ title, value, subtitle }: KpiCardProps) {
  return (
    <Card elevation={2}>
      <CardContent>
        <Typography variant="subtitle2" color="text.secondary">
          {title}
        </Typography>
        <Typography variant="h4" sx={{ my: 1 }}>
          {value}
        </Typography>
        {subtitle && (
          <Typography variant="body2" color="text.secondary">
            {subtitle}
          </Typography>
        )}
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Simple bar chart (pure CSS -- avoids adding a charting dep)
// ---------------------------------------------------------------------------

interface BarDatum {
  label: string;
  value: number;
}

function SimpleBarChart({ data, title }: { data: BarDatum[]; title: string }) {
  const max = Math.max(...data.map((d) => d.value), 1);
  return (
    <Card elevation={2} sx={{ p: 2 }}>
      <Typography variant="subtitle1" gutterBottom>
        {title}
      </Typography>
      {data.map((d) => (
        <Box key={d.label} sx={{ mb: 1 }}>
          <Typography variant="caption">
            {d.label} &mdash; ${d.value.toLocaleString()}
          </Typography>
          <Box
            sx={{
              height: 18,
              width: `${(d.value / max) * 100}%`,
              backgroundColor: "primary.main",
              borderRadius: 1,
              minWidth: 4,
            }}
          />
        </Box>
      ))}
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Dashboard page
// ---------------------------------------------------------------------------

export default function Dashboard() {
  const today = new Date().toISOString().slice(0, 10);
  const thirtyDaysAgo = new Date(Date.now() - 30 * 86_400_000)
    .toISOString()
    .slice(0, 10);

  const {
    data: kpiData,
    loading: kpiLoading,
    error: kpiError,
  } = useQuery(GET_KPI_SUMMARY, {
    variables: { startDate: thirtyDaysAgo, endDate: today },
  });

  const {
    data: slotData,
    loading: slotLoading,
    error: slotError,
  } = useQuery(GET_SLOT_PERFORMANCE, {
    variables: { date: today },
  });

  if (kpiLoading || slotLoading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", py: 6 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (kpiError) return <Alert severity="error">KPI query failed: {kpiError.message}</Alert>;
  if (slotError) return <Alert severity="error">Slot query failed: {slotError.message}</Alert>;

  const kpi = kpiData?.kpiSummary ?? {};

  const denomRevenue: BarDatum[] = (() => {
    const items = slotData?.slotPerformance?.items ?? [];
    const grouped: Record<string, number> = {};
    for (const item of items) {
      grouped[item.denomination] =
        (grouped[item.denomination] ?? 0) + (item.coin_in - item.coin_out);
    }
    return Object.entries(grouped)
      .map(([label, value]) => ({ label, value }))
      .sort((a, b) => b.value - a.value);
  })();

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        30-Day KPI Summary
      </Typography>

      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <KpiCard title="Total Coin-In" value={`$${(kpi.total_coin_in ?? 0).toLocaleString()}`} />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <KpiCard title="Net Revenue" value={`$${(kpi.net_revenue ?? 0).toLocaleString()}`} />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <KpiCard title="Avg Hold %" value={`${(kpi.avg_hold_pct ?? 0).toFixed(2)}%`} />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <KpiCard
            title="Active Machines"
            value={(kpi.active_machines ?? 0).toLocaleString()}
            subtitle={`${(kpi.total_games_played ?? 0).toLocaleString()} games played`}
          />
        </Grid>
      </Grid>

      <SimpleBarChart data={denomRevenue} title="Today's Revenue by Denomination" />
    </Box>
  );
}
