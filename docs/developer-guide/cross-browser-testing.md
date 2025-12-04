# Cross-Browser Testing Guide

## Overview

This guide outlines the cross-browser testing strategy for PEFT Studio to ensure consistent functionality across all supported browsers.

## Supported Browsers

### Desktop
- **Chrome** 90+ (Primary)
- **Firefox** 88+
- **Safari** 14+
- **Edge** 90+

### Mobile
- **Safari iOS** 14+
- **Chrome Android** 90+

## Testing Checklist

### Core Functionality

#### Navigation
- [ ] Sidebar navigation works in all browsers
- [ ] Breadcrumb navigation functions correctly
- [ ] Mobile hamburger menu opens/closes properly
- [ ] Keyboard shortcuts work (Ctrl+K, Ctrl+N, etc.)
- [ ] Back/forward browser buttons work correctly

#### Forms
- [ ] All input fields accept and validate data
- [ ] Multi-select dropdowns work correctly
- [ ] Sliders respond to mouse and keyboard input
- [ ] File upload (drag-and-drop) works
- [ ] Form submission succeeds
- [ ] Error messages display correctly

#### Real-Time Features
- [ ] WebSocket connections establish successfully
- [ ] Training metrics update in real-time
- [ ] Connection status indicator works
- [ ] Automatic reconnection functions

#### Offline Support
- [ ] Offline indicator appears when disconnected
- [ ] Operations queue while offline
- [ ] Automatic sync on reconnection
- [ ] Conflict resolution UI works

### Visual Consistency

#### Layout
- [ ] Responsive breakpoints work (768px, 1024px)
- [ ] Grid layouts render correctly
- [ ] Flexbox layouts work as expected
- [ ] Sticky headers/footers position correctly
- [ ] Modals center properly
- [ ] Tooltips appear in correct position

#### Typography
- [ ] Fonts load correctly
- [ ] Text sizes are consistent
- [ ] Line heights are appropriate
- [ ] Text doesn't overflow containers

#### Colors & Themes
- [ ] Dark theme renders correctly
- [ ] Light theme renders correctly
- [ ] Color contrast meets WCAG standards
- [ ] Gradients display smoothly
- [ ] Shadows render correctly

### Interactions

#### Mouse
- [ ] Click events fire correctly
- [ ] Hover states work
- [ ] Drag-and-drop functions
- [ ] Context menus work
- [ ] Double-click events work

#### Keyboard
- [ ] Tab navigation works
- [ ] Enter/Space activate buttons
- [ ] Arrow keys navigate lists
- [ ] Escape closes modals
- [ ] Keyboard shortcuts function

#### Touch (Mobile)
- [ ] Tap events work
- [ ] Swipe gestures function
- [ ] Pinch-to-zoom works on charts
- [ ] Touch targets are 44x44px minimum
- [ ] Scroll momentum feels natural

### Performance

#### Load Times
- [ ] Initial page load < 3s on 3G
- [ ] Code splitting reduces bundle size
- [ ] Images load progressively
- [ ] Fonts load without FOUT/FOIT

#### Runtime
- [ ] Smooth scrolling (60fps)
- [ ] No jank during animations
- [ ] Virtual scrolling handles 10,000+ items
- [ ] WebSocket messages process quickly

### Accessibility

#### Screen Readers
- [ ] NVDA (Windows) announces content correctly
- [ ] VoiceOver (Mac/iOS) works properly
- [ ] JAWS (Windows) navigates correctly
- [ ] Dynamic content is announced

#### Keyboard Navigation
- [ ] All interactive elements are reachable
- [ ] Focus indicators are visible
- [ ] Focus order is logical
- [ ] Skip links work

#### Visual
- [ ] Text scales to 200% without breaking
- [ ] High contrast mode works
- [ ] Color isn't the only indicator
- [ ] Animations respect prefers-reduced-motion

## Browser-Specific Issues

### Chrome
**Known Issues:**
- None currently

**Testing Focus:**
- WebSocket performance
- Service worker functionality
- IndexedDB operations

### Firefox
**Known Issues:**
- Flexbox gap property may need fallback for older versions

**Testing Focus:**
- CSS Grid layouts
- WebSocket reconnection
- File upload

### Safari
**Known Issues:**
- Date input styling differs from other browsers
- Backdrop-filter may have performance issues

**Testing Focus:**
- WebKit-specific CSS
- Touch events on iOS
- Service worker support

### Edge
**Known Issues:**
- None currently (Chromium-based)

**Testing Focus:**
- Legacy Edge compatibility (if needed)
- Windows-specific features

## Testing Tools

### Automated Testing

#### BrowserStack
```bash
# Run tests on BrowserStack
npm run test:browserstack
```

#### Playwright
```bash
# Run cross-browser tests
npm run test:e2e -- --project=chromium
npm run test:e2e -- --project=firefox
npm run test:e2e -- --project=webkit
```

#### Selenium Grid
```bash
# Run Selenium tests
npm run test:selenium
```

### Manual Testing

#### Local Testing
1. Install browsers locally
2. Test on actual devices when possible
3. Use browser DevTools for debugging

#### Virtual Machines
- Use VirtualBox for Windows testing on Mac
- Use Parallels for Mac testing on Windows
- Use Android Studio emulator for Android testing

### Visual Regression Testing

#### Percy
```bash
# Capture screenshots for visual comparison
npm run test:visual
```

#### Chromatic
```bash
# Test Storybook components
npm run chromatic
```

## Testing Workflow

### Pre-Release Checklist

1. **Run Automated Tests**
   ```bash
   npm run test
   npm run test:e2e
   npm run test:visual
   ```

2. **Manual Testing**
   - Test on Chrome (primary browser)
   - Test on Firefox
   - Test on Safari
   - Test on Edge
   - Test on mobile devices

3. **Accessibility Testing**
   ```bash
   npm run test:a11y
   ```

4. **Performance Testing**
   ```bash
   npm run lighthouse
   ```

5. **Document Issues**
   - Create GitHub issues for browser-specific bugs
   - Tag with browser label (chrome, firefox, safari, edge)
   - Prioritize based on browser market share

### Continuous Integration

#### GitHub Actions
```yaml
name: Cross-Browser Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        browser: [chromium, firefox, webkit]
    steps:
      - uses: actions/checkout@v2
      - name: Install dependencies
        run: npm ci
      - name: Run tests
        run: npm run test:e2e -- --project=${{ matrix.browser }}
```

## Debugging Browser Issues

### Chrome DevTools
```javascript
// Enable verbose logging
localStorage.setItem('debug', '*');

// Check WebSocket connection
console.log(webSocketManager.getStats());

// Profile performance
performance.mark('start');
// ... code to profile
performance.mark('end');
performance.measure('operation', 'start', 'end');
```

### Firefox Developer Tools
- Use Network Monitor for WebSocket debugging
- Use Performance tool for profiling
- Use Accessibility Inspector

### Safari Web Inspector
- Use Timelines for performance
- Use Storage tab for IndexedDB
- Use Console for debugging

## Common Issues & Solutions

### Issue: WebSocket Connection Fails in Safari
**Solution:** Ensure WSS (secure WebSocket) is used in production

### Issue: Flexbox Gap Not Working in Older Browsers
**Solution:** Use margin fallback
```css
.container {
  gap: 1rem;
  /* Fallback for older browsers */
  margin: -0.5rem;
}
.container > * {
  margin: 0.5rem;
}
```

### Issue: Date Input Looks Different in Safari
**Solution:** Use custom date picker component

### Issue: Smooth Scrolling Doesn't Work in Safari
**Solution:** Use JavaScript scroll behavior
```javascript
element.scrollIntoView({ behavior: 'smooth', block: 'start' });
```

## Reporting Issues

When reporting browser-specific issues:

1. **Browser & Version**: Chrome 96.0.4664.110
2. **Operating System**: Windows 11
3. **Steps to Reproduce**: Detailed steps
4. **Expected Behavior**: What should happen
5. **Actual Behavior**: What actually happens
6. **Screenshots**: Visual evidence
7. **Console Errors**: Any error messages

## Resources

- [Can I Use](https://caniuse.com/) - Browser compatibility tables
- [MDN Web Docs](https://developer.mozilla.org/) - Web standards documentation
- [BrowserStack](https://www.browserstack.com/) - Cross-browser testing platform
- [Playwright](https://playwright.dev/) - End-to-end testing framework
- [WebPageTest](https://www.webpagetest.org/) - Performance testing
