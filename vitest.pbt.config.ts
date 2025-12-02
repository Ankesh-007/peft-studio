import { defineConfig } from 'vitest/config';
import path from 'path';

export default defineConfig({
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    include: ['src/**/*.pbt.test.ts', 'src/**/*.pbt.test.tsx'],
    exclude: [
      'node_modules/',
      'dist/',
      'build/',
      'electron/',
      'backend/',
    ],
    testTimeout: 60000, // Property-based tests run many iterations
    hookTimeout: 10000,
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
