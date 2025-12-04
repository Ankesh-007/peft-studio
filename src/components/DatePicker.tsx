import { Calendar, ChevronLeft, ChevronRight } from 'lucide-react';
import React, { useState, useRef, useEffect } from 'react';

import { cn } from '../lib/utils';

export interface DatePickerProps {
  value: Date | null;
  onChange: (date: Date | null) => void;
  label?: string;
  placeholder?: string;
  disabled?: boolean;
  error?: string;
  minDate?: Date;
  maxDate?: Date;
  'aria-label': string;
  className?: string;
}

export const DatePicker: React.FC<DatePickerProps> = ({
  value,
  onChange,
  label,
  placeholder = 'Select date...',
  disabled = false,
  error,
  minDate,
  maxDate,
  'aria-label': ariaLabel,
  className,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [viewDate, setViewDate] = useState(value || new Date());
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const daysInMonth = (date: Date) => {
    return new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
  };

  const firstDayOfMonth = (date: Date) => {
    return new Date(date.getFullYear(), date.getMonth(), 1).getDay();
  };

  const handlePrevMonth = () => {
    setViewDate(new Date(viewDate.getFullYear(), viewDate.getMonth() - 1));
  };

  const handleNextMonth = () => {
    setViewDate(new Date(viewDate.getFullYear(), viewDate.getMonth() + 1));
  };

  const handleDateSelect = (day: number) => {
    const selectedDate = new Date(viewDate.getFullYear(), viewDate.getMonth(), day);
    
    if (minDate && selectedDate < minDate) return;
    if (maxDate && selectedDate > maxDate) return;
    
    onChange(selectedDate);
    setIsOpen(false);
  };

  const isDateDisabled = (day: number) => {
    const date = new Date(viewDate.getFullYear(), viewDate.getMonth(), day);
    if (minDate && date < minDate) return true;
    if (maxDate && date > maxDate) return true;
    return false;
  };

  const isDateSelected = (day: number) => {
    if (!value) return false;
    return (
      value.getDate() === day &&
      value.getMonth() === viewDate.getMonth() &&
      value.getFullYear() === viewDate.getFullYear()
    );
  };

  const formatDate = (date: Date | null) => {
    if (!date) return '';
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
  };

  const renderCalendar = () => {
    const days = [];
    const totalDays = daysInMonth(viewDate);
    const firstDay = firstDayOfMonth(viewDate);

    // Empty cells for days before month starts
    for (let i = 0; i < firstDay; i++) {
      days.push(<div key={`empty-${i}`} className="p-2" />);
    }

    // Days of the month
    for (let day = 1; day <= totalDays; day++) {
      const disabled = isDateDisabled(day);
      const selected = isDateSelected(day);

      days.push(
        <button
          key={day}
          type="button"
          onClick={() => !disabled && handleDateSelect(day)}
          disabled={disabled}
          className={cn(
            'p-2 text-sm rounded hover:bg-gray-100 transition-colors',
            selected && 'bg-blue-600 text-white hover:bg-blue-700',
            disabled && 'opacity-50 cursor-not-allowed hover:bg-transparent',
            !selected && !disabled && 'text-gray-900'
          )}
        >
          {day}
        </button>
      );
    }

    return days;
  };

  return (
    <div ref={containerRef} className={cn('relative', className)}>
      {label && <label className="block text-sm font-medium text-gray-700 mb-2">{label}</label>}
      
      <button
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        aria-label={ariaLabel}
        className={cn(
          'w-full px-3 py-2 border rounded-md text-left flex items-center justify-between',
          'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
          error ? 'border-red-500' : 'border-gray-300',
          disabled && 'bg-gray-100 cursor-not-allowed opacity-50'
        )}
      >
        <span className={value ? 'text-gray-900' : 'text-gray-400'}>
          {value ? formatDate(value) : placeholder}
        </span>
        <Calendar className="w-4 h-4 text-gray-400" />
      </button>

      {isOpen && (
        <div className="absolute z-50 mt-1 bg-white border border-gray-300 rounded-md shadow-lg p-4">
          <div className="flex items-center justify-between mb-4">
            <button
              type="button"
              onClick={handlePrevMonth}
              className="p-1 hover:bg-gray-100 rounded"
              aria-label="Previous month"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
            <span className="font-semibold text-gray-900">
              {viewDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
            </span>
            <button
              type="button"
              onClick={handleNextMonth}
              className="p-1 hover:bg-gray-100 rounded"
              aria-label="Next month"
            >
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>

          <div className="grid grid-cols-7 gap-1">
            {['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'].map(day => (
              <div key={day} className="p-2 text-xs font-semibold text-gray-500 text-center">
                {day}
              </div>
            ))}
            {renderCalendar()}
          </div>
        </div>
      )}

      {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
    </div>
  );
};
