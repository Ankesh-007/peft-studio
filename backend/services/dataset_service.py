"""
Dataset Processing Service for validating, analyzing, and preparing training data.
Supports CSV, JSON, JSONL, and TXT formats with quality checks and error detection.
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
import csv
import logging
import re
from collections import Counter

logger = logging.getLogger(__name__)


class DatasetFormat(str, Enum):
    """Supported dataset formats"""
    CSV = "csv"
    JSON = "json"
    JSONL = "jsonl"
    TXT = "txt"
    UNKNOWN = "unknown"


class ValidationLevel(str, Enum):
    """Validation message severity levels"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationResult:
    """Result of dataset validation"""
    field: str
    level: ValidationLevel
    message: str
    suggestion: Optional[str] = None
    auto_fixable: bool = False
    line_number: Optional[int] = None


@dataclass
class DatasetStatistics:
    """Statistical analysis of dataset"""
    num_samples: int
    total_tokens: int
    avg_tokens_per_sample: float
    min_tokens: int
    max_tokens: int
    token_length_distribution: Dict[str, int]  # Buckets: 0-100, 100-500, 500-1000, 1000+
    avg_chars_per_sample: float
    empty_samples: int
    duplicate_samples: int
    unique_samples: int
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses"""
        return {
            "num_samples": self.num_samples,
            "total_tokens": self.total_tokens,
            "avg_tokens_per_sample": self.avg_tokens_per_sample,
            "min_tokens": self.min_tokens,
            "max_tokens": self.max_tokens,
            "token_length_distribution": self.token_length_distribution,
            "avg_chars_per_sample": self.avg_chars_per_sample,
            "empty_samples": self.empty_samples,
            "duplicate_samples": self.duplicate_samples,
            "unique_samples": self.unique_samples
        }


@dataclass
class DatasetPreview:
    """Preview of dataset samples"""
    samples: List[Dict[str, Any]]
    total_count: int
    format: DatasetFormat
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses"""
        return {
            "samples": self.samples,
            "total_count": self.total_count,
            "format": self.format.value
        }


@dataclass
class QualityReport:
    """Dataset quality assessment"""
    overall_score: float  # 0-100
    issues: List[ValidationResult]
    recommendations: List[str]
    is_ready_for_training: bool
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses"""
        return {
            "overall_score": self.overall_score,
            "issues": [
                {
                    "field": issue.field,
                    "level": issue.level.value,
                    "message": issue.message,
                    "suggestion": issue.suggestion,
                    "auto_fixable": issue.auto_fixable,
                    "line_number": issue.line_number
                }
                for issue in self.issues
            ],
            "recommendations": self.recommendations,
            "is_ready_for_training": self.is_ready_for_training
        }


class DatasetService:
    """Service for dataset processing and validation"""
    
    def __init__(self):
        logger.info("DatasetService initialized")
        self._format_detectors = {
            DatasetFormat.CSV: self._is_csv,
            DatasetFormat.JSON: self._is_json,
            DatasetFormat.JSONL: self._is_jsonl,
            DatasetFormat.TXT: self._is_txt
        }
    
    def detect_format(self, file_path: str) -> DatasetFormat:
        """
        Detect the format of a dataset file.
        
        Args:
            file_path: Path to the dataset file
            
        Returns:
            DatasetFormat enum value
        """
        path = Path(file_path)
        
        if not path.exists():
            logger.error(f"File not found: {file_path}")
            return DatasetFormat.UNKNOWN
        
        # First try extension-based detection
        extension = path.suffix.lower()
        if extension == '.csv':
            if self._is_csv(file_path):
                return DatasetFormat.CSV
        elif extension == '.json':
            # Could be JSON or JSONL - check JSONL first as it's more specific
            if self._is_jsonl(file_path):
                return DatasetFormat.JSONL
            elif self._is_json(file_path):
                return DatasetFormat.JSON
        elif extension == '.jsonl':
            if self._is_jsonl(file_path):
                return DatasetFormat.JSONL
        elif extension == '.txt':
            if self._is_txt(file_path):
                return DatasetFormat.TXT
        
        # If extension-based detection fails, try content-based detection
        # Order matters: check more specific formats first
        detection_order = [
            (DatasetFormat.JSONL, self._is_jsonl),
            (DatasetFormat.JSON, self._is_json),
            (DatasetFormat.CSV, self._is_csv),
            (DatasetFormat.TXT, self._is_txt),
        ]
        
        for format_type, detector in detection_order:
            try:
                if detector(file_path):
                    logger.info(f"Detected format: {format_type.value}")
                    return format_type
            except Exception as e:
                logger.debug(f"Format detection failed for {format_type.value}: {str(e)}")
                continue
        
        logger.warning(f"Could not detect format for: {file_path}")
        return DatasetFormat.UNKNOWN
    
    def _is_csv(self, file_path: str) -> bool:
        """Check if file is valid CSV"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Read first few lines
                sample = f.read(4096)
            
            if not sample.strip():
                return False
            
            lines = sample.splitlines()
            if len(lines) < 2:  # Need at least header + one data row
                return False
            
            # Try to parse as CSV
            dialect = csv.Sniffer().sniff(sample)
            
            # CSV should have delimiters (comma, tab, etc.)
            if not hasattr(dialect, 'delimiter'):
                return False
            
            # Check if delimiter appears consistently
            delimiter = dialect.delimiter
            first_line_count = lines[0].count(delimiter)
            
            # Header should have at least one delimiter (2+ columns)
            if first_line_count == 0:
                return False
            
            # Check if subsequent lines have similar delimiter counts
            consistent_lines = 0
            for line in lines[1:min(10, len(lines))]:
                if abs(line.count(delimiter) - first_line_count) <= 1:
                    consistent_lines += 1
            
            # At least 50% of lines should have consistent delimiter count
            return consistent_lines >= len(lines[1:min(10, len(lines))]) * 0.5
            
        except Exception:
            return False
    
    def _is_json(self, file_path: str) -> bool:
        """Check if file is valid JSON (single object or array)"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Valid JSON should be a list or dict
            return isinstance(data, (list, dict))
            
        except Exception:
            return False
    
    def _is_jsonl(self, file_path: str) -> bool:
        """Check if file is valid JSONL (JSON Lines)"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if not lines:
                return False
            
            # Each non-empty line should be valid JSON
            valid_lines = 0
            non_empty_lines = 0
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                non_empty_lines += 1
                try:
                    obj = json.loads(line)
                    # JSONL should have objects, not arrays or primitives
                    if isinstance(obj, dict):
                        valid_lines += 1
                    else:
                        return False
                except json.JSONDecodeError:
                    return False
            
            # All non-empty lines should be valid JSON objects
            return valid_lines > 0 and valid_lines == non_empty_lines
            
        except Exception:
            return False
    
    def _is_txt(self, file_path: str) -> bool:
        """Check if file is plain text"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Try to read the file as text
                f.read(4096)
            return True
        except UnicodeDecodeError:
            return False
        except Exception:
            return False
    
    def validate_dataset(
        self,
        file_path: str,
        format: Optional[DatasetFormat] = None
    ) -> List[ValidationResult]:
        """
        Validate dataset structure and quality.
        
        Args:
            file_path: Path to the dataset file
            format: Optional format hint (will auto-detect if not provided)
            
        Returns:
            List of ValidationResult objects
        """
        results = []
        
        # Detect format if not provided
        if format is None:
            format = self.detect_format(file_path)
        
        if format == DatasetFormat.UNKNOWN:
            results.append(ValidationResult(
                field="format",
                level=ValidationLevel.ERROR,
                message="Could not detect dataset format",
                suggestion="Ensure file is in CSV, JSON, JSONL, or TXT format",
                auto_fixable=False
            ))
            return results
        
        # Format-specific validation
        if format == DatasetFormat.CSV:
            results.extend(self._validate_csv(file_path))
        elif format == DatasetFormat.JSON:
            results.extend(self._validate_json(file_path))
        elif format == DatasetFormat.JSONL:
            results.extend(self._validate_jsonl(file_path))
        elif format == DatasetFormat.TXT:
            results.extend(self._validate_txt(file_path))
        
        # Common validation checks
        results.extend(self._validate_common(file_path, format))
        
        return results
    
    def _validate_csv(self, file_path: str) -> List[ValidationResult]:
        """Validate CSV format"""
        results = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames
                
                if not fieldnames:
                    results.append(ValidationResult(
                        field="structure",
                        level=ValidationLevel.ERROR,
                        message="CSV file has no headers",
                        suggestion="Add column headers to the first row",
                        auto_fixable=False
                    ))
                    return results
                
                # Check for required fields (common patterns)
                has_text_field = any(
                    field.lower() in ['text', 'content', 'input', 'prompt', 'instruction']
                    for field in fieldnames
                )
                
                if not has_text_field:
                    results.append(ValidationResult(
                        field="columns",
                        level=ValidationLevel.WARNING,
                        message="No standard text field found (text, content, input, prompt, instruction)",
                        suggestion="Ensure your CSV has a column containing the training text",
                        auto_fixable=False
                    ))
                
                # Check for empty rows
                empty_rows = 0
                row_count = 0
                for i, row in enumerate(reader, start=2):  # Start at 2 (after header)
                    row_count += 1
                    if all(not value.strip() for value in row.values()):
                        empty_rows += 1
                        if empty_rows <= 3:  # Report first 3 empty rows
                            results.append(ValidationResult(
                                field="data",
                                level=ValidationLevel.WARNING,
                                message=f"Empty row found",
                                suggestion="Remove empty rows from the dataset",
                                auto_fixable=True,
                                line_number=i
                            ))
                
                if empty_rows > 3:
                    results.append(ValidationResult(
                        field="data",
                        level=ValidationLevel.WARNING,
                        message=f"Found {empty_rows} empty rows total",
                        suggestion="Remove all empty rows from the dataset",
                        auto_fixable=True
                    ))
                
        except Exception as e:
            results.append(ValidationResult(
                field="format",
                level=ValidationLevel.ERROR,
                message=f"Error reading CSV file: {str(e)}",
                suggestion="Check file encoding and CSV format",
                auto_fixable=False
            ))
        
        return results
    
    def _validate_json(self, file_path: str) -> List[ValidationResult]:
        """Validate JSON format"""
        results = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                results.append(ValidationResult(
                    field="structure",
                    level=ValidationLevel.ERROR,
                    message="JSON file must contain an array of objects",
                    suggestion="Wrap your data in a JSON array: [{...}, {...}]",
                    auto_fixable=False
                ))
                return results
            
            if len(data) == 0:
                results.append(ValidationResult(
                    field="data",
                    level=ValidationLevel.ERROR,
                    message="JSON array is empty",
                    suggestion="Add training samples to the array",
                    auto_fixable=False
                ))
                return results
            
            # Check first item structure
            first_item = data[0]
            if not isinstance(first_item, dict):
                results.append(ValidationResult(
                    field="structure",
                    level=ValidationLevel.ERROR,
                    message="JSON array items must be objects",
                    suggestion="Each item should be a JSON object with key-value pairs",
                    auto_fixable=False
                ))
            
        except json.JSONDecodeError as e:
            results.append(ValidationResult(
                field="format",
                level=ValidationLevel.ERROR,
                message=f"Invalid JSON syntax: {str(e)}",
                suggestion="Fix JSON syntax errors (check for missing commas, brackets, quotes)",
                auto_fixable=False
            ))
        except Exception as e:
            results.append(ValidationResult(
                field="format",
                level=ValidationLevel.ERROR,
                message=f"Error reading JSON file: {str(e)}",
                suggestion="Check file encoding and JSON format",
                auto_fixable=False
            ))
        
        return results
    
    def _validate_jsonl(self, file_path: str) -> List[ValidationResult]:
        """Validate JSONL format"""
        results = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if len(lines) == 0:
                results.append(ValidationResult(
                    field="data",
                    level=ValidationLevel.ERROR,
                    message="JSONL file is empty",
                    suggestion="Add training samples (one JSON object per line)",
                    auto_fixable=False
                ))
                return results
            
            invalid_lines = []
            for i, line in enumerate(lines, start=1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    obj = json.loads(line)
                    if not isinstance(obj, dict):
                        invalid_lines.append(i)
                        if len(invalid_lines) <= 3:
                            results.append(ValidationResult(
                                field="structure",
                                level=ValidationLevel.ERROR,
                                message=f"Line {i} is not a JSON object",
                                suggestion="Each line must be a valid JSON object",
                                auto_fixable=False,
                                line_number=i
                            ))
                except json.JSONDecodeError:
                    invalid_lines.append(i)
                    if len(invalid_lines) <= 3:
                        results.append(ValidationResult(
                            field="format",
                            level=ValidationLevel.ERROR,
                            message=f"Line {i} has invalid JSON syntax",
                            suggestion="Fix JSON syntax on this line",
                            auto_fixable=False,
                            line_number=i
                        ))
            
            if len(invalid_lines) > 3:
                results.append(ValidationResult(
                    field="format",
                    level=ValidationLevel.ERROR,
                    message=f"Found {len(invalid_lines)} lines with invalid JSON",
                    suggestion="Fix all JSON syntax errors in the file",
                    auto_fixable=False
                ))
        
        except Exception as e:
            results.append(ValidationResult(
                field="format",
                level=ValidationLevel.ERROR,
                message=f"Error reading JSONL file: {str(e)}",
                suggestion="Check file encoding",
                auto_fixable=False
            ))
        
        return results
    
    def _validate_txt(self, file_path: str) -> List[ValidationResult]:
        """Validate TXT format"""
        results = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.strip():
                results.append(ValidationResult(
                    field="data",
                    level=ValidationLevel.ERROR,
                    message="Text file is empty",
                    suggestion="Add training text to the file",
                    auto_fixable=False
                ))
                return results
            
            # Check for reasonable line breaks
            lines = content.split('\n')
            if len(lines) < 10:
                results.append(ValidationResult(
                    field="structure",
                    level=ValidationLevel.WARNING,
                    message=f"File has only {len(lines)} lines",
                    suggestion="For better training, consider having more samples (one per line or paragraph)",
                    auto_fixable=False
                ))
        
        except UnicodeDecodeError:
            results.append(ValidationResult(
                field="encoding",
                level=ValidationLevel.ERROR,
                message="File encoding is not UTF-8",
                suggestion="Convert file to UTF-8 encoding",
                auto_fixable=False
            ))
        except Exception as e:
            results.append(ValidationResult(
                field="format",
                level=ValidationLevel.ERROR,
                message=f"Error reading text file: {str(e)}",
                suggestion="Check file encoding and format",
                auto_fixable=False
            ))
        
        return results
    
    def _validate_common(
        self,
        file_path: str,
        format: DatasetFormat
    ) -> List[ValidationResult]:
        """Common validation checks across all formats"""
        results = []
        
        # Check file size
        path = Path(file_path)
        size_mb = path.stat().st_size / (1024 * 1024)
        
        if size_mb > 1000:  # 1GB
            results.append(ValidationResult(
                field="size",
                level=ValidationLevel.WARNING,
                message=f"Large dataset file ({size_mb:.1f} MB)",
                suggestion="Consider splitting into smaller files for faster processing",
                auto_fixable=False
            ))
        
        if size_mb < 0.01:  # 10KB
            results.append(ValidationResult(
                field="size",
                level=ValidationLevel.WARNING,
                message=f"Very small dataset file ({size_mb:.2f} MB)",
                suggestion="Ensure you have enough training data for effective fine-tuning",
                auto_fixable=False
            ))
        
        return results
    
    def analyze_statistics(
        self,
        file_path: str,
        format: Optional[DatasetFormat] = None
    ) -> DatasetStatistics:
        """
        Analyze dataset statistics.
        
        Args:
            file_path: Path to the dataset file
            format: Optional format hint
            
        Returns:
            DatasetStatistics object
        """
        if format is None:
            format = self.detect_format(file_path)
        
        samples = self._load_samples(file_path, format)
        
        if not samples:
            return DatasetStatistics(
                num_samples=0,
                total_tokens=0,
                avg_tokens_per_sample=0.0,
                min_tokens=0,
                max_tokens=0,
                token_length_distribution={},
                avg_chars_per_sample=0.0,
                empty_samples=0,
                duplicate_samples=0,
                unique_samples=0
            )
        
        # Extract text from samples
        texts = []
        for sample in samples:
            text = self._extract_text_from_sample(sample)
            texts.append(text)
        
        # Calculate statistics
        token_counts = [self._estimate_token_count(text) for text in texts]
        char_counts = [len(text) for text in texts]
        
        # Token length distribution
        distribution = {
            "0-100": sum(1 for t in token_counts if 0 <= t < 100),
            "100-500": sum(1 for t in token_counts if 100 <= t < 500),
            "500-1000": sum(1 for t in token_counts if 500 <= t < 1000),
            "1000+": sum(1 for t in token_counts if t >= 1000)
        }
        
        # Duplicates
        text_counter = Counter(texts)
        duplicates = sum(count - 1 for count in text_counter.values() if count > 1)
        unique = len(text_counter)
        
        # Empty samples
        empty = sum(1 for text in texts if not text.strip())
        
        return DatasetStatistics(
            num_samples=len(samples),
            total_tokens=sum(token_counts),
            avg_tokens_per_sample=sum(token_counts) / len(token_counts) if token_counts else 0.0,
            min_tokens=min(token_counts) if token_counts else 0,
            max_tokens=max(token_counts) if token_counts else 0,
            token_length_distribution=distribution,
            avg_chars_per_sample=sum(char_counts) / len(char_counts) if char_counts else 0.0,
            empty_samples=empty,
            duplicate_samples=duplicates,
            unique_samples=unique
        )
    
    def generate_preview(
        self,
        file_path: str,
        format: Optional[DatasetFormat] = None,
        num_samples: int = 5
    ) -> DatasetPreview:
        """
        Generate a preview of the dataset.
        
        Args:
            file_path: Path to the dataset file
            format: Optional format hint
            num_samples: Number of samples to include in preview
            
        Returns:
            DatasetPreview object
        """
        if format is None:
            format = self.detect_format(file_path)
        
        samples = self._load_samples(file_path, format, limit=num_samples)
        total_count = self._count_samples(file_path, format)
        
        return DatasetPreview(
            samples=samples,
            total_count=total_count,
            format=format
        )
    
    def check_quality(
        self,
        file_path: str,
        format: Optional[DatasetFormat] = None
    ) -> QualityReport:
        """
        Perform comprehensive quality check on dataset.
        
        Args:
            file_path: Path to the dataset file
            format: Optional format hint
            
        Returns:
            QualityReport object
        """
        if format is None:
            format = self.detect_format(file_path)
        
        # Run validation
        issues = self.validate_dataset(file_path, format)
        
        # Get statistics
        stats = self.analyze_statistics(file_path, format)
        
        # Calculate quality score
        score = 100.0
        recommendations = []
        
        # Deduct points for errors and warnings
        for issue in issues:
            if issue.level == ValidationLevel.ERROR:
                score -= 20
            elif issue.level == ValidationLevel.WARNING:
                score -= 5
        
        # Check sample count
        if stats.num_samples < 100:
            score -= 10
            recommendations.append(
                f"Dataset has only {stats.num_samples} samples. "
                "Consider adding more data (recommended: 500+ samples)"
            )
        
        # Check for duplicates
        if stats.duplicate_samples > stats.num_samples * 0.1:
            score -= 10
            recommendations.append(
                f"High duplicate rate ({stats.duplicate_samples} duplicates). "
                "Consider removing duplicate samples"
            )
        
        # Check for empty samples
        if stats.empty_samples > 0:
            score -= 5
            recommendations.append(
                f"Found {stats.empty_samples} empty samples. Remove them before training"
            )
        
        # Check token distribution
        if stats.avg_tokens_per_sample < 10:
            score -= 10
            recommendations.append(
                "Average sample length is very short. Consider using longer, more detailed examples"
            )
        
        if stats.max_tokens > 4096:
            recommendations.append(
                f"Some samples exceed 4096 tokens (max: {stats.max_tokens}). "
                "They may be truncated during training"
            )
        
        # Ensure score is in valid range
        score = max(0.0, min(100.0, score))
        
        # Determine if ready for training
        has_errors = any(issue.level == ValidationLevel.ERROR for issue in issues)
        is_ready = not has_errors and score >= 60.0 and stats.num_samples >= 10
        
        if not is_ready and not has_errors:
            recommendations.append(
                "Dataset quality is below recommended threshold. "
                "Address the issues above to improve training results"
            )
        
        return QualityReport(
            overall_score=score,
            issues=issues,
            recommendations=recommendations,
            is_ready_for_training=is_ready
        )
    
    def _load_samples(
        self,
        file_path: str,
        format: DatasetFormat,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Load samples from dataset file"""
        samples = []
        
        try:
            if format == DatasetFormat.CSV:
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for i, row in enumerate(reader):
                        if limit and i >= limit:
                            break
                        samples.append(dict(row))
            
            elif format == DatasetFormat.JSON:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if isinstance(data, list):
                    samples = data[:limit] if limit else data
            
            elif format == DatasetFormat.JSONL:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for i, line in enumerate(f):
                        if limit and i >= limit:
                            break
                        line = line.strip()
                        if line:
                            samples.append(json.loads(line))
            
            elif format == DatasetFormat.TXT:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                for i, line in enumerate(lines):
                    if limit and i >= limit:
                        break
                    if line.strip():
                        samples.append({"text": line.strip()})
        
        except Exception as e:
            logger.error(f"Error loading samples: {str(e)}")
        
        return samples
    
    def _count_samples(self, file_path: str, format: DatasetFormat) -> int:
        """Count total number of samples in dataset"""
        try:
            if format == DatasetFormat.CSV:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return sum(1 for _ in csv.DictReader(f))
            
            elif format == DatasetFormat.JSON:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return len(data) if isinstance(data, list) else 0
            
            elif format == DatasetFormat.JSONL:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return sum(1 for line in f if line.strip())
            
            elif format == DatasetFormat.TXT:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return sum(1 for line in f if line.strip())
        
        except Exception as e:
            logger.error(f"Error counting samples: {str(e)}")
            return 0
    
    def _extract_text_from_sample(self, sample: Dict[str, Any]) -> str:
        """Extract text content from a sample"""
        # Try common field names
        text_fields = ['text', 'content', 'input', 'prompt', 'instruction', 'question', 'answer']
        
        for field in text_fields:
            if field in sample:
                value = sample[field]
                if isinstance(value, str):
                    return value
        
        # If no standard field found, concatenate all string values
        texts = []
        for value in sample.values():
            if isinstance(value, str):
                texts.append(value)
        
        return ' '.join(texts)
    
    def _estimate_token_count(self, text: str) -> int:
        """Estimate token count (rough approximation)"""
        # Simple approximation: ~4 characters per token on average
        # This is a rough estimate; actual tokenization would be more accurate
        return len(text) // 4


# Singleton instance
_dataset_service_instance = None


def get_dataset_service() -> DatasetService:
    """Get singleton instance of DatasetService"""
    global _dataset_service_instance
    if _dataset_service_instance is None:
        _dataset_service_instance = DatasetService()
    return _dataset_service_instance
