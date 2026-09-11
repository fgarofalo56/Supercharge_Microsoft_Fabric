# Documentation E2E Tests

This directory contains Playwright end-to-end tests for the Microsoft Fabric documentation site.

## What These Tests Verify

- **Page Loading**: All key pages load without 404 errors
- **Navigation**: Menu structure works correctly
- **Links**: Internal links are not broken
- **Images**: Images load properly
- **Code Blocks**: Syntax highlighting and copy buttons work
- **Mermaid Diagrams**: Diagrams render correctly
- **Responsive Design**: Site works on mobile and tablet
- **Accessibility**: Basic accessibility checks (headings, alt text)
- **Performance**: Pages load within acceptable time

## Running Tests Locally

### Prerequisites

- Node.js 18+ installed
- npm or yarn

### Setup

```bash
cd tests/e2e
npm install
npx playwright install chromium
```

### Run Tests

```bash
# Run all tests
npm test

# Run with browser visible
npm run test:headed

# Run with Playwright UI
npm run test:ui

# Debug tests
npm run test:debug
```

### Test Against Local MkDocs Server

```bash
# In project root, start MkDocs dev server
mkdocs serve

# In another terminal, run tests against local server
cd tests/e2e
BASE_URL=http://localhost:8000 npm test
```

### Test Against Production

```bash
# Tests default to the GitHub Pages URL
npm test

# Or specify a custom URL
BASE_URL=https://your-site.github.io/repo/ npm test
```

## Viewing Reports

After running tests, view the HTML report:

```bash
npm run report
```

This opens an interactive report showing:
- Test results (pass/fail)
- Screenshots on failure
- Traces for debugging
- Timing information

## CI/CD Integration

These tests run automatically:

1. **After Documentation Deployment**: Tests run after the docs workflow deploys to GitHub Pages
2. **On Pull Requests**: Tests run when PRs modify documentation files
3. **Manual Trigger**: Can be triggered manually from GitHub Actions

## Test Structure

```
tests/e2e/
├── docs.spec.ts      # Main test file
├── playwright.config.ts  # Playwright configuration
├── package.json      # Node.js dependencies
├── tsconfig.json     # TypeScript configuration
└── README.md         # This file
```

## Adding New Tests

Add new tests to `docs.spec.ts` or create new `.spec.ts` files:

```typescript
import { test, expect } from '@playwright/test';

test.describe('New Feature', () => {
  test('should work correctly', async ({ page }) => {
    await page.goto('/some-page/');
    await expect(page.locator('h1')).toContainText('Expected Title');
  });
});
```

## Troubleshooting

### Tests fail with timeout

- Increase timeout in `playwright.config.ts`
- Check if the site is accessible
- Verify BASE_URL is correct

### Tests pass locally but fail in CI

- CI uses the production URL; check if deployment succeeded
- CI waits 30 seconds for deployment propagation
- Check GitHub Actions logs for details

### Screenshots not appearing

- Screenshots are only captured on failure
- Check `test-results/` directory
- View HTML report for embedded screenshots

## Configuration

Edit `playwright.config.ts` to modify:

- Test timeout
- Browser settings
- Screenshot/video options
- Parallel execution
- Retry behavior
