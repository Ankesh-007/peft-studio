import { Menu, X } from 'lucide-react';
import React, { useEffect } from 'react';

import { cn } from '../lib/utils';

export interface MobileNavProps {
  isOpen: boolean;
  onToggle: () => void;
  children: React.ReactNode;
  className?: string;
}

export const MobileNav: React.FC<MobileNavProps> = ({
  isOpen,
  onToggle,
  children,
  className,
}) => {
  useEffect(() => {
    // Prevent body scroll when menu is open
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }

    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  useEffect(() => {
    // Close menu on escape key
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onToggle();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onToggle]);

  return (
    <>
      {/* Hamburger Button */}
      <button
        onClick={onToggle}
        className={cn(
          'fixed top-4 left-4 z-50 p-2 rounded-lg bg-white shadow-lg',
          'md:hidden focus:outline-none focus:ring-2 focus:ring-blue-500',
          className
        )}
        aria-label={isOpen ? 'Close menu' : 'Open menu'}
        aria-expanded={isOpen}
      >
        {isOpen ? (
          <X className="w-6 h-6 text-gray-700" />
        ) : (
          <Menu className="w-6 h-6 text-gray-700" />
        )}
      </button>

      {/* Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 md:hidden"
          onClick={onToggle}
          aria-hidden="true"
        />
      )}

      {/* Slide-out Drawer */}
      <div
        className={cn(
          'fixed top-0 left-0 h-full w-80 bg-white shadow-xl z-40',
          'transform transition-transform duration-300 ease-in-out',
          'md:hidden overflow-y-auto',
          isOpen ? 'translate-x-0' : '-translate-x-full'
        )}
        role="dialog"
        aria-modal="true"
        aria-label="Mobile navigation"
      >
        <div className="pt-16 pb-6 px-4">
          {children}
        </div>
      </div>
    </>
  );
};
