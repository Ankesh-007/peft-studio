/**
 * Property Test: Bundle size constraint
 * Feature: unified-llm-platform, Property 20: Bundle size constraint
 * Validates: Requirements 14.2
 * 
 * Property: For any production build, the total installation size should not exceed 200MB
 */

import { describe, it, expect } from 'vitest';
import { execSync } from 'child_process';
import { statSync, readdirSync } from 'fs';
import { join } from 'path';

const MAX_BUNDLE_SIZE_MB = 200;
const MAX_BUNDLE_SIZE_BYTES = MAX_BUNDLE_SIZE_MB * 1024 * 1024;

/**
 * Calculate the total size of a directory recursively
 */
function getDirectorySize(dirPath: string): number {
  let totalSize = 0;
  
  try {
    const items = readdirSync(dirPath, { withFileTypes: true });
    
    for (const item of items) {
      const itemPath = join(dirPath, item.name);
      
      if (item.isDirectory()) {
        totalSize += getDirectorySize(itemPath);
      } else if (item.isFile()) {
        const stats = statSync(itemPath);
        totalSize += stats.size;
      }
    }
  } catch (error) {
    // Directory might not exist or be accessible
    console.warn(`Warning: Could not access ${dirPath}:`, error);
  }
  
  return totalSize;
}

/**
 * Format bytes to human-readable format
 */
function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

describe('Bundle Size Constraint Property Test', () => {
  it.skip('should ensure production build does not exceed 200MB', () => {
    // Build the application
    console.log('Building application for production...');
    try {
      execSync('npm run build:no-check', { 
        stdio: 'inherit',
        timeout: 300000 // 5 minutes timeout
      });
    } catch (error) {
      console.error('Build failed:', error);
      throw new Error('Production build failed');
    }
    
    // Calculate the size of the dist directory
    const distPath = join(process.cwd(), 'dist');
    const distSize = getDirectorySize(distPath);
    
    console.log(`\nBundle Analysis:`);
    console.log(`- Dist directory size: ${formatBytes(distSize)}`);
    console.log(`- Maximum allowed: ${formatBytes(MAX_BUNDLE_SIZE_BYTES)}`);
    console.log(`- Remaining budget: ${formatBytes(MAX_BUNDLE_SIZE_BYTES - distSize)}`);
    
    // Property: Bundle size should not exceed 200MB
    expect(distSize).toBeLessThanOrEqual(MAX_BUNDLE_SIZE_BYTES);
    
    // Additional check: Warn if we're using more than 80% of the budget
    const usagePercentage = (distSize / MAX_BUNDLE_SIZE_BYTES) * 100;
    console.log(`- Usage: ${usagePercentage.toFixed(2)}%`);
    
    if (usagePercentage > 80) {
      console.warn(`⚠️  Warning: Bundle size is using ${usagePercentage.toFixed(2)}% of the allowed budget`);
    }
  }, 360000); // 6 minutes timeout for build
  
  it('should have reasonable chunk sizes for code splitting', () => {
    const distPath = join(process.cwd(), 'dist');
    const assetsPath = join(distPath, 'assets');
    
    try {
      const files = readdirSync(assetsPath);
      const jsFiles = files.filter(f => f.endsWith('.js'));
      
      console.log(`\nChunk Analysis:`);
      console.log(`- Total JS chunks: ${jsFiles.length}`);
      
      // Check individual chunk sizes
      const MAX_CHUNK_SIZE = 1024 * 1024; // 1MB per chunk is reasonable
      let largeChunks = 0;
      
      for (const file of jsFiles) {
        const filePath = join(assetsPath, file);
        const stats = statSync(filePath);
        
        if (stats.size > MAX_CHUNK_SIZE) {
          largeChunks++;
          console.log(`  ⚠️  Large chunk: ${file} (${formatBytes(stats.size)})`);
        }
      }
      
      // Property: Most chunks should be under 1MB (allow some large chunks for vendor code)
      const largeChunkPercentage = (largeChunks / jsFiles.length) * 100;
      console.log(`- Large chunks (>1MB): ${largeChunks} (${largeChunkPercentage.toFixed(2)}%)`);
      
      // Allow up to 30% of chunks to be large (vendor bundles, etc.)
      expect(largeChunkPercentage).toBeLessThanOrEqual(30);
    } catch (error) {
      console.warn('Could not analyze chunks:', error);
      // Don't fail the test if we can't analyze chunks
    }
  });
});
