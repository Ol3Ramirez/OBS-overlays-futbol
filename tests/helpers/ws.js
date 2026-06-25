// Envia un comando { fn, args } al relay WS desde el contexto del navegador.
// Usa el WebSocket de la pagina (siempre disponible, sin depender de Node) para
// ejercer el camino real: comando -> ws_relay -> broadcast -> overlay.
async function sendCmd(page, wsPort, fn, ...args) {
  await page.evaluate(
    ({ wsPort, fn, args }) =>
      new Promise((resolve, reject) => {
        const ws = new WebSocket(`ws://localhost:${wsPort}`);
        ws.onopen = () => {
          ws.send(JSON.stringify({ fn, args }));
          // pequeño margen para que el relay haga broadcast antes de cerrar
          setTimeout(() => {
            ws.close();
            resolve();
          }, 150);
        };
        ws.onerror = () => reject(new Error(`No se pudo conectar a ws://localhost:${wsPort}`));
      }),
    { wsPort, fn, args },
  );
}

module.exports = { sendCmd };
