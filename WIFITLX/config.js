import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

// wifi-tlx-marketing es un repo hermano bajo 20-projects/. Se resuelve relativo a ESTE
// archivo para funcionar igual en Mac (/Users/…), Windows (A:\OLE\…) o cualquier ruta,
// sin paths absolutos quemados. Normalizado a '/' para servir tanto en file:/// (setup_obs)
// como en el sistema de archivos. Override explícito: variable de entorno WIFITLX_MARKETING_DIR.
const MARKETING_DIR = (
  process.env.WIFITLX_MARKETING_DIR ||
  resolve(dirname(fileURLToPath(import.meta.url)), '..', '..', 'wifi-tlx-marketing')
).replace(/\\/g, '/');

export const WIFITLX = {
  PHONE:      '951 367 6266',
  SPEED:      '7 Mbps',
  PRICE:      '$300/mes',
  LOCATION:   'Tlaxiaco, Oaxaca',
  FB_PAGE_ID: '1721540274827982',

  COLORS: {
    BG:   '#050D1A',
    BLUE: '#0A6FD4',
    CYAN: '#00C8FF',
    TEXT: '#F0F8FF',
  },

  OBS_WS_URL:    'ws://localhost:4455',
  OBS_COLLECTION: 'WIFI TLX Mundial 2026',

  HTML_BASE:  `${MARKETING_DIR}/html`,
  VIDEOS_OUT: `${MARKETING_DIR}/videos`,

  TEMPLATES: [
    { name: 'WIFITLX-05-Mundial-Promo',    file: '05-mundial-promo.html',     durMs: 13000 },
    { name: 'WIFITLX-06-Mexico-Juega',      file: '06-mexico-juega.html',      durMs: 13000 },
    { name: 'WIFITLX-07-Streaming-Compare', file: '07-streaming-compare.html', durMs: 13000 },
    { name: 'WIFITLX-01-Promo-Basica',      file: '01-promo-basica.html',      durMs: 13000 },
    { name: 'WIFITLX-02-Nueva-Cobertura',   file: '02-nueva-cobertura.html',   durMs: 13000 },
    { name: 'WIFITLX-03-Velocidad',         file: '03-velocidad.html',         durMs: 13000 },
    { name: 'WIFITLX-04-Conecta-Tlaxcala',  file: '04-conecta-tlaxcala.html',  durMs: 13000 },
  ],
};
