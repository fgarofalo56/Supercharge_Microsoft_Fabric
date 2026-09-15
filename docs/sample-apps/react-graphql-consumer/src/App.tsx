import React from "react";
import {
  ApolloClient,
  ApolloProvider,
  InMemoryCache,
  createHttpLink,
} from "@apollo/client";
import { setContext } from "@apollo/client/link/context";
import {
  CssBaseline,
  ThemeProvider,
  createTheme,
  AppBar,
  Toolbar,
  Typography,
  Container,
  Box,
  Tab,
  Tabs,
  Alert,
} from "@mui/material";
import Dashboard from "./components/Dashboard";
import PlayerTable from "./components/PlayerTable";

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

const FABRIC_GRAPHQL_ENDPOINT =
  process.env.REACT_APP_FABRIC_GRAPHQL_ENDPOINT ?? "";
const MSAL_CLIENT_ID = process.env.REACT_APP_MSAL_CLIENT_ID ?? "";
const MSAL_AUTHORITY = process.env.REACT_APP_MSAL_AUTHORITY ?? "";

// ---------------------------------------------------------------------------
// MSAL token acquisition (simplified - see README for full MSAL setup)
// ---------------------------------------------------------------------------

async function acquireToken(): Promise<string> {
  // In production, use @azure/msal-react's useMsal hook.
  // This helper demonstrates the concept for non-interactive flows.
  const { PublicClientApplication } = await import("@azure/msal-browser");
  const msalInstance = new PublicClientApplication({
    auth: {
      clientId: MSAL_CLIENT_ID,
      authority: MSAL_AUTHORITY,
    },
  });

  await msalInstance.initialize();

  const accounts = msalInstance.getAllAccounts();
  if (accounts.length === 0) {
    const loginResp = await msalInstance.loginPopup({
      scopes: ["https://analysis.windows.net/powerbi/api/.default"],
    });
    return loginResp.accessToken;
  }

  const silentResp = await msalInstance.acquireTokenSilent({
    scopes: ["https://analysis.windows.net/powerbi/api/.default"],
    account: accounts[0],
  });
  return silentResp.accessToken;
}

// ---------------------------------------------------------------------------
// Apollo Client
// ---------------------------------------------------------------------------

const httpLink = createHttpLink({ uri: FABRIC_GRAPHQL_ENDPOINT });

const authLink = setContext(async (_, { headers }) => {
  const token = await acquireToken();
  return {
    headers: {
      ...headers,
      authorization: `Bearer ${token}`,
    },
  };
});

const client = new ApolloClient({
  link: authLink.concat(httpLink),
  cache: new InMemoryCache(),
});

// ---------------------------------------------------------------------------
// Theme
// ---------------------------------------------------------------------------

const theme = createTheme({
  palette: {
    primary: { main: "#1a73e8" },
    secondary: { main: "#e8710a" },
    background: { default: "#f5f5f5" },
  },
  typography: {
    fontFamily: "'Segoe UI', Roboto, sans-serif",
  },
});

// ---------------------------------------------------------------------------
// App
// ---------------------------------------------------------------------------

interface TabPanelProps {
  children: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel({ children, value, index }: TabPanelProps) {
  return (
    <div role="tabpanel" hidden={value !== index}>
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

function App() {
  const [tab, setTab] = React.useState(0);

  const missingConfig = !FABRIC_GRAPHQL_ENDPOINT || !MSAL_CLIENT_ID;

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <ApolloProvider client={client}>
        <AppBar position="static">
          <Toolbar>
            <Typography variant="h6" sx={{ flexGrow: 1 }}>
              Casino Analytics &mdash; Fabric GraphQL Consumer
            </Typography>
          </Toolbar>
        </AppBar>

        <Container maxWidth="xl" sx={{ mt: 3 }}>
          {missingConfig && (
            <Alert severity="warning" sx={{ mb: 2 }}>
              Set <code>REACT_APP_FABRIC_GRAPHQL_ENDPOINT</code> and{" "}
              <code>REACT_APP_MSAL_CLIENT_ID</code> in your{" "}
              <code>.env</code> file.
            </Alert>
          )}

          <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
            <Tabs value={tab} onChange={(_, v) => setTab(v)}>
              <Tab label="Dashboard" />
              <Tab label="Player Data" />
            </Tabs>
          </Box>

          <TabPanel value={tab} index={0}>
            <Dashboard />
          </TabPanel>
          <TabPanel value={tab} index={1}>
            <PlayerTable />
          </TabPanel>
        </Container>
      </ApolloProvider>
    </ThemeProvider>
  );
}

export default App;
