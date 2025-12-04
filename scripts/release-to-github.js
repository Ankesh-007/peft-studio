#!/usr/bin/env node

/**
 * GitHub Release Manager
 * 
 * Creates GitHub releases with automated asset uploads, release notes extraction,
 * and comprehensive verification.
 * 
 * Usage:
 *   node scripts/release-to-github.js [options]
 * 
 * Environment Variables:
 *   GITHUB_TOKEN - GitHub personal access token (required)
 *   GITHUB_REPOSITORY - Repository in format owner/repo (optional, reads from package.json)
 */

const fs = require('fs');
const path = require('path');
const https = require('https');
const { execSync } = require('child_process');

/**
 * Configuration for GitHub release
 */
const RELEASE_CONFIG = {
  maxRetries: 3,
  retryDelay: 2000, // milliseconds
  changelogFile: 'CHANGELOG.md',
  packageFile: 'package.json',
  releaseDir: 'release',
};

/**
 * Extract release notes from CHANGELOG.md for a specific version
 * @param {string} version - Version to extract notes for (e.g., "1.0.1")
 * @param {string} changelogPath - Path to CHANGELOG.md
 * @returns {string} - Extracted release notes
 */
function extractReleaseNotes(version, changelogPath = RELEASE_CONFIG.changelogFile) {
  if (!fs.existsSync(changelogPath)) {
    throw new Error(`CHANGELOG.md not found at ${changelogPath}`);
  }
  
  const content = fs.readFileSync(changelogPath, 'utf8');
  const lines = content.split('\n');
  
  // Find the version header
  const versionPattern = new RegExp(`^##\\s+\\[${version}\\]`, 'i');
  let startIndex = -1;
  
  for (let i = 0; i < lines.length; i++) {
    if (versionPattern.test(lines[i])) {
      startIndex = i;
      break;
    }
  }
  
  if (startIndex === -1) {
    throw new Error(`Version ${version} not found in CHANGELOG.md`);
  }
  
  // Extract content until next version header or end of file
  const releaseLines = [];
  for (let i = startIndex + 1; i < lines.length; i++) {
    // Stop at next version header
    if (/^##\s+\[/.test(lines[i])) {
      break;
    }
    releaseLines.push(lines[i]);
  }
  
  // Clean up and return
  const notes = releaseLines.join('\n').trim();
  
  if (!notes) {
    throw new Error(`No release notes found for version ${version}`);
  }
  
  return notes;
}

/**
 * Get repository information from package.json
 * @param {string} packagePath - Path to package.json
 * @returns {{owner: string, repo: string, url: string}} - Repository information
 */
function getRepositoryInfo(packagePath = RELEASE_CONFIG.packageFile) {
  if (!fs.existsSync(packagePath)) {
    throw new Error(`package.json not found at ${packagePath}`);
  }
  
  const pkg = JSON.parse(fs.readFileSync(packagePath, 'utf8'));
  
  // Check environment variable first
  if (process.env.GITHUB_REPOSITORY) {
    const [owner, repo] = process.env.GITHUB_REPOSITORY.split('/');
    return {
      owner,
      repo,
      url: `https://github.com/${owner}/${repo}`,
    };
  }
  
  // Parse from package.json
  if (!pkg.repository) {
    throw new Error('No repository field in package.json and GITHUB_REPOSITORY not set');
  }
  
  let repoUrl = typeof pkg.repository === 'string' ? pkg.repository : pkg.repository.url;
  
  // Handle git+https:// format
  repoUrl = repoUrl.replace(/^git\+/, '').replace(/\.git$/, '');
  
  // Extract owner and repo from URL
  const match = repoUrl.match(/github\.com[/:]([\w-]+)\/([\w-]+)/);
  if (!match) {
    throw new Error(`Could not parse repository URL: ${repoUrl}`);
  }
  
  return {
    owner: match[1],
    repo: match[2],
    url: `https://github.com/${match[1]}/${match[2]}`,
  };
}

/**
 * Get version from package.json
 * @param {string} packagePath - Path to package.json
 * @returns {string} - Version string
 */
function getVersion(packagePath = RELEASE_CONFIG.packageFile) {
  if (!fs.existsSync(packagePath)) {
    throw new Error(`package.json not found at ${packagePath}`);
  }
  
  const pkg = JSON.parse(fs.readFileSync(packagePath, 'utf8'));
  
  if (!pkg.version) {
    throw new Error('No version field in package.json');
  }
  
  return pkg.version;
}

/**
 * Create or verify git tag
 * @param {string} version - Version to tag
 * @param {boolean} push - Whether to push the tag
 * @returns {{created: boolean, pushed: boolean}} - Tag operation results
 */
function createGitTag(version, push = true) {
  const tag = `v${version}`;
  
  try {
    // Check if tag already exists
    const existingTags = execSync('git tag', { encoding: 'utf8' });
    const tagExists = existingTags.split('\n').includes(tag);
    
    if (tagExists) {
      console.log(`   Tag ${tag} already exists`);
      return { created: false, pushed: false };
    }
    
    // Create annotated tag
    execSync(`git tag -a ${tag} -m "Release ${tag}"`, { stdio: 'inherit' });
    console.log(`   ✓ Created tag ${tag}`);
    
    if (push) {
      // Push tag to origin
      execSync(`git push origin ${tag}`, { stdio: 'inherit' });
      console.log(`   ✓ Pushed tag ${tag} to origin`);
      return { created: true, pushed: true };
    }
    
    return { created: true, pushed: false };
  } catch (error) {
    throw new Error(`Failed to create/push git tag: ${error.message}`);
  }
}

/**
 * Make an HTTPS request with retry logic
 * @param {object} options - HTTPS request options
 * @param {string|Buffer} data - Request body data
 * @param {number} retries - Number of retries remaining
 * @returns {Promise<object>} - Response data
 */
function makeRequest(options, data = null, retries = RELEASE_CONFIG.maxRetries) {
  return new Promise((resolve, reject) => {
    const req = https.request(options, (res) => {
      let responseData = '';
      
      res.on('data', (chunk) => {
        responseData += chunk;
      });
      
      res.on('end', () => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          try {
            const parsed = JSON.parse(responseData);
            resolve(parsed);
          } catch (e) {
            resolve(responseData);
          }
        } else if (retries > 0 && res.statusCode >= 500) {
          // Retry on server errors
          console.log(`   ⚠️  Request failed with status ${res.statusCode}, retrying... (${retries} retries left)`);
          setTimeout(() => {
            makeRequest(options, data, retries - 1)
              .then(resolve)
              .catch(reject);
          }, RELEASE_CONFIG.retryDelay);
        } else {
          reject(new Error(`Request failed with status ${res.statusCode}: ${responseData}`));
        }
      });
    });
    
    req.on('error', (error) => {
      if (retries > 0) {
        console.log(`   ⚠️  Request error: ${error.message}, retrying... (${retries} retries left)`);
        setTimeout(() => {
          makeRequest(options, data, retries - 1)
            .then(resolve)
            .catch(reject);
        }, RELEASE_CONFIG.retryDelay);
      } else {
        reject(error);
      }
    });
    
    if (data) {
      req.write(data);
    }
    
    req.end();
  });
}

/**
 * Create a GitHub release
 * @param {object} releaseData - Release data
 * @returns {Promise<object>} - Created release data
 */
async function createRelease(releaseData) {
  const { owner, repo, tag, name, body, draft = false, prerelease = false } = releaseData;
  const token = process.env.GITHUB_TOKEN;
  
  if (!token) {
    throw new Error('GITHUB_TOKEN environment variable not set');
  }
  
  const requestData = JSON.stringify({
    tag_name: tag,
    name: name,
    body: body,
    draft: draft,
    prerelease: prerelease,
  });
  
  const options = {
    hostname: 'api.github.com',
    path: `/repos/${owner}/${repo}/releases`,
    method: 'POST',
    headers: {
      'User-Agent': 'PEFT-Studio-Release-Script',
      'Authorization': `token ${token}`,
      'Content-Type': 'application/json',
      'Content-Length': Buffer.byteLength(requestData),
    },
  };
  
  return makeRequest(options, requestData);
}

/**
 * Upload an asset to a GitHub release
 * @param {object} uploadData - Upload data
 * @returns {Promise<object>} - Uploaded asset data
 */
async function uploadAsset(uploadData) {
  const { uploadUrl, filePath, name, contentType } = uploadData;
  const token = process.env.GITHUB_TOKEN;
  
  if (!token) {
    throw new Error('GITHUB_TOKEN environment variable not set');
  }
  
  // Read file
  const fileData = fs.readFileSync(filePath);
  
  // Parse upload URL (remove {?name,label} template)
  const cleanUrl = uploadUrl.replace(/\{[^}]+\}/, '');
  const url = new URL(`${cleanUrl}?name=${encodeURIComponent(name)}`);
  
  const options = {
    hostname: url.hostname,
    path: url.pathname + url.search,
    method: 'POST',
    headers: {
      'User-Agent': 'PEFT-Studio-Release-Script',
      'Authorization': `token ${token}`,
      'Content-Type': contentType || 'application/octet-stream',
      'Content-Length': fileData.length,
    },
  };
  
  return makeRequest(options, fileData);
}

/**
 * Verify uploaded assets
 * @param {object} release - Release data with assets
 * @param {Array<string>} expectedFiles - Expected file names
 * @returns {{valid: boolean, uploaded: Array<string>, missing: Array<string>}} - Verification result
 */
function verifyUploadedAssets(release, expectedFiles) {
  const uploadedNames = release.assets.map(asset => asset.name);
  const missing = expectedFiles.filter(file => !uploadedNames.includes(file));
  
  return {
    valid: missing.length === 0,
    uploaded: uploadedNames,
    missing: missing,
  };
}

/**
 * Collect release artifacts
 * @param {string} releaseDir - Release directory path
 * @returns {Array<{filename: string, path: string, size: number}>} - Array of artifacts
 */
function collectReleaseArtifacts(releaseDir = RELEASE_CONFIG.releaseDir) {
  if (!fs.existsSync(releaseDir)) {
    throw new Error(`Release directory not found: ${releaseDir}`);
  }
  
  const files = fs.readdirSync(releaseDir);
  const artifacts = [];
  
  // Include installer files and checksums
  const includePatterns = [
    /\.exe$/,
    /\.dmg$/,
    /\.zip$/,
    /\.AppImage$/,
    /\.deb$/,
    /SHA256SUMS\.txt$/,
  ];
  
  // Exclude certain files
  const excludePatterns = [
    /\.blockmap$/,
    /builder-/,
    /latest\.yml$/,
  ];
  
  for (const file of files) {
    const filePath = path.join(releaseDir, file);
    const stats = fs.statSync(filePath);
    
    // Only process files
    if (!stats.isFile()) {
      continue;
    }
    
    // Check if file should be included
    const shouldInclude = includePatterns.some(pattern => pattern.test(file));
    const shouldExclude = excludePatterns.some(pattern => pattern.test(file));
    
    if (shouldInclude && !shouldExclude) {
      artifacts.push({
        filename: file,
        path: filePath,
        size: stats.size,
      });
    }
  }
  
  return artifacts;
}

/**
 * Generate release summary
 * @param {object} release - Release data
 * @param {Array<object>} artifacts - Uploaded artifacts
 * @returns {string} - Formatted summary
 */
function generateReleaseSummary(release, artifacts) {
  const lines = [];
  
  lines.push('');
  lines.push('='.repeat(60));
  lines.push('GitHub Release Summary');
  lines.push('='.repeat(60));
  lines.push('');
  lines.push(`Release: ${release.name}`);
  lines.push(`Tag: ${release.tag_name}`);
  lines.push(`URL: ${release.html_url}`);
  lines.push('');
  lines.push(`Assets (${artifacts.length}):`);
  
  for (const artifact of artifacts) {
    const sizeMB = (artifact.size / (1024 * 1024)).toFixed(2);
    lines.push(`  - ${artifact.filename} (${sizeMB} MB)`);
  }
  
  lines.push('');
  lines.push('='.repeat(60));
  lines.push('');
  
  return lines.join('\n');
}

/**
 * Main release function
 * @param {object} options - Release options
 * @returns {Promise<object>} - Release result
 */
async function performRelease(options = {}) {
  const {
    dryRun = false,
    draft = false,
    prerelease = false,
    skipTag = false,
  } = options;
  
  console.log('🚀 GitHub Release Manager');
  console.log('');
  
  try {
    // Step 1: Get version and repository info
    console.log('[1/6] Getting version and repository information...');
    const version = getVersion();
    const repoInfo = getRepositoryInfo();
    console.log(`   Version: ${version}`);
    console.log(`   Repository: ${repoInfo.owner}/${repoInfo.repo}`);
    
    // Step 2: Extract release notes
    console.log('');
    console.log('[2/6] Extracting release notes from CHANGELOG.md...');
    const releaseNotes = extractReleaseNotes(version);
    console.log(`   ✓ Extracted ${releaseNotes.split('\n').length} lines of release notes`);
    
    // Step 3: Create/verify git tag
    if (!skipTag && !dryRun) {
      console.log('');
      console.log('[3/6] Creating git tag...');
      const tagResult = createGitTag(version, true);
      if (tagResult.created) {
        console.log(`   ✓ Tag created and pushed`);
      }
    } else {
      console.log('');
      console.log('[3/6] Skipping git tag creation');
    }
    
    // Step 4: Collect release artifacts
    console.log('');
    console.log('[4/6] Collecting release artifacts...');
    const artifacts = collectReleaseArtifacts();
    console.log(`   ✓ Found ${artifacts.length} artifact(s)`);
    for (const artifact of artifacts) {
      const sizeMB = (artifact.size / (1024 * 1024)).toFixed(2);
      console.log(`      - ${artifact.filename} (${sizeMB} MB)`);
    }
    
    if (dryRun) {
      console.log('');
      console.log('[DRY RUN] Would create release and upload assets');
      console.log('');
      console.log('Release Details:');
      console.log(`  Tag: v${version}`);
      console.log(`  Name: PEFT Studio v${version}`);
      console.log(`  Assets: ${artifacts.length}`);
      return {
        dryRun: true,
        version,
        artifacts: artifacts.length,
      };
    }
    
    // Step 5: Create GitHub release
    console.log('');
    console.log('[5/6] Creating GitHub release...');
    const release = await createRelease({
      owner: repoInfo.owner,
      repo: repoInfo.repo,
      tag: `v${version}`,
      name: `PEFT Studio v${version}`,
      body: releaseNotes,
      draft,
      prerelease,
    });
    console.log(`   ✓ Release created: ${release.html_url}`);
    
    // Step 6: Upload assets
    console.log('');
    console.log('[6/6] Uploading release assets...');
    const uploadedAssets = [];
    
    for (const artifact of artifacts) {
      console.log(`   Uploading ${artifact.filename}...`);
      
      try {
        const asset = await uploadAsset({
          uploadUrl: release.upload_url,
          filePath: artifact.path,
          name: artifact.filename,
          contentType: 'application/octet-stream',
        });
        
        uploadedAssets.push(artifact);
        console.log(`   ✓ Uploaded ${artifact.filename}`);
      } catch (error) {
        console.error(`   ✗ Failed to upload ${artifact.filename}: ${error.message}`);
        throw error;
      }
    }
    
    // Verify all assets uploaded
    const verification = verifyUploadedAssets(release, artifacts.map(a => a.filename));
    if (!verification.valid) {
      console.warn(`   ⚠️  Missing assets: ${verification.missing.join(', ')}`);
    }
    
    // Generate summary
    const summary = generateReleaseSummary(release, uploadedAssets);
    console.log(summary);
    
    return {
      success: true,
      version,
      release,
      artifacts: uploadedAssets,
      verification,
    };
    
  } catch (error) {
    console.error('');
    console.error('❌ Release failed:', error.message);
    throw error;
  }
}

// Export functions for testing
module.exports = {
  RELEASE_CONFIG,
  extractReleaseNotes,
  getRepositoryInfo,
  getVersion,
  createGitTag,
  createRelease,
  uploadAsset,
  verifyUploadedAssets,
  collectReleaseArtifacts,
  generateReleaseSummary,
  performRelease,
};

// CLI execution
if (require.main === module) {
  const args = process.argv.slice(2);
  const options = {
    dryRun: args.includes('--dry-run'),
    draft: args.includes('--draft'),
    prerelease: args.includes('--prerelease'),
    skipTag: args.includes('--skip-tag'),
  };
  
  performRelease(options)
    .then(() => {
      process.exit(0);
    })
    .catch((error) => {
      console.error(error);
      process.exit(1);
    });
}
