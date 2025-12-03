# Multi-Run Management System

## Overview

The Multi-Run Management System provides comprehensive functionality for tracking, monitoring, filtering, and managing multiple concurrent training runs. This system ensures proper isolation between runs and provides a unified interface for managing the complete lifecycle of training jobs.

## Requirements Addressed

- **16.1**: Track each run independently with unique identifiers
- **16.2**: Display progress, metrics, and resource usage for each run
- **16.3**: Preserve state when switching between runs
- **16.4**: Display all runs with filtering by status, provider, and date
- **16.5**: Send notifications and update run status on completion

## Components

### 1. MultiRunManager

The main service class that orchestrates multi-run management:

```python
from services.multi_run_service import MultiRunManager, get_multi_run_manager

# Get singleton instance
manager = get_multi_run_manager()

# Or create with custom orchestrator
manager = MultiRunManager(orchestrator=custom_orchestrator)
```

### 2. Database Schema

The `TrainingRun` table stores all run information:

- **job_id**: Unique identifier for the run
- **status**: Current state (running, paused, completed, failed, stopped)
- **provider**: Compute provider (runpod, lambda, vastai, local)
- **config**: Complete training configuration (JSON)
- **metrics**: Current and historical metrics
- **timestamps**: started_at, completed_at, paused_at
- **artifacts**: artifact_path, artifact_hash

### 3. Key Features

#### Run Tracking

```python
# Sync a job to database
db_run = manager.sync_run_to_database(job, db_session)

# Get active runs
active_runs = manager.get_active_runs(db_session)

# Get run details
details = manager.get_run_details(job_id, db_session)
```

#### Run History and Filtering

```python
from services.multi_run_service import RunFilter

# Create filter
filter_criteria = RunFilter(
    status=["completed", "failed"],
    provider=["runpod", "lambda"],
    date_from=datetime(2024, 1, 1),
    date_to=datetime(2024, 12, 31)
)

# Get filtered history
runs = manager.get_run_history(
    db_session,
    filter_criteria=filter_criteria,
    limit=50,
    offset=0
)
```

#### Concurrent Run Statistics

```python
# Get statistics about concurrent runs
stats = manager.get_concurrent_stats(db_session)

print(f"Total active: {stats.total_active}")
print(f"Running: {stats.running}")
print(f"Paused: {stats.paused}")
print(f"Providers: {stats.active_providers}")
```

#### Run Cancellation and Cleanup

```python
# Cancel a running job
success = manager.cancel_run(job_id, db_session)

# Cleanup resources for a completed job
success = manager.cleanup_run(job_id, db_session)
```

## Data Models

### RunSummary

Provides a summary view of a training run:

```python
@dataclass
class RunSummary:
    job_id: str
    name: Optional[str]
    status: str
    provider: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]
    duration_seconds: Optional[float]
    current_step: int
    total_steps: Optional[int]
    progress_percent: float
    current_loss: Optional[float]
    final_loss: Optional[float]
    error_message: Optional[str]
```

### ConcurrentRunStats

Statistics about concurrent runs:

```python
@dataclass
class ConcurrentRunStats:
    total_active: int
    running: int
    paused: int
    total_completed: int
    total_failed: int
    active_providers: Dict[str, int]
```

### RunFilter

Filter criteria for querying runs:

```python
@dataclass
class RunFilter:
    status: Optional[List[str]] = None
    provider: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    model_name: Optional[str] = None
    job_ids: Optional[List[str]] = None
```

## API Integration

### FastAPI Endpoints

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from services.multi_run_service import get_multi_run_manager

router = APIRouter(prefix="/api/runs", tags=["runs"])

@router.get("/active")
async def get_active_runs(db: Session = Depends(get_db)):
    """Get all active training runs"""
    manager = get_multi_run_manager()
    runs = manager.get_active_runs(db)
    return [run.to_dict() for run in runs]

@router.get("/history")
async def get_run_history(
    status: Optional[str] = None,
    provider: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get run history with optional filtering"""
    manager = get_multi_run_manager()
    
    filter_criteria = None
    if status or provider:
        filter_criteria = RunFilter(
            status=status.split(",") if status else None,
            provider=provider.split(",") if provider else None
        )
    
    runs = manager.get_run_history(db, filter_criteria, limit, offset)
    return [run.to_dict() for run in runs]

@router.get("/stats")
async def get_concurrent_stats(db: Session = Depends(get_db)):
    """Get statistics about concurrent runs"""
    manager = get_multi_run_manager()
    stats = manager.get_concurrent_stats(db)
    return stats.to_dict()

@router.get("/{job_id}")
async def get_run_details(job_id: str, db: Session = Depends(get_db)):
    """Get detailed information about a specific run"""
    manager = get_multi_run_manager()
    details = manager.get_run_details(job_id, db)
    if not details:
        raise HTTPException(status_code=404, detail="Run not found")
    return details

@router.post("/{job_id}/cancel")
async def cancel_run(job_id: str, db: Session = Depends(get_db)):
    """Cancel a running or paused training run"""
    manager = get_multi_run_manager()
    success = manager.cancel_run(job_id, db)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to cancel run")
    return {"status": "cancelled", "job_id": job_id}

@router.delete("/{job_id}")
async def cleanup_run(job_id: str, db: Session = Depends(get_db)):
    """Cleanup resources for a completed/failed/stopped run"""
    manager = get_multi_run_manager()
    success = manager.cleanup_run(job_id, db)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to cleanup run")
    return {"status": "cleaned", "job_id": job_id}
```

## Property-Based Testing

The system includes comprehensive property-based tests to verify multi-run isolation:

### Property 9: Multi-run isolation

**Validates Requirements 16.1, 16.3**

The property tests verify that:

1. **Isolated Metrics**: Each run maintains its own isolated metrics that never mix with other runs
2. **Separate State**: State changes in one run do not affect other concurrent runs
3. **Unique Job IDs**: Job IDs uniquely identify runs without collision
4. **Database Isolation**: Database records for different runs are properly isolated

```python
# Run property tests
pytest backend/tests/test_multi_run_isolation.py -v
```

## Usage Examples

### Example 1: Monitor Active Runs

```python
from database import get_db
from services.multi_run_service import get_multi_run_manager

manager = get_multi_run_manager()
db = next(get_db())

# Get all active runs
active_runs = manager.get_active_runs(db)

for run in active_runs:
    print(f"Job: {run.job_id}")
    print(f"Status: {run.status}")
    print(f"Progress: {run.progress_percent:.1f}%")
    print(f"Loss: {run.current_loss}")
    print()
```

### Example 2: Filter Run History

```python
from datetime import datetime, timedelta
from services.multi_run_service import RunFilter

# Get completed runs from last 7 days
filter_criteria = RunFilter(
    status=["completed"],
    date_from=datetime.now() - timedelta(days=7)
)

runs = manager.get_run_history(db, filter_criteria)

for run in runs:
    print(f"{run.job_id}: {run.duration_seconds}s, Loss: {run.final_loss}")
```

### Example 3: Dashboard Statistics

```python
# Get statistics for dashboard
stats = manager.get_concurrent_stats(db)

print(f"Active Runs: {stats.total_active}")
print(f"  Running: {stats.running}")
print(f"  Paused: {stats.paused}")
print(f"\nCompleted: {stats.total_completed}")
print(f"Failed: {stats.total_failed}")
print(f"\nProviders:")
for provider, count in stats.active_providers.items():
    print(f"  {provider}: {count}")
```

## Implementation Details

### Synchronization Strategy

The system uses a synchronization strategy to keep the in-memory orchestrator state in sync with the database:

1. **On Query**: When querying runs, the system first syncs all jobs from the orchestrator to the database
2. **On Update**: When updating a job, the system immediately syncs to the database
3. **Periodic Sync**: Background tasks can periodically sync all jobs

### Isolation Guarantees

The system ensures isolation through:

1. **Unique Job IDs**: Each run has a globally unique job_id
2. **Separate Metrics Storage**: Metrics are stored per-job in both memory and database
3. **Independent State Machines**: Each job has its own state machine
4. **Database Constraints**: Unique constraints on job_id prevent collisions

### Performance Considerations

- **Pagination**: Run history queries support pagination to handle large datasets
- **Indexing**: Database indexes on job_id, status, and started_at for fast queries
- **Lazy Loading**: Detailed run information is loaded only when requested
- **Batch Operations**: Multiple runs can be synced in a single database transaction

## Testing

### Unit Tests

```bash
# Run all multi-run tests
pytest backend/tests/test_multi_run_isolation.py -v

# Run specific test
pytest backend/tests/test_multi_run_isolation.py::test_concurrent_runs_have_isolated_metrics -v
```

### Property-Based Tests

The property tests use Hypothesis to generate random test cases:

- **50 examples** for isolated metrics test
- **30 examples** for separate state test
- **30 examples** for unique job IDs test
- **30 examples** for database isolation test

## Future Enhancements

1. **Real-time Updates**: WebSocket support for real-time run updates
2. **Run Groups**: Group related runs together
3. **Run Templates**: Save and reuse run configurations
4. **Advanced Filtering**: More sophisticated query capabilities
5. **Run Comparison**: Side-by-side comparison of multiple runs
6. **Export/Import**: Export run history and import for analysis

## Related Documentation

- [Training Orchestration Service](./training-orchestrator.md)
- [Database Schema](../../backend/database.py)
- [API Documentation](./api-documentation.md)
