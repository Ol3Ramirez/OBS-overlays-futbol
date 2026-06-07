/**
 * setup_obs.js — Crea la colección "WIFI TLX Mundial 2026" en OBS
 *
 * Qué hace:
 *   1. Conecta a OBS WebSocket (puerto 4455)
 *   2. Crea o activa la colección "WIFI TLX Mundial 2026"
 *   3. Ajusta resolución a 1080×1080 @ 30 FPS
 *   4. Crea una escena por template HTML con browser source 1080×1080
 *
 * Uso:
 *   cp .env.example .env  → poner contraseña OBS
 *   npm install
 *   npm run setup
 */
import 'dotenv/config';
import OBSWebSocket from 'obs-websocket-js';
import { WIFITLX } from './config.js';

const obs = new OBSWebSocket();
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function connect() {
  const password = process.env.OBS_WS_PASSWORD || '';
  await obs.connect(WIFITLX.OBS_WS_URL, password);
  const { obsVersion, obsWebSocketVersion } = await obs.call('GetVersion');
  console.log(`✓ OBS ${obsVersion}  ws-protocol ${obsWebSocketVersion}`);
}

/** Guarda colección activa + resolución de video antes de tocar nada */
async function guardarEstado() {
  const { currentSceneCollectionName } = await obs.call('GetSceneCollectionList');
  const video = await obs.call('GetVideoSettings');
  const estado = {
    collection: currentSceneCollectionName,
    video: {
      baseWidth:      video.baseWidth,
      baseHeight:     video.baseHeight,
      outputWidth:    video.outputWidth,
      outputHeight:   video.outputHeight,
      fpsNumerator:   video.fpsNumerator,
      fpsDenominator: video.fpsDenominator,
    },
  };
  console.log(`✓ Estado guardado: "${estado.collection}" ${estado.video.baseWidth}×${estado.video.baseHeight} @${Math.round(estado.video.fpsNumerator / estado.video.fpsDenominator)}fps`);
  return estado;
}

/** Restaura la colección y resolución de video originales */
async function restaurarEstado(estado) {
  console.log('\nRestaurando configuración original...');
  if (estado.collection !== WIFITLX.OBS_COLLECTION) {
    await obs.call('SetCurrentSceneCollection', {
      sceneCollectionName: estado.collection,
    });
    await sleep(1500);
    console.log(`✓ Colección restaurada: "${estado.collection}"`);
  }
  await obs.call('SetVideoSettings', {
    baseWidth:      estado.video.baseWidth,
    baseHeight:     estado.video.baseHeight,
    outputWidth:    estado.video.outputWidth,
    outputHeight:   estado.video.outputHeight,
    fpsNumerator:   estado.video.fpsNumerator,
    fpsDenominator: estado.video.fpsDenominator,
  });
  console.log(`✓ Resolución restaurada: ${estado.video.baseWidth}×${estado.video.baseHeight} @${Math.round(estado.video.fpsNumerator / estado.video.fpsDenominator)}fps`);
}

async function ensureCollection() {
  try {
    await obs.call('CreateSceneCollection', {
      sceneCollectionName: WIFITLX.OBS_COLLECTION,
    });
    console.log(`✓ Colección creada: "${WIFITLX.OBS_COLLECTION}"`);
    await sleep(1500);
  } catch {
    await obs.call('SetCurrentSceneCollection', {
      sceneCollectionName: WIFITLX.OBS_COLLECTION,
    });
    console.log(`✓ Colección activa: "${WIFITLX.OBS_COLLECTION}"`);
    await sleep(1000);
  }
}

async function setResolution() {
  await obs.call('SetVideoSettings', {
    baseWidth: 1080,
    baseHeight: 1080,
    outputWidth: 1080,
    outputHeight: 1080,
    fpsNumerator: 30,
    fpsDenominator: 1,
  });
  console.log('✓ Resolución: 1080×1080 @ 30 FPS');
}

async function createScene(tmpl) {
  const fileUrl = encodeURI(
    `file:///${WIFITLX.HTML_BASE}/${tmpl.file}`
  );
  const inputName = `${tmpl.name}-browser`;

  try {
    await obs.call('CreateScene', { sceneName: tmpl.name });
  } catch {
    // ya existe → ok
  }

  try {
    await obs.call('CreateInput', {
      sceneName: tmpl.name,
      inputName,
      inputKind: 'browser_source',
      inputSettings: {
        url: fileUrl,
        width: 1080,
        height: 1080,
        fps: 30,
        shutdown: false,
        restart_when_active: true,
      },
      sceneItemEnabled: true,
    });
  } catch {
    // browser source ya existe → ok
  }

  // Forzar transform 1:1
  try {
    const { sceneItemId } = await obs.call('GetSceneItemId', {
      sceneName: tmpl.name,
      sourceName: inputName,
    });
    await obs.call('SetSceneItemTransform', {
      sceneName: tmpl.name,
      sceneItemId,
      sceneItemTransform: {
        positionX: 0,
        positionY: 0,
        scaleX: 1,
        scaleY: 1,
        boundsType: 'OBS_BOUNDS_SCALE_INNER',
        boundsWidth: 1080,
        boundsHeight: 1080,
      },
    });
  } catch {
    // transform no crítico
  }

  console.log(`  ✓ ${tmpl.name}  →  ${tmpl.file}`);
}

async function main() {
  try {
    await connect();
  } catch (err) {
    console.error('✗ Sin conexión a OBS WebSocket:', err.message);
    console.error('  OBS debe estar abierto con el servidor WebSocket activado en puerto 4455.');
    process.exit(1);
  }

  // Guardar estado antes de modificar nada
  let estadoAnterior;
  try {
    estadoAnterior = await guardarEstado();
  } catch (err) {
    console.warn('⚠ No se pudo guardar el estado:', err.message);
  }

  try {
    await ensureCollection();

    try {
      await setResolution();
    } catch (err) {
      console.warn('⚠ No se pudo ajustar resolución:', err.message);
    }

    console.log(`\nCreando ${WIFITLX.TEMPLATES.length} escenas...`);
    for (const tmpl of WIFITLX.TEMPLATES) {
      await createScene(tmpl);
    }

    console.log(`
--- Coleccion WIFI TLX lista en OBS

Siguiente paso:
  npm run grabar          <- graba los 7 templates
  npm run grabar -- 05    <- solo template 05
  npm run grabar -- 06    <- solo template 06`);

  } finally {
    // Siempre restaurar la colección y resolución originales
    if (estadoAnterior) {
      try {
        await restaurarEstado(estadoAnterior);
      } catch (err) {
        console.error('✗ No se pudo restaurar el estado:', err.message);
      }
    }
    await obs.disconnect();
    console.log('--- OBS listo para streaming\n');
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
