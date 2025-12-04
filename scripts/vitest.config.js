const { defineConfig } = require('vitest/config');
const path = require('path');

module.exports = defineConfig({
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
