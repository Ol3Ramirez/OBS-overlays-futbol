/**
 * ws-client.js -- SRYiyo WebSocket auto-reconnect
 *
 * Principios aplicados:
 *   DRY        — patron unico de reconexion compartido por todos los overlays
 *   Fail-fast  — errores de conexion son inmediatamente visibles en consola
 *   Single Responsibility — solo gestiona la conexion WS y el dispatch de comandos
 *
 * Requiere: config.js cargado antes (window.SRYI con WS_PORT)
 * Requiere: el overlay defina window.obsOverlay con sus handlers
 */
(function () {
  "use strict";

  var _delay = 1000;
  var _MAX_DELAY = 30000;

  function connect() {
    var port = (window.SRYI && window.SRYI.WS_PORT) || 8891;
    var ws;

    try {
      ws = new WebSocket("ws://localhost:" + port);
    } catch (err) {
      console.error("[ws-client] No se pudo crear WebSocket:", err);
      setTimeout(connect, _delay);
      _delay = Math.min(_delay * 1.5, _MAX_DELAY);
      return;
    }

    ws.onopen = function () {
      _delay = 1000; // reset backoff en conexion exitosa
    };

    ws.onmessage = function (e) {
      try {
        var cmd = JSON.parse(e.data);
        if (
          cmd &&
          typeof cmd.fn === "string" &&
          window.obsOverlay &&
          typeof window.obsOverlay[cmd.fn] === "function"
        ) {
          window.obsOverlay[cmd.fn].apply(null, cmd.args || []);
        }
      } catch (err) {
        console.warn("[ws-client] Mensaje invalido:", e.data, err);
      }
    };

    ws.onclose = function () {
      setTimeout(connect, _delay);
      _delay = Math.min(_delay * 1.5, _MAX_DELAY);
    };

    ws.onerror = function (err) {
      console.warn("[ws-client] Error WS (reconectando en " + _delay + "ms)");
    };
  }

  // Arrancar cuando el DOM este listo
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", connect);
  } else {
    connect();
  }
})();
