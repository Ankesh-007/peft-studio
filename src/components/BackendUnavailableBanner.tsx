import React from 'react';
import { AlertTriangle, ExternalLink, RefreshCw } from 'lucide-react';

export const BackendUnavailableBanner: React.FC = () => {
  const handleRefresh = () => {
    window.location.reload();
  };

  const handleOpenDocs = () => {
    window.open('https://github.com/Ankesh-007/peft-studio#-quick-installation', '_blank');
  };

  return (
    <div className="bg-yellow-50 border-b border-yellow-200">
      <div className="max-w-7xl mx-auto py-3 px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between flex-wrap">
          <div className="w-0 flex-1 flex items-center">
            <span className="flex p-2 rounded-lg bg-yellow-100">
              <AlertTriangle className="h-5 w-5 text-yellow-600" aria-hidden="true" />
            </span>
            <p className="ml-3 font-medium text-yellow-800">
              <span className="md:hidden">Backend service unavailable</span>
              <span className="hidden md:inline">
                Backend service is not running. Training and model management features are unavailable.
              </span>
            </p>
          </div>
          <div className="order-3 mt-2 flex-shrink-0 w-full sm:order-2 sm:mt-0 sm:w-auto">
            <div className="flex space-x-2">
              <button
                onClick={handleOpenDocs}
                className="flex items-center justify-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-yellow-800 bg-yellow-100 hover:bg-yellow-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-yellow-500"
              >
                <ExternalLink className="h-4 w-4 mr-2" />
                Setup Guide
              </button>
              <button
                onClick={handleRefresh}
                className="flex items-center justify-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-yellow-600 hover:bg-yellow-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-yellow-500"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Retry
              </button>
            </div>
          </div>
        </div>
        <div className="mt-2 text-sm text-yellow-700">
          <p className="font-semibold">To enable full functionality:</p>
          <ol className="list-decimal list-inside mt-1 space-y-1">
            <li>Install Python 3.10 or higher from <a href="https://www.python.org/downloads/" target="_blank" rel="noopener noreferrer" className="underline hover:text-yellow-900">python.org</a></li>
            <li>Install dependencies: <code className="bg-yellow-100 px-2 py-0.5 rounded">pip install -r backend/requirements.txt</code></li>
            <li>Restart the application</li>
          </ol>
        </div>
      </div>
    </div>
  );
};
