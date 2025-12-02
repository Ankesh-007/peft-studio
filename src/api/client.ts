const API_BASE_URL = "http://127.0.0.1:8000";

class APIClient {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    const response = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }

    return response.json();
  }

  // Health check
  async healthCheck() {
    return this.request("/api/health");
  }

  // Dataset operations
  async listDatasets() {
    return this.request("/api/datasets");
  }

  async uploadDataset(file: File) {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${this.baseURL}/api/datasets/upload`, {
      method: "POST",
      body: formData,
    });

    return response.json();
  }

  async deleteDataset(id: number) {
    return this.request(`/api/datasets/${id}`, { method: "DELETE" });
  }

  // Model operations
  async listModels() {
    return this.request("/api/models/local");
  }

  async searchModels(query: string) {
    return this.request(
      `/api/models/search?query=${encodeURIComponent(query)}`,
    );
  }

  async downloadModel(modelId: string) {
    return this.request("/api/models/download", {
      method: "POST",
      body: JSON.stringify({ model_id: modelId }),
    });
  }

  // Training operations
  async startTraining(config: any) {
    return this.request("/api/training/start", {
      method: "POST",
      body: JSON.stringify(config),
    });
  }

  async listTrainingRuns() {
    return this.request("/api/training/list");
  }

  async pauseTraining(id: number) {
    return this.request(`/api/training/${id}/pause`, { method: "POST" });
  }

  async stopTraining(id: number) {
    return this.request(`/api/training/${id}/stop`, { method: "POST" });
  }

  // Inference operations
  async generateText(config: any) {
    return this.request("/api/inference/generate", {
      method: "POST",
      body: JSON.stringify(config),
    });
  }

  // System operations
  async getSystemInfo() {
    return this.request("/api/system/info");
  }

  // Profile operations
  async listProfiles() {
    return this.request("/api/profiles");
  }

  async getProfile(profileId: string) {
    return this.request(`/api/profiles/${profileId}`);
  }

  async getProfileByUseCase(useCase: string) {
    return this.request(`/api/profiles/use-case/${useCase}`);
  }

  async applyProfileConfig(profileId: string, overrides?: any) {
    return this.request("/api/profiles/apply", {
      method: "POST",
      body: JSON.stringify({ profile_id: profileId, overrides }),
    });
  }

  async validateProfileCompatibility(
    profileId: string,
    gpuMemoryGb: number,
    datasetSize: number,
  ) {
    return this.request("/api/profiles/validate-compatibility", {
      method: "POST",
      body: JSON.stringify({
        profile_id: profileId,
        gpu_memory_gb: gpuMemoryGb,
        dataset_size: datasetSize,
      }),
    });
  }

  // Hardware operations
  async getHardwareProfile() {
    return this.request("/api/hardware/profile");
  }
}

export const apiClient = new APIClient();
export default APIClient;
