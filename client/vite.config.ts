import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig, type Plugin } from 'vite'
import path from 'node:path'
import fs from 'node:fs'

function hashPathResolverPlugin(): Plugin {
  return {
    name: 'hash-path-resolver',
    enforce: 'pre',
    resolveId(source, importer) {
      if (source.startsWith('.') && importer) {
        const dir = path.dirname(importer)
        const target = path.resolve(dir, source)
        const extensions = ['', '.tsx', '.ts', '.jsx', '.js', '/index.tsx', '/index.ts']
        for (const ext of extensions) {
          const candidate = target + ext
          if (fs.existsSync(candidate) && fs.statSync(candidate).isFile()) {
            return candidate
          }
        }
      }
      return null
    },
  }
}

function serveDistFallbackPlugin(): Plugin {
  return {
    name: 'serve-dist-fallback',
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        const url = req.url?.split('?')[0] || ''
        if (url.startsWith('/assets/') || url === '/' || url.startsWith('/favicon')) {
          const filePath = path.join(__dirname, 'dist', url === '/' ? 'index.html' : url)
          if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
            const ext = path.extname(filePath)
            const contentType =
              ext === '.js'
                ? 'text/javascript'
                : ext === '.css'
                ? 'text/css'
                : ext === '.html'
                ? 'text/html'
                : ext === '.svg'
                ? 'image/svg+xml'
                : 'application/octet-stream'
            res.setHeader('Content-Type', contentType)
            fs.createReadStream(filePath).pipe(res)
            return
          }
        }
        next()
      })
    },
  }
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [hashPathResolverPlugin(), serveDistFallbackPlugin(), react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  preview: {
    port: 4173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
