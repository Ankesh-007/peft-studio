# Notification System

The notification system provides comprehensive desktop notifications, taskbar progress indicators, and Do Not Disturb integration for PEFT Studio training events.

## Features

### 1. Progress Milestone Notifications
- Automatic notifications at 25%, 50%, 75%, and 100% completion
- Customizable messages for each milestone
- Taskbar progress indicator integration
- Completion sound on 100%

### 2. Error Notifications
- Urgent notifications for training errors
- Multiple urgency levels: low, normal, high, critical
- Automatic urgency assignment based on error type
- Always bypass Do Not Disturb settings
- Actionable buttons (View Details, Retry)

### 3. Taskbar Progress
- Real-time progress indicator in taskbar/dock
- Automatic flash on completion
- Cross-platform support (Windows, macOS, Linux)

### 4. Do Not Disturb Integration
- Respects system DND settings for progress notifications
- Critical errors always notify regardless of DND
- Platform-specific DND detection

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Training Orchestrator                   │
│  • Monitors training progress                            │
│  • Detects errors and anomalies                          │
│  • Emits notification events                             │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Notification Service (Backend)              │
│  • NotificationManager: State management                 │
│  • check_progress_milestone(): Milestone detection       │
│  • create_error_notification(): Error formatting         │
│  • check_do_not_disturb(): DND detection                 │
│  • calculate_taskbar_progress(): Progress calculation    │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  WebSocket / HTTP API                    │
│  • /ws/notifications/{job_id}: Real-time stream          │
│  • /api/notifications/{job_id}: Get all notifications    │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Electron Main Process (IPC)                 │
│  • show-notification: Desktop notification               │
│  • set-progress: Taskbar progress                        │
│  • check-dnd: DND status check                           │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│           React Frontend (NotificationHandler)           │
│  • Receives notifications via WebSocket                  │
│  • Triggers desktop notifications                        │
│  • Updates taskbar progress                              │
│  • Plays notification sounds                             │
└─────────────────────────────────────────────────────────┘
```

## Usage

### Backend: Creating Notifications

```python
from services.notification_service import (
    NotificationManager,
    ProgressUpdate,
    create_error_notification
)

# Initialize notification manager
notification_manager = NotificationManager()

# Check for progress milestones
progress_update = ProgressUpdate(
    current_step=250,
    total_steps=1000,
    previous_step=200
)

notification = notification_manager.get_next_notification(progress_update)
if notification:
    # Send notification to frontend
    send_notification(job_id, notification)

# Create error notification
error_notification = create_error_notification(
    error_message="Out of memory error occurred",
    error_type="oom_error"
)
send_notification(job_id, error_notification)
```

### Frontend: Handling Notifications

```typescript
import { NotificationHandler } from './components/NotificationHandler';

function TrainingView() {
  const [jobId, setJobId] = useState<string>();
  
  const handleNotification = (notification) => {
    console.log('Received:', notification);
    // Update UI, show toast, etc.
  };
  
  return (
    <div>
      <NotificationHandler 
        jobId={jobId}
        onNotificationReceived={handleNotification}
      />
      {/* Rest of your training UI */}
    </div>
  );
}
```

### Electron: IPC Handlers

The Electron main process provides three IPC handlers:

1. **show-notification**: Display desktop notification
2. **set-progress**: Update taskbar progress (0.0 to 1.0)
3. **check-dnd**: Check Do Not Disturb status

These are automatically called by the NotificationHandler component.

## Notification Types

### Progress Notifications
- **Type**: `NotificationType.PROGRESS`
- **Urgency**: `normal`
- **Sound**: `false` (except 100%)
- **Respects DND**: `true`
- **Milestones**: 25%, 50%, 75%, 100%

### Error Notifications
- **Type**: `NotificationType.ERROR`
- **Urgency**: `high` or `critical` (based on error type)
- **Sound**: `true`
- **Respects DND**: `false` (always notify)
- **Actions**: ["View Details", "Retry"]

### Completion Notifications
- **Type**: `NotificationType.COMPLETION`
- **Urgency**: `normal`
- **Sound**: `true`
- **Respects DND**: `true`
- **Special**: Flashes taskbar

### Warning Notifications
- **Type**: `NotificationType.WARNING`
- **Urgency**: `normal`
- **Sound**: `false`
- **Respects DND**: `true`

## Error Urgency Levels

The system automatically assigns urgency levels based on error type:

- **Critical**: `oom_error`, `cuda_error`, `system_crash`
- **High**: `loss_divergence`, `gradient_explosion`, `data_error`
- **Normal**: All other errors (can be overridden)

## Do Not Disturb Integration

### Platform Support

- **macOS**: Checks Focus/DND status via `defaults` command
- **Windows**: Checks Focus Assist via registry
- **Linux**: Checks GNOME/KDE notification settings

### Behavior

- Progress notifications respect DND settings
- Error notifications always bypass DND
- Completion notifications respect DND settings
- Warning notifications respect DND settings

## Taskbar Progress

### Platform Behavior

- **Windows**: Progress bar in taskbar button
- **macOS**: Progress bar in dock icon
- **Linux**: Progress in Unity/GNOME launcher

### States

- **0.0 - 0.99**: Active progress indicator
- **1.0**: Completion (flashes taskbar, then removes indicator)
- **-1**: Remove progress indicator

## Testing

The notification system includes comprehensive property-based tests:

```bash
# Run notification tests
python -m pytest backend/tests/test_error_notifications.py -v

# Run with coverage
python -m pytest backend/tests/test_error_notifications.py --cov=services.notification_service
```

### Test Coverage

- ✅ Error notification creation
- ✅ Urgency level assignment
- ✅ Required field validation
- ✅ Action button presence
- ✅ DND respect flag
- ✅ Progress milestone detection
- ✅ Taskbar progress calculation

## API Reference

### NotificationEvent

```python
@dataclass
class NotificationEvent:
    type: NotificationType
    title: str
    message: str
    milestone: Optional[int] = None
    urgency: str = "normal"
    sound: bool = False
    actions: Optional[List[str]] = None
    taskbar_progress: Optional[float] = None
    respect_dnd: bool = True
```

### NotificationManager

```python
class NotificationManager:
    def should_send_notification(progress_update: ProgressUpdate) -> bool
    def mark_milestone_sent(milestone: int) -> None
    def reset() -> None
    def get_next_notification(progress_update: ProgressUpdate) -> Optional[NotificationEvent]
    def update_dnd_status() -> None
    def should_respect_dnd(notification: NotificationEvent) -> bool
```

### Helper Functions

```python
def check_progress_milestone(progress_update: ProgressUpdate) -> Optional[NotificationEvent]
def create_error_notification(error_message: str, error_type: str, urgency: str) -> NotificationEvent
def create_warning_notification(warning_message: str) -> NotificationEvent
def check_do_not_disturb() -> bool
def calculate_taskbar_progress(current_step: int, total_steps: int) -> float
```

## WebSocket Protocol

### Connection

```
ws://localhost:8000/ws/notifications/{job_id}
```

### Message Format

```json
{
  "type": "notification",
  "data": {
    "type": "error",
    "title": "Training Error",
    "message": "Out of memory error occurred",
    "urgency": "critical",
    "sound": true,
    "actions": ["View Details", "Retry"],
    "taskbar_progress": 0.45,
    "respect_dnd": false
  }
}
```

## Best Practices

1. **Always register notification callbacks** before starting training
2. **Handle WebSocket reconnection** for long-running training
3. **Request notification permission** early in the app lifecycle
4. **Test notification sounds** at appropriate volume levels
5. **Respect user preferences** for notification frequency
6. **Provide clear action buttons** for error notifications
7. **Update taskbar progress** frequently for smooth animation

## Troubleshooting

### Notifications not showing

1. Check notification permissions in system settings
2. Verify WebSocket connection is established
3. Check browser console for errors
4. Ensure Electron IPC handlers are registered

### Taskbar progress not updating

1. Verify progress values are between 0.0 and 1.0
2. Check Electron main process logs
3. Ensure window is not minimized (some platforms)

### DND detection not working

1. Check platform-specific requirements
2. Verify system commands are available
3. Fall back to always showing notifications if detection fails

## Future Enhancements

- [ ] Custom notification sounds per event type
- [ ] Notification history/log
- [ ] User-configurable notification preferences
- [ ] Rich notifications with images/charts
- [ ] Notification grouping for multiple training runs
- [ ] Email/SMS notifications for long-running jobs
- [ ] Integration with Slack/Discord webhooks
