/**
 * Simple in-memory cache for API responses
 * Implements TTL (Time To Live) for automatic cache invalidation
 */

interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number;
}

class Cache {
  private cache: Map<string, CacheEntry<unknown>> = new Map();
  private defaultTTL: number = 5 * 60 * 1000; // 5 minutes

  /**
   * Get cached data if it exists and hasn't expired
   */
  get<T>(key: string): T | null {
    const entry = this.cache.get(key);

    if (!entry) {
      return null;
    }

    const now = Date.now();
    const age = now - entry.timestamp;

    if (age > entry.ttl) {
      // Cache expired, remove it
      this.cache.delete(key);
      return null;
    }

    return entry.data as T;
  }

  /**
   * Set cached data with optional TTL
   */
  set<T>(key: string, data: T, ttl?: number): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl: ttl || this.defaultTTL,
    });
  }

  /**
   * Check if key exists and hasn't expired
   */
  has(key: string): boolean {
    return this.get(key) !== null;
  }

  /**
   * Remove specific cache entry
   */
  invalidate(key: string): void {
    this.cache.delete(key);
  }

  /**
   * Remove all cache entries matching a pattern
   */
  invalidatePattern(pattern: string | RegExp): void {
    const regex = typeof pattern === "string" ? new RegExp(pattern) : pattern;

    for (const key of this.cache.keys()) {
      if (regex.test(key)) {
        this.cache.delete(key);
      }
    }
  }

  /**
   * Clear all cache entries
   */
  clear(): void {
    this.cache.clear();
  }

  /**
   * Get cache statistics
   */
  getStats(): { size: number; keys: string[] } {
    return {
      size: this.cache.size,
      keys: Array.from(this.cache.keys()),
    };
  }

  /**
   * Clean up expired entries
   */
  cleanup(): void {
    const now = Date.now();

    for (const [key, entry] of this.cache.entries()) {
      const age = now - entry.timestamp;
      if (age > entry.ttl) {
        this.cache.delete(key);
      }
    }
  }
}

// Singleton instance
export const cache = new Cache();

// Run cleanup every minute
if (typeof window !== "undefined") {
  setInterval(() => cache.cleanup(), 60 * 1000);
}

/**
 * Fetch with caching
 * @param url - URL to fetch
 * @param options - Fetch options
 * @param ttl - Cache TTL in milliseconds (default: 5 minutes)
 * @returns Cached or fresh data
 */
export async function fetchWithCache<T>(
  url: string,
  options?: RequestInit,
  ttl?: number
): Promise<T> {
  const cacheKey = `${url}:${JSON.stringify(options || {})}`;

  // Check cache first
  const cached = cache.get<T>(cacheKey);
  if (cached !== null) {
    return cached;
  }

  // Fetch fresh data
  const response = await fetch(url, options);

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  const data = await response.json();

  // Cache the response
  cache.set(cacheKey, data, ttl);

  return data;
}

/**
 * React hook for cached API calls
 */
import { useState, useEffect } from "react";

export function useCachedFetch<T>(
  url: string | null,
  options?: RequestInit,
  ttl?: number
): {
  data: T | null;
  loading: boolean;
  error: Error | null;
  refetch: () => void;
} {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);
  const [refetchTrigger, setRefetchTrigger] = useState(0);

  useEffect(() => {
    if (!url) {
      return;
    }

    const fetchData = async () => {
      setLoading(true);
      setError(null);

      try {
        const result = await fetchWithCache<T>(url, options, ttl);
        setData(result);
      } catch (err) {
        setError(err instanceof Error ? err : new Error("Unknown error"));
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [url, refetchTrigger, options, ttl]);

  const refetch = () => {
    // Invalidate cache and trigger refetch
    if (url) {
      cache.invalidate(`${url}:${JSON.stringify(options || {})}`);
      setRefetchTrigger((prev) => prev + 1);
    }
  };

  return { data, loading, error, refetch };
}
