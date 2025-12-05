import React, { useState, useRef } from "react";

import { getTooltip } from "../config/tooltips";

interface TechnicalTermDetectorProps {
  children: React.ReactNode;
  className?: string;
}

/**
 * Technical term detector that automatically detects and provides tooltips
 * for technical terms in text content
 */
export const TechnicalTermDetector: React.FC<TechnicalTermDetectorProps> = ({
  children,
  className = "",
}) => {
  const [hoveredTerm, setHoveredTerm] = useState<string | null>(null);
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });
  const containerRef = useRef<HTMLDivElement>(null);

  // Technical terms mapping to tooltip keys
  const technicalTerms: Record<string, string> = {
    LoRA: "lora_r",
    rank: "lora_r",
    alpha: "lora_alpha",
    dropout: "lora_dropout",
    "learning rate": "learning_rate",
    epoch: "num_epochs",
    epochs: "num_epochs",
    "batch size": "batch_size",
    "gradient accumulation": "gradient_accumulation",
    precision: "precision",
    quantization: "quantization",
    fp16: "precision",
    bf16: "precision",
    int8: "quantization",
    "8-bit": "quantization",
    "4-bit": "quantization",
    warmup: "warmup_ratio",
    scheduler: "scheduler",
    optimizer: "optimizer",
    AdamW: "optimizer",
    "weight decay": "weight_decay",
    "gradient clipping": "max_grad_norm",
    "sequence length": "max_seq_length",
    "target modules": "target_modules",
    "GPU memory": "min_gpu_memory",
    VRAM: "min_gpu_memory",
    checkpoint: "save_steps",
    validation: "eval_steps",
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    const target = e.target as HTMLElement;
    const text = target.textContent || "";

    // Check if hovering over a technical term
    let foundTerm: string | null = null;
    for (const [term, key] of Object.entries(technicalTerms)) {
      if (text.toLowerCase().includes(term.toLowerCase())) {
        foundTerm = key;
        break;
      }
    }

    if (foundTerm) {
      setHoveredTerm(foundTerm);
      setTooltipPosition({ x: e.clientX, y: e.clientY });
    } else {
      setHoveredTerm(null);
    }
  };

  const handleMouseLeave = () => {
    setHoveredTerm(null);
  };

  const tooltipData = hoveredTerm ? getTooltip(hoveredTerm) : null;

  return (
    <div
      ref={containerRef}
      className={`relative ${className}`}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
      {children}

      {tooltipData && hoveredTerm && (
        <div
          className="fixed z-50 w-80 p-4 bg-white border border-gray-200 rounded-lg shadow-xl pointer-events-none"
          style={{
            left: `${tooltipPosition.x + 10}px`,
            top: `${tooltipPosition.y + 10}px`,
          }}
          data-testid={`technical-term-tooltip-${hoveredTerm}`}
        >
          <div className="text-xs text-blue-600 font-semibold mb-1">
            TECHNICAL TERM
          </div>
          <div className="text-sm font-semibold text-gray-900 mb-2">
            {tooltipData.title}
          </div>
          <div className="text-sm text-gray-600 mb-2">
            {tooltipData.description}
          </div>
          {tooltipData.example && (
            <div className="text-xs text-gray-500 italic border-t border-gray-100 pt-2">
              <span className="font-medium">Example:</span>{" "}
              {tooltipData.example}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default TechnicalTermDetector;
