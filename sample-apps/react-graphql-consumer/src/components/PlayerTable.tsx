import React, { useState, useMemo } from "react";
import { useQuery } from "@apollo/client";
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TableSortLabel,
  TablePagination,
  Paper,
  TextField,
  Box,
  Typography,
  CircularProgress,
  Alert,
  Chip,
} from "@mui/material";
import { GET_PLAYERS } from "../queries";

interface Player {
  player_id: string;
  first_name: string;
  last_name: string;
  loyalty_tier: string;
  total_coin_in: number;
  total_coin_out: number;
  visit_count: number;
  last_visit_date: string;
  signup_date: string;
}

type SortDirection = "asc" | "desc";

const TIER_COLORS: Record<string, "default" | "info" | "warning" | "success" | "error"> = {
  Bronze: "default",
  Silver: "info",
  Gold: "warning",
  Platinum: "success",
  Diamond: "error",
};

const PAGE_SIZE = 25;

export default function PlayerTable() {
  const [page, setPage] = useState(0);
  const [sortField, setSortField] = useState<keyof Player>("last_name");
  const [sortDir, setSortDir] = useState<SortDirection>("asc");
  const [filter, setFilter] = useState("");

  const { data, loading, error } = useQuery(GET_PLAYERS, {
    variables: { first: PAGE_SIZE, offset: page * PAGE_SIZE, sortBy: sortField },
  });

  const players: Player[] = data?.players?.items ?? [];
  const totalCount: number = data?.players?.totalCount ?? 0;

  const filtered = useMemo(() => {
    if (!filter) return players;
    const lower = filter.toLowerCase();
    return players.filter(
      (p) =>
        p.first_name.toLowerCase().includes(lower) ||
        p.last_name.toLowerCase().includes(lower) ||
        p.player_id.toLowerCase().includes(lower) ||
        p.loyalty_tier.toLowerCase().includes(lower),
    );
  }, [players, filter]);

  const sorted = useMemo(() => {
    return [...filtered].sort((a, b) => {
      const av = a[sortField];
      const bv = b[sortField];
      const cmp = typeof av === "number" ? av - (bv as number) : String(av).localeCompare(String(bv));
      return sortDir === "asc" ? cmp : -cmp;
    });
  }, [filtered, sortField, sortDir]);

  const handleSort = (field: keyof Player) => {
    setSortDir(sortField === field && sortDir === "asc" ? "desc" : "asc");
    setSortField(field);
  };

  if (error) return <Alert severity="error">Query failed: {error.message}</Alert>;

  const columns: { key: keyof Player; label: string; align?: "right" }[] = [
    { key: "player_id", label: "Player ID" },
    { key: "first_name", label: "First Name" },
    { key: "last_name", label: "Last Name" },
    { key: "loyalty_tier", label: "Tier" },
    { key: "total_coin_in", label: "Coin-In", align: "right" },
    { key: "total_coin_out", label: "Coin-Out", align: "right" },
    { key: "visit_count", label: "Visits", align: "right" },
    { key: "last_visit_date", label: "Last Visit" },
  ];

  return (
    <Paper sx={{ p: 2 }}>
      <Box sx={{ display: "flex", justifyContent: "space-between", mb: 2 }}>
        <Typography variant="h6">Player Directory</Typography>
        <TextField
          size="small"
          label="Search"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
        />
      </Box>

      {loading ? (
        <Box sx={{ display: "flex", justifyContent: "center", py: 4 }}>
          <CircularProgress />
        </Box>
      ) : (
        <>
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  {columns.map((col) => (
                    <TableCell key={col.key} align={col.align}>
                      <TableSortLabel
                        active={sortField === col.key}
                        direction={sortField === col.key ? sortDir : "asc"}
                        onClick={() => handleSort(col.key)}
                      >
                        {col.label}
                      </TableSortLabel>
                    </TableCell>
                  ))}
                </TableRow>
              </TableHead>
              <TableBody>
                {sorted.map((p) => (
                  <TableRow key={p.player_id} hover>
                    <TableCell>{p.player_id}</TableCell>
                    <TableCell>{p.first_name}</TableCell>
                    <TableCell>{p.last_name}</TableCell>
                    <TableCell>
                      <Chip
                        label={p.loyalty_tier}
                        size="small"
                        color={TIER_COLORS[p.loyalty_tier] ?? "default"}
                      />
                    </TableCell>
                    <TableCell align="right">${p.total_coin_in.toLocaleString()}</TableCell>
                    <TableCell align="right">${p.total_coin_out.toLocaleString()}</TableCell>
                    <TableCell align="right">{p.visit_count}</TableCell>
                    <TableCell>{p.last_visit_date}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
          <TablePagination
            component="div"
            count={totalCount}
            page={page}
            onPageChange={(_, p) => setPage(p)}
            rowsPerPage={PAGE_SIZE}
            rowsPerPageOptions={[PAGE_SIZE]}
          />
        </>
      )}
    </Paper>
  );
}
