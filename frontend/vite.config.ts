import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// Frontend do ARIS — React + Tailwind v4. Conecta ao backend por WebSocket
// (ws://127.0.0.1:8000/ws), então não precisa de proxy HTTP.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: { port: 5173 },
});
