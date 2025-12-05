import React, { useState } from "react";

import Sidebar from "./Sidebar";
import TopBar from "./TopBar";
import { OfflineIndicator } from "./OfflineIndicator";

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [rightPanelOpen, setRightPanelOpen] = useState(false);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-dark-bg-primary">
      {/* Skip to main content link for keyboard navigation */}
      <a href="#main-content" className="skip-to-main">
        Skip to main content
      </a>

      {/* Left Sidebar */}
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Bar */}
        <TopBar onToggleRightPanel={() => setRightPanelOpen(!rightPanelOpen)} />

        {/* Content */}
        <main
          id="main-content"
          className="flex-1 overflow-auto p-24 focus:outline-none"
          tabIndex={-1}
          role="main"
          aria-label="Main content"
        >
          <div className="max-w-[1200px] mx-auto">{children}</div>
        </main>
      </div>

      {/* Right Panel (collapsible) */}
      {rightPanelOpen && (
        <aside
          className="w-[320px] bg-dark-bg-secondary border-l border-dark-border p-20 overflow-auto animate-slide-down"
          role="complementary"
          aria-label="Quick help panel"
        >
          <div className="flex items-center justify-between mb-20">
            <h3 className="text-h3">Quick Help</h3>
            <button
              onClick={() => setRightPanelOpen(false)}
              className="text-dark-text-tertiary hover:text-dark-text-primary focus-visible-ring rounded p-2"
              aria-label="Close help panel"
            >
              ✕
            </button>
          </div>
          <div className="space-y-16">
            <section className="text-small text-dark-text-secondary">
              <h4 className="mb-8 font-medium">Keyboard Shortcuts:</h4>
              <ul className="space-y-4 font-mono text-tiny" role="list">
                <li>
                  <kbd className="px-2 py-1 bg-dark-bg-tertiary rounded">
                    ⌘K
                  </kbd>{" "}
                  - Command Palette
                </li>
                <li>
                  <kbd className="px-2 py-1 bg-dark-bg-tertiary rounded">
                    ⌘N
                  </kbd>{" "}
                  - New Training
                </li>
                <li>
                  <kbd className="px-2 py-1 bg-dark-bg-tertiary rounded">
                    ⌘O
                  </kbd>{" "}
                  - Open Dataset
                </li>
                <li>
                  <kbd className="px-2 py-1 bg-dark-bg-tertiary rounded">
                    ⌘,
                  </kbd>{" "}
                  - Settings
                </li>
              </ul>
            </section>
          </div>
        </aside>
      )}

      {/* Offline Indicator - Fixed position in bottom-right */}
      <OfflineIndicator />
    </div>
  );
};

export default Layout;
