const { test, expect } = require('@playwright/test');
const { startProfileServers } = require('./helpers/servers');
const { sendCmd } = require('./helpers/ws');

// ── Feature flags: el panel muestra/oculta segun los flags de profile.json ──
const FLAG_LOCATORS = {
  penales: '.tab[data-feature="ENABLE_PENALTIES"]',
  qr: '[data-feature="ENABLE_QR"]',
  undo: '#log-panel',
};

// Un feature "encendido" deja el elemento con display != 'none' (el panel hace
// el.style.display = flag ? '' : 'none'). Verificamos eso en vez de visibilidad
// geometrica, porque algunos paneles arrancan colapsados (altura 0) aun activos.
async function featureDisplay(page, selector) {
  return page.locator(selector).first().evaluate((el) => getComputedStyle(el).display);
}

test.describe('control_remoto.html [original] — flags apagados', () => {
  let servers;
  test.beforeAll(async () => {
    servers = await startProfileServers('original');
  });
  test.afterAll(() => servers?.stop());

  test('oculta penales, QR y el panel de undo', async ({ page }) => {
    await page.goto(`http://localhost:${servers.httpPort}/control_remoto.html`);
    for (const sel of Object.values(FLAG_LOCATORS)) {
      expect(await featureDisplay(page, sel)).toBe('none');
    }
  });
});

test.describe('control_remoto.html [SRYiyo] — flags encendidos', () => {
  let servers;
  test.beforeAll(async () => {
    servers = await startProfileServers('SRYiyo');
  });
  test.afterAll(() => servers?.stop());

  test.beforeEach(async ({ page }) => {
    await page.goto(`http://localhost:${servers.httpPort}/control_remoto.html`);
  });

  test('muestra penales, QR y el panel de undo', async ({ page }) => {
    for (const sel of Object.values(FLAG_LOCATORS)) {
      expect(await featureDisplay(page, sel)).not.toBe('none');
    }
  });

  test('el event log persiste en sessionStorage al recargar', async ({ page }) => {
    await page.waitForTimeout(800); // esperar a que el panel conecte al relay
    // Hotkey Y (tarjeta amarilla): las tarjetas/cambios son lo que va al event log.
    await page.locator('body').press('y');
    await expect(page.locator('#log-list')).not.toBeEmpty();
    await page.reload();
    const log = await page.evaluate(() => sessionStorage.getItem('eventLog'));
    expect(log).toBeTruthy();
    await expect(page.locator('#log-list')).not.toBeEmpty();
  });

  test('hotkey G envia gol que llega al marcador (panel -> relay -> overlay)', async ({
    context,
  }) => {
    const marcador = await context.newPage();
    await marcador.goto(`http://localhost:${servers.httpPort}/marcador.html`);
    await marcador.waitForFunction(() => typeof window.obsOverlay === 'object');
    await sendCmd(marcador, servers.wsPort, 'setScore', 0, 0);

    const panel = await context.newPage();
    await panel.goto(`http://localhost:${servers.httpPort}/control_remoto.html`);
    await panel.waitForTimeout(500); // dejar que el panel conecte al relay
    await panel.locator('body').press('g');

    await expect(marcador.locator('#home-score')).toHaveText('1');
    await marcador.close();
    await panel.close();
  });
});
