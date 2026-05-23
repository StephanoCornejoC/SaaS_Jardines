import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Permite overridear el puerto del backend (por defecto 8000) sin tocar
// este archivo. Útil cuando 8000 está ocupado por otro proyecto local.
const backendPort = process.env.BACKEND_PORT || "8000";
const backendTarget = `http://localhost:${backendPort}`;

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      // changeOrigin debe ser FALSE para preservar el Host original
      // (ej. "garabato.localhost:3001"). Si lo seteamos true, Vite lo
      // reescribe al target ("localhost:8001"), django-tenants resuelve
      // al schema PUBLIC y /api/v1/auth/ devuelve 404 porque ese endpoint
      // solo existe en el urlconf de los tenants.
      "/api": {
        target: backendTarget,
        changeOrigin: false,
      },
      "/media": {
        target: backendTarget,
        changeOrigin: false,
      },
    },
  },
  build: {
    outDir: "dist",
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ["react", "react-dom", "react-router-dom"],
          antd: ["antd", "@ant-design/icons"],
          charts: ["chart.js", "react-chartjs-2"],
        },
      },
    },
  },
});
