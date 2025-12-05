/**
 * Model types for the unified model browser
 */

export interface ModelMetadata {
  model_id: string;
  author: string;
  model_name: string;
  downloads: number;
  likes: number;
  tags: string[];
  pipeline_tag: string | null;
  library_name: string | null;
  size_mb: number | null;
  parameters: number | null;
  architecture: string | null;
  license: string | null;
  created_at?: string;
  last_modified?: string;
}

export interface ModelSearchFilters {
  query?: string;
  task?: string;
  library?: string;
  tags?: string[];
  minParameters?: number;
  maxParameters?: number;
  architectures?: string[];
  registries?: string[];
  sort?: "downloads" | "likes" | "trending";
}

export interface ModelRegistry {
  id: string;
  name: string;
  enabled: boolean;
}

export interface ModelCompatibility {
  compatible: boolean;
  warnings: string[];
  recommendations: string[];
  estimatedVRAM: number;
  estimatedTrainingTime: number;
}

export interface ModelComparison {
  models: ModelMetadata[];
  comparisonMetrics: {
    [modelId: string]: {
      downloads: number;
      likes: number;
      size_mb: number;
      parameters: number;
      license: string;
    };
  };
}

export interface CachedModel {
  model_id: string;
  cached_at: string;
  expires_at: string;
  size_bytes: number;
  path: string;
}
