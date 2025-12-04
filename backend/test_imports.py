#!/usr/bin/env python3
"""
Comprehensive backend import test.
Tests all critical modules to ensure they can be imported without errors.
"""

import sys
import traceback

def test_import(module_name, from_list=None):
    """Test importing a module and report success or failure."""
    try:
        if from_list:
            module = __import__(module_name, fromlist=from_list)
            for item in from_list:
                if not hasattr(module, item):
                    print(f"❌ FAIL: {module_name}.{item} not found")
                    return False
        else:
            __import__(module_name)
        print(f"✓ OK: {module_name}")
        return True
    except Exception as e:
        print(f"❌ FAIL: {module_name}")
        print(f"   Error: {str(e)}")
        traceback.print_exc()
        return False

def main():
    """Run all import tests."""
    print("=" * 60)
    print("Backend Import Verification Test")
    print("=" * 60)
    
    tests = [
        # Core modules
        ("main", None),
        ("config", None),
        ("database", ["engine"]),
        
        # Services
        ("services", ["get_peft_service", "get_hardware_service", "get_model_registry_service"]),
        ("services.inference_service", ["get_inference_service"]),
        ("services.offline_queue_service", ["get_queue_manager", "OperationType"]),
        ("services.network_service", ["get_network_monitor"]),
        ("services.sync_engine", ["get_sync_engine", "ConflictResolution"]),
        ("services.startup_service", ["get_startup_optimizer", "measure_startup"]),
        ("services.dependency_checker", ["get_dependency_checker"]),
        ("services.performance_service", ["get_performance_service", "get_performance_monitor"]),
        
        # API Routers
        ("services.experiment_tracking_api", ["router"]),
        ("services.deployment_api", ["router"]),
        ("services.gradio_demo_api", ["router"]),
        ("services.security_api", ["router"]),
        ("services.telemetry_api", ["router"]),
        ("services.settings_api", ["router"]),
        ("services.inference_api", ["router"]),
        ("services.configuration_management_api", ["router"]),
        ("services.logging_api", ["router"]),
        
        # Security
        ("services.security_middleware", ["SecurityMiddleware", "InputValidationMiddleware"]),
        
        # Connectors
        ("connectors.registry", None),
        ("connectors.manager", None),
        ("connectors.base", None),
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        module_name, from_list = test
        if test_import(module_name, from_list):
            passed += 1
        else:
            failed += 1
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed > 0:
        print("\n⚠️  Some imports failed. Please review the errors above.")
        sys.exit(1)
    else:
        print("\n✅ All backend imports successful!")
        sys.exit(0)

if __name__ == "__main__":
    main()
