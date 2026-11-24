import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

function computeGlbContentHash(): string {
  try {
    const glbPath = resolve(__dirname, 'public/models/crossroads_environment.glb');
    const buf = readFileSync(glbPath);
    return createHash('sha256').update(buf).digest('hex').slice(0, 12);
  } catch {
    return 'v7';
  }
}

const glbContentHash = computeGlbContentHash();

export default defineConfig({
  plugins: [react()],
  define: {
    __GLB_CONTENT_HASH__: JSON.stringify(glbContentHash),
  },
  assetsInclude: ['**/*.glb', '**/*.gltf', '**/*.hdr'],
  build: {
    target: 'es2020',
    sourcemap: false,
    chunkSizeWarningLimit: 1200,
    rollupOptions: {
      output: {
        manualChunks: {
          three: ['three'],
          r3f: ['@react-three/fiber', '@react-three/drei'],
        },
      },
    },
  },
});
