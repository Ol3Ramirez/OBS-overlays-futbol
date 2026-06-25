const { test, expect } = require('@playwright/test');
const { startProfileServers } = require('./helpers/servers');
const { sendCmd } = require('./helpers/ws');

// penalty.html solo existe en el perfil SRYiyo (ENABLE_PENALTIES).
test.describe('penalty.html [SRYiyo]', () => {
  let servers;
  test.beforeAll(async () => {
    servers = await startProfileServers('SRYiyo');
  });
  test.afterAll(() => servers?.stop());

  test.beforeEach(async ({ page }) => {
    await page.goto(`http://localhost:${servers.httpPort}/penalty.html`);
    await page.waitForFunction(() => typeof window.obsOverlay === 'object');
    await sendCmd(page, servers.wsPort, 'resetPenalty');
    await sendCmd(page, servers.wsPort, 'setPenaltyKicks', 5);
  });

  test('setPenaltyKick suma solo los goles al marcador de penales', async ({ page }) => {
    await sendCmd(page, servers.wsPort, 'setPenaltyKick', 'home', 0, 'goal');
    await sendCmd(page, servers.wsPort, 'setPenaltyKick', 'home', 1, 'goal');
    await sendCmd(page, servers.wsPort, 'setPenaltyKick', 'away', 0, 'miss');

    await expect(page.locator('#home-count')).toHaveText('2');
    await expect(page.locator('#away-count')).toHaveText('0');
  });

  test('resetPenalty vuelve el marcador a cero', async ({ page }) => {
    await sendCmd(page, servers.wsPort, 'setPenaltyKick', 'home', 0, 'goal');
    await expect(page.locator('#home-count')).toHaveText('1');
    await sendCmd(page, servers.wsPort, 'resetPenalty');
    await expect(page.locator('#home-count')).toHaveText('0');
  });

  test('setPenaltyTeams actualiza los nombres', async ({ page }) => {
    await sendCmd(page, servers.wsPort, 'setPenaltyTeams', 'rojos', 'azules');
    await expect(page.locator('#home-team')).toHaveText('ROJOS');
    await expect(page.locator('#away-team')).toHaveText('AZULES');
  });
});
