/**
 * SRYiyo — Configuración del perfil
 * Un solo lugar para cambiar equipos, colores y puertos.
 */
window.SRYI = {
  HOME:        'MOTO EQUIPOS RODRIGUEZ',
  AWAY:        'HERMANOS OSORIO',
  MATCH_LABEL: 'PARTIDO',
  IDA_HOME:    0,
  IDA_AWAY:    0,
  HOME_COLOR:  '#C62828',   // rojo — Moto Equipos Rodriguez
  AWAY_COLOR:  '#FFFFFF',   // blanco — Hermanos Rodriguez
  HOME_LOGO:   'MER',
  AWAY_LOGO:   'HR',
  ACCENT:      '#FFD700',   // gold
  WS_PORT:     8891,
  HTTP_PORT:   8890,
  WS_URL:      'ws://localhost:8891',
  LOGO:           './logo_robles.jpeg',
  ALTAVOZ_LOGO:   './logo_altavoz_studio.png',
  ALTAVOZ_FB:     'https://www.facebook.com/profile.php?id=61575665086642',
  HOST_FB:        'https://www.facebook.com/profile.php?id=61581762022193',
  SPORT:          'FÚTBOL 5',
  SPONSOR:        'Altavoz Studio',
  SPONSOR_SOCIAL: 'AltavozEstudio',
  // Control remoto desde cancha (Tailscale)
  // null = auto-detectar desde window.location.hostname
  WS_HOST:  null,
  // El token real NUNCA va aqui (este archivo se commitea).
  // Va en config.local.js (gitignoreado, control_remoto.html lo carga despues de este archivo).
  // Ver config.local.js.example.
  WS_TOKEN: null,

  // Plantilla Moto Equipos Rodriguez — agregar desde control remoto
  PLAYERS: [],

  // Control remoto compartido (shared/control_remoto.html) — features que
  // este perfil usa (roster visitante, penales, undo+historial, QR, marcador IDA).
  ENABLE_AWAY_ROSTER: true,
  ENABLE_PENALTIES:   true,
  ENABLE_UNDO:        true,
  ENABLE_IDA_SCORE:   true,
  ENABLE_QR:          true,
};
