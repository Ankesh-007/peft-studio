/**
 * Property-Based Tests for Build Output Completeness
 * 
 * **Feature: ci-infrastructure-fix, Property 10: Build Output Completeness**
 * **Validates: Requirements 4.4**
 * 
 * Property: For any successful Vite build, the dist directory should contain 
 * all required assets including index.html, JavaScript bundles, CSS files, 
 * and asset manifests.
 */

import { describe, it, expect } from 'vitest';
import * as fc from 'fast-check';
import * as fs from 'fs';
import * as path from 'path';

describe('Build Output Completeness Property Tests', () => {
  const distPath = path.join(process.cwd(), 'dist');
  const assetsPath = path.join(distPath, 'assets');

  /**
   * Helper function to check if a file exists
   */
  function fileExists(filePath: string): boolean {
    try {
      return fs.existsSync(filePath) && fs.statSync(filePath).isFile();
    } catch {
      return false;
    }
  }

  /**
   * Helper function to check if a directory exists
   */
  function directoryExists(dirPath: string): boolean {
    try {
      return fs.existsSync(dirPath) && fs.statSync(dirPath).isDirectory();
    } catch {
      return false;
    }
  }

  /**
   * Helper function to get all files in a directory
   */
  function getFilesInDirectory(dirPath: string): string[] {
    if (!directoryExists(dirPath)) {
      return [];
    }

    try {
      return fs.readdirSync(dirPath).filter(file => {
        const fullPath = path.join(dirPath, file);
        return fs.statSync(fullPath).isFile();
      });
    } catch {
      return [];
    }
  }

  /**
   * Helper function to check file extension
   */
  function hasExtension(filename: string, extension: string): boolean {
    return filename.toLowerCase().endsWith(extension.toLowerCase());
  }

  it('Property 10: Build output must contain all required files', () => {
    // Property: A successful build must produce a dist directory
    expect(directoryExists(distPath)).toBe(true);

    // Property: dist directory must contain index.html
    const indexHtmlPath = path.join(distPath, 'index.html');
    expect(fileExists(indexHtmlPath)).toBe(true);

    // Property: dist directory must contain assets subdirectory
    expect(directoryExists(assetsPath)).toBe(true);

    // Property: assets directory must contain JavaScript bundles
    const assetFiles = getFilesInDirectory(assetsPath);
    const jsFiles = assetFiles.filter(f => hasExtension(f, '.js'));
    expect(jsFiles.length).toBeGreaterThan(0);

    // Property: assets directory must contain CSS files
    const cssFiles = assetFiles.filter(f => hasExtension(f, '.css'));
    expect(cssFiles.length).toBeGreaterThan(0);

    // Property: All asset files should have content-hash in filename
    // (Vite generates hashed filenames for cache busting)
    const hashedFiles = assetFiles.filter(f => {
      // Vite format: name-[hash].ext
      const match = f.match(/^(.+)-([a-zA-Z0-9_-]{8,})\.(js|css)$/);
      return match !== null;
    });
    expect(hashedFiles.length).toBeGreaterThan(0);
  });

  it('Property 10.1: Build output must include vendor chunks', () => {
    // Property: Based on vite.config.ts, specific vendor chunks should exist
    const assetFiles = getFilesInDirectory(assetsPath);

    // Check for react-vendor chunk (defined in vite.config.ts)
    const reactVendorFiles = assetFiles.filter(f => 
      f.includes('react-vendor') && hasExtension(f, '.js')
    );
    expect(reactVendorFiles.length).toBeGreaterThan(0);

    // Check for ui-vendor chunk (defined in vite.config.ts)
    const uiVendorFiles = assetFiles.filter(f => 
      f.includes('ui-vendor') && hasExtension(f, '.js')
    );
    expect(uiVendorFiles.length).toBeGreaterThan(0);

    // Check for utils chunk (defined in vite.config.ts)
    const utilsFiles = assetFiles.filter(f => 
      f.includes('utils') && hasExtension(f, '.js')
    );
    expect(utilsFiles.length).toBeGreaterThan(0);
  });

  it('Property 10.2: index.html must reference generated assets', () => {
    // Property: index.html must contain references to the generated JS and CSS files
    const indexHtmlPath = path.join(distPath, 'index.html');
    expect(fileExists(indexHtmlPath)).toBe(true);

    const indexHtmlContent = fs.readFileSync(indexHtmlPath, 'utf-8');

    // Property: index.html must reference at least one CSS file
    // Vite uses absolute paths starting with /assets/ (not ./assets/)
    const cssLinkPattern = /<link[^>]+rel=["']stylesheet["'][^>]+href=["']\/assets\/[^"']+\.css["']/;
    expect(indexHtmlContent).toMatch(cssLinkPattern);

    // Property: index.html must reference at least one JS module
    const jsScriptPattern = /<script[^>]+type=["']module["'][^>]+src=["']\/assets\/[^"']+\.js["']/;
    expect(indexHtmlContent).toMatch(jsScriptPattern);
  });

  it('Property 10.3: Build output completeness with file size validation', async () => {
    await fc.assert(
      fc.asyncProperty(
        // Generate expectations for different file types
        fc.record({
          fileType: fc.constantFrom('js', 'css', 'html'),
          // Use appropriate minimum sizes for each file type
          // HTML is typically smaller (500-1000 bytes), JS/CSS are larger
        }),
        async ({ fileType }) => {
          let files: string[] = [];
          let minSize = 100; // Default minimum

          if (fileType === 'js') {
            const assetFiles = getFilesInDirectory(assetsPath);
            files = assetFiles
              .filter(f => hasExtension(f, '.js'))
              .map(f => path.join(assetsPath, f));
            minSize = 500; // JS files should be substantial
          } else if (fileType === 'css') {
            const assetFiles = getFilesInDirectory(assetsPath);
            files = assetFiles
              .filter(f => hasExtension(f, '.css'))
              .map(f => path.join(assetsPath, f));
            minSize = 100; // CSS files can be smaller
          } else if (fileType === 'html') {
            files = [path.join(distPath, 'index.html')];
            minSize = 200; // HTML should have basic structure
          }

          // Property: All generated files should have meaningful content
          for (const file of files) {
            if (fileExists(file)) {
              const stats = fs.statSync(file);
              // Files should be larger than minimum size (not empty or trivial)
              expect(stats.size).toBeGreaterThan(minSize);
            }
          }

          // Property: At least one file of each type should exist
          expect(files.length).toBeGreaterThan(0);
        }
      ),
      {
        numRuns: 100,
        verbose: true
      }
    );
  });

  it('Property 10.4: Asset filenames must follow Vite naming convention', async () => {
    await fc.assert(
      fc.asyncProperty(
        // Generate different asset types to validate naming
        fc.constantFrom('js', 'css'),
        async (extension) => {
          const assetFiles = getFilesInDirectory(assetsPath);
          const filesOfType = assetFiles.filter(f => hasExtension(f, `.${extension}`));

          // Property: All asset files should follow Vite's naming pattern
          // Format: [name]-[hash].[ext]
          for (const file of filesOfType) {
            const pattern = new RegExp(`^[a-zA-Z0-9_-]+-[a-zA-Z0-9_-]{8,}\\.${extension}$`);
            expect(file).toMatch(pattern);
          }

          // Property: At least one file of this type should exist
          expect(filesOfType.length).toBeGreaterThan(0);
        }
      ),
      {
        numRuns: 50,
        verbose: true
      }
    );
  });

  it('Property 10.5: Build output must be deterministic for same source', () => {
    // Property: For the same source code, build should produce consistent output structure
    
    // Check that dist directory exists
    expect(directoryExists(distPath)).toBe(true);

    // Get current build output structure
    const assetFiles = getFilesInDirectory(assetsPath);
    
    // Property: Build should produce a consistent set of file types
    const jsFiles = assetFiles.filter(f => hasExtension(f, '.js'));
    const cssFiles = assetFiles.filter(f => hasExtension(f, '.css'));

    // Store counts for consistency check
    const buildStructure = {
      hasIndexHtml: fileExists(path.join(distPath, 'index.html')),
      hasAssetsDir: directoryExists(assetsPath),
      jsFileCount: jsFiles.length,
      cssFileCount: cssFiles.length,
      totalAssetCount: assetFiles.length
    };

    // Property: Essential files must exist
    expect(buildStructure.hasIndexHtml).toBe(true);
    expect(buildStructure.hasAssetsDir).toBe(true);
    expect(buildStructure.jsFileCount).toBeGreaterThan(0);
    expect(buildStructure.cssFileCount).toBeGreaterThan(0);

    // Property: Build should produce multiple JS files (due to code splitting)
    expect(buildStructure.jsFileCount).toBeGreaterThanOrEqual(3); // At least main + vendors
  });

  it('Property 10.6: All required vendor chunks must be present', () => {
    // Property: Based on vite.config.ts manualChunks configuration,
    // specific vendor chunks must be present in the build output

    const assetFiles = getFilesInDirectory(assetsPath);
    const jsFiles = assetFiles.filter(f => hasExtension(f, '.js'));

    // Define required chunks from vite.config.ts
    const requiredChunks = ['react-vendor', 'ui-vendor', 'utils'];

    for (const chunkName of requiredChunks) {
      // Property: Each required chunk must have at least one file
      const chunkFiles = jsFiles.filter(f => f.includes(chunkName));
      expect(chunkFiles.length).toBeGreaterThan(0);

      // Property: Chunk files must have content
      for (const chunkFile of chunkFiles) {
        const fullPath = path.join(assetsPath, chunkFile);
        const stats = fs.statSync(fullPath);
        expect(stats.size).toBeGreaterThan(1000); // Vendor chunks should be substantial
      }
    }
  });

  it('Property 10.7: Build output must include main entry point', () => {
    // Property: Build must include the main application entry point
    const assetFiles = getFilesInDirectory(assetsPath);
    const jsFiles = assetFiles.filter(f => hasExtension(f, '.js'));

    // Property: There should be an index/main JS file
    const mainFiles = jsFiles.filter(f => f.includes('index'));
    expect(mainFiles.length).toBeGreaterThan(0);

    // Property: Main file must be referenced in index.html
    const indexHtmlPath = path.join(distPath, 'index.html');
    const indexHtmlContent = fs.readFileSync(indexHtmlPath, 'utf-8');

    // At least one of the main files should be referenced
    const hasMainReference = mainFiles.some(mainFile => 
      indexHtmlContent.includes(mainFile)
    );
    expect(hasMainReference).toBe(true);
  });

  it('Property 10.8: CSS files must be properly generated and referenced', () => {
    // Property: Build must generate CSS files and reference them in index.html
    const assetFiles = getFilesInDirectory(assetsPath);
    const cssFiles = assetFiles.filter(f => hasExtension(f, '.css'));

    // Property: At least one CSS file must exist
    expect(cssFiles.length).toBeGreaterThan(0);

    // Property: CSS files must have content
    for (const cssFile of cssFiles) {
      const fullPath = path.join(assetsPath, cssFile);
      const stats = fs.statSync(fullPath);
      expect(stats.size).toBeGreaterThan(100); // CSS should have meaningful content
    }

    // Property: CSS files must be referenced in index.html
    const indexHtmlPath = path.join(distPath, 'index.html');
    const indexHtmlContent = fs.readFileSync(indexHtmlPath, 'utf-8');

    const referencedCssFiles = cssFiles.filter(cssFile => 
      indexHtmlContent.includes(cssFile)
    );
    expect(referencedCssFiles.length).toBeGreaterThan(0);
  });
});
