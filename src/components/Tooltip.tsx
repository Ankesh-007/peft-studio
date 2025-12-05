import { HelpCircle } from "lucide-react";
import React, { useState } from "react";

import { getTooltip } from "../config/tooltips";

interface TooltipProps {
  configKey: string;
  children?: React.ReactNode;
  className?: string;
}

/**
 * Tooltip component that displays plain-language explanations for configuration settings
 */
export const Tooltip: React.FC<TooltipProps> = ({ configKey, children, className = "" }) => {
  const [isVisible, setIsVisible] = useState(false);
  const tooltipData = getTooltip(configKey);

  if (!tooltipData) {
    return <>{children}</>;
  }

  return (
    <div className={`relative inline-block ${className}`}>
      <div
        className="inline-flex items-center gap-1 cursor-help"
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
        data-testid={`tooltip-trigger-${configKey}`}
      >
        {children}
        <HelpCircle className="w-4 h-4 text-gray-400 hover:text-gray-600" />
      </div>

      {isVisible && (
        <div
          className="absolute z-50 w-80 p-4 bg-white border border-gray-200 rounded-lg shadow-lg -top-2 left-full ml-2"
          data-testid={`tooltip-content-${configKey}`}
        >
          <div className="text-sm font-semibold text-gray-900 mb-2">{tooltipData.title}</div>
          <div className="text-sm text-gray-600 mb-2">{tooltipData.description}</div>
          {tooltipData.example && (
            <div className="text-xs text-gray-500 italic border-t border-gray-100 pt-2">
              <span className="font-medium">Example:</span> {tooltipData.example}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Tooltip;
