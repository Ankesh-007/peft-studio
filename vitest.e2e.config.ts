import { defineConfig } from 'vitest/config';
import path from 'path';

export default defineConfig({
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    include: ['src/**/*.e2e.test.ts', 'src/**/*.e2e.test.tsx'],
    exclude: [
      'node_modules/',
      'dist/',
      'build/',
      'electron/',
      'backend/',
    ],
    testTimeout: 30000, // E2E tests may take longer
    hookTimeout: 30000,
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
