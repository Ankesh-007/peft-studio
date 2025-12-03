import React, { useState, useEffect } from 'react';
import {
  Settings as SettingsIcon,
  Palette,
  Bell,
  Cloud,
  Database,
  Code,
  Download,
  Upload,
  RotateCcw,
  Save,
  Check,
  X,
  AlertCircle
} from 'lucide-react';
import { cn } from '../lib/utils';

interface Settings {
  appearance: {
    theme: 'dark' | 'light' | 'auto';
    accentColor: string;
    fontSize: 'small' | 'medium' | 'large';
    compactMode: boolean;
  };
  notifications: {
    enabled: boolean;
    trainingComplete: boolean;
    trainingFailed: boolean;
    deploymentReady: boolean;
    systemUpdates: boolean;
    soundEnabled: boolean;
    desktopNotifications: boolean;
  };
  providers: {
    defaultCompute: string;
    defaultRegistry: string;
    defaultTracker: string | null;
    autoSelectCheapest: boolean;
    preferredRegion: string;
  };
  dataRetention: {
    keepLogs: number;
    keepCheckpoints: number;
    keepFailedRuns: number;
    autoCleanup: boolean;
    maxCacheSize: number;
  };
  training: {
    autoSaveCheckpoints: boolean;
    checkpointInterval: number;
    enableTelemetry: boolean;
    autoResume: boolean;
  };
  advanced: {
    enableDebugMode: boolean;
    logLevel: string;
    maxConcurrentRuns: number;
    enableExperimentalFeatures: boolean;
  };
}

type TabId = 'appearance' | 'notifications' | 'providers' | 'dataRetention' | 'training' | 'advanced';

const SettingsComponent: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabId>('appearance');
  const [settings, setSettings] = useState<Settings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const tabs = [
    { id: 'appearance' as TabId, label: 'Appearance', icon: Palette },
    { id: 'notifications' as TabId, label: 'Notifications', icon: Bell },
    { id: 'providers' as TabId, label: 'Default Providers', icon: Cloud },
    { id: 'dataRetention' as TabId, label: 'Data Retention', icon: Database },
    { id: 'training' as TabId, label: 'Training', icon: Code },
    { id: 'advanced' as TabId, label: 'Advanced', icon: SettingsIcon },
  ];

  useEffect(() => {
    loadSettings();
  }, []);

  useEffect(() => {
    if (message) {
      const timer = setTimeout(() => setMessage(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [message]);

  const showMessage = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text });
  };

  const loadSettings = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/settings');
      const data = await response.json();
      if (data.success) {
        setSettings(data.settings);
      }
    } catch (error) {
      console.error('Error loading settings:', error);
      showMessage('error', 'Failed to load settings');
    } finally {
      setLoading(false);
    }
  };

  const updateSetting = (category: string, key: string, value: any) => {
    if (!settings) return;
    setSettings({
      ...settings,
      [category]: {
        ...settings[category as keyof Settings],
        [key]: value
      }
    });
  };

  const saveSettings = async () => {
    if (!settings) return;
    
    setSaving(true);
    try {
      const response = await fetch('http://localhost:8000/api/settings/category', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          category: activeTab,
          values: settings[activeTab]
        })
      });
      
      const data = await response.json();
      if (data.success) {
        showMessage('success', 'Settings saved successfully');
      } else {
        showMessage('error', 'Failed to save settings');
      }
    } catch (error) {
      console.error('Error saving settings:', error);
      showMessage('error', 'Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const resetCategory = async () => {
    if (!confirm(`Reset ${activeTab} settings to defaults?`)) return;
    
    try {
      const response = await fetch(`http://localhost:8000/api/settings/reset?category=${activeTab}`, {
        method: 'POST'
      });
      
      const data = await response.json();
      if (data.success) {
        setSettings(data.settings);
        showMessage('success', 'Settings reset to defaults');
      }
    } catch (error) {
      console.error('Error resetting settings:', error);
      showMessage('error', 'Failed to reset settings');
    }
  };

  const exportSettings = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/settings/export/json');
      const data = await response.json();
      
      if (data.success) {
        const blob = new Blob([data.settings_json], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `peft-studio-settings-${new Date().toISOString().split('T')[0]}.json`;
        a.click();
        URL.revokeObjectURL(url);
        showMessage('success', 'Settings exported successfully');
      }
    } catch (error) {
      console.error('Error exporting settings:', error);
      showMessage('error', 'Failed to export settings');
    }
  };

  const importSettings = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    
    try {
      const text = await file.text();
      const response = await fetch('http://localhost:8000/api/settings/import', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ settings_json: text })
      });
      
      const data = await response.json();
      if (data.success) {
        setSettings(data.settings);
        showMessage('success', 'Settings imported successfully');
      } else {
        showMessage('error', 'Failed to import settings');
      }
    } catch (error) {
      console.error('Error importing settings:', error);
      showMessage('error', 'Failed to import settings');
    }
    
    // Reset file input
    event.target.value = '';
  };

  const renderAppearanceTab = () => {
    if (!settings) return null;
    
    return (
      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium mb-2">Theme</label>
          <select
            value={settings.appearance.theme}
            onChange={(e) => updateSetting('appearance', 'theme', e.target.value)}
            className="w-full px-3 py-2 border rounded-lg bg-white dark:bg-gray-800"
          >
            <option value="dark">Dark</option>
            <option value="light">Light</option>
            <option value="auto">Auto (System)</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Accent Color</label>
          <select
            value={settings.appearance.accentColor}
            onChange={(e) => updateSetting('appearance', 'accentColor', e.target.value)}
            className="w-full px-3 py-2 border rounded-lg bg-white dark:bg-gray-800"
          >
            <option value="blue">Blue</option>
            <option value="purple">Purple</option>
            <option value="green">Green</option>
            <option value="orange">Orange</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Font Size</label>
          <select
            value={settings.appearance.fontSize}
            onChange={(e) => updateSetting('appearance', 'fontSize', e.target.value)}
            className="w-full px-3 py-2 border rounded-lg bg-white dark:bg-gray-800"
          >
            <option value="small">Small</option>
            <option value="medium">Medium</option>
            <option value="large">Large</option>
          </select>
        </div>

        <div className="flex items-center justify-between">
          <div>
            <div className="font-medium">Compact Mode</div>
            <div className="text-sm text-gray-500">Reduce spacing for more content</div>
          </div>
          <input
            type="checkbox"
            checked={settings.appearance.compactMode}
            onChange={(e) => updateSetting('appearance', 'compactMode', e.target.checked)}
            className="w-4 h-4"
          />
        </div>
      </div>
    );
  };

  const renderNotificationsTab = () => {
    if (!settings) return null;
    
    const notificationOptions = [
      { key: 'enabled', label: 'Enable Notifications', description: 'Master switch for all notifications' },
      { key: 'trainingComplete', label: 'Training Complete', description: 'Notify when training finishes' },
      { key: 'trainingFailed', label: 'Training Failed', description: 'Notify when training fails' },
      { key: 'deploymentReady', label: 'Deployment Ready', description: 'Notify when deployment is ready' },
      { key: 'systemUpdates', label: 'System Updates', description: 'Notify about app updates' },
      { key: 'soundEnabled', label: 'Sound', description: 'Play sound with notifications' },
      { key: 'desktopNotifications', label: 'Desktop Notifications', description: 'Show system notifications' },
    ];

    return (
      <div className="space-y-4">
        {notificationOptions.map((option) => (
          <div key={option.key} className="flex items-center justify-between py-3 border-b">
            <div>
              <div className="font-medium">{option.label}</div>
              <div className="text-sm text-gray-500">{option.description}</div>
            </div>
            <input
              type="checkbox"
              checked={settings.notifications[option.key as keyof typeof settings.notifications] as boolean}
              onChange={(e) => updateSetting('notifications', option.key, e.target.checked)}
              className="w-4 h-4"
            />
          </div>
        ))}
      </div>
    );
  };

  const renderProvidersTab = () => {
    if (!settings) return null;
    
    return (
      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium mb-2">Default Compute Provider</label>
          <select
            value={settings.providers.defaultCompute}
            onChange={(e) => updateSetting('providers', 'defaultCompute', e.target.value)}
            className="w-full px-3 py-2 border rounded-lg bg-white dark:bg-gray-800"
          >
            <option value="local">Local GPU</option>
            <option value="runpod">RunPod</option>
            <option value="lambda">Lambda Labs</option>
            <option value="vastai">Vast.ai</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Default Model Registry</label>
          <select
            value={settings.providers.defaultRegistry}
            onChange={(e) => updateSetting('providers', 'defaultRegistry', e.target.value)}
            className="w-full px-3 py-2 border rounded-lg bg-white dark:bg-gray-800"
          >
            <option value="huggingface">HuggingFace</option>
            <option value="civitai">Civitai</option>
            <option value="ollama">Ollama</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Default Experiment Tracker</label>
          <select
            value={settings.providers.defaultTracker || ''}
            onChange={(e) => updateSetting('providers', 'defaultTracker', e.target.value || null)}
            className="w-full px-3 py-2 border rounded-lg bg-white dark:bg-gray-800"
          >
            <option value="">None</option>
            <option value="wandb">Weights & Biases</option>
            <option value="cometml">Comet ML</option>
            <option value="phoenix">Arize Phoenix</option>
          </select>
        </div>

        <div className="flex items-center justify-between">
          <div>
            <div className="font-medium">Auto-Select Cheapest</div>
            <div className="text-sm text-gray-500">Automatically select the cheapest provider</div>
          </div>
          <input
            type="checkbox"
            checked={settings.providers.autoSelectCheapest}
            onChange={(e) => updateSetting('providers', 'autoSelectCheapest', e.target.checked)}
            className="w-4 h-4"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Preferred Region</label>
          <select
            value={settings.providers.preferredRegion}
            onChange={(e) => updateSetting('providers', 'preferredRegion', e.target.value)}
            className="w-full px-3 py-2 border rounded-lg bg-white dark:bg-gray-800"
          >
            <option value="us-east">US East</option>
            <option value="us-west">US West</option>
            <option value="eu-west">EU West</option>
            <option value="ap-southeast">AP Southeast</option>
          </select>
        </div>
      </div>
    );
  };

  const renderDataRetentionTab = () => {
    if (!settings) return null;
    
    return (
      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium mb-2">Keep Logs (days)</label>
          <input
            type="number"
            min="1"
            value={settings.dataRetention.keepLogs}
            onChange={(e) => updateSetting('dataRetention', 'keepLogs', parseInt(e.target.value))}
            className="w-full px-3 py-2 border rounded-lg bg-white dark:bg-gray-800"
          />
          <p className="text-sm text-gray-500 mt-1">Logs older than this will be deleted</p>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Keep Checkpoints (days)</label>
          <input
            type="number"
            min="1"
            value={settings.dataRetention.keepCheckpoints}
            onChange={(e) => updateSetting('dataRetention', 'keepCheckpoints', parseInt(e.target.value))}
            className="w-full px-3 py-2 border rounded-lg bg-white dark:bg-gray-800"
          />
          <p className="text-sm text-gray-500 mt-1">Checkpoints older than this will be deleted</p>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Keep Failed Runs (days)</label>
          <input
            type="number"
            min="1"
            value={settings.dataRetention.keepFailedRuns}
            onChange={(e) => updateSetting('dataRetention', 'keepFailedRuns', parseInt(e.target.value))}
            className="w-full px-3 py-2 border rounded-lg bg-white dark:bg-gray-800"
          />
          <p className="text-sm text-gray-500 mt-1">Failed runs older than this will be deleted</p>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Max Cache Size (MB)</label>
          <input
            type="number"
            min="100"
            step="100"
            value={settings.dataRetention.maxCacheSize}
            onChange={(e) => updateSetting('dataRetention', 'maxCacheSize', parseInt(e.target.value))}
            className="w-full px-3 py-2 border rounded-lg bg-white dark:bg-gray-800"
          />
          <p className="text-sm text-gray-500 mt-1">Maximum size for cached data</p>
        </div>

        <div className="flex items-center justify-between">
          <div>
            <div className="font-medium">Auto Cleanup</div>
            <div className="text-sm text-gray-500">Automatically clean up old data</div>
          </div>
          <input
            type="checkbox"
            checked={settings.dataRetention.autoCleanup}
            onChange={(e) => updateSetting('dataRetention', 'autoCleanup', e.target.checked)}
            className="w-4 h-4"
          />
        </div>
      </div>
    );
  };

  const renderTrainingTab = () => {
    if (!settings) return null;
    
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <div className="font-medium">Auto-Save Checkpoints</div>
            <div className="text-sm text-gray-500">Automatically save training checkpoints</div>
          </div>
          <input
            type="checkbox"
            checked={settings.training.autoSaveCheckpoints}
            onChange={(e) => updateSetting('training', 'autoSaveCheckpoints', e.target.checked)}
            className="w-4 h-4"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Checkpoint Interval (steps)</label>
          <input
            type="number"
            min="1"
            value={settings.training.checkpointInterval}
            onChange={(e) => updateSetting('training', 'checkpointInterval', parseInt(e.target.value))}
            className="w-full px-3 py-2 border rounded-lg bg-white dark:bg-gray-800"
          />
          <p className="text-sm text-gray-500 mt-1">Save checkpoint every N steps</p>
        </div>

        <div className="flex items-center justify-between">
          <div>
            <div className="font-medium">Enable Telemetry</div>
            <div className="text-sm text-gray-500">Send anonymous usage data to improve the app</div>
          </div>
          <input
            type="checkbox"
            checked={settings.training.enableTelemetry}
            onChange={(e) => updateSetting('training', 'enableTelemetry', e.target.checked)}
            className="w-4 h-4"
          />
        </div>

        <div className="flex items-center justify-between">
          <div>
            <div className="font-medium">Auto-Resume</div>
            <div className="text-sm text-gray-500">Automatically resume failed training runs</div>
          </div>
          <input
            type="checkbox"
            checked={settings.training.autoResume}
            onChange={(e) => updateSetting('training', 'autoResume', e.target.checked)}
            className="w-4 h-4"
          />
        </div>
      </div>
    );
  };

  const renderAdvancedTab = () => {
    if (!settings) return null;
    
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <div className="font-medium">Debug Mode</div>
            <div className="text-sm text-gray-500">Enable verbose logging for troubleshooting</div>
          </div>
          <input
            type="checkbox"
            checked={settings.advanced.enableDebugMode}
            onChange={(e) => updateSetting('advanced', 'enableDebugMode', e.target.checked)}
            className="w-4 h-4"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Log Level</label>
          <select
            value={settings.advanced.logLevel}
            onChange={(e) => updateSetting('advanced', 'logLevel', e.target.value)}
            className="w-full px-3 py-2 border rounded-lg bg-white dark:bg-gray-800"
          >
            <option value="DEBUG">Debug</option>
            <option value="INFO">Info</option>
            <option value="WARNING">Warning</option>
            <option value="ERROR">Error</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Max Concurrent Runs</label>
          <input
            type="number"
            min="1"
            max="10"
            value={settings.advanced.maxConcurrentRuns}
            onChange={(e) => updateSetting('advanced', 'maxConcurrentRuns', parseInt(e.target.value))}
            className="w-full px-3 py-2 border rounded-lg bg-white dark:bg-gray-800"
          />
          <p className="text-sm text-gray-500 mt-1">Maximum number of training runs to run simultaneously</p>
        </div>

        <div className="flex items-center justify-between">
          <div>
            <div className="font-medium">Experimental Features</div>
            <div className="text-sm text-gray-500">Enable experimental and beta features</div>
          </div>
          <input
            type="checkbox"
            checked={settings.advanced.enableExperimentalFeatures}
            onChange={(e) => updateSetting('advanced', 'enableExperimentalFeatures', e.target.checked)}
            className="w-4 h-4"
          />
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p>Loading settings...</p>
        </div>
      </div>
    );
  }

  if (!settings) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <p>Failed to load settings</p>
          <button
            onClick={loadSettings}
            className="mt-4 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <SettingsIcon className="w-6 h-6" />
            <h1 className="text-2xl font-bold">Settings</h1>
          </div>
          <div className="flex gap-2">
            <button
              onClick={exportSettings}
              className="flex items-center gap-2 px-4 py-2 border rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              <Download className="w-4 h-4" />
              Export
            </button>
            <label className="flex items-center gap-2 px-4 py-2 border rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer">
              <Upload className="w-4 h-4" />
              Import
              <input
                type="file"
                accept=".json"
                onChange={importSettings}
                className="hidden"
              />
            </label>
          </div>
        </div>
      </div>

      {/* Message Banner */}
      {message && (
        <div className={cn(
          "px-6 py-3 flex items-center gap-2",
          message.type === 'success' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
        )}>
          {message.type === 'success' ? <Check className="w-5 h-5" /> : <X className="w-5 h-5" />}
          <span>{message.text}</span>
        </div>
      )}

      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <div className="w-64 bg-white dark:bg-gray-800 border-r overflow-y-auto">
          <div className="p-4 space-y-1">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={cn(
                    "w-full flex items-center gap-3 px-4 py-3 rounded-lg text-left transition-colors",
                    activeTab === tab.id
                      ? "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-200"
                      : "hover:bg-gray-100 dark:hover:bg-gray-700"
                  )}
                >
                  <Icon className="w-5 h-5" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto">
          <div className="max-w-3xl mx-auto p-8">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
              {activeTab === 'appearance' && renderAppearanceTab()}
              {activeTab === 'notifications' && renderNotificationsTab()}
              {activeTab === 'providers' && renderProvidersTab()}
              {activeTab === 'dataRetention' && renderDataRetentionTab()}
              {activeTab === 'training' && renderTrainingTab()}
              {activeTab === 'advanced' && renderAdvancedTab()}
              
              {/* Action Buttons */}
              <div className="flex gap-3 mt-8 pt-6 border-t">
                <button
                  onClick={saveSettings}
                  disabled={saving}
                  className="flex items-center gap-2 px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
                >
                  <Save className="w-4 h-4" />
                  {saving ? 'Saving...' : 'Save Changes'}
                </button>
                <button
                  onClick={resetCategory}
                  className="flex items-center gap-2 px-6 py-2 border rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  <RotateCcw className="w-4 h-4" />
                  Reset to Defaults
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsComponent;
