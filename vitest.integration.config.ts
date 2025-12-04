import { defineConfig } from 'vitest/config';
import path from 'path';

export default defineConfig({
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    include: [
      'src/**/*.integration.test.ts',
      'src/**/*.integration.test.tsx',
      'src/test/integration/**/*.test.ts',
      'src/test/integration/**/*.test.tsx',
      'src/test/training-flow-integration.test.tsx',
    ],
    exclude: [
      'node_modules/',
      'dist/',
      'build/',
      'electron/',
      'backend/',
      'scripts/',
      'src/test/integration/onboarding.test.tsx', // Onboarding components not yet implemented
    ],
    testTimeout: 15000, // Integration tests may need more time
    hookTimeout: 15000,
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
