import { useState, useEffect } from 'react';

/**
 * Hook for managing the contextual help panel state and keyboard shortcuts
 */
export function useHelpPanel() {
  const [isHelpOpen, setIsHelpOpen] = useState(false);
  const [currentContext, setCurrentContext] = useState<string | undefined>(undefined);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl+H to toggle help panel
      if (e.ctrlKey && e.key === 'h') {
        e.preventDefault();
        setIsHelpOpen(prev => !prev);
      }
      
      // Escape to close help panel
      if (e.key === 'Escape' && isHelpOpen) {
        e.preventDefault();
        setIsHelpOpen(false);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isHelpOpen]);

  const openHelp = (context?: string) => {
    setCurrentContext(context);
    setIsHelpOpen(true);
  };

  const closeHelp = () => {
    setIsHelpOpen(false);
    setCurrentContext(undefined);
  };

  return {
    isHelpOpen,
    currentContext,
    openHelp,
    closeHelp,
    toggleHelp: () => setIsHelpOpen(prev => !prev)
  };
}
