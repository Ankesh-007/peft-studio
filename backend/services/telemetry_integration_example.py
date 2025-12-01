"""
Telemetry Integration Example

Shows how to integrate telemetry tracking throughout the application.

Requirements: 15.5
"""

import asyncio
import time
from services.telemetry_service import get_telemetry, track_event, track_error, track_performance


async def example_application_startup():
    """Example: Track application startup."""
    telemetry = get_telemetry()
    
    # Track startup event
    await track_event("app_started", {
        "version": "1.0.0",
        "environment": "production"
    })


async def example_feature_usage():
    """Example: Track feature usage."""
    # Track when user uses a feature
    await track_event("training_started", {
        "algorithm": "lora",
        "model_size": "7B",
        "provider": "runpod"
    })
    
    await track_event("model_loaded", {
        "model_name": "llama-2-7b",
        "quantization": "4bit"
    })
    
    await track_event("inference_completed", {
        "tokens_generated": 150,
        "time_seconds": 2.5
    })


async def example_error_tracking():
    """Example: Track errors with context."""
    try:
        # Simulate an error
        raise ValueError("Model not found")
    except Exception as e:
        # Track the error with context
        await track_error(e, {
            "operation": "load_model",
            "model_name": "invalid-model",
            "provider": "huggingface"
        })


async def example_performance_tracking():
    """Example: Track performance metrics."""
    # Track API response time
    start = time.time()
    # ... API call ...
    await asyncio.sleep(0.15)  # Simulate API call
    duration = (time.time() - start) * 1000
    
    await track_performance("api_response_time", duration, "ms")
    
    # Track database query time
    start = time.time()
    # ... database query ...
    await asyncio.sleep(0.05)  # Simulate query
    duration = (time.time() - start) * 1000
    
    await track_performance("db_query_time", duration, "ms")


async def example_with_decorator():
    """Example: Create a decorator for automatic performance tracking."""
    
    def track_performance_decorator(metric_name: str):
        """Decorator to automatically track function performance."""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                start = time.time()
                try:
                    result = await func(*args, **kwargs)
                    return result
                finally:
                    duration = (time.time() - start) * 1000
                    await track_performance(metric_name, duration, "ms")
            return wrapper
        return decorator
    
    # Use the decorator
    @track_performance_decorator("training_step")
    async def training_step():
        await asyncio.sleep(0.1)  # Simulate training
        return "success"
    
    result = await training_step()
    print(f"Training step result: {result}")


async def example_analytics_retrieval():
    """Example: Retrieve and display analytics."""
    telemetry = get_telemetry()
    
    # Get analytics
    analytics = await telemetry.get_analytics()
    
    print(f"Total events: {analytics['total_events']}")
    print(f"Event counts: {analytics['event_counts']}")
    print(f"Performance metrics: {analytics['performance_metrics']}")
    print(f"Session duration: {analytics['session_duration_minutes']:.2f} minutes")


async def example_data_export():
    """Example: Export telemetry data."""
    telemetry = get_telemetry()
    
    # Export all data
    data = await telemetry.export_data()
    
    print(f"Exported {len(data['events'])} events")
    print(f"Config: {data['config']}")


async def example_consent_management():
    """Example: Manage user consent."""
    telemetry = get_telemetry()
    
    # Check if enabled
    if not telemetry.is_enabled():
        print("Telemetry is disabled")
        
        # Show consent dialog to user
        # ... UI code ...
        
        # If user consents, enable telemetry
        telemetry.enable()
        print("Telemetry enabled")
    
    # Get consent status for UI
    status = telemetry.get_consent_status()
    print(f"Consent status: {status}")


async def example_application_shutdown():
    """Example: Properly shutdown telemetry."""
    telemetry = get_telemetry()
    
    # Track shutdown event
    await track_event("app_shutdown", {
        "clean_shutdown": True
    })
    
    # Shutdown telemetry (flushes remaining events)
    await telemetry.shutdown()


async def main():
    """Run all examples."""
    telemetry = get_telemetry()
    
    # Enable telemetry for examples
    telemetry.enable()
    
    print("=== Telemetry Integration Examples ===\n")
    
    print("1. Application Startup")
    await example_application_startup()
    
    print("\n2. Feature Usage Tracking")
    await example_feature_usage()
    
    print("\n3. Error Tracking")
    await example_error_tracking()
    
    print("\n4. Performance Tracking")
    await example_performance_tracking()
    
    print("\n5. Performance Decorator")
    await example_with_decorator()
    
    print("\n6. Analytics Retrieval")
    await example_analytics_retrieval()
    
    print("\n7. Data Export")
    await example_data_export()
    
    print("\n8. Consent Management")
    await example_consent_management()
    
    print("\n9. Application Shutdown")
    await example_application_shutdown()
    
    print("\n=== Examples Complete ===")


if __name__ == "__main__":
    asyncio.run(main())
