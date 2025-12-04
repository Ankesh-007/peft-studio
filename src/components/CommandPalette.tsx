import { Search, Zap, Database, Brain, Settings, FileText } from "lucide-react";
import React, { useState, useEffect } from "react";

import { cn } from "../lib/utils";

interface Command {
  id: string;
  label: string;
  icon: React.ElementType;
  category: string;
  action: () => void;
}

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
}

const commands: Command[] = [
  {
    id: "new-training",
    label: "Start New Training",
    icon: Zap,
    category: "Actions",
    action: () => console.log("New training"),
  },
  {
    id: "upload-dataset",
    label: "Upload Dataset",
    icon: Database,
    category: "Actions",
    action: () => console.log("Upload dataset"),
  },
  {
    id: "browse-models",
    label: "Browse Models",
    icon: Brain,
    category: "Actions",
    action: () => console.log("Browse models"),
  },
  {
    id: "settings",
    label: "Open Settings",
    icon: Settings,
    category: "Navigation",
    action: () => console.log("Settings"),
  },
  {
    id: "docs",
    label: "View Documentation",
    icon: FileText,
    category: "Help",
    action: () => console.log("Docs"),
  },
];

const CommandPalette: React.FC<CommandPaletteProps> = ({ isOpen, onClose }) => {
  const [search, setSearch] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);

  const filteredCommands = commands.filter(
    (cmd) =>
      cmd.label.toLowerCase().includes(search.toLowerCase()) ||
      cmd.category.toLowerCase().includes(search.toLowerCase()),
  );

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;

      if (e.key === "Escape") {
        onClose();
      } else if (e.key === "ArrowDown") {
        e.preventDefault();
        setSelectedIndex((prev) => (prev + 1) % filteredCommands.length);
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setSelectedIndex(
          (prev) =>
            (prev - 1 + filteredCommands.length) % filteredCommands.length,
        );
      } else if (e.key === "Enter") {
        e.preventDefault();
        if (filteredCommands[selectedIndex]) {
          filteredCommands[selectedIndex].action();
          onClose();
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, selectedIndex, filteredCommands, onClose]);

  useEffect(() => {
    if (isOpen) {
      setSearch("");
      setSelectedIndex(0);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-start justify-center pt-[20vh]"
      onClick={onClose}
    >
      <div
        className="w-[600px] bg-dark-bg-secondary border border-dark-border rounded-xl shadow-2xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search Input */}
        <div className="flex items-center gap-12 p-16 border-b border-dark-border">
          <Search size={20} className="text-dark-text-tertiary" />
          <input
            type="text"
            role="searchbox"
            placeholder="Type a command or search..."
            className="flex-1 bg-transparent text-body text-dark-text-primary placeholder:text-dark-text-tertiary outline-none"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            autoFocus
          />
          <kbd className="px-8 py-4 bg-dark-bg-tertiary rounded text-tiny text-dark-text-tertiary font-mono">
            ESC
          </kbd>
        </div>

        {/* Commands List */}
        <div className="max-h-[400px] overflow-y-auto">
          {filteredCommands.length === 0 ? (
            <div className="p-32 text-center text-dark-text-tertiary">
              No commands found
            </div>
          ) : (
            <div className="p-8">
              {Object.entries(
                filteredCommands.reduce(
                  (acc, cmd) => {
                    if (!acc[cmd.category]) acc[cmd.category] = [];
                    acc[cmd.category].push(cmd);
                    return acc;
                  },
                  {} as Record<string, Command[]>,
                ),
              ).map(([category, cmds]) => (
                <div key={category} className="mb-12">
                  <div className="px-12 py-8 text-tiny text-dark-text-tertiary uppercase font-medium">
                    {category}
                  </div>
                  {cmds.map((cmd, index) => {
                    const Icon = cmd.icon;
                    const globalIndex = filteredCommands.indexOf(cmd);
                    const isSelected = globalIndex === selectedIndex;

                    return (
                      <button
                        key={cmd.id}
                        className={cn(
                          "w-full flex items-center gap-12 px-12 py-10 rounded-lg transition-all",
                          isSelected
                            ? "bg-accent-primary text-white"
                            : "text-dark-text-primary hover:bg-dark-bg-tertiary",
                        )}
                        onClick={() => {
                          cmd.action();
                          onClose();
                        }}
                        onMouseEnter={() => setSelectedIndex(globalIndex)}
                      >
                        <Icon size={18} />
                        <span className="text-body">{cmd.label}</span>
                      </button>
                    );
                  })}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-16 py-12 border-t border-dark-border bg-dark-bg-tertiary/50">
          <div className="flex items-center gap-16 text-tiny text-dark-text-tertiary">
            <div className="flex items-center gap-4">
              <kbd className="px-6 py-2 bg-dark-bg-secondary rounded font-mono">
                ↑
              </kbd>
              <kbd className="px-6 py-2 bg-dark-bg-secondary rounded font-mono">
                ↓
              </kbd>
              <span>Navigate</span>
            </div>
            <div className="flex items-center gap-4">
              <kbd className="px-6 py-2 bg-dark-bg-secondary rounded font-mono">
                ↵
              </kbd>
              <span>Select</span>
            </div>
          </div>
          <div className="text-tiny text-dark-text-tertiary">
            {filteredCommands.length} commands
          </div>
        </div>
      </div>
    </div>
  );
};

export default CommandPalette;
