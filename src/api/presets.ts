/**
 * API client for configuration preset operations
 */

import type { ConfigurationPreset, TrainingConfig } from "../types/wizard";

const API_BASE_URL = "http://127.0.0.1:8000/api";

/**
 * Convert TrainingConfig to ConfigurationPreset format
 */
export function trainingConfigToPreset(
  config: Partial<TrainingConfig>,
  id: string,
  name: string,
  description: string = "",
  tags: string[] = [],
): Omit<ConfigurationPreset, "created_at" | "updated_at"> {
  return {
    id,
    name,
    description,
    tags,
    model_name: config.modelName || "",
    model_path: config.modelPath || "",
    dataset_id: config.datasetId || "",
    dataset_path: config.datasetPath || "",
    peft_method: config.peftMethod || "lora",
    lora_r: config.loraR || 8,
    lora_alpha: config.loraAlpha || 16,
    lora_dropout: config.loraDropout || 0.1,
    target_modules: config.targetModules || [],
    learning_rate: config.learningRate || 2e-4,
    batch_size: config.batchSize || 4,
    gradient_accumulation: config.gradientAccumulation || 4,
    epochs: config.epochs || 3,
    max_steps: config.maxSteps || 0,
    warmup_steps: config.warmupSteps || 0,
    optimizer: config.optimizer || "adamw",
    scheduler: config.scheduler || "linear",
    weight_decay: config.weightDecay || 0.0,
    max_grad_norm: config.maxGradNorm || 1.0,
    precision: config.precision || "fp16",
    quantization: config.quantization || null,
    save_steps: config.saveSteps || 500,
    save_total: config.saveTotal || 3,
    eval_steps: config.evalSteps || 500,
    eval_strategy: config.evalStrategy || "steps",
  };
}

/**
 * Convert ConfigurationPreset to TrainingConfig format
 */
export function presetToTrainingConfig(
  preset: ConfigurationPreset,
): Partial<TrainingConfig> {
  return {
    modelName: preset.model_name,
    modelPath: preset.model_path,
    datasetId: preset.dataset_id,
    datasetPath: preset.dataset_path,
    peftMethod: preset.peft_method,
    loraR: preset.lora_r,
    loraAlpha: preset.lora_alpha,
    loraDropout: preset.lora_dropout,
    targetModules: preset.target_modules,
    learningRate: preset.learning_rate,
    batchSize: preset.batch_size,
    gradientAccumulation: preset.gradient_accumulation,
    epochs: preset.epochs,
    maxSteps: preset.max_steps,
    warmupSteps: preset.warmup_steps,
    optimizer: preset.optimizer,
    scheduler: preset.scheduler,
    weightDecay: preset.weight_decay,
    maxGradNorm: preset.max_grad_norm,
    precision: preset.precision,
    quantization: preset.quantization,
    saveSteps: preset.save_steps,
    saveTotal: preset.save_total,
    evalSteps: preset.eval_steps,
    evalStrategy: preset.eval_strategy,
  };
}

/**
 * Save a configuration preset
 */
export async function savePreset(
  preset: Omit<ConfigurationPreset, "created_at" | "updated_at">,
): Promise<ConfigurationPreset> {
  const response = await fetch(`${API_BASE_URL}/presets/save`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(preset),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to save preset");
  }

  const data = await response.json();
  return data.preset;
}

/**
 * List all presets with optional filtering
 */
export async function listPresets(
  search?: string,
  tags?: string[],
): Promise<ConfigurationPreset[]> {
  const params = new URLSearchParams();
  if (search) params.append("search", search);
  if (tags && tags.length > 0) params.append("tags", tags.join(","));

  const response = await fetch(`${API_BASE_URL}/presets?${params.toString()}`);

  if (!response.ok) {
    throw new Error("Failed to list presets");
  }

  const data = await response.json();
  return data.presets;
}

/**
 * Get a specific preset by ID
 */
export async function getPreset(
  presetId: string,
): Promise<ConfigurationPreset> {
  const response = await fetch(`${API_BASE_URL}/presets/${presetId}`);

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error(`Preset not found: ${presetId}`);
    }
    throw new Error("Failed to get preset");
  }

  return await response.json();
}

/**
 * Delete a preset
 */
export async function deletePreset(presetId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/presets/${presetId}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error(`Preset not found: ${presetId}`);
    }
    throw new Error("Failed to delete preset");
  }
}

/**
 * Export a preset to JSON
 */
export async function exportPreset(presetId: string): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/presets/${presetId}/export`);

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error(`Preset not found: ${presetId}`);
    }
    throw new Error("Failed to export preset");
  }

  return await response.json();
}

/**
 * Import a preset from JSON
 */
export async function importPreset(
  importData: any,
  newId?: string,
): Promise<ConfigurationPreset> {
  const response = await fetch(`${API_BASE_URL}/presets/import`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      import_data: importData,
      new_id: newId,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to import preset");
  }

  const data = await response.json();
  return data.preset;
}

/**
 * Update an existing preset
 */
export async function updatePreset(
  presetId: string,
  updates: Partial<ConfigurationPreset>,
): Promise<ConfigurationPreset> {
  const response = await fetch(`${API_BASE_URL}/presets/${presetId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ updates }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to update preset");
  }

  const data = await response.json();
  return data.preset;
}

/**
 * Download preset as JSON file
 */
export async function downloadPresetAsFile(
  presetId: string,
  filename?: string,
): Promise<void> {
  const exportData = await exportPreset(presetId);

  const blob = new Blob([JSON.stringify(exportData, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename || `preset-${presetId}.json`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Upload and import preset from file
 */
export async function uploadPresetFile(
  file: File,
  newId?: string,
): Promise<ConfigurationPreset> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();

    reader.onload = async (e) => {
      try {
        const content = e.target?.result as string;
        const importData = JSON.parse(content);
        const preset = await importPreset(importData, newId);
        resolve(preset);
      } catch (error) {
        reject(error);
      }
    };

    reader.onerror = () => reject(new Error("Failed to read file"));
    reader.readAsText(file);
  });
}
