const { test, expect } = require('@playwright/test');
const fs = require('node:fs');
const path = require('node:path');
const { startProfileServers, PROFILES } = require('./helpers/servers');
const { sendCmd } = require('./helpers/ws');

const ROOT = path.resolve(__dirname, '..');

for (const profileName of Object.keys(PROFILES)) {
  test.describe(`marcador.html [${profileName}]`, () => {
    let servers;
    const profile = JSON.parse(
      fs.readFileSync(path.join(ROOT, PROFILES[profileName].dir, 'profile.json'), 'utf-8'),
    );

    test.beforeAll(async () => {
      servers = await startProfileServers(profileName);
    });
    test.afterAll(() => servers?.stop());

    test.beforeEach(async ({ page }) => {
      await page.goto(`http://localhost:${servers.httpPort}/marcador.html`);
      // Esperar a que ws-client.js conecte (window.obsOverlay definido por el overlay).
      await page.waitForFunction(() => typeof window.obsOverlay === 'object');
      await sendCmd(page, servers.wsPort, 'setScore', 0, 0);
    });

    test('carga los equipos desde el config.js generado (SSOT)', async ({ page }) => {
      // El nombre que renderiza el overlay debe venir de profile.json -> config.js.
      await expect(page.locator('#home-name')).toHaveText(profile.home);
      await expect(page.locator('#away-name')).toHaveText(profile.away);
    });

    test('setScore fija el marcador exacto', async ({ page }) => {
      await sendCmd(page, servers.wsPort, 'setScore', 3, 2);
      await expect(page.locator('#home-score')).toHaveText('3');
      await expect(page.locator('#away-score')).toHaveText('2');
    });

    test('goalHome y goalAway incrementan el marcador', async ({ page }) => {
      await sendCmd(page, servers.wsPort, 'goalHome', 'Jugador 10');
      await expect(page.locator('#home-score')).toHaveText('1');
      await sendCmd(page, servers.wsPort, 'goalAway', 'Jugador 7');
      await expect(page.locator('#away-score')).toHaveText('1');
    });

    test('setTeams sobreescribe los nombres en vivo', async ({ page }) => {
      await sendCmd(page, servers.wsPort, 'setTeams', 'LOCAL TEST', 'VISITA TEST');
      await expect(page.locator('#home-name')).toHaveText('LOCAL TEST');
      await expect(page.locator('#away-name')).toHaveText('VISITA TEST');
    });
  });
}
