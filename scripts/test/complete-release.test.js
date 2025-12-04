/**
 * Unit Tests for Complete Release Orchestration Script
 * 
 * Tests step sequencing, error handling and halt behavior, dry-run mode,
 * working directory verification, and summary generation.
 * 
 * Requirements: 8.1, 8.2, 8.3, 8.4
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

const {
  ORCHESTRATION_CONFIG,
  generateFinalSummary,
  extractReleaseInfo,
} = require('../complete-release');

/**
 * Helper: Create a temporary test directory
 */
function createTestDirectory() {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'release-test-'));
  return tempDir;
}

/**
 * Helper: Create a file
 */
function createFile(dirPath, filename, content = '') {
  const filePath = path.join(dirPath, filename);
  const dir = path.dirname(filePath);
  
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
  
  fs.writeFileSync(filePath, content, 'utf8');
  return filePath;
}

/**
 * Helper: Clean up test directory
 */
function cleanupTestDirectory(dirPath) {
  if (fs.existsSync(dirPath)) {
    fs.rmSync(dirPath, { recursive: true, force: true });
  }
}

describe('Complete Release Orchestration - Unit Tests', () => {
  describe('Configuration', () => {
    it('should have all required steps defined', () => {
      expect(ORCHESTRATION_CONFIG.steps).toBeDefined();
      expect(ORCHESTRATION_CONFIG.steps.length).toBeGreaterThan(0);
      
      const stepNames = ORCHESTRATION_CONFIG.steps.map(s => s.name);
      expect(stepNames).toContain('cleanup');
      expect(stepNames).toContain('validate');
      expect(stepNames).toContain('build');
      expect(stepNames).toContain('checksum');
      expect(stepNames).toContain('release');
    });
    
    it('should have steps in correct order', () => {
      const stepNames = ORCHESTRATION_CONFIG.steps.map(s => s.name);
      const expectedOrder = ['cleanup', 'validate', 'build', 'checksum', 'release'];
      
      expectedOrder.forEach((name, index) => {
        expect(stepNames[index]).toBe(name);
      });
    });
    
    it('should have command for each step', () => {
      ORCHESTRATION_CONFIG.steps.forEach(step => {
        expect(step.command).toBeDefined();
        expect(typeof step.command).toBe('string');
        expect(step.command.length).toBeGreaterThan(0);
      });
    });
  });
  
  describe('Step Configuration Validation', () => {
    it('should have required fields for each step', () => {
      ORCHESTRATION_CONFIG.steps.forEach(step => {
        expect(step.name).toBeDefined();
        expect(step.description).toBeDefined();
        expect(step.command).toBeDefined();
        expect(typeof step.required).toBe('boolean');
      });
    });
    
    it('should have unique step names', () => {
      const names = ORCHESTRATION_CONFIG.steps.map(s => s.name);
      const uniqueNames = [...new Set(names)];
      expect(names.length).toBe(uniqueNames.length);
    });
    
    it('should have valid commands', () => {
      ORCHESTRATION_CONFIG.steps.forEach(step => {
        expect(step.command).toContain('node scripts/');
      });
    });
  });
  
  describe('Release Information Extraction', () => {
    it('should extract release URL from results', () => {
      const results = [
        { step: 'cleanup', success: true },
        { step: 'release', success: true, releaseUrl: 'https://github.com/owner/repo/releases/tag/v1.0.0' },
      ];
      
      const info = extractReleaseInfo(results);
      
      expect(info).toBeDefined();
      expect(info.url).toBe('https://github.com/owner/repo/releases/tag/v1.0.0');
    });
    
    it('should extract assets from results', () => {
      const results = [
        { step: 'cleanup', success: true },
        { 
          step: 'release', 
          success: true,
          assets: [
            { filename: 'installer.exe', size: 1024000 },
            { filename: 'app.dmg', size: 2048000 },
          ],
        },
      ];
      
      const info = extractReleaseInfo(results);
      
      expect(info).toBeDefined();
      expect(info.assets).toHaveLength(2);
      expect(info.assets[0].filename).toBe('installer.exe');
    });
    
    it('should return null when release step not found', () => {
      const results = [
        { step: 'cleanup', success: true },
        { step: 'validate', success: true },
      ];
      
      const info = extractReleaseInfo(results);
      
      expect(info).toBeNull();
    });
    
    it('should return null when release step failed', () => {
      const results = [
        { step: 'cleanup', success: true },
        { step: 'release', success: false, error: 'Failed' },
      ];
      
      const info = extractReleaseInfo(results);
      
      expect(info).toBeNull();
    });
  });
  
  describe('Step Sequencing Logic', () => {
    it('should have correct step order in configuration', () => {
      const stepNames = ORCHESTRATION_CONFIG.steps.map(s => s.name);
      const expectedOrder = ['cleanup', 'validate', 'build', 'checksum', 'release'];
      
      expect(stepNames).toEqual(expectedOrder);
    });
    
    it('should mark all steps as required', () => {
      const allRequired = ORCHESTRATION_CONFIG.steps.every(s => s.required === true);
      expect(allRequired).toBe(true);
    });
    
    it('should have cleanup step with skip flag', () => {
      const cleanupStep = ORCHESTRATION_CONFIG.steps.find(s => s.name === 'cleanup');
      expect(cleanupStep.skipFlag).toBe('--skip-cleanup');
    });
  });
  
  describe('Error Handling Logic', () => {
    it('should identify failed step in summary', () => {
      const results = [
        { step: 'cleanup', success: true, duration: 1.0 },
        { step: 'validate', success: false, duration: 2.0, error: 'Validation failed' },
      ];
      
      const summary = generateFinalSummary(results, Date.now() - 3000, false);
      
      expect(summary.success).toBe(false);
      expect(summary.failedStep).toBe('validate');
    });
    
    it('should include error details in summary', () => {
      const results = [
        { step: 'cleanup', success: true, duration: 1.0 },
        { step: 'validate', success: false, duration: 2.0, error: 'Specific error message' },
      ];
      
      const summary = generateFinalSummary(results, Date.now(), false);
      
      const failedStepSummary = summary.steps.find(s => s.name === 'validate');
      expect(failedStepSummary.error).toBe('Specific error message');
    });
    
    it('should count failed steps correctly', () => {
      const results = [
        { step: 'cleanup', success: true, duration: 1.0 },
        { step: 'validate', success: false, duration: 2.0, error: 'Failed' },
        { step: 'build', success: false, duration: 3.0, error: 'Failed' },
      ];
      
      const summary = generateFinalSummary(results, Date.now(), false);
      
      expect(summary.failedSteps).toBe(2);
      expect(summary.successfulSteps).toBe(1);
    });
  });
  
  describe('Dry-Run Mode', () => {
    it('should mark summary as dry-run', () => {
      const results = [
        { step: 'cleanup', success: true, skipped: true },
        { step: 'validate', success: true, skipped: true },
      ];
      
      const summary = generateFinalSummary(results, Date.now(), true);
      
      expect(summary.dryRun).toBe(true);
    });
    
    it('should include skipped flag in step details', () => {
      const results = [
        { step: 'cleanup', success: true, skipped: true, duration: 0 },
        { step: 'validate', success: true, skipped: true, duration: 0 },
      ];
      
      const summary = generateFinalSummary(results, Date.now(), true);
      
      expect(summary.steps.every(s => s.skipped === true)).toBe(true);
    });
    
    it('should still report success in dry-run mode', () => {
      const results = [
        { step: 'cleanup', success: true, skipped: true },
        { step: 'validate', success: true, skipped: true },
        { step: 'build', success: true, skipped: true },
      ];
      
      const summary = generateFinalSummary(results, Date.now(), true);
      
      expect(summary.success).toBe(true);
      expect(summary.dryRun).toBe(true);
    });
  });
  
  describe('Summary Generation', () => {
    it('should generate complete summary for successful release', () => {
      const results = [
        { step: 'cleanup', success: true, duration: 1.5 },
        { step: 'validate', success: true, duration: 2.0 },
        { step: 'build', success: true, duration: 30.0 },
        { step: 'checksum', success: true, duration: 0.5 },
        { step: 'release', success: true, duration: 5.0 },
      ];
      
      const startTime = Date.now() - 39000; // 39 seconds ago
      const summary = generateFinalSummary(results, startTime, false);
      
      expect(summary.success).toBe(true);
      expect(summary.totalSteps).toBe(5);
      expect(summary.successfulSteps).toBe(5);
      expect(summary.failedSteps).toBe(0);
      expect(summary.totalDuration).toBeDefined();
      expect(summary.steps).toHaveLength(5);
    });
    
    it('should generate summary for failed release', () => {
      const results = [
        { step: 'cleanup', success: true, duration: 1.5 },
        { step: 'validate', success: false, duration: 2.0, error: 'Validation failed' },
      ];
      
      const summary = generateFinalSummary(results, Date.now() - 3500, false);
      
      expect(summary.success).toBe(false);
      expect(summary.totalSteps).toBe(2);
      expect(summary.successfulSteps).toBe(1);
      expect(summary.failedSteps).toBe(1);
      expect(summary.failedStep).toBe('validate');
    });
    
    it('should include step details in summary', () => {
      const results = [
        { step: 'cleanup', success: true, duration: 1.5 },
        { step: 'validate', success: true, duration: 2.0 },
      ];
      
      const summary = generateFinalSummary(results, Date.now(), false);
      
      expect(summary.steps).toHaveLength(2);
      summary.steps.forEach(step => {
        expect(step.name).toBeDefined();
        expect(step.success).toBeDefined();
        expect(step.duration).toBeDefined();
      });
    });
    
    it('should mark dry-run in summary', () => {
      const results = [
        { step: 'cleanup', success: true, skipped: true },
        { step: 'validate', success: true, skipped: true },
      ];
      
      const summary = generateFinalSummary(results, Date.now(), true);
      
      expect(summary.dryRun).toBe(true);
    });
    
    it('should calculate total duration correctly', () => {
      const results = [
        { step: 'cleanup', success: true, duration: 1.0 },
        { step: 'validate', success: true, duration: 2.0 },
        { step: 'build', success: true, duration: 30.0 },
      ];
      
      const startTime = Date.now() - 33000; // 33 seconds ago
      const summary = generateFinalSummary(results, startTime, false);
      
      expect(summary.totalDuration).toBeGreaterThanOrEqual(33);
    });
  });
  
  describe('Summary Validation', () => {
    it('should validate summary structure', () => {
      const results = [
        { step: 'cleanup', success: true, duration: 1.0 },
        { step: 'validate', success: true, duration: 2.0 },
      ];
      
      const summary = generateFinalSummary(results, Date.now(), false);
      
      expect(summary).toHaveProperty('success');
      expect(summary).toHaveProperty('dryRun');
      expect(summary).toHaveProperty('totalSteps');
      expect(summary).toHaveProperty('successfulSteps');
      expect(summary).toHaveProperty('failedSteps');
      expect(summary).toHaveProperty('totalDuration');
      expect(summary).toHaveProperty('steps');
      expect(summary).toHaveProperty('timestamp');
    });
    
    it('should include all step details', () => {
      const results = [
        { step: 'cleanup', success: true, duration: 1.0 },
        { step: 'validate', success: true, duration: 2.0 },
      ];
      
      const summary = generateFinalSummary(results, Date.now(), false);
      
      expect(summary.steps).toHaveLength(2);
      summary.steps.forEach(step => {
        expect(step).toHaveProperty('name');
        expect(step).toHaveProperty('success');
        expect(step).toHaveProperty('duration');
        expect(step).toHaveProperty('skipped');
      });
    });
  });
  
  describe('Release URL and Asset List', () => {
    it('should include release URL in summary when available', () => {
      const results = [
        { step: 'cleanup', success: true, duration: 1.0 },
        { step: 'validate', success: true, duration: 2.0 },
        { step: 'build', success: true, duration: 30.0 },
        { step: 'checksum', success: true, duration: 0.5 },
        { 
          step: 'release', 
          success: true, 
          duration: 5.0,
          releaseUrl: 'https://github.com/owner/repo/releases/tag/v1.0.0',
        },
      ];
      
      const summary = generateFinalSummary(results, Date.now(), false);
      
      expect(summary.releaseUrl).toBeDefined();
      expect(summary.releaseUrl).toContain('github.com');
    });
    
    it('should include asset list in summary when available', () => {
      const results = [
        { step: 'cleanup', success: true, duration: 1.0 },
        { step: 'validate', success: true, duration: 2.0 },
        { step: 'build', success: true, duration: 30.0 },
        { step: 'checksum', success: true, duration: 0.5 },
        { 
          step: 'release', 
          success: true, 
          duration: 5.0,
          assets: [
            { filename: 'installer.exe', size: 1024000 },
            { filename: 'app.dmg', size: 2048000 },
          ],
        },
      ];
      
      const summary = generateFinalSummary(results, Date.now(), false);
      
      expect(summary.assets).toBeDefined();
      expect(summary.assets).toHaveLength(2);
      expect(summary.assets[0].filename).toBe('installer.exe');
    });
  });
});
