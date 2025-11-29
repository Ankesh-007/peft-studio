"""
Training Quality Analysis Service

Analyzes completed training runs and provides quality scores with improvement suggestions.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class SuggestionPriority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SuggestionCategory(str, Enum):
    CONVERGENCE = "convergence"
    OVERFITTING = "overfitting"
    UNDERFITTING = "underfitting"
    EFFICIENCY = "efficiency"
    STABILITY = "stability"


@dataclass
class ImprovementSuggestion:
    """Represents a specific improvement suggestion for training."""
    category: SuggestionCategory
    description: str
    priority: SuggestionPriority
    action: Optional[str] = None


@dataclass
class TrainingResult:
    """Represents the results of a completed training run."""
    final_loss: float
    initial_loss: float
    epochs_completed: int
    total_steps: int
    best_val_loss: Optional[float] = None
    convergence_achieved: bool = False
    gradient_norm_stable: bool = True
    loss_history: Optional[List[float]] = None
    val_loss_history: Optional[List[float]] = None
    learning_rate_history: Optional[List[float]] = None


@dataclass
class QualityAnalysis:
    """Represents the quality analysis of a training run."""
    quality_score: float  # 0-100
    improvement_suggestions: List[ImprovementSuggestion]
    metrics_summary: Dict[str, Any]
    overall_assessment: str


def analyze_training_quality(training_result: TrainingResult) -> QualityAnalysis:
    """
    Analyze training quality and provide improvement suggestions.
    
    Args:
        training_result: The completed training run results
        
    Returns:
        QualityAnalysis with score and suggestions
    """
    suggestions = []
    metrics_summary = {}
    
    # Calculate loss reduction
    loss_reduction = (training_result.initial_loss - training_result.final_loss) / training_result.initial_loss
    metrics_summary['loss_reduction'] = loss_reduction
    metrics_summary['loss_reduction_percent'] = loss_reduction * 100
    
    # Initialize quality score
    quality_score = 50.0  # Base score
    
    # Factor 1: Loss Reduction (0-30 points)
    if loss_reduction > 0.8:
        quality_score += 30
    elif loss_reduction > 0.6:
        quality_score += 25
    elif loss_reduction > 0.4:
        quality_score += 20
    elif loss_reduction > 0.2:
        quality_score += 10
    else:
        quality_score += 5
        suggestions.append(ImprovementSuggestion(
            category=SuggestionCategory.CONVERGENCE,
            description="Loss reduction is low. Consider training for more epochs or adjusting the learning rate.",
            priority=SuggestionPriority.HIGH,
            action="Increase epochs or adjust learning rate"
        ))
    
    # Factor 2: Convergence (0-25 points)
    if training_result.convergence_achieved:
        quality_score += 25
        metrics_summary['convergence_status'] = 'achieved'
    else:
        quality_score += 10
        metrics_summary['convergence_status'] = 'not_achieved'
        
        # Check if loss is still decreasing
        if training_result.loss_history and len(training_result.loss_history) > 10:
            recent_losses = training_result.loss_history[-10:]
            if recent_losses[0] > recent_losses[-1]:
                suggestions.append(ImprovementSuggestion(
                    category=SuggestionCategory.CONVERGENCE,
                    description="Loss is still decreasing. Training for more epochs may improve results.",
                    priority=SuggestionPriority.MEDIUM,
                    action="Increase number of epochs"
                ))
    
    # Factor 3: Stability (0-20 points)
    if training_result.gradient_norm_stable:
        quality_score += 20
        metrics_summary['stability'] = 'stable'
    else:
        quality_score += 5
        metrics_summary['stability'] = 'unstable'
        suggestions.append(ImprovementSuggestion(
            category=SuggestionCategory.STABILITY,
            description="Gradient norms were unstable. Consider enabling gradient clipping or reducing learning rate.",
            priority=SuggestionPriority.HIGH,
            action="Enable gradient clipping"
        ))
    
    # Factor 4: Overfitting Detection (0-15 points)
    if training_result.best_val_loss is not None:
        val_gap = abs(training_result.final_loss - training_result.best_val_loss) / training_result.best_val_loss
        
        if val_gap < 0.1:
            quality_score += 15
            metrics_summary['overfitting_risk'] = 'low'
        elif val_gap < 0.3:
            quality_score += 10
            metrics_summary['overfitting_risk'] = 'moderate'
            suggestions.append(ImprovementSuggestion(
                category=SuggestionCategory.OVERFITTING,
                description="Moderate gap between training and validation loss. Consider adding regularization.",
                priority=SuggestionPriority.MEDIUM,
                action="Add dropout or weight decay"
            ))
        else:
            quality_score += 0
            metrics_summary['overfitting_risk'] = 'high'
            suggestions.append(ImprovementSuggestion(
                category=SuggestionCategory.OVERFITTING,
                description="Large gap between training and validation loss indicates overfitting. Increase regularization or use more training data.",
                priority=SuggestionPriority.HIGH,
                action="Increase dropout rate or add more training data"
            ))
    else:
        quality_score += 10
        metrics_summary['overfitting_risk'] = 'unknown'
    
    # Factor 5: Efficiency (0-10 points)
    if training_result.epochs_completed > 0:
        loss_per_epoch = loss_reduction / training_result.epochs_completed
        
        if loss_per_epoch > 0.1:
            quality_score += 10
            metrics_summary['efficiency'] = 'high'
        elif loss_per_epoch > 0.05:
            quality_score += 7
            metrics_summary['efficiency'] = 'moderate'
        else:
            quality_score += 3
            metrics_summary['efficiency'] = 'low'
            suggestions.append(ImprovementSuggestion(
                category=SuggestionCategory.EFFICIENCY,
                description="Training efficiency is low. Consider increasing learning rate or batch size.",
                priority=SuggestionPriority.LOW,
                action="Increase learning rate"
            ))
    
    # Ensure score is within bounds
    quality_score = max(0, min(100, quality_score))
    
    # Generate overall assessment
    if quality_score >= 90:
        overall_assessment = "Excellent training run with strong convergence and stability."
    elif quality_score >= 75:
        overall_assessment = "Good training run with room for minor improvements."
    elif quality_score >= 60:
        overall_assessment = "Acceptable training run, but several areas could be optimized."
    elif quality_score >= 40:
        overall_assessment = "Training run completed but with significant issues. Review suggestions carefully."
    else:
        overall_assessment = "Training run had major issues. Consider adjusting hyperparameters significantly."
    
    # Sort suggestions by priority
    priority_order = {SuggestionPriority.HIGH: 0, SuggestionPriority.MEDIUM: 1, SuggestionPriority.LOW: 2}
    suggestions.sort(key=lambda s: priority_order[s.priority])
    
    return QualityAnalysis(
        quality_score=quality_score,
        improvement_suggestions=suggestions,
        metrics_summary=metrics_summary,
        overall_assessment=overall_assessment
    )


def generate_quality_report(analysis: QualityAnalysis) -> str:
    """
    Generate a human-readable quality report.
    
    Args:
        analysis: The quality analysis results
        
    Returns:
        Formatted report string
    """
    report = []
    report.append(f"Training Quality Score: {analysis.quality_score:.1f}/100")
    report.append(f"\n{analysis.overall_assessment}\n")
    
    if analysis.improvement_suggestions:
        report.append("\nImprovement Suggestions:")
        for i, suggestion in enumerate(analysis.improvement_suggestions, 1):
            priority_emoji = "🔴" if suggestion.priority == SuggestionPriority.HIGH else "🟡" if suggestion.priority == SuggestionPriority.MEDIUM else "🟢"
            report.append(f"\n{i}. {priority_emoji} [{suggestion.category.value.upper()}] {suggestion.description}")
            if suggestion.action:
                report.append(f"   → Action: {suggestion.action}")
    
    report.append("\n\nMetrics Summary:")
    for key, value in analysis.metrics_summary.items():
        report.append(f"  • {key.replace('_', ' ').title()}: {value}")
    
    return "\n".join(report)
