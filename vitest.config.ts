import { defineConfig } from 'vitest/config';
import path from 'path';

export default defineConfig({
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'lcov'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.test.ts',
        '**/*.test.tsx',
        '**/*.spec.ts',
        '**/*.spec.tsx',
        'dist/',
        'build/',
        'electron/',
        'backend/',
        '*.config.ts',
        '*.config.js',
      ],
      thresholds: {
        lines: 70,
        functions: 70,
        branches: 70,
        statements: 70,
      },
    },
    include: ['src/**/*.test.ts', 'src/**/*.test.tsx'],
    exclude: [
      'node_modules/',
      'dist/',
      'build/',
      'electron/',
      'backend/',
      '**/*.e2e.test.ts',
      '**/*.e2e.test.tsx',
      '**/*.integration.test.ts',
      '**/*.integration.test.tsx',
      '**/*.pbt.test.ts',
      '**/*.pbt.test.tsx',
    ],
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
