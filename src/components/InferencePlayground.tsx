import {
  Play,
  Copy,
  RotateCcw,
  Settings,
  Sparkles,
  MessageSquare,
  FileText,
  Code,
  Zap,
} from "lucide-react";
import React, { useState } from "react";

import { cn } from "../lib/utils";

interface GenerationSettings {
  temperature: number;
  topP: number;
  topK: number;
  maxTokens: number;
  repetitionPenalty: number;
  stopSequences: string;
}

const InferencePlayground: React.FC = () => {
  const [selectedModel, setSelectedModel] = useState("llama-3-finance");
  const [template, setTemplate] = useState<"chat" | "instruct" | "raw">(
    "instruct",
  );
  const [prompt, setPrompt] = useState("");
  const [output, setOutput] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [charCount, setCharCount] = useState(0);
  const [tokenCount, setTokenCount] = useState(0);

  const [settings, setSettings] = useState<GenerationSettings>({
    temperature: 0.7,
    topP: 0.9,
    topK: 50,
    maxTokens: 512,
    repetitionPenalty: 1.1,
    stopSequences: "",
  });

  const models = [
    {
      id: "llama-3-finance",
      name: "Llama-3 Finance",
      type: "Fine-tuned",
      size: "8B",
    },
    {
      id: "mistral-chat",
      name: "Mistral Chat",
      type: "Fine-tuned",
      size: "7B",
    },
    {
      id: "llama-2-base",
      name: "Llama-2 Base",
      type: "Base Model",
      size: "13B",
    },
  ];

  const templates = [
    {
      id: "chat",
      label: "Chat",
      icon: MessageSquare,
      example: "<|user|>\nHello, how are you?\n<|assistant|>\n",
    },
    {
      id: "instruct",
      label: "Instruction",
      icon: FileText,
      example: "### Instruction:\nExplain quantum computing\n\n### Response:\n",
    },
    {
      id: "raw",
      label: "Raw",
      icon: Code,
      example: "Once upon a time",
    },
  ];

  const handleGenerate = async () => {
    setIsGenerating(true);
    setOutput("");

    // Simulate generation
    const mockOutput = `Based on your prompt, here's a detailed response that demonstrates the model's capabilities. This is a simulated output that would normally come from the actual model inference.

The model has been fine-tuned on domain-specific data and can provide relevant, contextual responses. Key features include:

1. Understanding of domain terminology
2. Coherent and structured responses
3. Appropriate tone and style
4. Factual accuracy within training data

This response would continue based on the generation settings you've configured, including temperature, top-p sampling, and maximum token length.`;

    // Simulate streaming
    for (let i = 0; i < mockOutput.length; i += 3) {
      await new Promise((resolve) => setTimeout(resolve, 20));
      setOutput(mockOutput.slice(0, i + 3));
    }

    setIsGenerating(false);
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(output);
  };

  const handleReset = () => {
    setPrompt("");
    setOutput("");
    setCharCount(0);
    setTokenCount(0);
  };

  const handlePromptChange = (value: string) => {
    setPrompt(value);
    setCharCount(value.length);
    // Rough token estimation (1 token ≈ 4 characters)
    setTokenCount(Math.ceil(value.length / 4));
  };

  return (
    <div className="space-y-24">
      {/* Header */}
      <div>
        <h1 className="text-h1 mb-8">Inference Playground</h1>
        <p className="text-body text-dark-text-secondary">
          Test your fine-tuned models with custom prompts
        </p>
      </div>

      {/* Model Selector */}
      <div className="card">
        <div className="flex items-center justify-between mb-16">
          <h2 className="text-h3">Select Model</h2>
          <button className="btn-ghost text-small">
            <Settings size={16} />
          </button>
        </div>

        <div className="grid grid-cols-3 gap-12">
          {models.map((model) => (
            <button
              key={model.id}
              onClick={() => setSelectedModel(model.id)}
              className={cn(
                "p-16 rounded-lg border-2 transition-all text-left",
                selectedModel === model.id
                  ? "border-accent-primary bg-accent-primary/10"
                  : "border-dark-border bg-dark-bg-tertiary hover:border-dark-border/50",
              )}
            >
              <div className="flex items-center justify-between mb-8">
                <span className="text-body font-medium">{model.name}</span>
                {selectedModel === model.id && (
                  <span className="text-accent-primary">✓</span>
                )}
              </div>
              <div className="flex items-center gap-8 text-tiny text-dark-text-tertiary">
                <span>{model.type}</span>
                <span>•</span>
                <span>{model.size}</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Template Selector */}
      <div className="card">
        <h2 className="text-h3 mb-16">Prompt Template</h2>
        <div className="flex gap-12">
          {templates.map((tmpl) => {
            const Icon = tmpl.icon;
            return (
              <button
                key={tmpl.id}
                onClick={() => setTemplate(tmpl.id as any)}
                className={cn(
                  "flex-1 p-16 rounded-lg border-2 transition-all",
                  template === tmpl.id
                    ? "border-accent-primary bg-accent-primary/10"
                    : "border-dark-border bg-dark-bg-tertiary hover:border-dark-border/50",
                )}
              >
                <Icon
                  size={24}
                  className={cn(
                    "mb-8",
                    template === tmpl.id
                      ? "text-accent-primary"
                      : "text-dark-text-tertiary",
                  )}
                />
                <div className="text-body font-medium mb-4">{tmpl.label}</div>
                <div className="text-tiny text-dark-text-tertiary font-mono">
                  {tmpl.example.slice(0, 30)}...
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Playground */}
      <div className="grid grid-cols-2 gap-24">
        {/* Input Section */}
        <div className="space-y-16">
          <div className="card">
            <div className="flex items-center justify-between mb-16">
              <h2 className="text-h3">Prompt Input</h2>
              <div className="flex items-center gap-12 text-tiny text-dark-text-tertiary">
                <span>{charCount} chars</span>
                <span>•</span>
                <span>~{tokenCount} tokens</span>
              </div>
            </div>

            <textarea
              value={prompt}
              onChange={(e) => handlePromptChange(e.target.value)}
              placeholder="Enter your prompt here..."
              className="w-full h-[400px] bg-dark-bg-tertiary border border-dark-border rounded-lg p-16 text-body text-dark-text-primary placeholder:text-dark-text-tertiary focus:outline-none focus:border-accent-primary focus:ring-1 focus:ring-accent-primary resize-none font-mono"
            />

            <div className="flex items-center gap-12 mt-16">
              <button
                onClick={handleGenerate}
                disabled={!prompt || isGenerating}
                className={cn(
                  "btn-primary flex-1 flex items-center justify-center gap-8",
                  isGenerating && "opacity-50 cursor-not-allowed",
                )}
              >
                {isGenerating ? (
                  <>
                    <Sparkles size={16} className="animate-spin" />
                    <span>Generating...</span>
                  </>
                ) : (
                  <>
                    <Play size={16} />
                    <span>Generate</span>
                  </>
                )}
              </button>

              <button onClick={handleReset} className="btn-ghost">
                <RotateCcw size={16} />
              </button>

              <button
                onClick={() => setShowSettings(!showSettings)}
                className={cn(
                  "btn-ghost",
                  showSettings && "bg-accent-primary/10 text-accent-primary",
                )}
              >
                <Settings size={16} />
              </button>
            </div>
          </div>

          {/* Generation Settings */}
          {showSettings && (
            <div className="card animate-scale-in">
              <h3 className="text-h3 mb-16">Generation Settings</h3>

              <div className="space-y-20">
                {/* Temperature */}
                <div>
                  <div className="flex items-center justify-between mb-8">
                    <label className="text-small text-dark-text-secondary">
                      Temperature
                    </label>
                    <span className="text-small font-mono text-accent-primary">
                      {settings.temperature}
                    </span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="2"
                    step="0.1"
                    value={settings.temperature}
                    onChange={(e) =>
                      setSettings({
                        ...settings,
                        temperature: parseFloat(e.target.value),
                      })
                    }
                    className="w-full"
                  />
                  <div className="flex justify-between text-tiny text-dark-text-tertiary mt-4">
                    <span>Precise</span>
                    <span>Creative</span>
                  </div>
                </div>

                {/* Top P */}
                <div>
                  <div className="flex items-center justify-between mb-8">
                    <label className="text-small text-dark-text-secondary">
                      Top P
                    </label>
                    <span className="text-small font-mono text-accent-primary">
                      {settings.topP}
                    </span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    value={settings.topP}
                    onChange={(e) =>
                      setSettings({
                        ...settings,
                        topP: parseFloat(e.target.value),
                      })
                    }
                    className="w-full"
                  />
                </div>

                {/* Top K */}
                <div>
                  <div className="flex items-center justify-between mb-8">
                    <label className="text-small text-dark-text-secondary">
                      Top K
                    </label>
                    <input
                      type="number"
                      value={settings.topK}
                      onChange={(e) =>
                        setSettings({
                          ...settings,
                          topK: parseInt(e.target.value),
                        })
                      }
                      className="input w-[80px] text-right"
                    />
                  </div>
                </div>

                {/* Max Tokens */}
                <div>
                  <div className="flex items-center justify-between mb-8">
                    <label className="text-small text-dark-text-secondary">
                      Max Tokens
                    </label>
                    <input
                      type="number"
                      value={settings.maxTokens}
                      onChange={(e) =>
                        setSettings({
                          ...settings,
                          maxTokens: parseInt(e.target.value),
                        })
                      }
                      className="input w-[100px] text-right"
                    />
                  </div>
                </div>

                {/* Repetition Penalty */}
                <div>
                  <div className="flex items-center justify-between mb-8">
                    <label className="text-small text-dark-text-secondary">
                      Repetition Penalty
                    </label>
                    <span className="text-small font-mono text-accent-primary">
                      {settings.repetitionPenalty}
                    </span>
                  </div>
                  <input
                    type="range"
                    min="1"
                    max="2"
                    step="0.1"
                    value={settings.repetitionPenalty}
                    onChange={(e) =>
                      setSettings({
                        ...settings,
                        repetitionPenalty: parseFloat(e.target.value),
                      })
                    }
                    className="w-full"
                  />
                </div>

                {/* Stop Sequences */}
                <div>
                  <label className="text-small text-dark-text-secondary mb-8 block">
                    Stop Sequences
                  </label>
                  <input
                    type="text"
                    value={settings.stopSequences}
                    onChange={(e) =>
                      setSettings({
                        ...settings,
                        stopSequences: e.target.value,
                      })
                    }
                    placeholder="Comma-separated, e.g., \n, ###"
                    className="input w-full"
                  />
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Output Section */}
        <div className="card">
          <div className="flex items-center justify-between mb-16">
            <h2 className="text-h3">Generated Output</h2>
            {output && (
              <div className="flex items-center gap-12">
                <div className="text-tiny text-dark-text-tertiary">
                  <Zap size={12} className="inline mr-4" />
                  {isGenerating ? "Generating..." : "24 tokens/sec"}
                </div>
                <button onClick={handleCopy} className="btn-ghost text-small">
                  <Copy size={14} />
                </button>
              </div>
            )}
          </div>

          <div className="min-h-[400px] max-h-[600px] overflow-y-auto bg-dark-bg-tertiary border border-dark-border rounded-lg p-16">
            {output ? (
              <div className="text-body text-dark-text-primary whitespace-pre-wrap font-mono">
                {output}
                {isGenerating && (
                  <span className="inline-block w-2 h-4 bg-accent-primary ml-1 animate-pulse" />
                )}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-[400px] text-dark-text-tertiary">
                <Sparkles size={48} className="mb-16 opacity-50" />
                <p className="text-body">Generated output will appear here</p>
                <p className="text-small mt-8">Click "Generate" to start</p>
              </div>
            )}
          </div>

          {output && !isGenerating && (
            <div className="mt-16 p-12 bg-dark-bg-tertiary rounded-lg">
              <div className="grid grid-cols-3 gap-16 text-center text-small">
                <div>
                  <div className="text-dark-text-tertiary mb-4">Tokens</div>
                  <div className="text-dark-text-primary font-medium">
                    {Math.ceil(output.length / 4)}
                  </div>
                </div>
                <div>
                  <div className="text-dark-text-tertiary mb-4">Time</div>
                  <div className="text-dark-text-primary font-medium">2.3s</div>
                </div>
                <div>
                  <div className="text-dark-text-tertiary mb-4">Speed</div>
                  <div className="text-dark-text-primary font-medium">
                    24 tok/s
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default InferencePlayground;
