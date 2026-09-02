import { test, expect } from '@playwright/test';

/**
 * E2E tests for the Copilot chat widget and compliance-threshold content
 * on the live GitHub Pages site.
 */

const CHAT_PAGE = './chat/';
const BACKEND_ORIGIN = 'https://fabric-copilot-docs-ldai.azurewebsites.net';

test.describe('Copilot Chat Widget', () => {
  test('chat page loads with widget initialized', async ({ page }) => {
    const response = await page.goto(CHAT_PAGE);
    expect(response?.status()).toBe(200);
    const launcher = page.locator(
      '#copilot-launcher, #copilot-fullpage, [class*="copilot"]'
    );
    await expect(launcher.first()).toBeVisible({ timeout: 15000 });
  });

  test('widget script loads without console errors', async ({ page }) => {
    const errors: string[] = [];
    page.on('pageerror', (err) => errors.push(err.message));
    await page.goto(CHAT_PAGE);
    await page.waitForTimeout(3000);
    const widgetErrors = errors.filter((e) =>
      e.toLowerCase().includes('copilot')
    );
    expect(widgetErrors).toEqual([]);
  });

  test('widget points at the Azure Function backend', async ({ page }) => {
    await page.goto(CHAT_PAGE);
    const config = await page.evaluate(
      () => (window as any).COPILOT_CONFIG ?? null
    );
    if (config?.apiEndpoint) {
      expect(config.apiEndpoint).toContain('azurewebsites.net');
    } else {
      const scriptResp = await page.request.get(
        './javascripts/copilot-chat.js'
      );
      expect(scriptResp.status()).toBe(200);
      const body = await scriptResp.text();
      expect(body).toContain('azurewebsites.net/api/chat');
      expect(body).toContain('/api/feedback');
      expect(body).toContain('/api/request');
    }
  });

  test('backend responds to a chat POST with grounded answer', async ({
    request,
  }) => {
    const response = await request.post(BACKEND_ORIGIN + '/api/chat', {
      headers: {
        'Content-Type': 'application/json',
        Origin: 'https://fgarofalo56.github.io',
      },
      data: {
        message: 'What is the CTR compliance threshold?',
        history: [],
      },
      timeout: 60000,
    });
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(body.reply).toBeTruthy();
    expect(body.reply).toContain('$10,000');
  });

  test('backend CORS is locked to the GitHub Pages origin', async ({
    request,
  }) => {
    const response = await request.fetch(BACKEND_ORIGIN + '/api/chat', {
      method: 'OPTIONS',
      headers: {
        Origin: 'https://fgarofalo56.github.io',
        'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'Content-Type',
      },
    });
    const allowOrigin = response.headers()['access-control-allow-origin'];
    expect(allowOrigin).toBe('https://fgarofalo56.github.io');
  });

  test('full chat round-trip through the UI', async ({ page }) => {
    test.setTimeout(90000);
    await page.goto(CHAT_PAGE);

    const launcher = page.locator(
      '#copilot-launcher, button[class*="copilot-launcher"], .copilot-fab'
    );
    if (await launcher.first().isVisible().catch(() => false)) {
      await launcher.first().click();
    }

    const input = page.locator(
      '#copilot-input, textarea[class*="copilot"], input[class*="copilot"]'
    );
    await expect(input.first()).toBeVisible({ timeout: 10000 });
    await input.first().fill('What is the CTR compliance threshold?');

    const sendBtn = page.locator(
      '#copilot-send, button[class*="copilot-send"], button[aria-label*="Send"]'
    );
    if (await sendBtn.first().isVisible().catch(() => false)) {
      await sendBtn.first().click();
    } else {
      await input.first().press('Enter');
    }

    const messages = page.locator(
      '[class*="copilot-message"], [class*="assistant"], #copilot-messages > *'
    );
    await expect(
      messages.filter({ hasText: '$10,000' }).first()
    ).toBeVisible({ timeout: 60000 });
  });
});

test.describe('Compliance Threshold Content (post-correction)', () => {
  const THRESHOLD_PAGES = [
    './features/paginated-reports/',
    './features/user-data-functions/',
    './best-practices/medallion-architecture-deep-dive/',
  ];

  for (const path of THRESHOLD_PAGES) {
    test(path + ' states keno threshold as $600', async ({ page }) => {
      const response = await page.goto(path);
      test.skip(response?.status() === 404, path + ' not found on site');

      const content = await page.textContent('body');
      expect(content).toBeTruthy();

      // Match a window around each "keno" mention in BOTH directions,
      // since docs write it both as "keno ... $600" and "$600 (keno)".
      const kenoMentions =
        content!.match(/[^.]{0,120}keno[^.]{0,120}/gi) ?? [];
      const hasCorrect = kenoMentions.some((m) => m.includes('600'));
      expect(
        hasCorrect,
        'Expected a keno mention with $600 on ' + path
      ).toBe(true);

      // Extract just the keno clause: from "keno" to the next ")" or
      // "," — so poker's $5,000 later in the same sentence isn't flagged.
      const wrongKeno = kenoMentions.filter((m) => {
        const clause = m.match(/keno[^),]*/i)?.[0] ?? '';
        return (
          clause.includes('1,500') ||
          clause.includes('1500') ||
          clause.includes('5,000')
        );
      });
      expect(wrongKeno, 'Stale keno threshold on ' + path).toEqual([]);
    });
  }

  test('glossary no longer claims keno threshold is $5,000', async ({
    page,
  }) => {
    const response = await page.goto('./GLOSSARY/');
    test.skip(response?.status() === 404, 'Glossary page not found');

    const content = await page.textContent('body');
    const w2gSection = content!.match(/W-2G[^|]{0,300}/i);
    if (w2gSection) {
      expect(w2gSection[0]).not.toContain('$5,000+ keno');
    }
  });
});
