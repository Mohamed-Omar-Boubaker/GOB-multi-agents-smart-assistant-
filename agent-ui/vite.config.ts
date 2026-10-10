import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import basicSsl from '@vitejs/plugin-basic-ssl'

export default defineConfig({
  plugins: [
    react(),
    basicSsl()
  ],
  base: './', // ⭐ CRITIQUE pour Capacitor
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: undefined // Éviter problèmes de chunking mobile
      }
    }
  },
  server: {
    host: true,
    https: {},
    port: 5173,
    allowedHosts: true,

    // 🔥 PROXY → VERY IMPORTANT
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        ws: true,
        rewrite: (path) => path.replace(/^\/api/, '')  // ✅ Retire /api du chemin
      }
    }
  }
})
