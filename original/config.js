/**
 * original — Configuración del perfil
 * Un solo lugar para cambiar equipos, colores y puertos.
 */
window.SRYI = {
  HOME:        'AUTOTRANSPORTES',
  AWAY:        'LA CASCADA',
  MATCH_LABEL: 'PARTIDO',
  HOME_COLOR:  '#3b82f6',   // azul
  AWAY_COLOR:  '#ef4444',   // rojo
  ACCENT:      '#FFD700',   // gold
  WS_PORT:     8889,
  HTTP_PORT:   8888,
  WS_HOST:     null,  // null = auto-detectar desde window.location.hostname (Tailscale)
  LOGO:        './logo_sponsor.jpg',
  ALTAVOZ_LOGO: './logo_sponsor.jpg',
  SPONSOR:     'Avila Fisioterapia',
  SPONSOR_SOCIAL: 'AvilaFisioterapia',

  // Control remoto compartido (shared/control_remoto.html) — features opcionales,
  // todas apagadas en este perfil. Ver SRYiyo/config.js para un perfil con todas activas.
  ENABLE_AWAY_ROSTER: false,
  ENABLE_PENALTIES:   false,
  ENABLE_UNDO:        false,
  ENABLE_IDA_SCORE:   false,
  ENABLE_QR:          false,
  IDA_HOME: 0,
  IDA_AWAY: 0,
  WS_TOKEN: null,
  PLAYERS: [],
};
