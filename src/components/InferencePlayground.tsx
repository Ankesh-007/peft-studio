import React, { useState, useEffect, useRef } from 'react';
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
  Download,
  Upload,
  Trash2,
  History,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  Loader,
} from 'lucide-react';
import { cn } from '../lib/utils';

interface GenerationSettings {
  temperature: number;
  topP: number;
  topK: number;
  maxTokens: number;
  repetitionPenalty: number;
  stopSequences: string;
}

interface LoadedModel {
  model_id: string;
  status: string;
  loaded_at: string;
  use_case: string;
  memory_usage_mb?: number;
}

interface ConversationMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  model_id?: string;
}

interface Conversation {
  id: string;
  messages: ConversationMessage[];
  use_case: string;
  model_id: string;
  created_at: string;
  updated_at: string;
}

const InferencePlayground: React.FC = () => {
  const [selectedModel, setSelectedModel] = useState('');
  const [loadedModels, setLoadedModels] = useState<LoadedModel[]>([]);
  const [isLoadingModel, setIsLoadingModel] = useState(false);
  const [modelToLoad, setModelToLoad] = useState('');
  const [adapterPath, setAdapterPath] = useState('');
  const [useCase, setUseCase] = useState('chatbot');
  
  const [template, setTemplate] = useState<'chat' | 'instruct' | 'raw'>('instruct');
  const [prompt, setPrompt] = useState('');
  const [output, setOutput] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [charCount, setCharCount] = useState(0);
  const [tokenCount, setTokenCount] = useState(0);
  const [useStreaming, setUseStreaming] = useState(true);
  
  const [generationStats, setGenerationStats] = useState({
    tokens: 0,
    time: 0,
    speed: 0,
  });
  
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversationId, setCurrentConversationId] = useState<string>('');
  const [showConversationHistory, setShowConversationHistory] = useState(false);
  const [conversationMessages, setConversationMessages] = useState<ConversationMessage[]>([]);
  
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const outputRef = useRef<HTMLDivElement>(null);
  
  const [settings, setSettings] = useState<GenerationSettings>({
    temperature: 0.7,
    topP: 0.9,
    topK: 50,
    maxTokens: 512,
    repetitionPenalty: 1.1,
    stopSequences: "",
  });

  // Load models on mount
  useEffect(() => {
    fetchLoadedModels();
    fetchConversations();
  }, []);
  
  // Auto-scroll output
  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight;
    }
  }, [output]);
  
  const fetchLoadedModels = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/inference/models/loaded');
      const data = await response.json();
      setLoadedModels(data.models || []);
      if (data.models && data.models.length > 0 && !selectedModel) {
        setSelectedModel(data.models[0].model_id);
      }
    } catch (err) {
      console.error('Error fetching loaded models:', err);
    }
  };
  
  const fetchConversations = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/inference/conversations');
      const data = await response.json();
      setConversations(data);
    } catch (err) {
      console.error('Error fetching conversations:', err);
    }
  };
  
  const handleLoadModel = async () => {
    if (!modelToLoad) {
      setError('Please enter a model ID');
      return;
    }
    
    setIsLoadingModel(true);
    setError(null);
    
    try {
      const response = await fetch('http://localhost:8000/api/inference/load', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model_id: modelToLoad,
          adapter_path: adapterPath || null,
          use_case: useCase,
        }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to load model');
      }
      
      const data = await response.json();
      setSuccess(`Model ${data.model_id} loaded successfully`);
      setSelectedModel(data.model_id);
      await fetchLoadedModels();
      setModelToLoad('');
      setAdapterPath('');
    } catch (err: any) {
      setError(err.message || 'Failed to load model');
    } finally {
      setIsLoadingModel(false);
    }
  };
  
  const handleUnloadModel = async (modelId: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/inference/models/${modelId}/unload`, {
        method: 'POST',
      });
      
      if (!response.ok) {
        throw new Error('Failed to unload model');
      }
      
      setSuccess(`Model ${modelId} unloaded`);
      if (selectedModel === modelId) {
        setSelectedModel('');
      }
      await fetchLoadedModels();
    } catch (err: any) {
      setError(err.message || 'Failed to unload model');
    }
  };

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
    if (!selectedModel) {
      setError('Please select a model first');
      return;
    }
    
    if (!prompt.trim()) {
      setError('Please enter a prompt');
      return;
    }
    
    setIsGenerating(true);
    setOutput('');
    setError(null);
    const startTime = Date.now();
    
    try {
      if (useStreaming) {
        // Use WebSocket for streaming
        await generateWithStreaming();
      } else {
        // Use REST API for non-streaming
        await generateWithoutStreaming();
      }
      
      // Save to conversation if we have a conversation ID
      if (currentConversationId) {
        await saveToConversation('user', prompt);
        await saveToConversation('assistant', output);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to generate response');
    } finally {
      setIsGenerating(false);
    }
  };
  
  const generateWithStreaming = async () => {
    return new Promise<void>((resolve, reject) => {
      const ws = new WebSocket('ws://localhost:8000/api/inference/stream');
      wsRef.current = ws;
      
      let generatedText = '';
      let tokenCount = 0;
      const startTime = Date.now();
      
      ws.onopen = () => {
        ws.send(JSON.stringify({
          model_id: selectedModel,
          prompt: prompt,
          max_tokens: settings.maxTokens,
          temperature: settings.temperature,
          top_p: settings.topP,
          top_k: settings.topK,
          repetition_penalty: settings.repetitionPenalty,
          stream: true,
        }));
      };
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'token') {
          generatedText += data.token;
          tokenCount++;
          setOutput(generatedText);
          
          // Update stats in real-time
          const elapsed = (Date.now() - startTime) / 1000;
          setGenerationStats({
            tokens: tokenCount,
            time: elapsed,
            speed: tokenCount / elapsed,
          });
        } else if (data.type === 'complete') {
          const elapsed = (Date.now() - startTime) / 1000;
          setGenerationStats({
            tokens: data.total_tokens || tokenCount,
            time: elapsed,
            speed: (data.total_tokens || tokenCount) / elapsed,
          });
          ws.close();
          resolve();
        } else if (data.type === 'error') {
          reject(new Error(data.error));
          ws.close();
        }
      };
      
      ws.onerror = (error) => {
        reject(new Error('WebSocket error'));
        ws.close();
      };
      
      ws.onclose = () => {
        wsRef.current = null;
      };
    });
  };
  
  const generateWithoutStreaming = async () => {
    const startTime = Date.now();
    
    const response = await fetch('http://localhost:8000/api/inference/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model_id: selectedModel,
        prompt: prompt,
        max_tokens: settings.maxTokens,
        temperature: settings.temperature,
        top_p: settings.topP,
        top_k: settings.topK,
        repetition_penalty: settings.repetitionPenalty,
      }),
    });
    
    if (!response.ok) {
      throw new Error('Failed to generate response');
    }
    
    const data = await response.json();
    setOutput(data.response);
    setGenerationStats({
      tokens: data.tokens_generated,
      time: data.generation_time_seconds,
      speed: data.tokens_per_second,
    });
  };
  
  const saveToConversation = async (role: 'user' | 'assistant', content: string) => {
    if (!currentConversationId) return;
    
    try {
      await fetch('http://localhost:8000/api/inference/conversation/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          conversation_id: currentConversationId,
          role,
          content,
          model_id: selectedModel,
          use_case: useCase,
        }),
      });
      
      // Refresh conversation
      await loadConversation(currentConversationId);
    } catch (err) {
      console.error('Error saving to conversation:', err);
    }
  };
  
  const loadConversation = async (conversationId: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/inference/conversation/${conversationId}`);
      const data = await response.json();
      setConversationMessages(data.messages);
    } catch (err) {
      console.error('Error loading conversation:', err);
    }
  };
  
  const startNewConversation = () => {
    const newId = `conv_${Date.now()}`;
    setCurrentConversationId(newId);
    setConversationMessages([]);
    setSuccess('Started new conversation');
  };
  
  const deleteConversation = async (conversationId: string) => {
    try {
      await fetch(`http://localhost:8000/api/inference/conversation/${conversationId}`, {
        method: 'DELETE',
      });
      setSuccess('Conversation deleted');
      await fetchConversations();
      if (currentConversationId === conversationId) {
        setCurrentConversationId('');
        setConversationMessages([]);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to delete conversation');
    }
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
          Test your fine-tuned models with custom prompts and streaming responses
        </p>
      </div>
      
      {/* Alerts */}
      {error && (
        <div className="card bg-red-500/10 border-red-500/50 flex items-start gap-12">
          <AlertCircle size={20} className="text-red-500 flex-shrink-0 mt-2" />
          <div className="flex-1">
            <p className="text-body text-red-500">{error}</p>
          </div>
          <button onClick={() => setError(null)} className="text-red-500 hover:text-red-400">
            ×
          </button>
        </div>
      )}
      
      {success && (
        <div className="card bg-green-500/10 border-green-500/50 flex items-start gap-12">
          <CheckCircle size={20} className="text-green-500 flex-shrink-0 mt-2" />
          <div className="flex-1">
            <p className="text-body text-green-500">{success}</p>
          </div>
          <button onClick={() => setSuccess(null)} className="text-green-500 hover:text-green-400">
            ×
          </button>
        </div>
      )}
      
      {/* Model Loading Section */}
      <div className="card">
        <h2 className="text-h3 mb-16">Load Model</h2>
        <div className="grid grid-cols-2 gap-16 mb-16">
          <div>
            <label className="text-small text-dark-text-secondary mb-8 block">Model ID</label>
            <input
              type="text"
              value={modelToLoad}
              onChange={(e) => setModelToLoad(e.target.value)}
              placeholder="e.g., llama-3-finance"
              className="input w-full"
            />
          </div>
          <div>
            <label className="text-small text-dark-text-secondary mb-8 block">
              Adapter Path (Optional)
            </label>
            <input
              type="text"
              value={adapterPath}
              onChange={(e) => setAdapterPath(e.target.value)}
              placeholder="Path to adapter weights"
              className="input w-full"
            />
          </div>
        </div>
        <div className="flex items-center gap-12">
          <select
            value={useCase}
            onChange={(e) => setUseCase(e.target.value)}
            className="input flex-1"
          >
            <option value="chatbot">Chatbot</option>
            <option value="code_generation">Code Generation</option>
            <option value="summarization">Summarization</option>
            <option value="qa">Question Answering</option>
            <option value="creative_writing">Creative Writing</option>
            <option value="domain_adaptation">Domain Adaptation</option>
          </select>
          <button
            onClick={handleLoadModel}
            disabled={isLoadingModel || !modelToLoad}
            className="btn-primary flex items-center gap-8"
          >
            {isLoadingModel ? (
              <>
                <Loader size={16} className="animate-spin" />
                <span>Loading...</span>
              </>
            ) : (
              <>
                <Upload size={16} />
                <span>Load Model</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Loaded Models */}
      <div className="card">
        <div className="flex items-center justify-between mb-16">
          <h2 className="text-h3">Loaded Models</h2>
          <button onClick={fetchLoadedModels} className="btn-ghost text-small">
            <RefreshCw size={16} />
          </button>
        </div>
        
        {loadedModels.length === 0 ? (
          <div className="text-center py-32 text-dark-text-tertiary">
            <Sparkles size={48} className="mx-auto mb-16 opacity-50" />
            <p className="text-body">No models loaded</p>
            <p className="text-small mt-8">Load a model above to get started</p>
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-12">
            {loadedModels.map((model) => (
              <div
                key={model.model_id}
                className={cn(
                  'p-16 rounded-lg border-2 transition-all',
                  selectedModel === model.model_id
                    ? 'border-accent-primary bg-accent-primary/10'
                    : 'border-dark-border bg-dark-bg-tertiary'
                )}
              >
                <div className="flex items-start justify-between mb-8">
                  <button
                    onClick={() => setSelectedModel(model.model_id)}
                    className="flex-1 text-left"
                  >
                    <span className="text-body font-medium block">{model.model_id}</span>
                    <span className="text-tiny text-dark-text-tertiary">{model.use_case}</span>
                  </button>
                  {selectedModel === model.model_id && (
                    <CheckCircle size={16} className="text-accent-primary flex-shrink-0" />
                  )}
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-tiny text-dark-text-tertiary">
                    {new Date(model.loaded_at).toLocaleTimeString()}
                  </span>
                  <button
                    onClick={() => handleUnloadModel(model.model_id)}
                    className="text-red-500 hover:text-red-400"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
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
          {/* Conversation Controls */}
          <div className="card">
            <div className="flex items-center justify-between mb-12">
              <h3 className="text-body font-medium">Conversation</h3>
              <button
                onClick={() => setShowConversationHistory(!showConversationHistory)}
                className="btn-ghost text-small"
              >
                <History size={16} />
              </button>
            </div>
            <div className="flex gap-12">
              <button
                onClick={startNewConversation}
                className="btn-secondary flex-1 flex items-center justify-center gap-8"
              >
                <MessageSquare size={16} />
                <span>New Conversation</span>
              </button>
              {currentConversationId && (
                <span className="text-tiny text-dark-text-tertiary flex items-center">
                  Active: {currentConversationId.slice(0, 12)}...
                </span>
              )}
            </div>
          </div>
          
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
                disabled={!prompt || isGenerating || !selectedModel}
                className={cn(
                  'btn-primary flex-1 flex items-center justify-center gap-8',
                  (isGenerating || !selectedModel) && 'opacity-50 cursor-not-allowed'
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
              
              <label className="flex items-center gap-8 text-small text-dark-text-secondary cursor-pointer">
                <input
                  type="checkbox"
                  checked={useStreaming}
                  onChange={(e) => setUseStreaming(e.target.checked)}
                  className="rounded"
                />
                Stream
              </label>
              
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
        <div className="space-y-16">
          <div className="card">
            <div className="flex items-center justify-between mb-16">
              <h2 className="text-h3">Generated Output</h2>
              {output && (
                <div className="flex items-center gap-12">
                  <div className="text-tiny text-dark-text-tertiary">
                    <Zap size={12} className="inline mr-4" />
                    {isGenerating
                      ? `${generationStats.speed.toFixed(1)} tok/s`
                      : `${generationStats.speed.toFixed(1)} tok/s`}
                  </div>
                  <button onClick={handleCopy} className="btn-ghost text-small">
                    <Copy size={14} />
                  </button>
                </div>
              )}
            </div>
            
            <div
              ref={outputRef}
              className="min-h-[400px] max-h-[600px] overflow-y-auto bg-dark-bg-tertiary border border-dark-border rounded-lg p-16"
            >
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
                  <p className="text-small mt-8">
                    {selectedModel ? 'Click "Generate" to start' : 'Load a model first'}
                  </p>
                </div>
              )}
            </div>

            {(output || isGenerating) && (
              <div className="mt-16 p-12 bg-dark-bg-tertiary rounded-lg">
                <div className="grid grid-cols-3 gap-16 text-center text-small">
                  <div>
                    <div className="text-dark-text-tertiary mb-4">Tokens</div>
                    <div className="text-dark-text-primary font-medium">
                      {generationStats.tokens}
                    </div>
                  </div>
                  <div>
                    <div className="text-dark-text-tertiary mb-4">Time</div>
                    <div className="text-dark-text-primary font-medium">
                      {generationStats.time.toFixed(2)}s
                    </div>
                  </div>
                  <div>
                    <div className="text-dark-text-tertiary mb-4">Speed</div>
                    <div className="text-dark-text-primary font-medium">
                      {generationStats.speed.toFixed(1)} tok/s
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
          
          {/* Conversation History */}
          {showConversationHistory && conversationMessages.length > 0 && (
            <div className="card animate-scale-in">
              <h3 className="text-h3 mb-16">Conversation History</h3>
              <div className="space-y-12 max-h-[400px] overflow-y-auto">
                {conversationMessages.map((msg, idx) => (
                  <div
                    key={idx}
                    className={cn(
                      'p-12 rounded-lg',
                      msg.role === 'user'
                        ? 'bg-accent-primary/10 border border-accent-primary/30'
                        : 'bg-dark-bg-tertiary border border-dark-border'
                    )}
                  >
                    <div className="flex items-center gap-8 mb-8">
                      <span className="text-tiny font-medium text-dark-text-secondary uppercase">
                        {msg.role}
                      </span>
                      <span className="text-tiny text-dark-text-tertiary">
                        {new Date(msg.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    <p className="text-small text-dark-text-primary whitespace-pre-wrap">
                      {msg.content}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default InferencePlayground;
