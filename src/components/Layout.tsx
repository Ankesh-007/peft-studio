import React, { useState } from 'react';
import Sidebar from './Sidebar';
import TopBar from './TopBar';
import { cn } from '../lib/utils';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [rightPanelOpen, setRightPanelOpen] = useState(false);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-dark-bg-primary">
      {/* Left Sidebar */}
      <Sidebar collapsed={sidebarCollapsed} onToggle={() => setSidebarCollapsed(!sidebarCollapsed)} />
      
      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Bar */}
        <TopBar onToggleRightPanel={() => setRightPanelOpen(!rightPanelOpen)} />
        
        {/* Content */}
        <main className="flex-1 overflow-auto p-24">
          <div className="max-w-[1200px] mx-auto">
            {children}
          </div>
        </main>
      </div>
      
      {/* Right Panel (collapsible) */}
      {rightPanelOpen && (
        <div className="w-[320px] bg-dark-bg-secondary border-l border-dark-border p-20 overflow-auto">
          <div className="flex items-center justify-between mb-20">
            <h3 className="text-h3">Quick Help</h3>
            <button
              onClick={() => setRightPanelOpen(false)}
              className="text-dark-text-tertiary hover:text-dark-text-primary"
            >
              ✕
            </button>
          </div>
          <div className="space-y-16">
            <div className="text-small text-dark-text-secondary">
              <p className="mb-8">Keyboard Shortcuts:</p>
              <ul className="space-y-4 font-mono text-tiny">
                <li>⌘K - Command Palette</li>
                <li>⌘N - New Training</li>
                <li>⌘O - Open Dataset</li>
                <li>⌘, - Settings</li>
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Layout;
