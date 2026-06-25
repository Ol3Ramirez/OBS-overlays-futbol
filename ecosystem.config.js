const path = require('path');
const isWin = process.platform === 'win32';

// __dirname funciona sin importar espacios ni usuario — cross-platform
const BASE = __dirname;

// Interprete de Python segun plataforma (Windows suele tener solo `python`).
const PYTHON = isWin ? 'python' : 'python3';

// Puertos leidos desde profile.json (SSOT) — no hardcodear.
// NOTA: PM2 arranca el http.server directo y NO regenera config.js. Antes de usar
// `pm2 start`, corre una vez iniciar_stream.sh/.ps1 (o `python gen_config.py <perfil>`).
const portsOf = (profile) => require(path.join(BASE, profile, 'profile.json'));

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

// App HTTP de un perfil — sirve los overlays en el puerto de su profile.json.
const httpApp = (profile) => ({
  name: `${profile.toLowerCase()}-http`,
  script: PYTHON,
  args: `-m http.server ${portsOf(profile).httpPort}`,
  cwd: path.join(BASE, profile),
  interpreter: 'none',
  autorestart: true,
  watch: false,
  ...logs(profile),
});

// App WS relay de un perfil — el puerto lo lee ws_relay.py de profile.json.
const wsApp = (profile) => ({
  name: `${profile.toLowerCase()}-ws`,
  cwd: path.join(BASE, profile),
  interpreter: 'none',
  autorestart: true,
  watch: false,
  ...wsScript(),
  ...wsLogs(profile),
});

const PROFILES = ['original', 'SRYiyo', 'plantilla'];

module.exports = {
  apps: PROFILES.flatMap((profile) => [httpApp(profile), wsApp(profile)]),
};
