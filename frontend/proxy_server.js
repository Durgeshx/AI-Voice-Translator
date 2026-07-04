/**
 * Reverse proxy — forwards :3000 traffic to Streamlit (:8501).
 * Handles HTTP + WebSocket so Streamlit's live reload works.
 * Kept intentionally tiny — Streamlit itself is supervised separately.
 */
const http = require("http");
const httpProxy = require("http-proxy");

const TARGET = process.env.STREAMLIT_TARGET || "http://127.0.0.1:8501";
const PORT = parseInt(process.env.PORT || "3000", 10);
const HOST = process.env.HOST || "0.0.0.0";

const proxy = httpProxy.createProxyServer({
  target: TARGET,
  ws: true,
  changeOrigin: true,
  xfwd: true,
});

proxy.on("error", (err, req, res) => {
  // eslint-disable-next-line no-console
  console.error("[proxy-error]", err.message);
  if (res && !res.headersSent) {
    res.writeHead(502, { "Content-Type": "text/html; charset=utf-8" });
    res.end(
      `<!doctype html><meta charset=utf-8><title>Streamlit warming up…</title>
       <body style="background:#050510;color:#F1F5F9;font-family:sans-serif;padding:60px;">
       <h1 style="background:linear-gradient(135deg,#B026FF,#00E5FF);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">AI Voice Translator</h1>
       <p style="color:#94A3B8;">Streamlit backend not reachable at ${TARGET}. Auto-retrying in 2s…</p>
       <script>setTimeout(()=>location.reload(),2000)</script>
       </body>`
    );
  }
});

const server = http.createServer((req, res) => {
  proxy.web(req, res);
});

server.on("upgrade", (req, socket, head) => {
  proxy.ws(req, socket, head);
});

server.listen(PORT, HOST, () => {
  // eslint-disable-next-line no-console
  console.log(`[proxy] listening on ${HOST}:${PORT} → ${TARGET}`);
});
