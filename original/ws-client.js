/**
 * ws-client.js -- original WebSocket auto-reconnect
 *
 * DRY: patron unico compartido por todos los overlays
 * Requiere: config.js cargado antes (window.SRYI con WS_PORT)
 * Requiere: el overlay defina window.obsOverlay con sus handlers
 */
(function () {
  "use strict";

  var _delay = 1000;
  var _MAX_DELAY = 30000;
  var _retries = 0;

  function _safeArgs(args) {
    if (!Array.isArray(args)) return [];
    return args.map(function (a) {
      if (a === null || typeof a === "string" || typeof a === "number" || typeof a === "boolean") return a;
      if (typeof a === "object") return JSON.stringify(a);
      return "";
    });
  }

  function connect() {
    var port = (window.SRYI && window.SRYI.WS_PORT) || 8889;
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
      _delay = 1000;
      _retries = 0;
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
          window.obsOverlay[cmd.fn].apply(null, _safeArgs(cmd.args));
        }
      } catch (err) {
        console.warn("[ws-client] Mensaje invalido:", e.data, err);
      }
    };

    ws.onclose = function () {
      _retries++;
      if (_retries % 5 === 0) {
        console.warn("[ws-client] " + _retries + " intentos de reconexion. Verifica que ws_relay.py este corriendo.");
      }
      setTimeout(connect, _delay);
      _delay = Math.min(_delay * 1.5, _MAX_DELAY);
    };

    ws.onerror = function () {
      console.warn("[ws-client] Error WS (reconectando en " + _delay + "ms, intento " + (_retries + 1) + ")");
    };
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", connect);
  } else {
    connect();
  }
})();
