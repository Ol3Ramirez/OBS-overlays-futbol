// Levanta los servidores reales de un perfil (http.server + ws_relay.py) para
// los tests E2E, de modo que se ejerza el camino real: panel -> relay -> overlay.
// Si el puerto ya responde (porque el stream esta corriendo), se reutiliza.
const { spawn } = require('node:child_process');
const path = require('node:path');
const net = require('node:net');

const ROOT = path.resolve(__dirname, '..', '..');

const PROFILES = {
  original: { dir: 'original', httpPort: 8888, wsPort: 8889 },
  SRYiyo: { dir: 'SRYiyo', httpPort: 8890, wsPort: 8891 },
};

const PYTHON = process.platform === 'win32' ? 'python' : 'python3';

function isPortOpen(port) {
  return new Promise((resolve) => {
    const socket = net.connect({ port, host: '127.0.0.1' }, () => {
      socket.end();
      resolve(true);
    });
    socket.on('error', () => resolve(false));
    socket.setTimeout(500, () => {
      socket.destroy();
      resolve(false);
    });
  });
}

async function waitForPort(port, timeoutMs = 12_000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    if (await isPortOpen(port)) return true;
    await new Promise((r) => setTimeout(r, 250));
  }
  throw new Error(`Timeout esperando el puerto ${port}`);
}

function runGenConfig(profileDir) {
  return new Promise((resolve, reject) => {
    const gen = spawn(PYTHON, [path.join(ROOT, 'shared', 'gen_config.py'), profileDir], {
      stdio: 'ignore',
    });
    gen.on('error', reject);
    gen.on('exit', (code) => (code === 0 ? resolve() : reject(new Error(`gen_config salio ${code}`))));
  });
}

// Arranca (o reutiliza) los servidores del perfil. Devuelve { httpPort, wsPort, stop }.
async function startProfileServers(profileName) {
  const cfg = PROFILES[profileName];
  if (!cfg) throw new Error(`Perfil desconocido: ${profileName}`);
  const profileDir = path.join(ROOT, cfg.dir);

  // Siempre regenerar config.js desde profile.json (esta gitignoreado).
  await runGenConfig(profileDir);

  const children = [];
  const spawned = { http: false, ws: false };

  if (!(await isPortOpen(cfg.httpPort))) {
    const http = spawn(PYTHON, ['-m', 'http.server', String(cfg.httpPort), '--directory', profileDir], {
      stdio: 'ignore',
    });
    children.push(http);
    spawned.http = true;
  }

  if (!(await isPortOpen(cfg.wsPort))) {
    const ws = spawn('uv', ['run', path.join(profileDir, 'ws_relay.py')], {
      cwd: profileDir,
      stdio: 'ignore',
    });
    children.push(ws);
    spawned.ws = true;
  }

  await waitForPort(cfg.httpPort);
  await waitForPort(cfg.wsPort);

  return {
    httpPort: cfg.httpPort,
    wsPort: cfg.wsPort,
    spawned,
    stop() {
      for (const child of children) {
        try {
          child.kill('SIGTERM');
        } catch {
          /* ya muerto */
        }
      }
    },
  };
}

module.exports = { startProfileServers, PROFILES };
