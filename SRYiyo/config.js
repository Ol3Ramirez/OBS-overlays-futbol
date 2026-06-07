/**
 * SRYiyo — Configuración del perfil
 * Un solo lugar para cambiar equipos, colores y puertos.
 */
window.SRYI = {
  HOME:        'PROVEEDORA ROBLES',
  AWAY:        'SAN SEBASTIÁN',
  MATCH_LABEL: 'TERCER LUGAR',
  IDA_HOME:    0,
  IDA_AWAY:    0,
  HOME_COLOR:  '#212121',   // negro — Robles
  AWAY_COLOR:  '#E91E63',   // rosa — San Sebastián
  HOME_LOGO:   '⚫',
  AWAY_LOGO:   '🩷',
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
  WS_TOKEN: '***REMOVED-TOKEN***',

  // Plantilla Proveedora Robles — VUELTA
  PLAYERS: [
    { num: 1, name: 'TOVAR',    pos: 'POR' },
    { num: 2, name: 'TOCHO',    pos: 'DEF' },
    { num: 3, name: 'PABLO',    pos: 'DEF' },
    { num: 4, name: 'MUNDO',    pos: 'DEF' },
    { num: 5, name: 'VELASCO',  pos: 'MED' },
    { num: 6, name: 'MAGALI',   pos: 'MED' },
    { num: 7, name: 'BANE',     pos: 'MED' },
    { num: 8, name: 'CHILANGO', pos: 'DEL' },
    { num: 9, name: 'POLLITO',  pos: 'DEL' },
  ],
};
