const { defineConfig, devices } = require('@playwright/test');

// Los servidores (http.server + ws_relay) se levantan por perfil dentro de cada
// spec con helpers/servers.js (cada perfil usa puertos distintos y ws_relay
// necesita uv), por eso aqui NO usamos webServer.
module.exports = defineConfig({
  testDir: './tests',
  fullyParallel: false,
  workers: 1,
  timeout: 30_000,
  expect: { timeout: 7_000 },
  retries: process.env.CI ? 1 : 0,
  reporter: [['list']],
  use: {
    headless: !process.env.HEADED,
    actionTimeout: 7_000,
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
});
