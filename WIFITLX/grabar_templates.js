/**
 * grabar_templates.js — Graba automáticamente templates WIFI TLX con OBS
 *
 * Qué hace:
 *   - Guarda el estado actual de OBS (colección + resolución de video)
 *   - Cambia a la colección WIFI TLX y ajusta 1080×1080
 *   - Graba cada template 13 segundos (12s loop + 1s buffer)
 *   - Restaura la colección y resolución originales al terminar
 *   - Guarda MP4 en 20-projects/wifi-tlx-marketing/videos/
 *
 * Uso:
 *   npm run grabar              ← todos los templates (7)
 *   node grabar_templates.js 05 ← solo el template 05
 *   node grabar_templates.js 06 ← solo el template 06
 *
 * Prerequisito: npm run setup (una sola vez)
 */
import 'dotenv/config';
import OBSWebSocket from 'obs-websocket-js';
import { WIFITLX } from './config.js';

const obs = new OBSWebSocket();
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function connect() {
  const password = process.env.OBS_WS_PASSWORD || '';
  await obs.connect(WIFITLX.OBS_WS_URL, password);
  console.log('✓ Conectado a OBS WebSocket');
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

  // 1. Volver a la colección del usuario
  if (estado.collection !== WIFITLX.OBS_COLLECTION) {
    await obs.call('SetCurrentSceneCollection', {
      sceneCollectionName: estado.collection,
    });
    await sleep(1500); // OBS necesita tiempo para cargar la colección
    console.log(`✓ Colección restaurada: "${estado.collection}"`);
  }

  // 2. Restaurar resolución original
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

async function activarColeccion() {
  await obs.call('SetCurrentSceneCollection', {
    sceneCollectionName: WIFITLX.OBS_COLLECTION,
  });
  await sleep(1500); // OBS necesita tiempo para cargar la colección
  console.log(`✓ Colección activa: "${WIFITLX.OBS_COLLECTION}"`);
}

async function configurarSalida() {
  try {
    await obs.call('SetRecordDirectory', {
      recordDirectory: WIFITLX.VIDEOS_OUT,
    });
    console.log(`✓ Salida: ${WIFITLX.VIDEOS_OUT}`);
  } catch (err) {
    console.warn('⚠ No se pudo cambiar directorio de grabación:', err.message);
  }
}

async function grabarTemplate(tmpl) {
  process.stdout.write(`\n📹 ${tmpl.name}\n   Cambiando escena...`);
  await obs.call('SetCurrentProgramScene', { sceneName: tmpl.name });
  await sleep(2000);

  process.stdout.write(' Grabando');
  await obs.call('StartRecord');

  const segundos = Math.ceil(tmpl.durMs / 1000);
  for (let i = segundos; i > 0; i--) {
    process.stdout.write(` ${i}s`);
    await sleep(1000);
  }

  const { outputPath } = await obs.call('StopRecord');
  console.log(`\n   ✓ ${outputPath}`);

  await sleep(2000);
  return outputPath;
}

async function main() {
  const filtro = process.argv[2]; // "05", "06", "07", etc.

  try {
    await connect();
  } catch (err) {
    console.error('✗ Sin conexión a OBS WebSocket:', err.message);
    process.exit(1);
  }

  // Guardar estado antes de tocar nada — se restaura al terminar
  let estadoAnterior;
  try {
    estadoAnterior = await guardarEstado();
  } catch (err) {
    console.warn('⚠ No se pudo guardar el estado:', err.message);
  }

  try {
    await activarColeccion();
    await configurarSalida();

    // Ajustar resolución WIFI TLX (puede ser diferente a la del usuario)
    await obs.call('SetVideoSettings', {
      baseWidth: 1080, baseHeight: 1080,
      outputWidth: 1080, outputHeight: 1080,
      fpsNumerator: 30, fpsDenominator: 1,
    });

    const lista = filtro
      ? WIFITLX.TEMPLATES.filter((t) => t.file.startsWith(filtro))
      : WIFITLX.TEMPLATES;

    if (lista.length === 0) {
      console.error(`✗ No hay template que empiece con "${filtro}"`);
      console.error(`  Opciones: 01 02 03 04 05 06 07`);
      await restaurarEstado(estadoAnterior);
      await obs.disconnect();
      process.exit(1);
    }

    const durTotal = lista.length * (Math.max(...lista.map((t) => t.durMs)) + 4000);
    console.log(`\n[GRABAR] ${lista.length} template(s) — ~${Math.ceil(durTotal / 1000)}s total\n`);

    const resultados = [];
    for (const tmpl of lista) {
      try {
        const outputPath = await grabarTemplate(tmpl);
        resultados.push({ ok: true, name: tmpl.name, outputPath });
      } catch (err) {
        console.error(`\n   ERROR: ${err.message}`);
        resultados.push({ ok: false, name: tmpl.name, error: err.message });
      }
    }

    const ok = resultados.filter((r) => r.ok).length;
    const fail = resultados.length - ok;

    console.log(`\n--- ${ok} grabado(s)${fail > 0 ? ` | ${fail} error(s)` : ''}`);
    console.log(`Videos en: ${WIFITLX.VIDEOS_OUT}`);

  } finally {
    // Siempre restaurar — incluso si hay un error durante la grabación
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
