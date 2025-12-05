import { Search, Bell, Plus, Sun, Moon, Command } from "lucide-react";
import React, { useState, useEffect } from "react";

import { cn } from "../lib/utils";

import CommandPalette from "./CommandPalette";

interface TopBarProps {
  onToggleRightPanel: () => void;
}

const TopBar: React.FC<TopBarProps> = ({ onToggleRightPanel }) => {
  const [searchFocused, setSearchFocused] = useState(false);
  const [theme, setTheme] = useState<"dark" | "light">("dark");
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setCommandPaletteOpen(true);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <>
      <CommandPalette isOpen={commandPaletteOpen} onClose={() => setCommandPaletteOpen(false)} />
      <div className="h-[56px] bg-dark-bg-secondary/80 backdrop-blur-lg border-b border-dark-border px-24 flex items-center justify-between sticky top-0 z-50">
        {/* Left: Breadcrumb */}
        <div className="flex items-center gap-8 text-small">
          <span className="text-dark-text-primary font-medium">Dashboard</span>
          <span className="text-dark-text-tertiary">/</span>
          <span className="text-dark-text-secondary">Overview</span>
        </div>

        {/* Center: Search */}
        <div className="flex-1 max-w-[400px] mx-32">
          <div
            className={cn(
              "relative flex items-center cursor-pointer",
              searchFocused && "ring-1 ring-accent-primary rounded-lg"
            )}
            onClick={() => setCommandPaletteOpen(true)}
          >
            <Search size={16} className="absolute left-12 text-dark-text-tertiary" />
            <input
              type="text"
              placeholder="Search datasets, models, or runs..."
              className="input w-full pl-40 pr-60 cursor-pointer"
              onFocus={() => setSearchFocused(true)}
              onBlur={() => setSearchFocused(false)}
              readOnly
            />
            <div className="absolute right-12 flex items-center gap-4 text-tiny text-dark-text-tertiary font-mono">
              <Command size={12} />
              <span>K</span>
            </div>
          </div>
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-12">
          {/* New Training Button */}
          <button className="btn-primary flex items-center gap-8">
            <Plus size={16} />
            <span>New Training</span>
          </button>

          {/* Notifications */}
          <button className="relative p-8 hover:bg-dark-bg-tertiary rounded-lg transition-all">
            <Bell size={20} className="text-dark-text-secondary" />
            <span className="absolute top-6 right-6 w-8 h-8 bg-accent-error rounded-full"></span>
          </button>

          {/* Theme Toggle */}
          <button
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            className="p-8 hover:bg-dark-bg-tertiary rounded-lg transition-all"
          >
            {theme === "dark" ? (
              <Sun size={20} className="text-dark-text-secondary" />
            ) : (
              <Moon size={20} className="text-dark-text-secondary" />
            )}
          </button>

          {/* Help Panel Toggle */}
          <button
            onClick={onToggleRightPanel}
            className="p-8 hover:bg-dark-bg-tertiary rounded-lg transition-all text-dark-text-secondary text-small"
          >
            ?
          </button>
        </div>
      </div>
    </>
  );
};

export default TopBar;
