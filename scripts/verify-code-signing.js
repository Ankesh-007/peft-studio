/**
 * Code Signing Verification Script
 *
 * This script verifies that code signing is properly configured for both
 * the main application and the bundled Python backend executable.
 */

import fs from "fs";
import path from "path";
import { execSync } from "child_process";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const platform = process.platform;
const colors = {
  reset: "\x1b[0m",
  green: "\x1b[32m",
  yellow: "\x1b[33m",
  red: "\x1b[31m",
  blue: "\x1b[34m",
};

function log(message, color = colors.reset) {
  console.log(`${color}${message}${colors.reset}`);
}

function checkEnvironmentVariables() {
  log("\n=== Checking Code Signing Environment Variables ===", colors.blue);

  const requiredVars = {
    windows: ["CSC_LINK", "CSC_KEY_PASSWORD"],
    darwin: [
      "CSC_LINK",
      "CSC_KEY_PASSWORD",
      "APPLE_ID",
      "APPLE_ID_PASSWORD",
      "APPLE_TEAM_ID",
    ],
  };

  const platformVars = requiredVars[platform] || [];
  let allPresent = true;

  platformVars.forEach((varName) => {
    if (process.env[varName]) {
      log(`✓ ${varName} is set`, colors.green);
    } else {
      log(`✗ ${varName} is not set`, colors.yellow);
      allPresent = false;
    }
  });

  if (!allPresent) {
    log(
      "\n⚠️  Some signing credentials are missing. Build will be unsigned.",
      colors.yellow
    );
    log(
      "   See docs/developer-guide/code-signing.md for setup instructions.",
      colors.yellow
    );
  } else {
    log("\n✓ All signing credentials are configured", colors.green);
  }

  return allPresent;
}

function checkPackageJsonConfiguration() {
  log("\n=== Checking package.json Configuration ===", colors.blue);

  const packageJsonPath = path.join(process.cwd(), "package.json");
  if (!fs.existsSync(packageJsonPath)) {
    log("✗ package.json not found", colors.red);
    return false;
  }

  const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, "utf8"));

  // Check extraResources includes backend
  if (!packageJson.build || !packageJson.build.extraResources) {
    log("✗ extraResources not configured in package.json", colors.red);
    return false;
  }

  const backendResource = packageJson.build.extraResources.find(
    (resource) =>
      resource.from && resource.from.includes("backend/dist/peft_engine")
  );

  if (!backendResource) {
    log("✗ Backend executable not in extraResources", colors.red);
    return false;
  }

  log("✓ Backend executable configured in extraResources", colors.green);

  // Check platform-specific configuration
  if (platform === "win32" && packageJson.build.win) {
    if (packageJson.build.win.sign) {
      log("✓ Windows signing script configured", colors.green);
    } else {
      log("⚠️  Windows signing script not configured", colors.yellow);
    }
  }

  if (platform === "darwin" && packageJson.build.mac) {
    if (packageJson.build.mac.entitlements) {
      log("✓ macOS entitlements configured", colors.green);
    } else {
      log("⚠️  macOS entitlements not configured", colors.yellow);
    }

    if (packageJson.build.mac.hardenedRuntime) {
      log("✓ Hardened runtime enabled", colors.green);
    } else {
      log("⚠️  Hardened runtime not enabled", colors.yellow);
    }
  }

  return true;
}

function checkBackendExecutable() {
  log("\n=== Checking Backend Executable ===", colors.blue);

  const backendDistDir = path.join(process.cwd(), "backend", "dist");
  if (!fs.existsSync(backendDistDir)) {
    log("⚠️  Backend dist directory not found", colors.yellow);
    log("   Run 'npm run build:backend' to build the backend", colors.yellow);
    return false;
  }

  const exeName =
    platform === "win32" ? "peft_engine.exe" : "peft_engine";
  const exePath = path.join(backendDistDir, exeName);

  if (!fs.existsSync(exePath)) {
    log(`✗ Backend executable not found: ${exePath}`, colors.red);
    return false;
  }

  const stats = fs.statSync(exePath);
  log(`✓ Backend executable found: ${exePath}`, colors.green);
  log(`  Size: ${(stats.size / 1024 / 1024).toFixed(2)} MB`, colors.reset);

  // Check if executable on Unix
  if (platform !== "win32") {
    const isExecutable = (stats.mode & 0o111) !== 0;
    if (isExecutable) {
      log("✓ Backend executable has execute permissions", colors.green);
    } else {
      log("✗ Backend executable lacks execute permissions", colors.red);
      log("  Run: chmod +x " + exePath, colors.yellow);
      return false;
    }
  }

  return true;
}

function checkEntitlementsFile() {
  if (platform !== "darwin") {
    return true; // Only relevant for macOS
  }

  log("\n=== Checking macOS Entitlements File ===", colors.blue);

  const entitlementsPath = path.join(
    process.cwd(),
    "build",
    "entitlements.mac.plist"
  );

  if (!fs.existsSync(entitlementsPath)) {
    log("✗ Entitlements file not found: " + entitlementsPath, colors.red);
    log(
      "  Create build/entitlements.mac.plist with required entitlements",
      colors.yellow
    );
    return false;
  }

  log("✓ Entitlements file found", colors.green);

  const entitlements = fs.readFileSync(entitlementsPath, "utf8");

  // Check for required entitlements
  const requiredEntitlements = [
    "com.apple.security.cs.allow-jit",
    "com.apple.security.cs.disable-library-validation",
    "com.apple.security.network.server",
    "com.apple.security.network.client",
  ];

  let allPresent = true;
  requiredEntitlements.forEach((entitlement) => {
    if (entitlements.includes(entitlement)) {
      log(`✓ ${entitlement}`, colors.green);
    } else {
      log(`✗ Missing: ${entitlement}`, colors.red);
      allPresent = false;
    }
  });

  return allPresent;
}

function checkSigningScripts() {
  log("\n=== Checking Signing Scripts ===", colors.blue);

  const scriptsDir = path.join(process.cwd(), "scripts");
  const requiredScripts = ["sign-windows.js", "sign-macos.js"];

  let allPresent = true;
  requiredScripts.forEach((script) => {
    const scriptPath = path.join(scriptsDir, script);
    if (fs.existsSync(scriptPath)) {
      log(`✓ ${script} found`, colors.green);
    } else {
      log(`✗ ${script} not found`, colors.red);
      allPresent = false;
    }
  });

  return allPresent;
}

function checkDocumentation() {
  log("\n=== Checking Documentation ===", colors.blue);

  const docsPath = path.join(
    process.cwd(),
    "docs",
    "developer-guide",
    "code-signing.md"
  );

  if (!fs.existsSync(docsPath)) {
    log("✗ Code signing documentation not found", colors.red);
    return false;
  }

  log("✓ Code signing documentation found", colors.green);

  const docs = fs.readFileSync(docsPath, "utf8");

  // Check for backend-specific documentation
  const requiredSections = [
    "Backend Executable Code Signing",
    "Antivirus Compatibility",
    "macOS Backend Signing",
    "Windows Backend Signing",
  ];

  let allPresent = true;
  requiredSections.forEach((section) => {
    if (docs.includes(section)) {
      log(`✓ ${section} section present`, colors.green);
    } else {
      log(`⚠️  ${section} section missing`, colors.yellow);
      allPresent = false;
    }
  });

  return allPresent;
}

function verifySignedExecutable(exePath) {
  if (!fs.existsSync(exePath)) {
    log(`✗ Executable not found: ${exePath}`, colors.red);
    return false;
  }

  log(`\n=== Verifying Signature: ${path.basename(exePath)} ===`, colors.blue);

  try {
    if (platform === "win32") {
      // Windows signature verification
      const result = execSync(
        `powershell -Command "Get-AuthenticodeSignature '${exePath}' | Select-Object -ExpandProperty Status"`,
        { encoding: "utf8" }
      ).trim();

      if (result === "Valid") {
        log("✓ Signature is valid", colors.green);
        return true;
      } else {
        log(`✗ Signature status: ${result}`, colors.yellow);
        return false;
      }
    } else if (platform === "darwin") {
      // macOS signature verification
      execSync(`codesign --verify --verbose "${exePath}"`, {
        encoding: "utf8",
      });
      log("✓ Signature is valid", colors.green);

      // Check notarization
      try {
        execSync(`spctl -a -vv "${exePath}"`, { encoding: "utf8" });
        log("✓ Notarization is valid", colors.green);
      } catch (error) {
        log("⚠️  Not notarized or notarization check failed", colors.yellow);
      }

      return true;
    } else {
      log("ℹ️  Signature verification not applicable on Linux", colors.blue);
      return true;
    }
  } catch (error) {
    log("✗ Signature verification failed", colors.red);
    log(`  ${error.message}`, colors.red);
    return false;
  }
}

function main() {
  log("\n╔════════════════════════════════════════════════════════╗", colors.blue);
  log("║     Code Signing Verification for PEFT Studio         ║", colors.blue);
  log("╚════════════════════════════════════════════════════════╝", colors.blue);

  const results = {
    environment: checkEnvironmentVariables(),
    packageJson: checkPackageJsonConfiguration(),
    backend: checkBackendExecutable(),
    entitlements: checkEntitlementsFile(),
    scripts: checkSigningScripts(),
    documentation: checkDocumentation(),
  };

  // Summary
  log("\n=== Verification Summary ===", colors.blue);

  const allPassed = Object.values(results).every((result) => result);

  if (allPassed) {
    log("\n✓ All checks passed!", colors.green);
    log(
      "  Code signing is properly configured for the bundled backend.",
      colors.green
    );
    process.exit(0);
  } else {
    log("\n⚠️  Some checks failed or have warnings", colors.yellow);
    log(
      "  Review the output above and fix any issues before building.",
      colors.yellow
    );
    log(
      "  See docs/developer-guide/code-signing.md for detailed instructions.",
      colors.yellow
    );

    // If environment variables are missing, it's just a warning (unsigned build)
    if (!results.environment) {
      log(
        "\n  Note: Missing credentials will result in unsigned builds.",
        colors.yellow
      );
      log("  This is acceptable for development but not for production.", colors.yellow);
    }

    // Exit with error only if critical checks failed
    const criticalFailed =
      !results.packageJson || !results.scripts || !results.documentation;

    if (criticalFailed) {
      process.exit(1);
    } else {
      process.exit(0);
    }
  }
}

// Run verification
main();
