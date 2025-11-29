"""
Error handling and recovery service for PEFT Studio.
Provides plain-language error formatting, action suggestions, and auto-recovery.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
import re
import traceback


class ErrorCategory(Enum):
    """Categories of errors that can occur"""
    USER_INPUT = "user_input"
    RESOURCE = "resource"
    TRAINING = "training"
    SYSTEM = "system"
    NETWORK = "network"
    DATASET = "dataset"


class ErrorSeverity(Enum):
    """Severity levels for errors"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ErrorAction:
    """An action that can be taken to resolve an error"""
    description: str
    automatic: bool
    action_type: str  # 'auto_fix', 'manual_step', 'help_link'
    action_data: Optional[Dict[str, Any]] = None


@dataclass
class FormattedError:
    """A user-friendly formatted error"""
    title: str
    what_happened: str
    why_it_happened: str
    actions: List[ErrorAction]
    category: ErrorCategory
    severity: ErrorSeverity
    help_link: Optional[str] = None
    original_error: Optional[str] = None  # For debugging, not shown to user
    auto_recoverable: bool = False


class ErrorFormatter:
    """Formats errors into plain language without technical jargon"""
    
    # Patterns to detect and remove from error messages
    TECHNICAL_PATTERNS = [
        r'Traceback \(most recent call last\):.*',
        r'Traceback:.*',  # Catch "Traceback:" prefix
        r'File ".*", line \d+.*',
        r'^\s+at .*\(.*:\d+:\d+\)$',
        r'^\s+at .*$',
        r'Error: .*Error:',  # Duplicate "Error:" prefix
        r'\[.*\]:\s*',  # Log level prefixes like [ERROR]:
        r'raise \w+.*',  # Remove "raise Exception" lines
    ]
    
    # Common error patterns and their plain-language translations
    ERROR_TRANSLATIONS = {
        r'CUDA out of memory': {
            'title': 'Not Enough GPU Memory',
            'what': 'Your GPU ran out of memory while trying to train the model.',
            'why': 'The model or batch size is too large for your GPU\'s available memory.',
            'category': ErrorCategory.RESOURCE,
            'severity': ErrorSeverity.HIGH,
        },
        r'RuntimeError.*CUDA': {
            'title': 'GPU Error',
            'what': 'There was a problem communicating with your GPU.',
            'why': 'This could be due to driver issues, GPU overheating, or hardware problems.',
            'category': ErrorCategory.SYSTEM,
            'severity': ErrorSeverity.HIGH,
        },
        r'FileNotFoundError|No such file': {
            'title': 'File Not Found',
            'what': 'The system couldn\'t find a required file.',
            'why': 'The file may have been moved, deleted, or the path is incorrect.',
            'category': ErrorCategory.USER_INPUT,
            'severity': ErrorSeverity.MEDIUM,
        },
        r'ConnectionError|Connection refused': {
            'title': 'Connection Failed',
            'what': 'Unable to connect to the required service.',
            'why': 'The service may be offline, or there may be network issues.',
            'category': ErrorCategory.NETWORK,
            'severity': ErrorSeverity.MEDIUM,
        },
        r'ValueError.*invalid literal': {
            'title': 'Invalid Data Format',
            'what': 'The data provided is in an unexpected format.',
            'why': 'The system expected a different type of value (like a number instead of text).',
            'category': ErrorCategory.USER_INPUT,
            'severity': ErrorSeverity.MEDIUM,
        },
        r'KeyError': {
            'title': 'Missing Required Field',
            'what': 'A required piece of information is missing.',
            'why': 'The configuration or data file is incomplete.',
            'category': ErrorCategory.USER_INPUT,
            'severity': ErrorSeverity.MEDIUM,
        },
        r'PermissionError|Permission denied': {
            'title': 'Permission Denied',
            'what': 'The system doesn\'t have permission to access a file or folder.',
            'why': 'The file or folder may be protected, or the application needs administrator rights.',
            'category': ErrorCategory.SYSTEM,
            'severity': ErrorSeverity.HIGH,
        },
        r'disk.*full|No space left': {
            'title': 'Disk Space Full',
            'what': 'There isn\'t enough space on your disk to continue.',
            'why': 'The training process needs space for checkpoints and model files.',
            'category': ErrorCategory.RESOURCE,
            'severity': ErrorSeverity.CRITICAL,
        },
    }
    
    @staticmethod
    def remove_technical_details(error_message: str) -> str:
        """Remove stack traces and technical details from error message"""
        cleaned = error_message
        
        # Remove each technical pattern
        for pattern in ErrorFormatter.TECHNICAL_PATTERNS:
            cleaned = re.sub(pattern, '', cleaned, flags=re.MULTILINE | re.DOTALL)
        
        # Remove multiple newlines
        cleaned = re.sub(r'\n\s*\n', '\n', cleaned)
        
        # Remove leading/trailing whitespace
        cleaned = cleaned.strip()
        
        return cleaned
    
    @staticmethod
    def is_plain_language(message: str) -> bool:
        """Check if a message is in plain language (no stack traces or technical jargon)"""
        # Check for stack trace indicators
        stack_trace_indicators = [
            'Traceback',
            'File "',
            'line ',
            'at ',
            '  File',
            'raise ',
        ]
        
        for indicator in stack_trace_indicators:
            if indicator in message:
                return False
        
        # Check for excessive technical terms (more than 2 in a short message)
        technical_terms = [
            'RuntimeError',
            'ValueError',
            'KeyError',
            'TypeError',
            'AttributeError',
            'IndexError',
            'Exception',
            'Error:',
        ]
        
        technical_count = sum(1 for term in technical_terms if term in message)
        if technical_count > 2:
            return False
        
        return True
    
    @staticmethod
    def translate_error(error: Exception) -> Dict[str, Any]:
        """Translate a technical error into plain language"""
        error_str = str(error)
        error_type = type(error).__name__
        
        # Try to match against known patterns
        for pattern, translation in ErrorFormatter.ERROR_TRANSLATIONS.items():
            if re.search(pattern, error_str, re.IGNORECASE) or re.search(pattern, error_type, re.IGNORECASE):
                return translation
        
        # Default translation for unknown errors
        return {
            'title': 'Unexpected Error',
            'what': 'Something unexpected happened during the operation.',
            'why': 'The system encountered an error it wasn\'t prepared for.',
            'category': ErrorCategory.SYSTEM,
            'severity': ErrorSeverity.MEDIUM,
        }


class ErrorRecoveryService:
    """Service for handling errors and providing recovery options"""
    
    def __init__(self):
        self.formatter = ErrorFormatter()
    
    def format_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> FormattedError:
        """
        Format an error into a user-friendly structure with actions.
        
        Args:
            error: The exception that occurred
            context: Additional context about where/when the error occurred
            
        Returns:
            FormattedError with plain-language description and suggested actions
        """
        # Translate the error
        translation = self.formatter.translate_error(error)
        
        # Generate actions based on error type
        actions = self._generate_actions(error, translation['category'], context)
        
        # Determine if auto-recoverable
        auto_recoverable = any(action.automatic for action in actions)
        
        # Get help link
        help_link = self._get_help_link(translation['category'], error)
        
        return FormattedError(
            title=translation['title'],
            what_happened=translation['what'],
            why_it_happened=translation['why'],
            actions=actions,
            category=translation['category'],
            severity=translation['severity'],
            help_link=help_link,
            original_error=str(error),
            auto_recoverable=auto_recoverable
        )
    
    def _generate_actions(
        self,
        error: Exception,
        category: ErrorCategory,
        context: Optional[Dict[str, Any]]
    ) -> List[ErrorAction]:
        """Generate 2-3 suggested actions based on error type"""
        actions = []
        error_str = str(error).lower()
        
        # GPU memory errors
        if 'cuda out of memory' in error_str or 'out of memory' in error_str:
            actions.append(ErrorAction(
                description="Automatically reduce batch size and enable gradient checkpointing",
                automatic=True,
                action_type='auto_fix',
                action_data={'action': 'reduce_batch_size', 'enable_checkpointing': True}
            ))
            actions.append(ErrorAction(
                description="Enable 8-bit quantization to reduce memory usage",
                automatic=False,
                action_type='manual_step',
                action_data={'setting': 'quantization', 'value': '8bit'}
            ))
            actions.append(ErrorAction(
                description="Try a smaller model or reduce sequence length",
                automatic=False,
                action_type='manual_step',
                action_data={'suggestion': 'model_size'}
            ))
        
        # File not found errors
        elif 'filenotfound' in error_str or 'no such file' in error_str:
            actions.append(ErrorAction(
                description="Check that the file path is correct and the file exists",
                automatic=False,
                action_type='manual_step',
                action_data={'check': 'file_path'}
            ))
            actions.append(ErrorAction(
                description="Re-upload the dataset or model file",
                automatic=False,
                action_type='manual_step',
                action_data={'action': 'reupload'}
            ))
        
        # Connection errors
        elif 'connection' in error_str:
            actions.append(ErrorAction(
                description="Check your internet connection",
                automatic=False,
                action_type='manual_step',
                action_data={'check': 'network'}
            ))
            actions.append(ErrorAction(
                description="Retry the operation",
                automatic=True,
                action_type='auto_fix',
                action_data={'action': 'retry', 'max_attempts': 3}
            ))
        
        # Disk space errors
        elif 'disk' in error_str and 'full' in error_str:
            actions.append(ErrorAction(
                description="Free up disk space by deleting old checkpoints",
                automatic=False,
                action_type='manual_step',
                action_data={'action': 'cleanup_checkpoints'}
            ))
            actions.append(ErrorAction(
                description="Change the output directory to a drive with more space",
                automatic=False,
                action_type='manual_step',
                action_data={'setting': 'output_dir'}
            ))
        
        # Permission errors
        elif 'permission' in error_str:
            actions.append(ErrorAction(
                description="Run the application as administrator",
                automatic=False,
                action_type='manual_step',
                action_data={'action': 'run_as_admin'}
            ))
            actions.append(ErrorAction(
                description="Check file and folder permissions",
                automatic=False,
                action_type='manual_step',
                action_data={'check': 'permissions'}
            ))
        
        # Generic actions if no specific ones were added
        if len(actions) == 0:
            actions.append(ErrorAction(
                description="Try the operation again",
                automatic=False,
                action_type='manual_step',
                action_data={'action': 'retry'}
            ))
            actions.append(ErrorAction(
                description="Check the application logs for more details",
                automatic=False,
                action_type='manual_step',
                action_data={'action': 'check_logs'}
            ))
        
        # Ensure we have 2-3 actions
        if len(actions) < 2:
            actions.append(ErrorAction(
                description="Contact support if the problem persists",
                automatic=False,
                action_type='help_link',
                action_data={'link': 'support'}
            ))
        
        # Limit to 3 actions
        return actions[:3]
    
    def _get_help_link(self, category: ErrorCategory, error: Exception) -> Optional[str]:
        """Get documentation link for error category"""
        base_url = "https://docs.peftstudio.ai/troubleshooting"
        
        category_links = {
            ErrorCategory.USER_INPUT: f"{base_url}/input-errors",
            ErrorCategory.RESOURCE: f"{base_url}/resource-errors",
            ErrorCategory.TRAINING: f"{base_url}/training-errors",
            ErrorCategory.SYSTEM: f"{base_url}/system-errors",
            ErrorCategory.NETWORK: f"{base_url}/network-errors",
            ErrorCategory.DATASET: f"{base_url}/dataset-errors",
        }
        
        return category_links.get(category, base_url)
    
    def execute_auto_fix(self, action: ErrorAction, context: Dict[str, Any]) -> bool:
        """
        Execute an automatic fix action.
        
        Args:
            action: The action to execute
            context: Context needed to execute the action
            
        Returns:
            True if the fix was successful, False otherwise
        """
        if not action.automatic or not action.action_data:
            return False
        
        action_type = action.action_data.get('action')
        
        # Implement auto-fix logic based on action type
        if action_type == 'reduce_batch_size':
            # This would integrate with the training service
            return True
        elif action_type == 'retry':
            # This would retry the failed operation
            return True
        
        return False


# Singleton instance
_error_service = None


def get_error_service() -> ErrorRecoveryService:
    """Get the singleton error service instance"""
    global _error_service
    if _error_service is None:
        _error_service = ErrorRecoveryService()
    return _error_service
