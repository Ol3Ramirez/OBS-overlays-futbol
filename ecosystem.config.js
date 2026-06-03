const path = require('path');
const isWin = process.platform === 'win32';

// __dirname funciona sin importar espacios ni usuario — cross-platform
const BASE = __dirname;

const logs = (profile) => ({
  out_file:   path.join(BASE, profile, 'logs', 'http.log'),
  error_file: path.join(BASE, profile, 'logs', 'http.error.log'),
});

const wsLogs = (profile) => ({
  out_file:   path.join(BASE, profile, 'logs', 'ws.log'),
  error_file: path.join(BASE, profile, 'logs', 'ws.error.log'),
});

// Script WS según plataforma — ruta relativa para evitar problemas con espacios en el path
const wsScript = () =>
  isWin
    ? { script: 'powershell', args: '-File .\\run_ws.ps1' }
    : { script: 'bash',       args: './run_ws.sh' };

module.exports = {
  apps: [
    // ─── original  (Avila Fisioterapia · HTTP 8888 · WS 8889) ────────
    {
      name: 'original-http',
      script: 'python3',
      args: '-m http.server 8888',
      cwd: path.join(BASE, 'original'),
      interpreter: 'none',
      autorestart: true,
      watch: false,
      ...logs('original'),
    },
    {
      name: 'original-ws',
      cwd: path.join(BASE, 'original'),
      interpreter: 'none',
      autorestart: true,
      watch: false,
      ...wsScript(),
      ...wsLogs('original'),
    },

    // ─── SRYiyo  (Robles Fútbol · HTTP 8890 · WS 8891) ───────────────
    {
      name: 'sryiyo-http',
      script: 'python3',
      args: '-m http.server 8890',
      cwd: path.join(BASE, 'SRYiyo'),
      interpreter: 'none',
      autorestart: true,
      watch: false,
      ...logs('SRYiyo'),
    },
    {
      name: 'sryiyo-ws',
      cwd: path.join(BASE, 'SRYiyo'),
      interpreter: 'none',
      autorestart: true,
      watch: false,
      ...wsScript(),
      ...wsLogs('SRYiyo'),
    },
  ],
};
