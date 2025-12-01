/**
 * Optimized Model Grid Component
 * 
 * Heavily optimized version of ModelGrid with:
 * - React.memo for preventing unnecessary re-renders
 * - useMemo for expensive computations
 * - Virtual scrolling for large datasets
 * - RequestAnimationFrame for smooth interactions
 * 
 * Requirements: 14.3
 */

import React, { memo, useMemo, useCallback, useState, useRef, useEffect } from 'react';
import { FixedSizeGrid as Grid } from 'react-window';
import { ModelMetadata } from '../types/model';
import { throttleRAF } from '../lib/performance';

interface OptimizedModelGridProps {
  models: ModelMetadata[];
  view: 'grid' | 'list';
  onModelClick: (model: ModelMetadata) => void;
  onAddToComparison?: (model: ModelMetadata) => void;
  comparisonModels?: ModelMetadata[];
}

// Memoized model card component
const ModelCard = memo<{
  model: ModelMetadata;
  onClick: () => void;
  onAddToComparison?: () => void;
  isInComparison: boolean;
}>(({ model, onClick, onAddToComparison, isInComparison }) => {
  return (
    <div
      className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 hover:shadow-lg transition-shadow cursor-pointer"
      onClick={onClick}
    >
      <div className="flex items-start justify-between mb-2">
        <h3 className="font-semibold text-gray-900 dark:text-white truncate flex-1">
          {model.model_name}
        </h3>
        {onAddToComparison && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onAddToComparison();
            }}
            disabled={isInComparison}
            className={`ml-2 px-2 py-1 text-xs rounded ${
              isInComparison
                ? 'bg-gray-200 text-gray-500 cursor-not-allowed'
                : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
            }`}
          >
            {isInComparison ? 'Added' : 'Compare'}
          </button>
        )}
      </div>
      
      <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
        by {model.author}
      </p>
      
      <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
        <span className="px-2 py-0.5 bg-gray-100 dark:bg-gray-700 rounded">
          {model.registry}
        </span>
        {model.downloads && (
          <span>↓ {formatNumber(model.downloads)}</span>
        )}
        {model.likes && (
          <span>♥ {formatNumber(model.likes)}</span>
        )}
      </div>
      
      {model.tags && model.tags.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {model.tags.slice(0, 3).map((tag, idx) => (
            <span
              key={idx}
              className="px-2 py-0.5 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 text-xs rounded"
            >
              {tag}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}, (prevProps, nextProps) => {
  // Custom comparison function for memo
  return (
    prevProps.model.model_id === nextProps.model.model_id &&
    prevProps.isInComparison === nextProps.isInComparison
  );
});

ModelCard.displayName = 'ModelCard';

// Memoized list item component
const ModelListItem = memo<{
  model: ModelMetadata;
  onClick: () => void;
  onAddToComparison?: () => void;
  isInComparison: boolean;
}>(({ model, onClick, onAddToComparison, isInComparison }) => {
  return (
    <div
      className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-4 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer"
      onClick={onClick}
    >
      <div className="flex items-center justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3">
            <h3 className="font-semibold text-gray-900 dark:text-white truncate">
              {model.model_name}
            </h3>
            <span className="px-2 py-0.5 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 text-xs rounded">
              {model.registry}
            </span>
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            by {model.author}
          </p>
        </div>
        
        <div className="flex items-center gap-4 ml-4">
          {model.downloads && (
            <div className="text-sm text-gray-600 dark:text-gray-400">
              <span className="font-medium">{formatNumber(model.downloads)}</span>
              <span className="ml-1">downloads</span>
            </div>
          )}
          
          {onAddToComparison && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onAddToComparison();
              }}
              disabled={isInComparison}
              className={`px-3 py-1 text-sm rounded ${
                isInComparison
                  ? 'bg-gray-200 text-gray-500 cursor-not-allowed'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              {isInComparison ? 'Added' : 'Compare'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}, (prevProps, nextProps) => {
  return (
    prevProps.model.model_id === nextProps.model.model_id &&
    prevProps.isInComparison === nextProps.isInComparison
  );
});

ModelListItem.displayName = 'ModelListItem';

// Helper function memoized outside component
const formatNumber = (num: number): string => {
  if (num >= 1000000) {
    return `${(num / 1000000).toFixed(1)}M`;
  }
  if (num >= 1000) {
    return `${(num / 1000).toFixed(1)}K`;
  }
  return num.toString();
};

export const OptimizedModelGrid: React.FC<OptimizedModelGridProps> = memo(({
  models,
  view,
  onModelClick,
  onAddToComparison,
  comparisonModels = []
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [containerSize, setContainerSize] = useState({ width: 0, height: 0 });

  // Memoize comparison model IDs set for O(1) lookup
  const comparisonModelIds = useMemo(() => {
    return new Set(comparisonModels.map(m => m.model_id));
  }, [comparisonModels]);

  // Memoize callbacks to prevent re-renders
  const handleModelClick = useCallback((model: ModelMetadata) => {
    onModelClick(model);
  }, [onModelClick]);

  const handleAddToComparison = useCallback((model: ModelMetadata) => {
    if (onAddToComparison) {
      onAddToComparison(model);
    }
  }, [onAddToComparison]);

  // Throttled resize handler using RAF
  const handleResize = useMemo(() => {
    return throttleRAF(() => {
      if (containerRef.current) {
        setContainerSize({
          width: containerRef.current.offsetWidth,
          height: containerRef.current.offsetHeight
        });
      }
    });
  }, []);

  // Update container size on mount and resize
  useEffect(() => {
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [handleResize]);

  // Calculate grid dimensions
  const gridConfig = useMemo(() => {
    if (view === 'grid') {
      const columnWidth = 280;
      const rowHeight = 200;
      const columnCount = Math.max(1, Math.floor(containerSize.width / columnWidth));
      const rowCount = Math.ceil(models.length / columnCount);
      
      return { columnWidth, rowHeight, columnCount, rowCount };
    } else {
      const rowHeight = 80;
      const rowCount = models.length;
      
      return { columnWidth: containerSize.width, rowHeight, columnCount: 1, rowCount };
    }
  }, [view, containerSize.width, models.length]);

  // Render cell for virtual grid
  const Cell = useCallback(({ columnIndex, rowIndex, style }: any) => {
    const index = view === 'grid'
      ? rowIndex * gridConfig.columnCount + columnIndex
      : rowIndex;
    
    if (index >= models.length) {
      return null;
    }

    const model = models[index];
    const isInComparison = comparisonModelIds.has(model.model_id);

    return (
      <div style={style} className="p-2">
        {view === 'grid' ? (
          <ModelCard
            model={model}
            onClick={() => handleModelClick(model)}
            onAddToComparison={onAddToComparison ? () => handleAddToComparison(model) : undefined}
            isInComparison={isInComparison}
          />
        ) : (
          <ModelListItem
            model={model}
            onClick={() => handleModelClick(model)}
            onAddToComparison={onAddToComparison ? () => handleAddToComparison(model) : undefined}
            isInComparison={isInComparison}
          />
        )}
      </div>
    );
  }, [models, view, gridConfig.columnCount, comparisonModelIds, handleModelClick, handleAddToComparison, onAddToComparison]);

  if (models.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        No models to display
      </div>
    );
  }

  return (
    <div ref={containerRef} className="w-full h-full">
      {containerSize.width > 0 && containerSize.height > 0 && (
        <Grid
          columnCount={gridConfig.columnCount}
          columnWidth={gridConfig.columnWidth}
          height={Math.min(containerSize.height, 800)}
          rowCount={gridConfig.rowCount}
          rowHeight={gridConfig.rowHeight}
          width={containerSize.width}
        >
          {Cell}
        </Grid>
      )}
    </div>
  );
});

OptimizedModelGrid.displayName = 'OptimizedModelGrid';

export default OptimizedModelGrid;
