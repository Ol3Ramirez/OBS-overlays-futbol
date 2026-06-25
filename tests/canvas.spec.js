const { test, expect } = require('@playwright/test');
const { startProfileServers, PROFILES } = require('./helpers/servers');
const { sendCmd } = require('./helpers/ws');

for (const profileName of Object.keys(PROFILES)) {
  test.describe(`canvas.html [${profileName}]`, () => {
    let servers;
    test.beforeAll(async () => {
      servers = await startProfileServers(profileName);
    });
    test.afterAll(() => servers?.stop());

    test.beforeEach(async ({ page }) => {
      await page.goto(`http://localhost:${servers.httpPort}/canvas.html`);
      await page.waitForFunction(() => typeof window.obsOverlay === 'object');
    });

    test('el canvas escala por devicePixelRatio (backing store > 0)', async ({ page }) => {
      const dims = await page.evaluate(() => {
        const c = document.getElementById('fx');
        return { w: c.width, h: c.height, expectedW: Math.round(c.clientWidth * (window.devicePixelRatio || 1)) };
      });
      expect(dims.w).toBeGreaterThan(0);
      expect(dims.h).toBeGreaterThan(0);
      expect(dims.w).toBe(dims.expectedW);
    });

    test('expone la API obsOverlay (start/stop/setColors/setIntensity)', async ({ page }) => {
      const api = await page.evaluate(() =>
        ['start', 'stop', 'setColors', 'setIntensity'].map((fn) => typeof window.obsOverlay[fn]),
      );
      expect(api).toEqual(['function', 'function', 'function', 'function']);
    });

    test('setIntensity por WS no rompe el overlay', async ({ page }) => {
      await sendCmd(page, servers.wsPort, 'setIntensity', 60);
      // sigue vivo y la API responde tras el comando
      const ok = await page.evaluate(() => typeof window.obsOverlay.start === 'function');
      expect(ok).toBe(true);
    });
  });
}
