# Requirements Document

## Introduction

This document specifies the requirements for bundling the Python backend into a self-contained executable within the PEFT Studio Electron application. The goal is to eliminate the need for end users to manually install Python, pip, or any Python dependencies, creating a true "one-click run" desktop application experience across Windows, macOS, and Linux platforms.

## Glossary

- **PyInstaller**: A Python package that bundles Python applications into standalone executables
- **Electron Main Process**: The Node.js process that manages the application lifecycle and spawns child processes
- **Backend Service Manager**: The existing service in electron/main.js that manages the Python backend lifecycle
- **PEFT Studio Backend**: The FastAPI-based Python server located in the backend/ directory
- **Bundled Executable**: A standalone binary file containing the Python interpreter, all dependencies, and application code
- **Resource Path**: The location where Electron stores application resources after packaging
- **Development Mode**: When the application runs from source code (app.isPackaged = false)
- **Production Mode**: When the application runs from an installed package (app.isPackaged = true)
- **NSIS**: Nullsoft Scriptable Install System, the Windows installer format used by electron-builder
- **Zombie Process**: A child process that continues running after its parent process terminates

## Requirements

### Requirement 1: Python Backend Compilation

**User Story:** As a developer, I want to compile the Python backend into a standalone executable, so that end users don't need to install Python manually.

#### Acceptance Criteria

1. WHEN the build process executes THEN the system SHALL compile backend/main.py and all dependencies into a single executable file
2. WHEN PyInstaller compiles the backend THEN the system SHALL include all Python packages listed in requirements.txt
3. WHEN the executable is created THEN the system SHALL hide the console window to prevent terminal windows from appearing
4. WHEN the backend includes data files or configuration files THEN the system SHALL bundle these files with the executable
5. WHERE the backend uses dynamic imports or lazy loading THEN the system SHALL ensure all required modules are included in the bundle

### Requirement 2: Cross-Platform Executable Generation

**User Story:** As a developer, I want to generate platform-specific executables, so that the application works on Windows, macOS, and Linux.

#### Acceptance Criteria

1. WHEN building for Windows THEN the system SHALL generate a peft_engine.exe file
2. WHEN building for macOS THEN the system SHALL generate a peft_engine executable compatible with both x64 and arm64 architectures
3. WHEN building for Linux THEN the system SHALL generate a peft_engine executable compatible with x64 architecture
4. WHEN the executable is created THEN the system SHALL name it consistently across platforms as "peft_engine" with platform-appropriate extensions
5. WHEN building for a target platform THEN the system SHALL place the executable in backend/dist/ directory

### Requirement 3: Electron Main Process Path Management

**User Story:** As a developer, I want the Electron main process to correctly locate the Python backend in both development and production modes, so that the application works seamlessly in all environments.

#### Acceptance Criteria

1. WHEN the application runs in development mode THEN the system SHALL execute the Python script at backend/main.py using the system Python interpreter
2. WHEN the application runs in production mode THEN the system SHALL execute the bundled executable from process.resourcesPath
3. WHEN determining the backend path THEN the system SHALL use app.isPackaged to distinguish between development and production modes
4. WHEN the backend path is resolved THEN the system SHALL log the resolved path for debugging purposes
5. WHEN the backend process is spawned THEN the system SHALL capture stdout and stderr for error reporting

### Requirement 4: Backend Process Lifecycle Management

**User Story:** As a user, I want the Python backend to start automatically when I launch the application and stop cleanly when I close it, so that no background processes remain running.

#### Acceptance Criteria

1. WHEN the Electron application starts THEN the system SHALL spawn the Python backend process automatically
2. WHEN the user closes the application window THEN the system SHALL send SIGTERM to the Python backend process
3. WHEN the backend process does not terminate within 1 second THEN the system SHALL send SIGKILL to force termination
4. WHEN the application quits THEN the system SHALL ensure no zombie Python processes remain running
5. WHEN the backend crashes unexpectedly THEN the system SHALL attempt to restart it according to existing restart logic

### Requirement 5: Electron-Builder Resource Packaging

**User Story:** As a developer, I want electron-builder to include the Python executable in the installer, so that it's available when users install the application.

#### Acceptance Criteria

1. WHEN electron-builder packages the application THEN the system SHALL copy the backend executable from backend/dist/ to the resources directory
2. WHEN the installer is created THEN the system SHALL include the backend executable in the extraResources configuration
3. WHEN the application is installed THEN the system SHALL place the backend executable in a location accessible via process.resourcesPath
4. WHEN building for Windows THEN the system SHALL use NSIS installer format with appropriate execution level settings
5. WHEN the installer runs THEN the system SHALL not require administrator privileges unless explicitly needed

### Requirement 6: Build Script Automation

**User Story:** As a developer, I want automated build scripts that compile the backend and frontend in the correct order, so that I can create distributable packages with a single command.

#### Acceptance Criteria

1. WHEN the developer runs the build command THEN the system SHALL execute backend compilation before frontend compilation
2. WHEN the backend build completes THEN the system SHALL verify the executable was created successfully
3. WHEN the frontend build completes THEN the system SHALL verify the dist/ directory contains the compiled assets
4. WHEN all builds complete THEN the system SHALL invoke electron-builder to create the installer
5. WHEN any build step fails THEN the system SHALL halt the process and report the error clearly

### Requirement 7: Dependency Management and Verification

**User Story:** As a developer, I want to ensure all Python dependencies are correctly bundled, so that the application doesn't fail due to missing packages at runtime.

#### Acceptance Criteria

1. WHEN PyInstaller analyzes the backend THEN the system SHALL detect all imports including lazy-loaded modules
2. WHEN the requirements.txt file is updated THEN the system SHALL include the new dependencies in the next build
3. WHEN the backend uses conditional imports THEN the system SHALL include all possible import paths
4. WHEN the executable is created THEN the system SHALL verify critical dependencies like torch, transformers, and peft are included
5. WHEN a dependency cannot be bundled THEN the system SHALL report the error during the build process

### Requirement 8: Error Handling and Diagnostics

**User Story:** As a user, I want clear error messages when the backend fails to start, so that I can understand what went wrong and how to fix it.

#### Acceptance Criteria

1. WHEN the bundled executable fails to start THEN the system SHALL capture and display the error message to the user
2. WHEN the executable is missing THEN the system SHALL display a message indicating the installation may be corrupted
3. WHEN the backend crashes during startup THEN the system SHALL log the crash details to the electron log file
4. WHEN a dependency is missing from the bundle THEN the system SHALL display the specific missing module name
5. WHEN the backend port is already in use THEN the system SHALL attempt alternative ports as per existing logic

### Requirement 9: Build Environment Configuration

**User Story:** As a developer, I want clear documentation and configuration for the build environment, so that other developers can build the application successfully.

#### Acceptance Criteria

1. WHEN a developer sets up the build environment THEN the system SHALL provide instructions for installing PyInstaller
2. WHEN PyInstaller is not installed THEN the build script SHALL display installation instructions
3. WHEN the build process requires specific Python versions THEN the system SHALL verify Python 3.10+ is available
4. WHEN building on Windows THEN the system SHALL use platform-appropriate path separators and commands
5. WHEN building on macOS or Linux THEN the system SHALL use Unix-style path separators and commands

### Requirement 10: Performance and Startup Time

**User Story:** As a user, I want the application to start quickly even with the bundled backend, so that I have a responsive user experience.

#### Acceptance Criteria

1. WHEN the bundled executable starts THEN the system SHALL complete startup within 5 seconds on modern hardware
2. WHEN the backend initializes THEN the system SHALL use lazy loading for heavy ML libraries as currently implemented
3. WHEN the application is in production mode THEN the system SHALL not perform unnecessary dependency checks
4. WHEN the backend is ready THEN the system SHALL notify the frontend via the existing backend-status event
5. WHEN startup time exceeds acceptable limits THEN the system SHALL log performance metrics for optimization

### Requirement 11: Security and Code Signing

**User Story:** As a user, I want the application to be properly signed, so that my operating system doesn't flag it as untrusted.

#### Acceptance Criteria

1. WHEN building for Windows THEN the system SHALL use the existing sign-windows.js script to sign the executable
2. WHEN building for macOS THEN the system SHALL use the existing entitlements and notarization process
3. WHEN the installer is created THEN the system SHALL sign both the application and the installer package
4. WHEN the bundled Python executable is included THEN the system SHALL ensure it doesn't trigger antivirus false positives
5. WHEN code signing fails THEN the system SHALL report the error but allow unsigned builds for development

### Requirement 12: Update and Maintenance

**User Story:** As a developer, I want the bundled backend to be updatable through the existing auto-update mechanism, so that users receive backend fixes and improvements.

#### Acceptance Criteria

1. WHEN a new version is released THEN the system SHALL include the updated backend executable in the update package
2. WHEN the auto-updater downloads an update THEN the system SHALL verify the integrity of the bundled executable
3. WHEN the update is installed THEN the system SHALL replace the old backend executable with the new one
4. WHEN the application restarts after an update THEN the system SHALL use the new backend executable
5. WHEN the backend version changes THEN the system SHALL log the version information for diagnostics
