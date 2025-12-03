import React, { useState, useEffect } from 'react';
import { ModelSearchFilters } from '../types/model';

interface ModelSearchBarProps {
  onSearch: (filters: ModelSearchFilters) => void;
  initialFilters?: ModelSearchFilters;
}

const ModelSearchBar: React.FC<ModelSearchBarProps> = ({ onSearch, initialFilters }) => {
  const [query, setQuery] = useState(initialFilters?.query || '');
  const [task, setTask] = useState(initialFilters?.task || 'text-generation');

  useEffect(() => {
    const debounceTimer = setTimeout(() => {
      if (query.length >= 3 || query.length === 0) {
        onSearch({ query, task });
      }
    }, 500);

    return () => clearTimeout(debounceTimer);
  }, [query, task, onSearch]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch({ query, task });
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <div className="flex-1 relative">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search models by name, author, or tags..."
          className="w-full px-4 py-2 pl-10 border border-gray-300 dark:border-gray-600 rounded-lg 
                   bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                   focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <svg
          className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
      </div>

      <select
        value={task}
        onChange={(e) => setTask(e.target.value)}
        className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg
                 bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
      >
        <option value="text-generation">Text Generation</option>
        <option value="text-classification">Text Classification</option>
        <option value="token-classification">Token Classification</option>
        <option value="question-answering">Question Answering</option>
        <option value="summarization">Summarization</option>
        <option value="translation">Translation</option>
        <option value="conversational">Conversational</option>
      </select>

      <button
        type="submit"
        className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 
                 transition-colors font-medium"
      >
        Search
      </button>
    </form>
  );
};

export default ModelSearchBar;
