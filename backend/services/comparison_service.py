"""
Training Run Comparison Service
Provides functionality to compare multiple training runs, generate charts,
highlight best performers, and calculate configuration differences.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class TrainingRunSummary:
    """Summary of a training run for comparison"""
    job_id: str
    model_name: str
    dataset_name: str
    
    # Final metrics
    final_loss: float
    best_val_loss: Optional[float] = None
    final_learning_rate: float = 0.0
    
    # Training info
    total_steps: int = 0
    epochs_completed: int = 0
    training_time_seconds: float = 0.0
    
    # Configuration
    config: Dict[str, Any] = field(default_factory=dict)
    
    # Quality
    quality_score: Optional[float] = None
    
    # Timestamps
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        data = asdict(self)
        if self.started_at:
            data['started_at'] = self.started_at.isoformat()
        if self.completed_at:
            data['completed_at'] = self.completed_at.isoformat()
        return data


@dataclass
class ComparisonChart:
    """Chart data for comparing training runs"""
    chart_type: str  # 'loss_curve', 'learning_rate', 'throughput', etc.
    title: str
    x_label: str
    y_label: str
    series: List[Dict[str, Any]]  # Each series has 'job_id', 'label', 'data' (list of {x, y})
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class BestPerformer:
    """Best performing run for a specific metric"""
    metric_name: str
    job_id: str
    value: float
    is_lower_better: bool  # True for loss, False for accuracy
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class ConfigDiff:
    """Difference between two configurations"""
    parameter: str
    run1_value: Any
    run2_value: Any
    is_different: bool
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class ComparisonResult:
    """Complete comparison result"""
    runs: List[TrainingRunSummary]
    charts: List[ComparisonChart]
    best_performers: List[BestPerformer]
    config_diffs: Optional[List[ConfigDiff]] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'runs': [r.to_dict() for r in self.runs],
            'charts': [c.to_dict() for c in self.charts],
            'best_performers': [b.to_dict() for b in self.best_performers],
            'config_diffs': [d.to_dict() for d in self.config_diffs] if self.config_diffs else None
        }


class ComparisonService:
    """Service for comparing training runs"""
    
    def __init__(self):
        self.runs_cache: Dict[str, TrainingRunSummary] = {}
        logger.info("ComparisonService initialized")
    
    def add_run(self, run: TrainingRunSummary) -> None:
        """
        Add a training run to the comparison cache.
        
        Args:
            run: Training run summary
        """
        self.runs_cache[run.job_id] = run
        logger.debug(f"Added run {run.job_id} to comparison cache")
    
    def get_run(self, job_id: str) -> Optional[TrainingRunSummary]:
        """
        Get a training run from cache.
        
        Args:
            job_id: Job identifier
            
        Returns:
            TrainingRunSummary or None if not found
        """
        return self.runs_cache.get(job_id)
    
    def compare_runs(
        self,
        job_ids: List[str],
        include_charts: bool = True,
        include_config_diff: bool = True
    ) -> ComparisonResult:
        """
        Compare multiple training runs.
        
        Args:
            job_ids: List of job IDs to compare (2-5 runs)
            include_charts: Whether to generate comparison charts
            include_config_diff: Whether to calculate configuration differences
            
        Returns:
            ComparisonResult with all comparison data
            
        Raises:
            ValueError: If job_ids is invalid or runs not found
        """
        # Validate input
        if not job_ids or len(job_ids) < 2:
            raise ValueError("Must provide at least 2 job IDs for comparison")
        
        if len(job_ids) > 5:
            raise ValueError("Cannot compare more than 5 runs at once")
        
        # Get runs
        runs = []
        for job_id in job_ids:
            run = self.get_run(job_id)
            if not run:
                raise ValueError(f"Run not found: {job_id}")
            runs.append(run)
        
        logger.info(f"Comparing {len(runs)} training runs")
        
        # Generate charts
        charts = []
        if include_charts:
            charts = self._generate_comparison_charts(runs)
        
        # Identify best performers
        best_performers = self._identify_best_performers(runs)
        
        # Calculate config diffs
        config_diffs = None
        if include_config_diff and len(runs) == 2:
            config_diffs = self._calculate_config_diff(runs[0], runs[1])
        
        return ComparisonResult(
            runs=runs,
            charts=charts,
            best_performers=best_performers,
            config_diffs=config_diffs
        )
    
    def _generate_comparison_charts(self, runs: List[TrainingRunSummary]) -> List[ComparisonChart]:
        """
        Generate side-by-side comparison charts.
        
        Args:
            runs: List of training runs
            
        Returns:
            List of ComparisonChart objects
        """
        charts = []
        
        # Loss comparison chart
        loss_series = []
        for run in runs:
            # In a real implementation, we would get the full loss history
            # For now, we create a simple series with start and end points
            loss_series.append({
                'job_id': run.job_id,
                'label': f"{run.model_name} ({run.job_id[:8]})",
                'data': [
                    {'x': 0, 'y': run.final_loss * 2},  # Simulated initial loss
                    {'x': run.total_steps, 'y': run.final_loss}
                ]
            })
        
        charts.append(ComparisonChart(
            chart_type='loss_curve',
            title='Training Loss Comparison',
            x_label='Steps',
            y_label='Loss',
            series=loss_series
        ))
        
        # Training time comparison (bar chart)
        time_series = [{
            'job_id': run.job_id,
            'label': f"{run.model_name} ({run.job_id[:8]})",
            'data': [{'x': run.job_id[:8], 'y': run.training_time_seconds / 3600}]  # Convert to hours
        } for run in runs]
        
        charts.append(ComparisonChart(
            chart_type='bar',
            title='Training Time Comparison',
            x_label='Run',
            y_label='Time (hours)',
            series=time_series
        ))
        
        # Quality score comparison (if available)
        if any(run.quality_score is not None for run in runs):
            quality_series = [{
                'job_id': run.job_id,
                'label': f"{run.model_name} ({run.job_id[:8]})",
                'data': [{'x': run.job_id[:8], 'y': run.quality_score or 0}]
            } for run in runs]
            
            charts.append(ComparisonChart(
                chart_type='bar',
                title='Quality Score Comparison',
                x_label='Run',
                y_label='Quality Score',
                series=quality_series
            ))
        
        logger.debug(f"Generated {len(charts)} comparison charts")
        return charts
    
    def _identify_best_performers(self, runs: List[TrainingRunSummary]) -> List[BestPerformer]:
        """
        Identify best performing runs for each metric.
        
        Args:
            runs: List of training runs
            
        Returns:
            List of BestPerformer objects
        """
        best_performers = []
        
        # Best final loss (lower is better)
        best_loss_run = min(runs, key=lambda r: r.final_loss)
        best_performers.append(BestPerformer(
            metric_name='final_loss',
            job_id=best_loss_run.job_id,
            value=best_loss_run.final_loss,
            is_lower_better=True
        ))
        
        # Best validation loss (if available)
        runs_with_val = [r for r in runs if r.best_val_loss is not None]
        if runs_with_val:
            best_val_run = min(runs_with_val, key=lambda r: r.best_val_loss)
            best_performers.append(BestPerformer(
                metric_name='best_val_loss',
                job_id=best_val_run.job_id,
                value=best_val_run.best_val_loss,
                is_lower_better=True
            ))
        
        # Fastest training time (lower is better)
        best_time_run = min(runs, key=lambda r: r.training_time_seconds)
        best_performers.append(BestPerformer(
            metric_name='training_time',
            job_id=best_time_run.job_id,
            value=best_time_run.training_time_seconds,
            is_lower_better=True
        ))
        
        # Best quality score (higher is better, if available)
        runs_with_quality = [r for r in runs if r.quality_score is not None]
        if runs_with_quality:
            best_quality_run = max(runs_with_quality, key=lambda r: r.quality_score)
            best_performers.append(BestPerformer(
                metric_name='quality_score',
                job_id=best_quality_run.job_id,
                value=best_quality_run.quality_score,
                is_lower_better=False
            ))
        
        logger.debug(f"Identified {len(best_performers)} best performers")
        return best_performers
    
    def _calculate_config_diff(
        self,
        run1: TrainingRunSummary,
        run2: TrainingRunSummary
    ) -> List[ConfigDiff]:
        """
        Calculate configuration differences between two runs.
        
        Args:
            run1: First training run
            run2: Second training run
            
        Returns:
            List of ConfigDiff objects
        """
        diffs = []
        
        # Get all unique parameter names
        all_params = set(run1.config.keys()) | set(run2.config.keys())
        
        for param in sorted(all_params):
            value1 = run1.config.get(param)
            value2 = run2.config.get(param)
            
            is_different = value1 != value2
            
            diffs.append(ConfigDiff(
                parameter=param,
                run1_value=value1,
                run2_value=value2,
                is_different=is_different
            ))
        
        logger.debug(f"Calculated {len(diffs)} configuration differences")
        return diffs
    
    def list_all_runs(self) -> List[TrainingRunSummary]:
        """
        Get all training runs in cache.
        
        Returns:
            List of all TrainingRunSummary objects
        """
        return list(self.runs_cache.values())
    
    def clear_cache(self) -> None:
        """Clear the runs cache"""
        self.runs_cache.clear()
        logger.info("Cleared comparison cache")


# Singleton instance
_comparison_service_instance = None


def get_comparison_service() -> ComparisonService:
    """Get singleton instance of ComparisonService"""
    global _comparison_service_instance
    if _comparison_service_instance is None:
        _comparison_service_instance = ComparisonService()
    return _comparison_service_instance
