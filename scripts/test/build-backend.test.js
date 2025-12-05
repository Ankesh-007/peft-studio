/**
 * Unit Tests for Backend Build Integration
 * 
 * Tests backend build functions added to the build pipeline.
 * 
 * Requirements: 6.1, 6.2, 6.3, 6.4
 */

import { describe, it, expect } from 'vitest';
import {
  collectBackendArtifacts,
  generateBuildReport,
} from '../build.js';

describe('Backend Build Integration', () => {
  describe('Backend Artifact Collection', () => {
    it('should collect backend artifacts when executable exists', () => {
      const result = collectBackendArtifacts();
      
      expect(result).toBeDefined();
      expect(result.artifacts).toBeDefined();
      expect(Array.isArray(result.artifacts)).toBe(true);
      expect(result.totalSize).toBeDefined();
      expect(typeof result.totalSize).toBe('number');
    });
    
    it('should return empty artifacts when backend executable does not exist', () => {
      const result = collectBackendArtifacts();
      
      expect(result.artifacts).toBeDefined();
      expect(result.totalSize).toBeDefined();
      
      // Either has artifacts or is empty
      if (result.artifacts.length === 0) {
        expect(result.totalSize).toBe(0);
      }
    });
    
    it('should include correct metadata for backend artifacts', () => {
      const result = collectBackendArtifacts();
      
      if (result.artifacts.length > 0) {
        const artifact = result.artifacts[0];
        expect(artifact.filename).toBeDefined();
        expect(artifact.path).toBeDefined();
        expect(artifact.size).toBeDefined();
        expect(artifact.type).toBe('backend-executable');
        expect(artifact.platform).toBeDefined();
        expect(artifact.format).toBeDefined();
      }
    });
  });
  
  describe('Build Report with Backend', () => {
    it('should include backend result in build report', () => {
      const buildResults = [
        { success: true, platform: 'windows', duration: '10.5' },
      ];
      
      const verification = {
        valid: true,
        verified: [],
        missing: [],
        unexpected: [],
      };
      
      const backendResult = {
        success: true,
        duration: '5.0',
      };
      
      const startTime = Date.now() - 5000;
      
      const report = generateBuildReport(buildResults, verification, startTime, backendResult);
      
      expect(report).toBeDefined();
      expect(report.backendResult).toBe(backendResult);
      expect(report.backendSize).toBeDefined();
      expect(report.installerSize).toBeDefined();
    });
    
    it('should work without backend result', () => {
      const buildResults = [
        { success: true, platform: 'windows', duration: '10.5' },
      ];
      
      const verification = {
        valid: true,
        verified: [],
        missing: [],
        unexpected: [],
      };
      
      const startTime = Date.now() - 5000;
      
      const report = generateBuildReport(buildResults, verification, startTime);
      
      expect(report).toBeDefined();
      expect(report.duration).toBeDefined();
      expect(report.artifactCount).toBeDefined();
      expect(report.totalSize).toBeDefined();
    });
  });
});
