/**
 * SRYiyo — Configuración del perfil
 * Un solo lugar para cambiar equipos, colores y puertos.
 */
window.SRYI = {
  HOME:        'PROVEEDORA ROBLES',
  AWAY:        'HERMANOS OSORIO',
  MATCH_LABEL: 'SEMIFINAL DE IDA',
  HOME_COLOR:  '#c0392b',   // rojo Robles
  AWAY_COLOR:  '#1a5276',   // azul marino Osorio
  ACCENT:      '#FFD700',   // gold
  WS_PORT:     8891,
  HTTP_PORT:   8890,
  WS_URL:      'ws://localhost:8891',
  LOGO:        './logo_robles.jpeg',
  SPONSOR:        'Robles Fútbol',
  SPONSOR_SOCIAL: 'RoblesUtbol',
  // Control remoto desde cancha (Tailscale)
  // null = auto-detectar desde window.location.hostname
  WS_HOST:  null,
  WS_TOKEN: 'robles2025',
};
