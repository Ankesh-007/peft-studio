/**
 * Worker Demo Component
 * 
 * Demonstrates Web Worker functionality for heavy tasks.
 * 
 * Requirements: 14.3
 */

import React, { useState } from 'react';
import { useFileProcessor, useDataProcessor, useWorkerStats } from '../hooks/useWorker';

export const WorkerDemo: React.FC = () => {
  const fileProcessor = useFileProcessor();
  const dataProcessor = useDataProcessor();
  const workerStats = useWorkerStats(1000);

  const [fileResult, setFileResult] = useState<any>(null);
  const [csvData, setCsvData] = useState<any[]>([]);
  const [metrics, setMetrics] = useState<any>(null);
  const [sortedData, setSortedData] = useState<any[]>([]);

  // Sample CSV data
  const sampleCSV = `name,age,score
Alice,25,95
Bob,30,87
Charlie,22,92
David,28,88
Eve,26,94`;

  // Sample numeric data
  const sampleNumbers = Array.from({ length: 10000 }, () => Math.random() * 100);

  // Sample data for sorting
  const sampleData = [
    { name: 'Alice', score: 95 },
    { name: 'Bob', score: 87 },
    { name: 'Charlie', score: 92 },
    { name: 'David', score: 88 },
    { name: 'Eve', score: 94 },
  ];

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const result = await fileProcessor.processFile(file);
      setFileResult(result);
    } catch (error) {
      console.error('File processing error:', error);
    }
  };

  const handleParseCSV = async () => {
    try {
      const result = await fileProcessor.parseCSV(sampleCSV, {
        delimiter: ',',
        headers: true,
      });
      setCsvData(result);
    } catch (error) {
      console.error('CSV parsing error:', error);
    }
  };

  const handleComputeMetrics = async () => {
    try {
      const result = await dataProcessor.computeMetrics(sampleNumbers, [
        'mean',
        'median',
        'std',
        'min',
        'max',
        'p95',
        'p99',
      ]);
      setMetrics(result);
    } catch (error) {
      console.error('Metrics computation error:', error);
    }
  };

  const handleSortData = async () => {
    try {
      const result = await dataProcessor.sortData(sampleData, 'score', 'desc');
      setSortedData(result);
    } catch (error) {
      console.error('Sorting error:', error);
    }
  };

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Web Worker Demo</h1>

      {/* Worker Stats */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Worker Pool Statistics</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-blue-50 p-4 rounded">
            <div className="text-sm text-gray-600">Total Workers</div>
            <div className="text-2xl font-bold text-blue-600">
              {workerStats.totalWorkers}
            </div>
          </div>
          <div className="bg-green-50 p-4 rounded">
            <div className="text-sm text-gray-600">Idle Workers</div>
            <div className="text-2xl font-bold text-green-600">
              {workerStats.idleWorkers}
            </div>
          </div>
          <div className="bg-yellow-50 p-4 rounded">
            <div className="text-sm text-gray-600">Busy Workers</div>
            <div className="text-2xl font-bold text-yellow-600">
              {workerStats.busyWorkers}
            </div>
          </div>
          <div className="bg-purple-50 p-4 rounded">
            <div className="text-sm text-gray-600">Tasks Completed</div>
            <div className="text-2xl font-bold text-purple-600">
              {workerStats.totalTasksCompleted}
            </div>
          </div>
        </div>
        <div className="mt-4 text-sm text-gray-600">
          <div>Queued Tasks: {workerStats.queuedTasks}</div>
          <div>Pending Tasks: {workerStats.pendingTasks}</div>
        </div>
      </div>

      {/* File Processing */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">File Processing</h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Upload File
            </label>
            <input
              type="file"
              onChange={handleFileUpload}
              className="block w-full text-sm text-gray-500
                file:mr-4 file:py-2 file:px-4
                file:rounded file:border-0
                file:text-sm file:font-semibold
                file:bg-blue-50 file:text-blue-700
                hover:file:bg-blue-100"
              disabled={fileProcessor.processing}
            />
          </div>
          {fileProcessor.processing && (
            <div className="text-sm text-gray-600">Processing file...</div>
          )}
          {fileResult && (
            <div className="bg-gray-50 p-4 rounded">
              <pre className="text-sm">{JSON.stringify(fileResult, null, 2)}</pre>
            </div>
          )}
        </div>
      </div>

      {/* CSV Parsing */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">CSV Parsing</h2>
        <button
          onClick={handleParseCSV}
          disabled={fileProcessor.processing}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400"
        >
          Parse Sample CSV
        </button>
        {csvData.length > 0 && (
          <div className="mt-4">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Age
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Score
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {csvData.map((row, index) => (
                  <tr key={index}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {row.name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {row.age}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {row.score}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Metrics Computation */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Metrics Computation</h2>
        <p className="text-sm text-gray-600 mb-4">
          Computing statistics for {sampleNumbers.length.toLocaleString()} random numbers
        </p>
        <button
          onClick={handleComputeMetrics}
          disabled={dataProcessor.processing}
          className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-gray-400"
        >
          Compute Metrics
        </button>
        {metrics && (
          <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(metrics).map(([key, value]) => (
              <div key={key} className="bg-gray-50 p-4 rounded">
                <div className="text-sm text-gray-600 uppercase">{key}</div>
                <div className="text-lg font-semibold">
                  {typeof value === 'number' ? value.toFixed(2) : value}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Data Sorting */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Data Sorting</h2>
        <button
          onClick={handleSortData}
          disabled={dataProcessor.processing}
          className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 disabled:bg-gray-400"
        >
          Sort by Score (Descending)
        </button>
        {sortedData.length > 0 && (
          <div className="mt-4">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Rank
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Score
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {sortedData.map((row, index) => (
                  <tr key={index}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {index + 1}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {row.name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {row.score}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default WorkerDemo;
