import { defineConfig } from 'vitest/config';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    root: path.resolve(__dirname),
    include: ['**/*.test.js', '**/*.pbt.test.js'],
    exclude: ['node_modules/', 'dist/', 'build/'],
    testTimeout: 60000, // Property-based tests may need more time
    hookTimeout: 10000,
  },
});
