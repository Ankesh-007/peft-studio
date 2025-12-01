"""
End-to-End Test Runner

This script runs all E2E tests and generates a comprehensive report.

Usage:
    python backend/tests/run_e2e_tests.py [--with-real-api] [--verbose]

Options:
    --with-real-api    Run tests with real API credentials (requires env vars)
    --verbose          Show detailed output
    --quick            Run only quick tests (skip performance tests)
    --security-only    Run only security tests
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path
from datetime import datetime


class E2ETestRunner:
    """End-to-end test runner"""
    
    def __init__(self, verbose=False, with_real_api=False, quick=False, security_only=False):
        self.verbose = verbose
        self.with_real_api = with_real_api
        self.quick = quick
        self.security_only = security_only
        self.results = {}
        
    def run_test_suite(self, test_file, description):
        """Run a test suite and capture results"""
        print(f"\n{'='*60}")
        print(f"Running: {description}")
        print(f"{'='*60}")
        
        cmd = ["pytest", test_file, "-v"]
        
        if self.verbose:
            cmd.append("-s")
        
        if not self.with_real_api:
            cmd.extend(["-m", "not real_api"])
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=not self.verbose,
                text=True,
                cwd=Path(__file__).parent.parent
            )
            
            self.results[description] = {
                "passed": result.returncode == 0,
                "return_code": result.returncode
            }
            
            if result.returncode == 0:
                print(f"✓ {description} - PASSED")
            else:
                print(f"✗ {description} - FAILED")
                if not self.verbose and result.stdout:
                    print(result.stdout[-500:])  # Show last 500 chars
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"✗ {description} - ERROR: {e}")
            self.results[description] = {
                "passed": False,
                "error": str(e)
            }
            return False
    
    def run_all_tests(self):
        """Run all E2E test suites"""
        print("\n" + "="*60)
        print("PEFT STUDIO - END-TO-END TEST SUITE")
        print("="*60)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Mode: {'With Real API' if self.with_real_api else 'Mock Only'}")
        print(f"Verbose: {self.verbose}")
        print("="*60)
        
        test_suites = []
        
        if self.security_only:
            test_suites = [
                ("tests/test_e2e_security_audit.py", "Security Audit"),
            ]
        elif self.quick:
            test_suites = [
                ("tests/test_e2e_complete_workflow.py", "Complete Workflow"),
                ("tests/test_e2e_platform_integration.py", "Platform Integration"),
            ]
        else:
            test_suites = [
                ("tests/test_e2e_complete_workflow.py", "Complete Workflow"),
                ("tests/test_e2e_platform_integration.py", "Platform Integration"),
                ("tests/test_e2e_performance_validation.py", "Performance Validation"),
                ("tests/test_e2e_security_audit.py", "Security Audit"),
            ]
        
        all_passed = True
        for test_file, description in test_suites:
            passed = self.run_test_suite(test_file, description)
            if not passed:
                all_passed = False
        
        self.print_summary(all_passed)
        
        return all_passed
    
    def print_summary(self, all_passed):
        """Print test summary"""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        passed_count = sum(1 for r in self.results.values() if r.get("passed", False))
        total_count = len(self.results)
        
        for description, result in self.results.items():
            status = "✓ PASSED" if result.get("passed", False) else "✗ FAILED"
            print(f"{status:12} - {description}")
        
        print("="*60)
        print(f"Total: {passed_count}/{total_count} test suites passed")
        print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if all_passed:
            print("\n🎉 ALL E2E TESTS PASSED! 🎉")
        else:
            print("\n⚠️  SOME TESTS FAILED - Review output above")
        
        print("="*60)
    
    def check_environment(self):
        """Check environment setup"""
        print("\nChecking environment...")
        
        # Check Python version
        python_version = sys.version_info
        print(f"✓ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
        
        # Check pytest
        try:
            result = subprocess.run(
                ["pytest", "--version"],
                capture_output=True,
                text=True
            )
            print(f"✓ {result.stdout.strip()}")
        except:
            print("✗ pytest not found")
            return False
        
        # Check for real API credentials if requested
        if self.with_real_api:
            print("\nChecking for real API credentials...")
            credentials = [
                "RUNPOD_API_KEY",
                "LAMBDA_API_KEY",
                "VASTAI_API_KEY",
                "HUGGINGFACE_TOKEN",
                "WANDB_API_KEY"
            ]
            
            found = []
            for cred in credentials:
                if os.getenv(cred):
                    found.append(cred)
                    print(f"✓ {cred} found")
                else:
                    print(f"  {cred} not set")
            
            if not found:
                print("\n⚠️  No real API credentials found")
                print("Tests will run with mock data only")
                self.with_real_api = False
            else:
                print(f"\n✓ Found {len(found)} API credentials")
        
        return True


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Run PEFT Studio End-to-End Tests"
    )
    parser.add_argument(
        "--with-real-api",
        action="store_true",
        help="Run tests with real API credentials"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed output"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run only quick tests (skip performance tests)"
    )
    parser.add_argument(
        "--security-only",
        action="store_true",
        help="Run only security tests"
    )
    
    args = parser.parse_args()
    
    runner = E2ETestRunner(
        verbose=args.verbose,
        with_real_api=args.with_real_api,
        quick=args.quick,
        security_only=args.security_only
    )
    
    # Check environment
    if not runner.check_environment():
        print("\n✗ Environment check failed")
        sys.exit(1)
    
    # Run tests
    success = runner.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
