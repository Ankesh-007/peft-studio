import React, { useRef, useEffect } from "react";

import { cn } from "../lib/utils";

export interface CodeEditorProps {
  value: string;
  onChange: (value: string) => void;
  language?: "json" | "python" | "yaml" | "javascript";
  height?: string;
  readOnly?: boolean;
  showLineNumbers?: boolean;
  theme?: "dark" | "light";
  error?: string;
  "aria-label": string;
  className?: string;
}

export const CodeEditor: React.FC<CodeEditorProps> = ({
  value,
  onChange,
  language = "json",
  height = "300px",
  readOnly = false,
  showLineNumbers = true,
  theme = "light",
  error,
  "aria-label": ariaLabel,
  className,
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const lineNumbersRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (textareaRef.current && lineNumbersRef.current) {
      const lineCount = value.split("\n").length;
      const lineNumbers = Array.from({ length: lineCount }, (_, i) => i + 1).join("\n");
      lineNumbersRef.current.textContent = lineNumbers;
    }
  }, [value]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Tab") {
      e.preventDefault();
      const start = e.currentTarget.selectionStart;
      const end = e.currentTarget.selectionEnd;
      const newValue = value.substring(0, start) + "  " + value.substring(end);
      onChange(newValue);

      setTimeout(() => {
        if (textareaRef.current) {
          textareaRef.current.selectionStart = textareaRef.current.selectionEnd = start + 2;
        }
      }, 0);
    }
  };

  const handleScroll = (e: React.UIEvent<HTMLTextAreaElement>) => {
    if (lineNumbersRef.current) {
      lineNumbersRef.current.scrollTop = e.currentTarget.scrollTop;
    }
  };

  return (
    <div className={cn("space-y-2", className)}>
      <div
        className={cn(
          "relative border rounded-md overflow-hidden",
          error ? "border-red-500" : "border-gray-300",
          theme === "dark" ? "bg-gray-900" : "bg-white"
        )}
        style={{ height }}
      >
        <div className="flex h-full">
          {showLineNumbers && (
            <div
              ref={lineNumbersRef}
              className={cn(
                "flex-shrink-0 w-12 py-3 px-2 text-right text-sm font-mono overflow-hidden select-none",
                theme === "dark" ? "bg-gray-800 text-gray-500" : "bg-gray-50 text-gray-400"
              )}
              aria-hidden="true"
            />
          )}

          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={handleKeyDown}
            onScroll={handleScroll}
            readOnly={readOnly}
            aria-label={ariaLabel}
            spellCheck={false}
            className={cn(
              "flex-1 p-3 font-mono text-sm resize-none outline-none",
              theme === "dark" ? "bg-gray-900 text-gray-100" : "bg-white text-gray-900",
              readOnly && "cursor-not-allowed"
            )}
            style={{
              tabSize: 2,
              lineHeight: "1.5",
            }}
          />
        </div>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="flex items-center justify-between text-xs text-gray-500">
        <span>Language: {language.toUpperCase()}</span>
        <span>{value.split("\n").length} lines</span>
      </div>
    </div>
  );
};
