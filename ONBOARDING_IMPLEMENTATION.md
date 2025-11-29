# Onboarding Flow Implementation

## Overview

The onboarding flow provides a guided introduction to PEFT Studio for first-time users, consisting of three main stages:

1. **Welcome Screen** - Feature overview and introduction
2. **Setup Wizard** - Hardware detection and sample data download
3. **Guided Tour** - Interactive walkthrough of key features

## Components

### WelcomeScreen (`src/components/onboarding/WelcomeScreen.tsx`)

The initial screen users see on their first visit.

**Features:**
- Displays 4 key features with icons and descriptions:
  - Smart Configuration
  - Real-Time Monitoring
  - Auto-Recovery
  - One-Click Export
- Two action buttons: "Get Started" and "Skip Tour"
- Animated entrance with staggered feature cards

**Props:**
- `onGetStarted: () => void` - Called when user clicks "Get Started"
- `onSkip: () => void` - Called when user clicks "Skip Tour"

### SetupWizard (`src/components/onboarding/SetupWizard.tsx`)

A 3-step wizard for initial setup.

**Steps:**
1. **Hardware Detection** - Detects GPU, CPU, and RAM
2. **Sample Dataset & Model** - Optional download of sample data
3. **Quick Preferences** - Configure notifications and settings

**Features:**
- Progress indicator showing current step
- Navigation buttons (Back/Next)
- Skip option at any point
- Auto-advance after completing certain steps

**Props:**
- `onComplete: () => void` - Called when setup is finished
- `onSkip: () => void` - Called when user skips setup

### GuidedTour (`src/components/onboarding/GuidedTour.tsx`)

Interactive tour highlighting key UI elements.

**Tour Steps:**
1. Dashboard Overview
2. Start Training button
3. Quick Actions panel
4. Training Runs list
5. System Resources chart

**Features:**
- Overlay with spotlight effect on target elements
- Tooltip with step information
- Progress dots showing current position
- Navigation controls (Back/Next/Skip)
- Automatic positioning based on target element location

**Props:**
- `isActive: boolean` - Controls tour visibility
- `onComplete: () => void` - Called when tour is finished
- `onSkip: () => void` - Called when user skips tour

## State Management

### useOnboarding Hook (`src/hooks/useOnboarding.ts`)

Manages onboarding state using localStorage.

**State:**
```typescript
{
  hasCompletedWelcome: boolean;
  hasCompletedSetup: boolean;
  hasCompletedTour: boolean;
  isFirstVisit: boolean;
}
```

**Methods:**
- `completeWelcome()` - Mark welcome screen as completed
- `completeSetup()` - Mark setup wizard as completed
- `completeTour()` - Mark guided tour as completed
- `skipOnboarding()` - Skip entire onboarding flow
- `resetOnboarding()` - Reset to first-time user state

**Computed Properties:**
- `shouldShowOnboarding` - True if welcome screen should be shown
- `shouldShowSetup` - True if setup wizard should be shown
- `shouldShowTour` - True if guided tour should be shown

## Sample Data

### Sample Dataset (`public/samples/sample-dataset.jsonl`)

A small JSONL dataset with 10 instruction-response pairs for testing.

**Format:**
```json
{"instruction": "Question or task", "input": "", "output": "Expected response"}
```

**Topics Covered:**
- General knowledge
- Programming tasks
- Science explanations
- Practical instructions

### Documentation (`public/samples/README.md`)

Comprehensive guide for using the sample dataset and creating custom datasets.

## Integration

The onboarding flow is integrated into `App.tsx`:

```typescript
// Show welcome screen on first visit
if (shouldShowOnboarding) {
  return <WelcomeScreen onGetStarted={completeWelcome} onSkip={skipOnboarding} />;
}

// Show setup wizard after welcome
if (shouldShowSetup) {
  return <SetupWizard onComplete={completeSetup} onSkip={skipOnboarding} />;
}

// Show guided tour after setup
<GuidedTour
  isActive={shouldShowTour}
  onComplete={completeTour}
  onSkip={skipOnboarding}
/>
```

## Styling

### Tour Highlight Effect

Added to `src/index.css`:

```css
.tour-highlight {
  position: relative;
  z-index: 45;
  box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.5), 0 0 0 9999px rgba(0, 0, 0, 0.6);
  border-radius: 8px;
  transition: all 0.3s ease;
}
```

### Button Size Variants

```css
.btn-sm { @apply px-12 py-6 text-small; }
.btn-lg { @apply px-24 py-12 text-body; }
```

## Data Attributes for Tour

Dashboard components are tagged with `data-tour` attributes:

- `data-tour="dashboard"` - Main dashboard container
- `data-tour="start-training"` - Start Training button
- `data-tour="quick-actions"` - Quick Actions panel
- `data-tour="training-runs"` - Training Runs list
- `data-tour="system-resources"` - System Resources chart

## Testing

Comprehensive test suite in `src/test/onboarding.test.tsx`:

**Test Coverage:**
- ✅ Welcome screen rendering and interactions
- ✅ Setup wizard step navigation
- ✅ Guided tour functionality
- ✅ useOnboarding hook state management
- ✅ localStorage persistence
- ✅ Sample dataset structure validation

**Run Tests:**
```bash
npx vitest run src/test/onboarding.test.tsx
```

## User Experience Flow

1. **First Visit:**
   - User sees Welcome Screen
   - Clicks "Get Started" or "Skip Tour"

2. **Setup (if not skipped):**
   - Hardware detection runs automatically
   - Option to download sample data
   - Configure basic preferences
   - Clicks "Complete Setup"

3. **Guided Tour (if not skipped):**
   - Interactive tour highlights key features
   - User navigates through 5 steps
   - Clicks "Finish" to complete

4. **Subsequent Visits:**
   - Onboarding is skipped
   - User goes directly to dashboard

## Resetting Onboarding

For testing or re-showing the onboarding:

```typescript
const { resetOnboarding } = useOnboarding();
resetOnboarding(); // Clears localStorage and resets state
```

Or manually clear localStorage:
```javascript
localStorage.removeItem('peft-studio-onboarding');
```

## Requirements Validation

This implementation satisfies **Requirement 1.1**:

> "WHEN a user launches the Training Wizard THEN the system SHALL display a welcome screen with clear, jargon-free language explaining the process"

**How it's met:**
- ✅ Welcome screen with clear, jargon-free language
- ✅ Feature overview with simple descriptions
- ✅ First-time setup wizard for hardware and preferences
- ✅ Sample dataset and model for testing
- ✅ Guided tour of key features
- ✅ Skip option at every stage
- ✅ State persistence across sessions

## Future Enhancements

Potential improvements for future iterations:

1. **Video Tutorials** - Embed short video clips in tour steps
2. **Interactive Demos** - Allow users to try features during tour
3. **Personalization** - Customize tour based on user's use case
4. **Progress Tracking** - Show completion percentage
5. **Tooltips** - Add contextual help throughout the app
6. **Onboarding Analytics** - Track completion rates and drop-off points
