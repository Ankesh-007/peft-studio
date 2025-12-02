import { X, Book, Keyboard, HelpCircle, ExternalLink } from "lucide-react";
import React, { useState } from "react";

import { getAllTooltipKeys, getTooltip } from "../config/tooltips";

interface ContextualHelpPanelProps {
  isOpen: boolean;
  onClose: () => void;
  currentContext?: string;
}

/**
 * Contextual help panel that provides comprehensive help information
 * including tooltips, keyboard shortcuts, and documentation links
 */
export const ContextualHelpPanel: React.FC<ContextualHelpPanelProps> = ({
  isOpen,
  onClose,
  currentContext,
}) => {
  const [activeTab, setActiveTab] = useState<"tooltips" | "shortcuts" | "docs">(
    "tooltips",
  );

  if (!isOpen) return null;

  const tooltipKeys = getAllTooltipKeys();
  const contextualTooltips = currentContext
    ? tooltipKeys.filter((key) => key.startsWith(currentContext))
    : tooltipKeys;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center gap-2">
            <HelpCircle className="w-6 h-6 text-blue-600" />
            <h2 className="text-2xl font-bold text-gray-900">
              Help & Documentation
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            aria-label="Close help panel"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-200">
          <button
            onClick={() => setActiveTab("tooltips")}
            className={`flex items-center gap-2 px-6 py-3 font-medium transition-colors ${
              activeTab === "tooltips"
                ? "text-blue-600 border-b-2 border-blue-600"
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            <Book className="w-4 h-4" />
            Configuration Guide
          </button>
          <button
            onClick={() => setActiveTab("shortcuts")}
            className={`flex items-center gap-2 px-6 py-3 font-medium transition-colors ${
              activeTab === "shortcuts"
                ? "text-blue-600 border-b-2 border-blue-600"
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            <Keyboard className="w-4 h-4" />
            Keyboard Shortcuts
          </button>
          <button
            onClick={() => setActiveTab("docs")}
            className={`flex items-center gap-2 px-6 py-3 font-medium transition-colors ${
              activeTab === "docs"
                ? "text-blue-600 border-b-2 border-blue-600"
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            <ExternalLink className="w-4 h-4" />
            Documentation
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {activeTab === "tooltips" && (
            <div className="space-y-4">
              <div className="mb-4">
                <p className="text-gray-600">
                  {currentContext
                    ? `Showing help for ${currentContext} settings`
                    : "Browse all configuration settings and their explanations"}
                </p>
              </div>
              {contextualTooltips.map((key) => {
                const tooltip = getTooltip(key);
                if (!tooltip) return null;

                return (
                  <div
                    key={key}
                    className="p-4 bg-gray-50 rounded-lg border border-gray-200"
                    data-testid={`help-item-${key}`}
                  >
                    <h3 className="font-semibold text-gray-900 mb-2">
                      {tooltip.title}
                    </h3>
                    <p className="text-sm text-gray-700 mb-2">
                      {tooltip.description}
                    </p>
                    {tooltip.example && (
                      <div className="text-xs text-gray-600 bg-white p-2 rounded border border-gray-200">
                        <span className="font-medium">Example:</span>{" "}
                        {tooltip.example}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {activeTab === "shortcuts" && (
            <div className="space-y-6">
              <div className="mb-4">
                <p className="text-gray-600">
                  Use these keyboard shortcuts to navigate PEFT Studio more
                  efficiently
                </p>
              </div>

              <div className="space-y-4">
                <div>
                  <h3 className="font-semibold text-gray-900 mb-3">General</h3>
                  <div className="space-y-2">
                    <ShortcutItem
                      keys={["Ctrl", "/"]}
                      description="Open command palette"
                    />
                    <ShortcutItem
                      keys={["Ctrl", "H"]}
                      description="Toggle this help panel"
                    />
                    <ShortcutItem
                      keys={["Esc"]}
                      description="Close dialogs and panels"
                    />
                  </div>
                </div>

                <div>
                  <h3 className="font-semibold text-gray-900 mb-3">
                    Training Wizard
                  </h3>
                  <div className="space-y-2">
                    <ShortcutItem
                      keys={["Ctrl", "N"]}
                      description="Start new training wizard"
                    />
                    <ShortcutItem
                      keys={["Ctrl", "Enter"]}
                      description="Proceed to next step"
                    />
                    <ShortcutItem
                      keys={["Ctrl", "Backspace"]}
                      description="Go back to previous step"
                    />
                  </div>
                </div>

                <div>
                  <h3 className="font-semibold text-gray-900 mb-3">
                    Training Monitor
                  </h3>
                  <div className="space-y-2">
                    <ShortcutItem
                      keys={["Space"]}
                      description="Pause/Resume training"
                    />
                    <ShortcutItem
                      keys={["Ctrl", "S"]}
                      description="Save checkpoint"
                    />
                    <ShortcutItem
                      keys={["Ctrl", "Q"]}
                      description="Stop training"
                    />
                  </div>
                </div>

                <div>
                  <h3 className="font-semibold text-gray-900 mb-3">
                    Navigation
                  </h3>
                  <div className="space-y-2">
                    <ShortcutItem
                      keys={["Ctrl", "1"]}
                      description="Go to Dashboard"
                    />
                    <ShortcutItem
                      keys={["Ctrl", "2"]}
                      description="Go to Training Wizard"
                    />
                    <ShortcutItem
                      keys={["Ctrl", "3"]}
                      description="Go to Inference Playground"
                    />
                    <ShortcutItem
                      keys={["Ctrl", "4"]}
                      description="Go to Preset Library"
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === "docs" && (
            <div className="space-y-4">
              <div className="mb-4">
                <p className="text-gray-600">
                  Access comprehensive documentation and resources
                </p>
              </div>

              <div className="space-y-3">
                <DocLink
                  title="Getting Started Guide"
                  description="Learn the basics of fine-tuning LLMs with PEFT Studio"
                  url="https://docs.peftstudio.ai/getting-started"
                />
                <DocLink
                  title="Training Wizard Tutorial"
                  description="Step-by-step guide through the training process"
                  url="https://docs.peftstudio.ai/training-wizard"
                />
                <DocLink
                  title="Dataset Preparation"
                  description="How to format and prepare your training data"
                  url="https://docs.peftstudio.ai/dataset-preparation"
                />
                <DocLink
                  title="Understanding LoRA Parameters"
                  description="Deep dive into LoRA configuration and tuning"
                  url="https://docs.peftstudio.ai/lora-parameters"
                />
                <DocLink
                  title="Hardware Requirements"
                  description="GPU, CPU, and memory requirements for different models"
                  url="https://docs.peftstudio.ai/hardware-requirements"
                />
                <DocLink
                  title="Troubleshooting Guide"
                  description="Common issues and how to resolve them"
                  url="https://docs.peftstudio.ai/troubleshooting"
                />
                <DocLink
                  title="Model Export Guide"
                  description="Export your models to HuggingFace, Ollama, and more"
                  url="https://docs.peftstudio.ai/model-export"
                />
                <DocLink
                  title="API Reference"
                  description="Complete API documentation for advanced users"
                  url="https://docs.peftstudio.ai/api-reference"
                />
                <DocLink
                  title="Community Forum"
                  description="Get help from the community and share your experiences"
                  url="https://community.peftstudio.ai"
                />
                <DocLink
                  title="GitHub Repository"
                  description="View source code, report issues, and contribute"
                  url="https://github.com/peftstudio/peftstudio"
                />
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200 bg-gray-50">
          <p className="text-sm text-gray-600 text-center">
            Press{" "}
            <kbd className="px-2 py-1 bg-white border border-gray-300 rounded text-xs">
              Ctrl+H
            </kbd>{" "}
            to toggle this help panel
          </p>
        </div>
      </div>
    </div>
  );
};

interface ShortcutItemProps {
  keys: string[];
  description: string;
}

const ShortcutItem: React.FC<ShortcutItemProps> = ({ keys, description }) => (
  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
    <span className="text-sm text-gray-700">{description}</span>
    <div className="flex items-center gap-1">
      {keys.map((key, index) => (
        <React.Fragment key={index}>
          <kbd className="px-3 py-1 bg-white border border-gray-300 rounded text-sm font-mono">
            {key}
          </kbd>
          {index < keys.length - 1 && <span className="text-gray-400">+</span>}
        </React.Fragment>
      ))}
    </div>
  </div>
);

interface DocLinkProps {
  title: string;
  description: string;
  url: string;
}

const DocLink: React.FC<DocLinkProps> = ({ title, description, url }) => (
  <a
    href={url}
    target="_blank"
    rel="noopener noreferrer"
    className="block p-4 bg-gray-50 rounded-lg border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-colors group"
    data-testid={`doc-link-${title.toLowerCase().replace(/\s+/g, "-")}`}
  >
    <div className="flex items-start justify-between">
      <div className="flex-1">
        <h3 className="font-semibold text-gray-900 group-hover:text-blue-600 mb-1">
          {title}
        </h3>
        <p className="text-sm text-gray-600">{description}</p>
      </div>
      <ExternalLink className="w-4 h-4 text-gray-400 group-hover:text-blue-600 ml-2 flex-shrink-0" />
    </div>
  </a>
);

export default ContextualHelpPanel;
