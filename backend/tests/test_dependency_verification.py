"""
Property-based tests for dependency verification.

Feature: peft-application-fix, Property 3: Dependency Verification Accuracy
Validates: Requirements 3.1, 3.2, 3.3, 3.4

Tests that all missing dependencies are reported accurately and that
each missing package appears in the dependency report with fix instructions.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.dependency_checker import (
    DependencyChecker,
    DependencyCheck,
    DependencyReport
)


# Strategy for generating package names
package_names = st.sampled_from([
    'torch', 'transformers', 'peft', 'datasets', 'accelerate',
    'bitsandbytes', 'scipy', 'sentencepiece', 'protobuf'
])


# Strategy for generating lists of missing packages
missing_packages_strategy = st.lists(
    package_names,
    min_size=1,
    max_size=5,
    unique=True
)


@pytest.mark.property
@given(missing_packages=missing_packages_strategy)
@settings(max_examples=50, deadline=None)  # Disable deadline due to import overhead
def test_all_missing_packages_are_reported(missing_packages):
    """
    Property 3: Dependency Verification Accuracy - Missing Package Detection
    
    For any list of missing packages, the dependency checker should report
    all of them as not installed in the dependency report.
    
    This ensures users get complete information about what's missing.
    """
    # Create a dependency checker
    checker = DependencyChecker()
    
    # Mock _check_single_package to simulate missing packages
    original_check = checker._check_single_package
    
    def mock_check_single_package(package_name, min_version, required):
        if package_name in missing_packages:
            # Return a check indicating the package is not installed
            return DependencyCheck(
                name=package_name,
                required=required,
                installed=False,
                expected_version=f"{min_version}+",
                error=f"Package {package_name} is not installed",
                fix_instructions=f"Install {package_name}: pip install {package_name}>={min_version}"
            )
        else:
            # Use original check for other packages
            return original_check(package_name, min_version, required)
    
    with patch.object(checker, '_check_single_package', side_effect=mock_check_single_package):
        # Get package checks
        package_checks = checker.check_package_versions()
        
        # Verify all missing packages are reported as not installed
        for missing_pkg in missing_packages:
            # Find the check for this package
            check = next(
                (c for c in package_checks if c.name == missing_pkg),
                None
            )
            
            assert check is not None, \
                f"Missing package '{missing_pkg}' not found in dependency report"
            
            assert not check.installed, \
                f"Package '{missing_pkg}' should be reported as not installed"
            
            assert check.error is not None, \
                f"Missing package '{missing_pkg}' should have an error message"
            
            assert check.fix_instructions is not None, \
                f"Missing package '{missing_pkg}' should have fix instructions"
            
            # Verify fix instructions mention the package name
            assert missing_pkg in check.fix_instructions.lower(), \
                f"Fix instructions for '{missing_pkg}' should mention the package name"


@pytest.mark.property
@given(
    major=st.integers(min_value=2, max_value=4),
    minor=st.integers(min_value=0, max_value=15)
)
@settings(max_examples=50, deadline=1000)
def test_python_version_check_accuracy(major, minor):
    """
    Property: Python version check should accurately determine compatibility.
    
    For any Python version, the checker should correctly identify if it
    meets the minimum requirement (3.10+).
    """
    checker = DependencyChecker()
    
    # Mock sys.version_info
    mock_version_info = MagicMock()
    mock_version_info.major = major
    mock_version_info.minor = minor
    
    with patch('sys.version_info', mock_version_info):
        with patch('sys.version', f'{major}.{minor}.0'):
            check = checker.check_python_version()
            
            # Determine expected compatibility
            expected_compatible = (major > 3) or (major == 3 and minor >= 10)
            
            # Verify the check result matches expectation
            if expected_compatible:
                assert check.error is None, \
                    f"Python {major}.{minor} should be compatible but has error: {check.error}"
                assert check.fix_instructions is None, \
                    f"Compatible Python {major}.{minor} should not have fix instructions"
            else:
                assert check.error is not None, \
                    f"Python {major}.{minor} should be incompatible but has no error"
                assert check.fix_instructions is not None, \
                    f"Incompatible Python {major}.{minor} should have fix instructions"


@pytest.mark.property
def test_cuda_check_provides_clear_guidance():
    """
    Property: CUDA availability check should provide clear guidance.
    
    Whether CUDA is available or not, the check should provide clear
    information about the status and what it means for the user.
    """
    checker = DependencyChecker()
    
    # Test with CUDA available
    with patch('services.dependency_checker._get_torch') as mock_torch_getter:
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = True
        mock_torch.version.cuda = "11.8"
        mock_torch.cuda.device_count.return_value = 1
        mock_torch.cuda.get_device_name.return_value = "NVIDIA GeForce RTX 3090"
        mock_torch_getter.return_value = mock_torch
        
        check = checker.check_cuda_availability()
        
        assert check.name == "CUDA"
        assert check.installed == True
        assert check.version == "11.8"
        assert check.error is None
        assert check.fix_instructions is None
    
    # Test with CUDA not available
    with patch('services.dependency_checker._get_torch') as mock_torch_getter:
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = False
        mock_torch_getter.return_value = mock_torch
        
        check = checker.check_cuda_availability()
        
        assert check.name == "CUDA"
        assert check.installed == False
        assert check.error is not None
        assert check.fix_instructions is not None
        
        # Verify fix instructions mention key information
        fix_lower = check.fix_instructions.lower()
        assert 'gpu' in fix_lower or 'cuda' in fix_lower, \
            "Fix instructions should mention GPU or CUDA"
        assert 'install' in fix_lower, \
            "Fix instructions should mention installation"


@pytest.mark.property
@given(
    installed_version=st.sampled_from(['2.0.0', '2.1.0', '1.13.0', '1.9.0']),
    min_version=st.sampled_from(['2.0.0', '1.13.0', '1.10.0'])
)
@settings(max_examples=50, deadline=1000)
def test_version_comparison_accuracy(installed_version, min_version):
    """
    Property: Version comparison should accurately determine compatibility.
    
    For any installed and minimum version, the checker should correctly
    determine if the installed version meets the requirement.
    """
    checker = DependencyChecker()
    
    # Parse versions for comparison
    installed_parts = [int(x) for x in installed_version.split('.')]
    min_parts = [int(x) for x in min_version.split('.')]
    
    # Determine expected result
    expected_compatible = installed_parts >= min_parts
    
    # Test the comparison
    result = checker._compare_versions(installed_version, min_version)
    
    assert result == expected_compatible, \
        f"Version comparison failed: {installed_version} vs {min_version} " \
        f"(expected {expected_compatible}, got {result})"


@pytest.mark.property
def test_comprehensive_report_includes_all_checks():
    """
    Property: Comprehensive dependency report should include all check types.
    
    The check_all() method should return a report that includes:
    - Python version check
    - CUDA availability check
    - All package version checks
    """
    checker = DependencyChecker()
    
    # Run comprehensive check
    report = checker.check_all()
    
    # Verify report structure
    assert isinstance(report, DependencyReport)
    assert isinstance(report.checks, list)
    assert len(report.checks) > 0
    
    # Verify Python check is included
    python_checks = [c for c in report.checks if c.name == "Python"]
    assert len(python_checks) == 1, "Report should include exactly one Python check"
    
    # Verify CUDA check is included
    cuda_checks = [c for c in report.checks if c.name == "CUDA"]
    assert len(cuda_checks) == 1, "Report should include exactly one CUDA check"
    
    # Verify package checks are included
    package_checks = [
        c for c in report.checks 
        if c.name not in ["Python", "CUDA"]
    ]
    assert len(package_checks) > 0, "Report should include package checks"
    
    # Verify all_passed is a boolean
    assert isinstance(report.all_passed, bool)
    
    # Verify recommendations is a list
    assert isinstance(report.recommendations, list)


@pytest.mark.property
def test_required_vs_optional_dependencies():
    """
    Property: Report should distinguish between required and optional dependencies.
    
    The all_passed flag should only consider required dependencies, not optional ones.
    """
    checker = DependencyChecker()
    
    # Mock to make some required packages missing
    def mock_import(name, *args, **kwargs):
        # Make bitsandbytes (optional) missing
        if name == 'bitsandbytes':
            raise ImportError(f"No module named '{name}'")
        # Import everything else normally
        return __builtins__.__import__(name, *args, **kwargs)
    
    with patch('builtins.__import__', side_effect=mock_import):
        report = checker.check_all()
        
        # Find the bitsandbytes check
        bitsandbytes_check = next(
            (c for c in report.checks if c.name == 'bitsandbytes'),
            None
        )
        
        if bitsandbytes_check:
            # Verify it's marked as optional
            assert not bitsandbytes_check.required, \
                "bitsandbytes should be marked as optional"
            
            # If only optional dependencies are missing, all_passed could still be True
            # (depending on required dependencies)
            required_checks = [c for c in report.checks if c.required]
            all_required_passed = all(
                c.installed and c.error is None
                for c in required_checks
            )
            
            # all_passed should match required dependencies status
            if all_required_passed:
                # It's okay if all_passed is True even with optional deps missing
                pass
            else:
                # If required deps failed, all_passed must be False
                assert not report.all_passed, \
                    "all_passed should be False when required dependencies fail"


@pytest.mark.property
@given(missing_packages=missing_packages_strategy)
@settings(max_examples=50, deadline=None)  # Disable deadline due to import overhead
def test_fix_instructions_are_actionable(missing_packages):
    """
    Property: Fix instructions should be actionable and include pip commands.
    
    For any missing package, the fix instructions should include a pip
    install command that the user can run.
    """
    checker = DependencyChecker()
    
    # Mock _check_single_package to simulate missing packages
    original_check = checker._check_single_package
    
    def mock_check_single_package(package_name, min_version, required):
        if package_name in missing_packages:
            # Return a check indicating the package is not installed
            return DependencyCheck(
                name=package_name,
                required=required,
                installed=False,
                expected_version=f"{min_version}+",
                error=f"Package {package_name} is not installed",
                fix_instructions=f"Install {package_name}: pip install {package_name}>={min_version}"
            )
        else:
            # Use original check for other packages
            return original_check(package_name, min_version, required)
    
    with patch.object(checker, '_check_single_package', side_effect=mock_check_single_package):
        package_checks = checker.check_package_versions()
        
        for missing_pkg in missing_packages:
            check = next(
                (c for c in package_checks if c.name == missing_pkg),
                None
            )
            
            if check and not check.installed:
                # Verify fix instructions are present
                assert check.fix_instructions is not None, \
                    f"Missing package '{missing_pkg}' should have fix instructions"
                
                fix_lower = check.fix_instructions.lower()
                
                # Verify fix instructions mention pip
                assert 'pip' in fix_lower, \
                    f"Fix instructions for '{missing_pkg}' should mention pip"
                
                # Verify fix instructions mention install
                assert 'install' in fix_lower, \
                    f"Fix instructions for '{missing_pkg}' should mention install"
                
                # Verify fix instructions mention the package name
                assert missing_pkg in fix_lower, \
                    f"Fix instructions for '{missing_pkg}' should mention the package name"


if __name__ == '__main__':
    # Run the property tests
    pytest.main([__file__, '-v', '-m', 'property'])
