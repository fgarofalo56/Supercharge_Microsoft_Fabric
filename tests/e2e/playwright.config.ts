import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for testing Microsoft Fabric documentation
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  testDir: '.',
  testMatch: '**/*.spec.ts',

  /* Run tests in parallel */
  fullyParallel: true,

  /* Fail the build on CI if you accidentally left test.only in the source code */
  forbidOnly: !!process.env.CI,

  /* Retry on CI only */
  retries: process.env.CI ? 2 : 0,

  /* Use fewer workers on CI */
  workers: process.env.CI ? 2 : undefined,

  /* Reporter configuration */
  reporter: [
    ['html', { open: 'never' }],
    ['list'],
    ['json', { outputFile: 'test-results/results.json' }],
  ],

  /* Shared settings for all projects */
  use: {
    /* Base URL from environment or default to GitHub Pages */
    /* Ensure trailing slash for GitHub Pages compatibility */
    baseURL: (process.env.BASE_URL || 'https://fgarofalo56.github.io/Supercharge_Microsoft_Fabric').replace(/\/?$/, '/'),

    /* Collect trace on first retry */
    trace: 'on-first-retry',

    /* Screenshot on failure */
    screenshot: 'only-on-failure',

    /* Video on failure */
    video: 'retain-on-failure',

    /* Navigation timeout */
    navigationTimeout: 30000,

    /* Action timeout */
    actionTimeout: 15000,
  },

  /* Test timeout */
  timeout: 60000,

  /* Expect timeout */
  expect: {
    timeout: 10000,
  },

  /* Configure projects for major browsers */
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  /* Output directory for test artifacts */
  outputDir: 'test-results/',
});
