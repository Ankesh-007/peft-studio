# Comprehensive Testing Workflow

## Overview

The `comprehensive-testing.yml` workflow provides dedicated test execution across all test categories with detailed reporting and coverage tracking.

## Workflow Structure

### Jobs

1. **Unit Tests** (Matrix: ubuntu, macos, windows)
   - Runs frontend unit tests via `npm test -- --run`
   - Runs backend unit tests via `pytest -m "not integration and not e2e and not performance"`
   - Uploads coverage to Codecov for ubuntu runs
   - Validates: Requirements 3.1, 5.3, 5.4, 5.5

2. **Integration Tests** (ubuntu-latest)
   - Runs frontend integration tests via `npm run test:integration`
   - Runs backend integration tests via `pytest -m integration`
   - Uploads coverage to Codecov
   - Validates: Requirements 3.2, 5.3, 5.4, 5.5

3. **Property-Based Tests** (ubuntu-latest)
   - Runs frontend PBT via `npm run test:pbt`
   - Runs backend PBT via `pytest -m pbt`
   - Uploads coverage to Codecov
   - Validates: Requirements 3.3, 5.3, 5.4, 5.5

4. **Performance Tests** (ubuntu-latest)
   - Checks for existence of performance tests
   - Runs frontend performance tests if found
   - Runs backend performance tests via `pytest -m performance`
   - Provides summary of test execution
   - Validates: Requirements 3.4, 5.3, 5.4, 5.5

5. **End-to-End Tests** (ubuntu-latest)
   - Installs Playwright browsers
   - Builds the application
   - Runs frontend E2E tests via `npm run test:e2e`
   - Runs backend E2E tests via `pytest -m e2e`
   - Uploads test artifacts and coverage
   - Validates: Requirements 3.5, 5.3, 5.4, 5.5

6. **Test Summary**
   - Aggregates results from all test jobs
   - Creates comprehensive summary in GitHub Actions UI
   - Fails if any critical test suite fails
   - Creates test badge data
   - Validates: Requirements 5.4, 5.5

## Triggers

- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches
- Manual workflow dispatch

## Coverage Reporting

All test jobs upload coverage data to Codecov with specific flags:
- `frontend-unit`, `backend-unit`
- `frontend-integration`, `backend-integration`
- `frontend-pbt`, `backend-pbt`
- `frontend-e2e`, `backend-e2e`

## Test Markers

Backend tests use pytest markers defined in `backend/pytest.ini`:
- `unit`: Unit tests for individual components
- `integration`: Integration tests for component interactions
- `pbt`: Property-based tests using Hypothesis
- `performance`: Performance and benchmark tests
- `e2e`: End-to-end tests

## NPM Scripts Used

- `npm test -- --run`: Run unit tests
- `npm run test:integration`: Run integration tests
- `npm run test:pbt`: Run property-based tests
- `npm run test:e2e`: Run end-to-end tests

## Caching Strategy

- Node.js dependencies cached via `cache: 'npm'`
- Python dependencies cached via `cache: 'pip'`
- Significantly reduces workflow execution time

## Artifacts

- E2E test results and Playwright reports (7-day retention)
- Test badge data in `.github/badges/tests.txt`

## Requirements Validation

This workflow validates the following requirements from the CI/CD Fixes spec:

- **3.1**: Unit Tests pass on all platforms (ubuntu, macos, windows)
- **3.2**: Integration Tests complete successfully
- **3.3**: Property-Based Tests complete successfully
- **3.4**: Performance Tests complete successfully
- **3.5**: End-to-End Tests complete successfully
- **5.3**: comprehensive-testing.yml workflow file exists
- **5.4**: All workflow files reference valid npm and Python scripts
- **5.5**: All workflow files use appropriate caching strategies

## Usage

The workflow runs automatically on push/PR events. To run manually:

1. Go to Actions tab in GitHub
2. Select "Comprehensive Testing" workflow
3. Click "Run workflow"
4. Select branch and click "Run workflow"

## Monitoring

Check the workflow summary for:
- ✅ Passed test suites
- ❌ Failed test suites
- ⚠️ Warnings (e.g., no performance tests found)

All test results are aggregated in the Test Summary job with clear status indicators.
