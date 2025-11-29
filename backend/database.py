from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from config import DATABASE_URL

Base = declarative_base()

class Model(Base):
    __tablename__ = 'models'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    base_model = Column(String)
    adapter_path = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    size_mb = Column(Float)
    architecture = Column(String)
    quantization = Column(String)
    metadata = Column(JSON)
    
    training_runs = relationship("TrainingRun", back_populates="model")

class Dataset(Base):
    __tablename__ = 'datasets'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    path = Column(String)
    format = Column(String)
    num_examples = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    size_mb = Column(Float)
    validation_status = Column(String)
    metadata = Column(JSON)
    
    training_runs = relationship("TrainingRun", back_populates="dataset")

class TrainingRun(Base):
    __tablename__ = 'training_runs'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    model_id = Column(Integer, ForeignKey('models.id'))
    dataset_id = Column(Integer, ForeignKey('datasets.id'))
    status = Column(String)  # running, paused, completed, failed
    config = Column(JSON)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    final_loss = Column(Float)
    best_checkpoint = Column(String)
    logs = Column(Text)
    
    model = relationship("Model", back_populates="training_runs")
    dataset = relationship("Dataset", back_populates="training_runs")

class Experiment(Base):
    __tablename__ = 'experiments'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class Configuration(Base):
    __tablename__ = 'configurations'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    type = Column(String)  # training, peft, inference
    config = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class Evaluation(Base):
    __tablename__ = 'evaluations'
    
    id = Column(Integer, primary_key=True)
    model_id = Column(Integer, ForeignKey('models.id'))
    dataset_id = Column(Integer, ForeignKey('datasets.id'))
    metrics = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

# Create engine and tables
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
