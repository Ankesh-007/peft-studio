import { ChevronRight, Home } from 'lucide-react';
import React from 'react';

import { cn } from '../lib/utils';

export interface BreadcrumbItem {
  label: string;
  path: string;
  icon?: React.ComponentType<{ className?: string }>;
}

export interface BreadcrumbsProps {
  items: BreadcrumbItem[];
  onNavigate: (path: string) => void;
  className?: string;
}

export const Breadcrumbs: React.FC<BreadcrumbsProps> = ({
  items,
  onNavigate,
  className,
}) => {
  return (
    <nav aria-label="Breadcrumb" className={cn('flex items-center space-x-2', className)}>
      <button
        onClick={() => onNavigate('/')}
        className="p-1 hover:bg-gray-100 rounded transition-colors"
        aria-label="Home"
      >
        <Home className="w-4 h-4 text-gray-500" />
      </button>

      {items.map((item, index) => {
        const isLast = index === items.length - 1;
        const Icon = item.icon;

        return (
          <React.Fragment key={item.path}>
            <ChevronRight className="w-4 h-4 text-gray-400" aria-hidden="true" />
            
            {isLast ? (
              <span className="flex items-center gap-1 text-sm font-medium text-gray-900">
                {Icon && <Icon className="w-4 h-4" />}
                {item.label}
              </span>
            ) : (
              <button
                onClick={() => onNavigate(item.path)}
                className="flex items-center gap-1 text-sm text-gray-600 hover:text-gray-900 transition-colors"
              >
                {Icon && <Icon className="w-4 h-4" />}
                {item.label}
              </button>
            )}
          </React.Fragment>
        );
      })}
    </nav>
  );
};
