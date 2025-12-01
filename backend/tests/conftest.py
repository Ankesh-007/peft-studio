"""
Pytest configuration and fixtures for multi-run management tests.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import tempfile
import shutil
from pathlib import Path

from backend.database import Base
from backend.services.training_orchestration_service import TrainingOrchestrator
from backend.services.multi_run_service import MultiRunManager


@pytest.fixture(scope="function")
def temp_dirs():
    """Create temporary directories for test artifacts"""
    checkpoint_dir = tempfile.mkdtemp(prefix="test_checkpoints_")
    artifacts_dir = tempfile.mkdtemp(prefix="test_artifacts_")
    
    yield {
        'checkpoint_dir': checkpoint_dir,
        'artifacts_dir': artifacts_dir
    }
    
    # Cleanup
    shutil.rmtree(checkpoint_dir, ignore_errors=True)
    shutil.rmtree(artifacts_dir, ignore_errors=True)


@pytest.fixture(scope="function")
def test_db():
    """Create a test database"""
    # Use in-memory SQLite for tests
    engine = create_engine('sqlite:///:memory:', echo=False)
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    yield SessionLocal
    
    # Cleanup
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_db):
    """Create a database session for tests"""
    session = test_db()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def orchestrator(temp_dirs):
    """Create a fresh TrainingOrchestrator instance for tests"""
    return TrainingOrchestrator(
        checkpoint_base_dir=temp_dirs['checkpoint_dir'],
        artifacts_base_dir=temp_dirs['artifacts_dir']
    )


@pytest.fixture(scope="function")
def multi_run_manager(orchestrator):
    """Create a MultiRunManager instance for tests"""
    return MultiRunManager(orchestrator=orchestrator)
