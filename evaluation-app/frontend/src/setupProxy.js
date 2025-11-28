const { createProxyMiddleware } = require("http-proxy-middleware");

module.exports = function (app) {
  // Proxy API requests
  app.use(
    "/api",
    createProxyMiddleware({
      target: "http://localhost:8000",
      changeOrigin: true,
      timeout: 300000, // 5 minutes timeout for file uploads
      proxyTimeout: 300000,
    }),
  );

  // Proxy WebSocket connections
  app.use(
    "/ws",
    createProxyMiddleware({
      target: "http://localhost:8000",
      ws: true, // Enable WebSocket proxying
      changeOrigin: true,
      logLevel: "debug", // Add logging to help debug
    }),
  );
};
