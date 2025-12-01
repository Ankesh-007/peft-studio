# Bundle Size Optimization Guide

This document describes the bundle size optimizations implemented for PEFT Studio.

## Current Optimizations

### 1. Code Splitting

**Implementation:**
- Lazy loading for all major routes and heavy components
- Manual chunk splitting for vendor libraries
- Separate chunks for React, UI libraries, and utilities

**Configuration in `vite.config.ts`:**
```typescript
rollupOptions: {
  output: {
    manualChunks: {
      'react-vendor': ['react', 'react-dom'],
      'ui-vendor': ['lucide-react', 'recharts'],
      'utils': ['clsx', 'tailwind-merge'],
    },
  },
}
```

### 2. Lazy Loading

**Components using lazy loading:**
- Dashboard
- TrainingWizard
- ContextualHelpPanel
- WelcomeScreen
- SetupWizard
- GuidedTour

**Implementation:**
```typescript
const Dashboard = lazy(() => import('./components/Dashboard'));
```

### 3. Tree Shaking

**Enabled by default in Vite with:**
- ES modules
- Named imports
- Dead code elimination via Terser

### 4. Minification

**Configuration:**
- Terser minification enabled
- Console.log removal in production
- Debugger statements removed
- Source maps disabled for production

### 5. Image Optimization

**Guidelines for adding images:**

1. **Convert to WebP format:**
   ```bash
   # Using imagemagick
   convert input.png -quality 85 output.webp
   
   # Using cwebp
   cwebp -q 85 input.png -o output.webp
   ```

2. **Generate multiple sizes:**
   ```bash
   # Small (mobile)
   cwebp -resize 640 0 -q 85 input.png -o output-sm.webp
   
   # Medium (tablet)
   cwebp -resize 1024 0 -q 85 input.png -o output-md.webp
   
   # Large (desktop)
   cwebp -resize 1920 0 -q 85 input.png -o output-lg.webp
   ```

3. **Use responsive images in components:**
   ```tsx
   <picture>
     <source srcSet="/images/hero-sm.webp" media="(max-width: 640px)" />
     <source srcSet="/images/hero-md.webp" media="(max-width: 1024px)" />
     <source srcSet="/images/hero-lg.webp" media="(min-width: 1025px)" />
     <img src="/images/hero.webp" alt="Hero" loading="lazy" />
   </picture>
   ```

### 6. Font Optimization

**Current approach:**
- Using system fonts via Tailwind CSS
- No custom fonts loaded by default

**If custom fonts are needed:**

1. **Subset fonts to include only used characters:**
   ```bash
   # Using pyftsubset (from fonttools)
   pyftsubset font.ttf \
     --output-file=font-subset.woff2 \
     --flavor=woff2 \
     --layout-features='*' \
     --unicodes="U+0020-007F"  # Basic Latin
   ```

2. **Use font-display: swap:**
   ```css
   @font-face {
     font-family: 'CustomFont';
     src: url('/fonts/custom-subset.woff2') format('woff2');
     font-display: swap;
   }
   ```

3. **Preload critical fonts:**
   ```html
   <link rel="preload" href="/fonts/custom-subset.woff2" as="font" type="font/woff2" crossorigin>
   ```

## Bundle Analysis

### Running the analyzer:

```bash
npm run build:analyze
```

This will:
1. Build the production bundle
2. Generate a visual report at `dist/stats.html`
3. Open the report in your browser

### Testing bundle size:

```bash
npm run test:bundle
```

This runs the property test that ensures the bundle stays under 200MB.

## Bundle Size Targets

- **Total bundle size:** < 200MB (hard limit)
- **Individual JS chunks:** < 1MB (recommended)
- **Vendor chunks:** < 500KB each (recommended)
- **Usage warning threshold:** 80% of budget (160MB)

## Monitoring

The bundle size is automatically tested in CI/CD via the property test:
- `src/test/bundle-size-constraint.test.ts`

This test will fail if:
- Total bundle size exceeds 200MB
- More than 30% of chunks are larger than 1MB

## Future Optimizations

### Potential improvements:

1. **Dynamic imports for routes:**
   - Implement React Router with lazy loading
   - Load routes on demand

2. **Component-level code splitting:**
   - Split large components into smaller chunks
   - Use dynamic imports for modals and dialogs

3. **Dependency optimization:**
   - Replace heavy libraries with lighter alternatives
   - Use tree-shakeable versions of libraries

4. **Asset optimization:**
   - Implement image CDN
   - Use progressive image loading
   - Implement blur-up placeholders

5. **CSS optimization:**
   - PurgeCSS for unused styles
   - Critical CSS extraction
   - CSS modules for better tree shaking

## Troubleshooting

### Bundle size increased unexpectedly:

1. Run the bundle analyzer to identify large chunks
2. Check for:
   - New heavy dependencies
   - Duplicate dependencies
   - Unused code not being tree-shaken
   - Large assets (images, fonts)

### Chunk size warnings:

1. Review the manual chunks configuration
2. Consider splitting large vendor chunks
3. Use dynamic imports for heavy components

### Build performance issues:

1. Disable source maps in production
2. Use esbuild for faster builds
3. Enable caching in CI/CD

## Resources

- [Vite Build Optimizations](https://vitejs.dev/guide/build.html)
- [Rollup Code Splitting](https://rollupjs.org/guide/en/#code-splitting)
- [Web.dev: Optimize Bundle Size](https://web.dev/reduce-javascript-payloads-with-code-splitting/)
- [WebP Image Format](https://developers.google.com/speed/webp)
