/**
 * Repository Metadata Update Module
 * 
 * Updates repository metadata including:
 * - package.json repository URLs
 * - package.json keywords
 * - Documentation URLs
 * - Repository description consistency
 */

const fs = require('fs');
const path = require('path');

/**
 * Extract repository URL from package.json
 */
function getRepositoryUrl(repoPath = process.cwd()) {
  const packageJsonPath = path.join(repoPath, 'package.json');
  
  if (!fs.existsSync(packageJsonPath)) {
    throw new Error('package.json not found');
  }
  
  const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
  
  if (!packageJson.repository || !packageJson.repository.url) {
    throw new Error('Repository URL not found in package.json');
  }
  
  return packageJson.repository.url;
}

/**
 * Extract all GitHub URLs from a markdown file
 */
function extractGitHubUrls(content) {
  const urlPattern = /https?:\/\/github\.com\/[^\s\)]+/g;
  const matches = content.match(urlPattern) || [];
  
  // Normalize URLs (remove .git suffix, trailing slashes)
  return matches.map(url => {
    return url
      .replace(/\.git$/, '')
      .replace(/\/$/, '')
      .replace(/#.*$/, '') // Remove anchors
      .replace(/\?.*$/, ''); // Remove query params
  });
}

/**
 * Get all markdown files in a directory recursively
 */
function getMarkdownFiles(dirPath, fileList = []) {
  const files = fs.readdirSync(dirPath);
  
  for (const file of files) {
    const filePath = path.join(dirPath, file);
    const stat = fs.statSync(filePath);
    
    if (stat.isDirectory()) {
      // Skip node_modules, .git, and other common directories
      if (!['node_modules', '.git', 'dist', 'build', 'release'].includes(file)) {
        getMarkdownFiles(filePath, fileList);
      }
    } else if (file.endsWith('.md')) {
      fileList.push(filePath);
    }
  }
  
  return fileList;
}

/**
 * Check URL consistency across all documentation files
 */
function checkUrlConsistency(repoPath = process.cwd()) {
  const expectedUrl = getRepositoryUrl(repoPath);
  const normalizedExpectedUrl = expectedUrl.replace(/\.git$/, '').replace(/\/$/, '');
  
  const markdownFiles = getMarkdownFiles(repoPath);
  const inconsistencies = [];
  
  // Extract owner/repo from expected URL
  const expectedParts = normalizedExpectedUrl.split('/');
  const expectedOwner = expectedParts[3];
  const expectedRepo = expectedParts[4];
  
  // Common placeholder patterns that should be replaced
  const placeholderPatterns = [
    'your-org',
    'yourusername',
    'YOUR_ORG',
    'your-username',
  ];
  
  for (const filePath of markdownFiles) {
    const content = fs.readFileSync(filePath, 'utf8');
    const urls = extractGitHubUrls(content);
    
    for (const url of urls) {
      // Extract owner/repo from URL
      const urlParts = url.split('/');
      if (urlParts.length < 5) continue;
      
      const urlOwner = urlParts[3];
      const urlRepo = urlParts[4];
      
      // Check if this is a placeholder that should be replaced
      const isPlaceholder = placeholderPatterns.some(pattern => 
        urlOwner.toLowerCase().includes(pattern.toLowerCase())
      );
      
      // Check if URL references this repository with wrong owner/repo
      const isSameRepo = urlRepo === expectedRepo || urlRepo.startsWith(expectedRepo);
      
      if (isPlaceholder || (isSameRepo && urlOwner !== expectedOwner)) {
        inconsistencies.push({
          file: path.relative(repoPath, filePath),
          found: url,
          expected: normalizedExpectedUrl,
        });
      }
    }
  }
  
  return {
    consistent: inconsistencies.length === 0,
    expectedUrl: normalizedExpectedUrl,
    inconsistencies,
  };
}

/**
 * Update package.json repository URLs
 */
function updatePackageJsonUrls(repoPath, newUrl) {
  const packageJsonPath = path.join(repoPath, 'package.json');
  const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
  
  const updated = {
    repository: false,
    homepage: false,
    bugs: false,
  };
  
  // Normalize URL
  const normalizedUrl = newUrl.replace(/\.git$/, '');
  
  // Update repository URL
  if (packageJson.repository) {
    if (packageJson.repository.url !== `${normalizedUrl}.git`) {
      packageJson.repository.url = `${normalizedUrl}.git`;
      updated.repository = true;
    }
  }
  
  // Update homepage
  const expectedHomepage = `${normalizedUrl}#readme`;
  if (packageJson.homepage !== expectedHomepage) {
    packageJson.homepage = expectedHomepage;
    updated.homepage = true;
  }
  
  // Update bugs URL
  const expectedBugsUrl = `${normalizedUrl}/issues`;
  if (!packageJson.bugs || packageJson.bugs.url !== expectedBugsUrl) {
    packageJson.bugs = { url: expectedBugsUrl };
    updated.bugs = true;
  }
  
  // Write back to file
  fs.writeFileSync(packageJsonPath, JSON.stringify(packageJson, null, 2) + '\n');
  
  return updated;
}

/**
 * Update package.json keywords
 */
function updatePackageJsonKeywords(repoPath, keywords) {
  const packageJsonPath = path.join(repoPath, 'package.json');
  const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
  
  const existingKeywords = packageJson.keywords || [];
  const newKeywords = [...new Set([...existingKeywords, ...keywords])];
  
  const updated = JSON.stringify(existingKeywords.sort()) !== JSON.stringify(newKeywords.sort());
  
  if (updated) {
    packageJson.keywords = newKeywords.sort();
    fs.writeFileSync(packageJsonPath, JSON.stringify(packageJson, null, 2) + '\n');
  }
  
  return {
    updated,
    added: newKeywords.filter(k => !existingKeywords.includes(k)),
    keywords: newKeywords,
  };
}

/**
 * Replace URLs in a file
 */
function replaceUrlsInFile(filePath, oldUrl, newUrl) {
  let content = fs.readFileSync(filePath, 'utf8');
  const originalContent = content;
  
  // Normalize URLs for replacement
  const normalizedOldUrl = oldUrl.replace(/\.git$/, '').replace(/\/$/, '');
  const normalizedNewUrl = newUrl.replace(/\.git$/, '').replace(/\/$/, '');
  
  // Replace all variations of the old URL
  const variations = [
    normalizedOldUrl,
    `${normalizedOldUrl}.git`,
    `${normalizedOldUrl}/`,
  ];
  
  for (const variation of variations) {
    const regex = new RegExp(variation.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g');
    content = content.replace(regex, normalizedNewUrl);
  }
  
  // Also replace placeholder patterns
  const placeholderPatterns = [
    /https:\/\/github\.com\/your-org\/peft-studio/gi,
    /https:\/\/github\.com\/yourusername\/peft-studio/gi,
    /https:\/\/github\.com\/YOUR_ORG\/peft-studio/gi,
    /https:\/\/github\.com\/your-username\/peft-studio/gi,
  ];
  
  for (const pattern of placeholderPatterns) {
    content = content.replace(pattern, normalizedNewUrl);
  }
  
  if (content !== originalContent) {
    fs.writeFileSync(filePath, content, 'utf8');
    return true;
  }
  
  return false;
}

/**
 * Update all documentation URLs
 */
function updateDocumentationUrls(repoPath, newUrl) {
  const markdownFiles = getMarkdownFiles(repoPath);
  const currentUrl = getRepositoryUrl(repoPath).replace(/\.git$/, '');
  const updatedFiles = [];
  
  for (const filePath of markdownFiles) {
    if (replaceUrlsInFile(filePath, currentUrl, newUrl)) {
      updatedFiles.push(path.relative(repoPath, filePath));
    }
  }
  
  return {
    updated: updatedFiles.length > 0,
    files: updatedFiles,
  };
}

/**
 * Verify repository description consistency
 */
function verifyDescriptionConsistency(repoPath = process.cwd()) {
  const packageJsonPath = path.join(repoPath, 'package.json');
  const readmePath = path.join(repoPath, 'README.md');
  
  if (!fs.existsSync(packageJsonPath) || !fs.existsSync(readmePath)) {
    return {
      consistent: false,
      error: 'Missing package.json or README.md',
    };
  }
  
  const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
  const readmeContent = fs.readFileSync(readmePath, 'utf8');
  
  const packageDescription = packageJson.description || '';
  
  // Check if description appears in README (case-insensitive)
  const descriptionInReadme = readmeContent.toLowerCase().includes(packageDescription.toLowerCase());
  
  return {
    consistent: descriptionInReadme,
    packageDescription,
    foundInReadme: descriptionInReadme,
  };
}

/**
 * Main function to update all repository metadata
 */
function updateRepositoryMetadata(repoPath = process.cwd(), options = {}) {
  const results = {
    urlConsistency: null,
    packageJsonUpdates: null,
    keywordUpdates: null,
    documentationUpdates: null,
    descriptionConsistency: null,
  };
  
  // Check URL consistency
  results.urlConsistency = checkUrlConsistency(repoPath);
  
  // Update package.json URLs if new URL provided
  if (options.newUrl) {
    results.packageJsonUpdates = updatePackageJsonUrls(repoPath, options.newUrl);
    results.documentationUpdates = updateDocumentationUrls(repoPath, options.newUrl);
  }
  
  // Update keywords if provided
  if (options.keywords && options.keywords.length > 0) {
    results.keywordUpdates = updatePackageJsonKeywords(repoPath, options.keywords);
  }
  
  // Verify description consistency
  results.descriptionConsistency = verifyDescriptionConsistency(repoPath);
  
  return results;
}

module.exports = {
  getRepositoryUrl,
  extractGitHubUrls,
  getMarkdownFiles,
  checkUrlConsistency,
  updatePackageJsonUrls,
  updatePackageJsonKeywords,
  replaceUrlsInFile,
  updateDocumentationUrls,
  verifyDescriptionConsistency,
  updateRepositoryMetadata,
};
