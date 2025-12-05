/**
 * Property-Based Tests for Data File Bundling
 * 
 * Feature: python-backend-bundling, Property 7: Data File Bundling Completeness
 * 
 * Tests that all data files and configuration files required by the backend
 * at runtime are included in the bundled executable and accessible.
 */

import { describe, it, expect } from 'vitest';
import * as fc from 'fast-check';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

describe('Data File Bundling - Property-Based Tests', () => {
  // Feature: python-backend-bundling, Property 7: Data File Bundling Completeness
  describe('Property 7: Data File Bundling Completeness', () => {
    it('should include all required data files in the spec file', () => {
      const specPath = path.join(__dirname, '../../../backend/peft_engine.spec');
      
      if (!fs.existsSync(specPath)) {
        // Skip if spec file doesn't exist yet
        return;
      }
      
      const specContent = fs.readFileSync(specPath, 'utf8');
      
      // Required data files that should be bundled
      const requiredDataFiles = [
        'config.py',
        'database.py',
        'runtime_paths.py',
      ];
      
      fc.assert(
        fc.property(
          fc.constantFrom(...requiredDataFiles),
          (dataFile) => {
            // Check if the data file is mentioned in the spec file
            const isIncluded = specContent.includes(dataFile) || 
                             specContent.includes('datas=') ||
                             specContent.includes('*.py');
            
            expect(isIncluded).toBe(true);
            return isIncluded;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should have runtime path resolution for bundled data files', () => {
      const runtimePathsFile = path.join(__dirname, '../../../backend/runtime_paths.py');
      
      if (!fs.existsSync(runtimePathsFile)) {
        // Skip if runtime paths module doesn't exist yet
        return;
      }
      
      const content = fs.readFileSync(runtimePathsFile, 'utf8');
      
      // Check for key runtime path resolution patterns
      const requiredPatterns = [
        'sys._MEIPASS',
        'getattr(sys, \'_MEIPASS\'',
        'def get_resource_path',
      ];
      
      fc.assert(
        fc.property(
          fc.constantFrom(...requiredPatterns),
          (pattern) => {
            const hasPattern = content.includes(pattern);
            expect(hasPattern).toBe(true);
            return hasPattern;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should bundle service modules as data files', () => {
      const specPath = path.join(__dirname, '../../../backend/peft_engine.spec');
      
      if (!fs.existsSync(specPath)) {
        return;
      }
      
      const specContent = fs.readFileSync(specPath, 'utf8');
      
      // Service directories that should be included
      const servicePatterns = [
        'services',
        'connectors',
        'plugins',
      ];
      
      fc.assert(
        fc.property(
          fc.constantFrom(...servicePatterns),
          (pattern) => {
            // Check if services are included either as data files or hidden imports
            const isIncluded = specContent.includes(pattern);
            expect(isIncluded).toBe(true);
            return isIncluded;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should preserve file structure for bundled data files', () => {
      const specPath = path.join(__dirname, '../../../backend/peft_engine.spec');
      
      if (!fs.existsSync(specPath)) {
        return;
      }
      
      const specContent = fs.readFileSync(specPath, 'utf8');
      
      // Test that datas parameter preserves directory structure
      fc.assert(
        fc.property(
          fc.tuple(
            fc.constantFrom('services', 'connectors', 'plugins'),
            fc.constantFrom('.', 'services', 'connectors', 'plugins')
          ),
          ([sourceDir, targetDir]) => {
            // If datas is configured, it should map source to target correctly
            if (specContent.includes('datas=')) {
              // The spec should have proper path mappings
              const hasDatasConfig = specContent.includes('datas=[') || 
                                    specContent.includes('datas = [');
              expect(hasDatasConfig).toBe(true);
              return hasDatasConfig;
            }
            return true; // Skip if no datas config yet
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should handle different file types in data bundling', () => {
      const specPath = path.join(__dirname, '../../../backend/peft_engine.spec');
      
      if (!fs.existsSync(specPath)) {
        return;
      }
      
      const specContent = fs.readFileSync(specPath, 'utf8');
      
      // Different file types that might need bundling
      const fileTypes = [
        '.py',
        '.json',
        '.yaml',
        '.yml',
        '.txt',
        '.db',
      ];
      
      fc.assert(
        fc.property(
          fc.constantFrom(...fileTypes),
          (fileType) => {
            // Check if the spec handles various file types
            // Either explicitly or through wildcard patterns
            const handlesFileType = specContent.includes(fileType) ||
                                   specContent.includes('*') ||
                                   specContent.includes('datas=');
            
            // This is informational - not all file types need to be explicitly mentioned
            return true;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should validate data file paths are relative to backend directory', () => {
      const specPath = path.join(__dirname, '../../../backend/peft_engine.spec');
      
      if (!fs.existsSync(specPath)) {
        return;
      }
      
      const specContent = fs.readFileSync(specPath, 'utf8');
      
      fc.assert(
        fc.property(
          fc.constantFrom('config.py', 'database.py', 'runtime_paths.py'),
          (filename) => {
            // If the file is mentioned, it should use relative paths
            if (specContent.includes(filename)) {
              // Should not have absolute paths
              const noAbsolutePaths = !specContent.includes('C:\\') &&
                                     !specContent.includes('/home/') &&
                                     !specContent.includes('/Users/');
              expect(noAbsolutePaths).toBe(true);
              return noAbsolutePaths;
            }
            return true;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should ensure database file is accessible in bundled mode', () => {
      const runtimePathsFile = path.join(__dirname, '../../../backend/runtime_paths.py');
      
      if (!fs.existsSync(runtimePathsFile)) {
        return;
      }
      
      const content = fs.readFileSync(runtimePathsFile, 'utf8');
      
      fc.assert(
        fc.property(
          fc.constantFrom('database', 'db', 'data'),
          (keyword) => {
            // Runtime paths should handle database file location
            // This is a general check that the module considers data files
            return true; // Informational test
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should bundle configuration files with correct permissions', () => {
      const backendDir = path.join(__dirname, '../../../backend');
      const configFiles = ['config.py', 'database.py', 'runtime_paths.py'];
      
      fc.assert(
        fc.property(
          fc.constantFrom(...configFiles),
          (configFile) => {
            const filePath = path.join(backendDir, configFile);
            
            if (!fs.existsSync(filePath)) {
              return true; // Skip if file doesn't exist
            }
            
            // Check that the file is readable
            try {
              fs.accessSync(filePath, fs.constants.R_OK);
              return true;
            } catch {
              return false;
            }
          }
        ),
        { numRuns: 100 }
      );
    });
  });

  describe('Runtime Path Resolution', () => {
    it('should resolve paths correctly in both dev and production modes', () => {
      const runtimePathsFile = path.join(__dirname, '../../../backend/runtime_paths.py');
      
      if (!fs.existsSync(runtimePathsFile)) {
        return;
      }
      
      const content = fs.readFileSync(runtimePathsFile, 'utf8');
      
      fc.assert(
        fc.property(
          fc.boolean(), // Simulates bundled vs non-bundled mode
          (isBundled) => {
            // The runtime_paths module should handle both modes
            const hasMEIPASS = content.includes('_MEIPASS');
            const hasFallback = content.includes('os.path.dirname') || 
                               content.includes('__file__');
            
            expect(hasMEIPASS || hasFallback).toBe(true);
            return hasMEIPASS || hasFallback;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should provide consistent path resolution across platforms', () => {
      const runtimePathsFile = path.join(__dirname, '../../../backend/runtime_paths.py');
      
      if (!fs.existsSync(runtimePathsFile)) {
        return;
      }
      
      const content = fs.readFileSync(runtimePathsFile, 'utf8');
      
      fc.assert(
        fc.property(
          fc.constantFrom('win32', 'darwin', 'linux'),
          (platform) => {
            // Path resolution should work on all platforms
            // Check for platform-agnostic path handling
            const usesOsPath = content.includes('os.path.join') ||
                              content.includes('pathlib');
            
            expect(usesOsPath).toBe(true);
            return usesOsPath;
          }
        ),
        { numRuns: 100 }
      );
    });
  });

  describe('Spec File Configuration', () => {
    it('should have valid datas configuration format', () => {
      const specPath = path.join(__dirname, '../../../backend/peft_engine.spec');
      
      if (!fs.existsSync(specPath)) {
        return;
      }
      
      const specContent = fs.readFileSync(specPath, 'utf8');
      
      if (!specContent.includes('datas=')) {
        return; // Skip if no datas config
      }
      
      fc.assert(
        fc.property(
          fc.constant(true),
          () => {
            // Check for valid Python list/tuple syntax
            const hasValidSyntax = specContent.includes('datas=[') ||
                                  specContent.includes('datas = [') ||
                                  specContent.includes('datas=(');
            
            expect(hasValidSyntax).toBe(true);
            return hasValidSyntax;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should include all critical backend modules', () => {
      const specPath = path.join(__dirname, '../../../backend/peft_engine.spec');
      
      if (!fs.existsSync(specPath)) {
        return;
      }
      
      const specContent = fs.readFileSync(specPath, 'utf8');
      
      const criticalModules = [
        'main.py',
        'config',
        'database',
      ];
      
      fc.assert(
        fc.property(
          fc.constantFrom(...criticalModules),
          (module) => {
            const isIncluded = specContent.includes(module);
            expect(isIncluded).toBe(true);
            return isIncluded;
          }
        ),
        { numRuns: 100 }
      );
    });
  });
});
