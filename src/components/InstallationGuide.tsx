import React, { useState } from 'react';
import { Download, Monitor, Apple, Terminal } from 'lucide-react';

type Platform = 'windows' | 'macos' | 'linux';

interface PlatformInstruction {
  icon: React.ReactNode;
  title: string;
  steps: string[];
  downloadFile: string;
}

export const InstallationGuide: React.FC = () => {
  const [selectedPlatform, setSelectedPlatform] = useState<Platform>('windows');

  const instructions: Record<Platform, PlatformInstruction> = {
    windows: {
      icon: <Monitor className="w-8 h-8" />,
      title: 'Windows',
      steps: [
        'Download PEFT-Studio-Setup.exe from releases',
        'Run the installer',
        'Follow the installation wizard',
        'Launch PEFT Studio from the Start Menu',
      ],
      downloadFile: 'PEFT-Studio-Setup.exe',
    },
    macos: {
      icon: <Apple className="w-8 h-8" />,
      title: 'macOS',
      steps: [
        'Download PEFT-Studio.dmg from releases',
        'Open the DMG file',
        'Drag PEFT Studio to Applications',
        'Launch from Applications folder',
      ],
      downloadFile: 'PEFT-Studio.dmg',
    },
    linux: {
      icon: <Terminal className="w-8 h-8" />,
      title: 'Linux',
      steps: [
        'Download PEFT-Studio.AppImage from releases',
        'Make it executable: chmod +x PEFT-Studio.AppImage',
        'Run: ./PEFT-Studio.AppImage',
      ],
      downloadFile: 'PEFT-Studio.AppImage',
    },
  };

  const currentInstruction = instructions[selectedPlatform];

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Installation Guide</h1>
        <p className="text-gray-600">
          Choose your platform and follow the installation steps
        </p>
      </div>

      {/* Platform Selector */}
      <div className="flex gap-4 mb-8">
        {(Object.keys(instructions) as Platform[]).map((platform) => (
          <button
            key={platform}
            onClick={() => setSelectedPlatform(platform)}
            className={`flex items-center gap-3 px-6 py-4 rounded-lg border-2 transition-all ${
              selectedPlatform === platform
                ? 'border-blue-500 bg-blue-50 text-blue-700'
                : 'border-gray-200 hover:border-gray-300 bg-white'
            }`}
          >
            {instructions[platform].icon}
            <span className="font-semibold">{instructions[platform].title}</span>
          </button>
        ))}
      </div>

      {/* Installation Steps */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="flex items-center gap-3 mb-6">
          {currentInstruction.icon}
          <h2 className="text-2xl font-bold">{currentInstruction.title} Installation</h2>
        </div>

        <div className="space-y-4">
          {currentInstruction.steps.map((step, index) => (
            <div key={index} className="flex gap-4">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-500 text-white flex items-center justify-center font-semibold">
                {index + 1}
              </div>
              <div className="flex-1 pt-1">
                <p className="text-gray-800">{step}</p>
                {step.includes('chmod') || step.includes('./') ? (
                  <code className="block mt-2 bg-gray-100 px-3 py-2 rounded text-sm font-mono">
                    {step.split(': ')[1]}
                  </code>
                ) : null}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Download Button */}
      <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg shadow-md p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-xl font-bold mb-2">Ready to install?</h3>
            <p className="text-blue-100">Download {currentInstruction.downloadFile}</p>
          </div>
          <a
            href="https://github.com/yourusername/peft-studio/releases/latest"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 bg-white text-blue-600 px-6 py-3 rounded-lg font-semibold hover:bg-blue-50 transition-colors"
          >
            <Download className="w-5 h-5" />
            Download
          </a>
        </div>
      </div>

      {/* System Requirements */}
      <div className="mt-8 bg-gray-50 rounded-lg p-6">
        <h3 className="text-lg font-bold mb-4">System Requirements</h3>
        <div className="grid md:grid-cols-3 gap-6">
          <div>
            <h4 className="font-semibold mb-2">Windows</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• Windows 10 or later</li>
              <li>• 4GB RAM minimum</li>
              <li>• 2GB disk space</li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold mb-2">macOS</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• macOS 10.15 or later</li>
              <li>• 4GB RAM minimum</li>
              <li>• 2GB disk space</li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold mb-2">Linux</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• Ubuntu 20.04+ or equivalent</li>
              <li>• 4GB RAM minimum</li>
              <li>• 2GB disk space</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};
