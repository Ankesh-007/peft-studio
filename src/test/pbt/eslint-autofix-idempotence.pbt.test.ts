/**
 * Property-Based Tests for ESLint Auto-Fix Idempotence
 * 
 * **Feature: ci-infrastructure-fix, Property 6: ESLint Auto-Fix Idempotence**
 * **Validates: Requirements 2.3**
 * 
 * Property: For any source file, running ESLint auto-fix multiple times should 
 * produce the same result after the first application, with no additional changes 
 * on subsequent runs.
 */

import { describe, it, expect } from 'vitest';
import * as fc from 'fast-check';
import { ESLint } from 'eslint';

describe('ESLint Auto-Fix Idempotence Property Tests', () => {
  it('Property 6: ESLint auto-fix should be idempotent', async () => {
    await fc.assert(
      fc.asyncProperty(
        // Generate TypeScript/JavaScript code with common linting issues
        fc.record({
          code: fc.oneof(
            // Code with trailing spaces
            fc.string().map(s => `const x = "${s}";  \n`),
            // Code with inconsistent quotes
            fc.string().map(s => `const y = '${s}';\n`),
            // Code with missing semicolons
            fc.string().map(s => `const z = "${s}"\n`),
            // Code with multiple issues
            fc.tuple(fc.string(), fc.string()).map(([a, b]) => 
              `const a = '${a}'  \nconst b = "${b}"\n`
            )
          ),
          filename: fc.constantFrom('test.ts', 'test.tsx', 'test.js', 'test.jsx')
        }),
        async ({ code, filename }) => {
          const eslint = new ESLint({
            fix: true,
            overrideConfigFile: true,
            baseConfig: {
              languageOptions: {
                parser: await import('@typescript-eslint/parser'),
                parserOptions: {
                  ecmaVersion: 2022,
                  sourceType: 'module',
                  ecmaFeatures: {
                    jsx: true
                  }
                }
              },
              rules: {
                'semi': ['error', 'always'],
                'quotes': ['error', 'single'],
                'no-trailing-spaces': 'error',
                'no-multiple-empty-lines': ['error', { max: 1 }]
              }
            }
          });

          // First fix
          const firstResult = await eslint.lintText(code, { filePath: filename });
          const firstFixed = firstResult[0]?.output ?? code;

          // Second fix (should be identical to first)
          const secondResult = await eslint.lintText(firstFixed, { filePath: filename });
          const secondFixed = secondResult[0]?.output ?? firstFixed;

          // Third fix (should still be identical)
          const thirdResult = await eslint.lintText(secondFixed, { filePath: filename });
          const thirdFixed = thirdResult[0]?.output ?? secondFixed;

          // Property: After first fix, subsequent fixes should not change the code
          expect(secondFixed).toBe(firstFixed);
          expect(thirdFixed).toBe(firstFixed);
          
          // Additional check: No fixable errors should remain after first fix
          const finalCheck = await eslint.lintText(firstFixed, { filePath: filename });
          const fixableErrors = finalCheck[0]?.messages.filter(m => m.fix) ?? [];
          expect(fixableErrors.length).toBe(0);
        }
      ),
      {
        numRuns: 100,
        verbose: true
      }
    );
  });

  it('Property 6.1: ESLint auto-fix idempotence with real project config', async () => {
    await fc.assert(
      fc.asyncProperty(
        // Generate code snippets that might appear in the actual project
        fc.record({
          code: fc.oneof(
            // React component with potential issues
            fc.tuple(fc.string(), fc.string()).map(([name, prop]) => 
              `export const ${name} = ({ ${prop} }) => {\n  return <div>{${prop}}</div>  \n}\n`
            ),
            // TypeScript interface with trailing spaces
            fc.string().map(name => 
              `interface ${name} {  \n  value: string  \n}  \n`
            ),
            // Import statement with quote inconsistencies
            fc.tuple(fc.string(), fc.string()).map(([mod, name]) => 
              `import { ${name} } from "${mod}"  \n`
            )
          ),
          filename: fc.constantFrom('Component.tsx', 'types.ts', 'utils.ts')
        }),
        async ({ code, filename }) => {
          // Use a minimal ESLint config similar to the project
          const eslint = new ESLint({
            fix: true,
            overrideConfigFile: true,
            baseConfig: {
              languageOptions: {
                parser: await import('@typescript-eslint/parser'),
                parserOptions: {
                  ecmaVersion: 2022,
                  sourceType: 'module',
                  ecmaFeatures: {
                    jsx: true
                  }
                }
              },
              rules: {
                'no-trailing-spaces': 'error',
                'no-multiple-empty-lines': ['error', { max: 1 }],
                'eol-last': ['error', 'always']
              }
            }
          });

          // Apply fix twice
          const firstResult = await eslint.lintText(code, { filePath: filename });
          const firstFixed = firstResult[0]?.output ?? code;

          const secondResult = await eslint.lintText(firstFixed, { filePath: filename });
          const secondFixed = secondResult[0]?.output ?? firstFixed;

          // Property: Second fix should not change anything
          expect(secondFixed).toBe(firstFixed);
        }
      ),
      {
        numRuns: 100,
        verbose: true
      }
    );
  });
});
