import { gql } from "@apollo/client";

// ---------------------------------------------------------------------------
// Player queries
// ---------------------------------------------------------------------------

export const GET_PLAYERS = gql`
  query GetPlayers($first: Int, $offset: Int, $sortBy: String) {
    players(first: $first, offset: $offset, sortBy: $sortBy) {
      items {
        player_id
        first_name
        last_name
        loyalty_tier
        total_coin_in
        total_coin_out
        visit_count
        last_visit_date
        signup_date
      }
      totalCount
      hasNextPage
    }
  }
`;

export const GET_PLAYER_DETAIL = gql`
  query GetPlayerDetail($playerId: String!) {
    player(player_id: $playerId) {
      player_id
      first_name
      last_name
      loyalty_tier
      total_coin_in
      total_coin_out
      visit_count
      last_visit_date
      signup_date
      favorite_machine_type
      avg_session_duration_min
    }
  }
`;

// ---------------------------------------------------------------------------
// Slot performance queries
// ---------------------------------------------------------------------------

export const GET_SLOT_PERFORMANCE = gql`
  query GetSlotPerformance($casinoName: String, $date: String) {
    slotPerformance(casino_name: $casinoName, play_date: $date) {
      items {
        machine_id
        casino_name
        denomination
        coin_in
        coin_out
        jackpot_amount
        theoretical_hold_pct
        actual_hold_pct
        games_played
        play_date
      }
      totalCount
    }
  }
`;

export const GET_KPI_SUMMARY = gql`
  query GetKpiSummary($startDate: String!, $endDate: String!) {
    kpiSummary(start_date: $startDate, end_date: $endDate) {
      total_coin_in
      total_coin_out
      net_revenue
      avg_hold_pct
      active_machines
      total_games_played
      unique_players
    }
  }
`;
