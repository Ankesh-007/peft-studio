import React, { useState, useEffect } from 'react';
import { Play, Square, ExternalLink, Code, Copy, Check, Trash2, RefreshCw } from 'lucide-react';

interface DemoConfig {
  demo_id: string;
  model_id: string;
  model_path: string;
  title: string;
  description: string;
  input_type: string;
  input_label: string;
  input_placeholder: string;
  output_type: string;
  output_label: string;
  max_tokens: number;
  temperature: number;
  top_p: number;
  top_k: number;
  server_name: string;
  server_port: number;
  share: boolean;
  use_local_model: boolean;
  api_endpoint?: string;
  api_key?: string;
}

interface DemoInfo {
  demo_id: string;
  status: string;
  local_url?: string;
  public_url?: string;
  process_id?: number;
  error_message?: string;
  created_at: string;
  started_at?: string;
  stopped_at?: string;
}

const GradioDemoGenerator: React.FC = () => {
  const [demos, setDemos] = useState<DemoInfo[]>([]);
  const [selectedDemo, setSelectedDemo] = useState<DemoInfo | null>(null);
  const [showConfigForm, setShowConfigForm] = useState(false);
  const [generatedCode, setGeneratedCode] = useState<string>('');
  const [embedCode, setEmbedCode] = useState<string>('');
  const [copiedCode, setCopiedCode] = useState(false);
  const [copiedEmbed, setCopiedEmbed] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');

  // Form state
  const [config, setConfig] = useState<DemoConfig>({
    demo_id: `demo_${Date.now()}`,
    model_id: '',
    model_path: '',
    title: 'My Fine-Tuned Model Demo',
    description: 'Interactive demo for my fine-tuned model',
    input_type: 'textbox',
    input_label: 'Input',
    input_placeholder: 'Enter your prompt here...',
    output_type: 'textbox',
    output_label: 'Output',
    max_tokens: 512,
    temperature: 0.7,
    top_p: 0.9,
    top_k: 50,
    server_name: '127.0.0.1',
    server_port: 7860,
    share: false,
    use_local_model: true,
  });

  useEffect(() => {
    loadDemos();
  }, []);

  const loadDemos = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/gradio-demos/');
      if (response.ok) {
        const data = await response.json();
        // Handle both array and object responses
        setDemos(Array.isArray(data) ? data : []);
      }
    } catch (err) {
      console.error('Failed to load demos:', err);
      setDemos([]);
    }
  };

  const createDemo = async () => {
    setLoading(true);
    setError('');
    
    try {
      const response = await fetch('http://localhost:8000/api/gradio-demos/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      });

      if (!response.ok) {
        throw new Error('Failed to create demo');
      }

      const demo = await response.json();
      setDemos([...demos, demo]);
      setSelectedDemo(demo);
      setShowConfigForm(false);
      
      // Generate code preview
      await loadDemoCode(demo.demo_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create demo');
    } finally {
      setLoading(false);
    }
  };

  const launchDemo = async (demoId: string) => {
    setLoading(true);
    setError('');
    
    try {
      const response = await fetch(`http://localhost:8000/api/gradio-demos/${demoId}/launch`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error('Failed to launch demo');
      }

      const demo = await response.json();
      setDemos(demos.map(d => d.demo_id === demoId ? demo : d));
      setSelectedDemo(demo);
      
      // Load embed code if public URL is available
      if (demo.public_url) {
        await loadEmbedCode(demoId);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to launch demo');
    } finally {
      setLoading(false);
    }
  };

  const stopDemo = async (demoId: string) => {
    setLoading(true);
    setError('');
    
    try {
      const response = await fetch(`http://localhost:8000/api/gradio-demos/${demoId}/stop`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error('Failed to stop demo');
      }

      const demo = await response.json();
      setDemos(demos.map(d => d.demo_id === demoId ? demo : d));
      if (selectedDemo?.demo_id === demoId) {
        setSelectedDemo(demo);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to stop demo');
    } finally {
      setLoading(false);
    }
  };

  const deleteDemo = async (demoId: string) => {
    if (!confirm('Are you sure you want to delete this demo?')) {
      return;
    }

    setLoading(true);
    setError('');
    
    try {
      const response = await fetch(`http://localhost:8000/api/gradio-demos/${demoId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Failed to delete demo');
      }

      setDemos(demos.filter(d => d.demo_id !== demoId));
      if (selectedDemo?.demo_id === demoId) {
        setSelectedDemo(null);
        setGeneratedCode('');
        setEmbedCode('');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete demo');
    } finally {
      setLoading(false);
    }
  };

  const loadDemoCode = async (demoId: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/gradio-demos/${demoId}/code`);
      if (response.ok) {
        const data = await response.json();
        setGeneratedCode(data.code);
      }
    } catch (err) {
      console.error('Failed to load demo code:', err);
    }
  };

  const loadEmbedCode = async (demoId: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/gradio-demos/${demoId}/embed`);
      if (response.ok) {
        const data = await response.json();
        setEmbedCode(data.embed_code);
      }
    } catch (err) {
      console.error('Failed to load embed code:', err);
      // If embed code fails (e.g., no public URL), just clear it
      setEmbedCode('');
    }
  };

  const copyToClipboard = async (text: string, type: 'code' | 'embed') => {
    try {
      await navigator.clipboard.writeText(text);
      if (type === 'code') {
        setCopiedCode(true);
        setTimeout(() => setCopiedCode(false), 2000);
      } else {
        setCopiedEmbed(true);
        setTimeout(() => setCopiedEmbed(false), 2000);
      }
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'text-green-600 bg-green-100';
      case 'stopped':
        return 'text-gray-600 bg-gray-100';
      case 'error':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-blue-600 bg-blue-100';
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Gradio Demo Generator</h1>
        <p className="text-gray-600">
          Create interactive demos for your fine-tuned models with Gradio
        </p>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Demo List */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">My Demos</h2>
              <button
                onClick={() => setShowConfigForm(true)}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                New Demo
              </button>
            </div>

            <div className="space-y-2">
              {demos.length === 0 ? (
                <p className="text-gray-500 text-center py-8">
                  No demos yet. Create your first demo!
                </p>
              ) : (
                demos.map((demo) => (
                  <div
                    key={demo.demo_id}
                    onClick={async () => {
                      setSelectedDemo(demo);
                      await loadDemoCode(demo.demo_id);
                      if (demo.public_url) {
                        await loadEmbedCode(demo.demo_id);
                      }
                    }}
                    className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                      selectedDemo?.demo_id === demo.demo_id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <span className="font-medium truncate">{demo.demo_id}</span>
                      <span className={`text-xs px-2 py-1 rounded-full ${getStatusColor(demo.status)}`}>
                        {demo.status}
                      </span>
                    </div>
                    {demo.local_url && (
                      <p className="text-xs text-gray-500 truncate">{demo.local_url}</p>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Demo Details */}
        <div className="lg:col-span-2">
          {selectedDemo ? (
            <div className="space-y-4">
              {/* Control Panel */}
              <div className="bg-white rounded-lg shadow-md p-4">
                <h2 className="text-xl font-semibold mb-4">Demo Controls</h2>
                
                <div className="flex flex-wrap gap-3">
                  {selectedDemo.status === 'created' && (
                    <button
                      onClick={() => launchDemo(selectedDemo.demo_id)}
                      disabled={loading}
                      className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50"
                    >
                      <Play size={16} />
                      Launch Demo
                    </button>
                  )}
                  
                  {selectedDemo.status === 'running' && (
                    <>
                      <button
                        onClick={() => stopDemo(selectedDemo.demo_id)}
                        disabled={loading}
                        className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50"
                      >
                        <Square size={16} />
                        Stop Demo
                      </button>
                      
                      {selectedDemo.local_url && (
                        <a
                          href={selectedDemo.local_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                        >
                          <ExternalLink size={16} />
                          Open Demo
                        </a>
                      )}
                    </>
                  )}
                  
                  <button
                    onClick={() => loadDemos()}
                    disabled={loading}
                    className="flex items-center gap-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors disabled:opacity-50"
                  >
                    <RefreshCw size={16} />
                    Refresh
                  </button>
                  
                  <button
                    onClick={() => deleteDemo(selectedDemo.demo_id)}
                    disabled={loading}
                    className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50 ml-auto"
                  >
                    <Trash2 size={16} />
                    Delete
                  </button>
                </div>

                {selectedDemo.error_message && (
                  <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                    <strong>Error:</strong> {selectedDemo.error_message}
                  </div>
                )}

                {selectedDemo.public_url && (
                  <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
                    <p className="text-sm font-medium text-green-800 mb-1">Public URL:</p>
                    <a
                      href={selectedDemo.public_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-green-600 hover:underline break-all"
                    >
                      {selectedDemo.public_url}
                    </a>
                  </div>
                )}
              </div>

              {/* Generated Code */}
              {generatedCode && (
                <div className="bg-white rounded-lg shadow-md p-4">
                  <div className="flex justify-between items-center mb-3">
                    <h3 className="text-lg font-semibold flex items-center gap-2">
                      <Code size={20} />
                      Generated Code
                    </h3>
                    <button
                      onClick={() => copyToClipboard(generatedCode, 'code')}
                      className="flex items-center gap-2 px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
                    >
                      {copiedCode ? <Check size={16} /> : <Copy size={16} />}
                      {copiedCode ? 'Copied!' : 'Copy'}
                    </button>
                  </div>
                  <pre className="bg-gray-50 p-4 rounded-lg overflow-x-auto text-sm">
                    <code>{generatedCode}</code>
                  </pre>
                </div>
              )}

              {/* Embed Code */}
              {embedCode && (
                <div className="bg-white rounded-lg shadow-md p-4">
                  <div className="flex justify-between items-center mb-3">
                    <h3 className="text-lg font-semibold flex items-center gap-2">
                      <Code size={20} />
                      Embeddable Code
                    </h3>
                    <button
                      onClick={() => copyToClipboard(embedCode, 'embed')}
                      className="flex items-center gap-2 px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
                    >
                      {copiedEmbed ? <Check size={16} /> : <Copy size={16} />}
                      {copiedEmbed ? 'Copied!' : 'Copy'}
                    </button>
                  </div>
                  <pre className="bg-gray-50 p-4 rounded-lg overflow-x-auto text-sm">
                    <code>{embedCode}</code>
                  </pre>
                  <p className="mt-2 text-sm text-gray-600">
                    Copy this code to embed the demo in your website
                  </p>
                </div>
              )}
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow-md p-8 text-center">
              <p className="text-gray-500">
                Select a demo from the list or create a new one to get started
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Configuration Form Modal */}
      {showConfigForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <h2 className="text-2xl font-bold mb-4">Create New Demo</h2>
              
              <div className="space-y-4">
                {/* Basic Info */}
                <div>
                  <label className="block text-sm font-medium mb-1">Demo ID</label>
                  <input
                    type="text"
                    value={config.demo_id}
                    onChange={(e) => setConfig({ ...config, demo_id: e.target.value })}
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Model ID</label>
                  <input
                    type="text"
                    value={config.model_id}
                    onChange={(e) => setConfig({ ...config, model_id: e.target.value })}
                    placeholder="e.g., meta-llama/Llama-2-7b-hf"
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Model Path</label>
                  <input
                    type="text"
                    value={config.model_path}
                    onChange={(e) => setConfig({ ...config, model_path: e.target.value })}
                    placeholder="Path to model files"
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Title</label>
                  <input
                    type="text"
                    value={config.title}
                    onChange={(e) => setConfig({ ...config, title: e.target.value })}
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Description</label>
                  <textarea
                    value={config.description}
                    onChange={(e) => setConfig({ ...config, description: e.target.value })}
                    rows={3}
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>

                {/* Interface Configuration */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Input Type</label>
                    <select
                      value={config.input_type}
                      onChange={(e) => setConfig({ ...config, input_type: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg"
                    >
                      <option value="textbox">Textbox</option>
                      <option value="chatbot">Chatbot</option>
                      <option value="audio">Audio</option>
                      <option value="image">Image</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1">Output Type</label>
                    <select
                      value={config.output_type}
                      onChange={(e) => setConfig({ ...config, output_type: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg"
                    >
                      <option value="textbox">Textbox</option>
                      <option value="chatbot">Chatbot</option>
                      <option value="audio">Audio</option>
                      <option value="image">Image</option>
                    </select>
                  </div>
                </div>

                {/* Generation Parameters */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Max Tokens</label>
                    <input
                      type="number"
                      value={config.max_tokens}
                      onChange={(e) => setConfig({ ...config, max_tokens: parseInt(e.target.value) })}
                      className="w-full px-3 py-2 border rounded-lg"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1">Temperature</label>
                    <input
                      type="number"
                      step="0.1"
                      value={config.temperature}
                      onChange={(e) => setConfig({ ...config, temperature: parseFloat(e.target.value) })}
                      className="w-full px-3 py-2 border rounded-lg"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1">Top P</label>
                    <input
                      type="number"
                      step="0.1"
                      value={config.top_p}
                      onChange={(e) => setConfig({ ...config, top_p: parseFloat(e.target.value) })}
                      className="w-full px-3 py-2 border rounded-lg"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1">Top K</label>
                    <input
                      type="number"
                      value={config.top_k}
                      onChange={(e) => setConfig({ ...config, top_k: parseInt(e.target.value) })}
                      className="w-full px-3 py-2 border rounded-lg"
                    />
                  </div>
                </div>

                {/* Server Configuration */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Server Port</label>
                    <input
                      type="number"
                      value={config.server_port}
                      onChange={(e) => setConfig({ ...config, server_port: parseInt(e.target.value) })}
                      className="w-full px-3 py-2 border rounded-lg"
                    />
                  </div>

                  <div className="flex items-center pt-6">
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={config.share}
                        onChange={(e) => setConfig({ ...config, share: e.target.checked })}
                        className="w-4 h-4"
                      />
                      <span className="text-sm font-medium">Enable Public Sharing</span>
                    </label>
                  </div>
                </div>

                {/* Model Source */}
                <div>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={config.use_local_model}
                      onChange={(e) => setConfig({ ...config, use_local_model: e.target.checked })}
                      className="w-4 h-4"
                    />
                    <span className="text-sm font-medium">Use Local Model</span>
                  </label>
                </div>

                {!config.use_local_model && (
                  <>
                    <div>
                      <label className="block text-sm font-medium mb-1">API Endpoint</label>
                      <input
                        type="text"
                        value={config.api_endpoint || ''}
                        onChange={(e) => setConfig({ ...config, api_endpoint: e.target.value })}
                        placeholder="https://api.example.com/v1/generate"
                        className="w-full px-3 py-2 border rounded-lg"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium mb-1">API Key</label>
                      <input
                        type="password"
                        value={config.api_key || ''}
                        onChange={(e) => setConfig({ ...config, api_key: e.target.value })}
                        placeholder="Your API key"
                        className="w-full px-3 py-2 border rounded-lg"
                      />
                    </div>
                  </>
                )}
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  onClick={createDemo}
                  disabled={loading || !config.model_id || !config.model_path}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
                >
                  {loading ? 'Creating...' : 'Create Demo'}
                </button>
                <button
                  onClick={() => setShowConfigForm(false)}
                  className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default GradioDemoGenerator;
