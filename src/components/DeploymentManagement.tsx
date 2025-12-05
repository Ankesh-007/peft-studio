/**
 * Deployment Management
 *
 * Main component for deployment management system.
 * Integrates wizard, dashboard, testing, and metrics views.
 *
 * Requirements: 9.1, 9.2, 9.3, 9.4, 9.5
 */

import React, { useState } from "react";
import { DeploymentConfigurationWizard } from "./DeploymentConfigurationWizard";
import { DeploymentDashboard } from "./DeploymentDashboard";
import { EndpointTestingInterface } from "./EndpointTestingInterface";
import { DeploymentMetricsView } from "./DeploymentMetricsView";

type View = "dashboard" | "wizard" | "testing" | "metrics";

interface DeploymentConfig {
  deployment_id: string;
  name: string;
  platform: string;
  model_path: string;
  base_model?: string;
  instance_type?: string;
  min_instances: number;
  max_instances: number;
  auto_scaling: boolean;
  max_batch_size: number;
  timeout_seconds: number;
  environment_vars: Record<string, string>;
  description?: string;
  tags: string[];
}

export const DeploymentManagement: React.FC = () => {
  const [currentView, setCurrentView] = useState<View>("dashboard");
  const [selectedDeployment, setSelectedDeployment] = useState<{
    id: string;
    name: string;
    endpointUrl?: string;
  } | null>(null);

  // Mock available models - in real app, this would come from API
  const availableModels = [
    {
      path: "/models/my-adapter-1",
      name: "My Fine-tuned Llama 2",
      base_model: "meta-llama/Llama-2-7b-hf",
    },
    {
      path: "/models/my-adapter-2",
      name: "Custom GPT-2 Adapter",
      base_model: "gpt2",
    },
    {
      path: "/models/full-model-1",
      name: "Complete Fine-tuned Model",
    },
  ];

  const handleCreateDeployment = () => {
    setCurrentView("wizard");
  };

  const handleDeploy = async (config: DeploymentConfig) => {
    try {
      // Create deployment
      const createResponse = await fetch("/api/deployments", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
      });

      if (!createResponse.ok) {
        throw new Error("Failed to create deployment");
      }

      const deployment = await createResponse.json();

      // Deploy to platform
      const deployResponse = await fetch(`/api/deployments/${deployment.deployment_id}/deploy`, {
        method: "POST",
      });

      if (!deployResponse.ok) {
        throw new Error("Failed to deploy to platform");
      }

      // Show success message
      alert(`Deployment ${config.name} created successfully!`);

      // Return to dashboard
      setCurrentView("dashboard");
    } catch (error) {
      console.error("Deployment error:", error);
      alert(`Deployment failed: ${error instanceof Error ? error.message : "Unknown error"}`);
    }
  };

  const handleTestEndpoint = (deploymentId: string) => {
    // Fetch deployment details
    fetch(`/api/deployments/${deploymentId}`)
      .then((res) => res.json())
      .then((deployment) => {
        setSelectedDeployment({
          id: deployment.deployment_id,
          name: deployment.config.name,
          endpointUrl: deployment.endpoint?.url,
        });
        setCurrentView("testing");
      })
      .catch((error) => {
        console.error("Failed to load deployment:", error);
        alert("Failed to load deployment details");
      });
  };

  const handleStopDeployment = async (deploymentId: string) => {
    if (!confirm("Are you sure you want to stop this deployment?")) {
      return;
    }

    try {
      const response = await fetch(`/api/deployments/${deploymentId}/stop`, {
        method: "POST",
      });

      if (!response.ok) {
        throw new Error("Failed to stop deployment");
      }

      alert("Deployment stopped successfully");
      // Dashboard will auto-refresh
    } catch (error) {
      console.error("Stop deployment error:", error);
      alert(
        `Failed to stop deployment: ${error instanceof Error ? error.message : "Unknown error"}`
      );
    }
  };

  const handleViewMetrics = (deploymentId: string) => {
    // Fetch deployment details
    fetch(`/api/deployments/${deploymentId}`)
      .then((res) => res.json())
      .then((deployment) => {
        setSelectedDeployment({
          id: deployment.deployment_id,
          name: deployment.config.name,
        });
        setCurrentView("metrics");
      })
      .catch((error) => {
        console.error("Failed to load deployment:", error);
        alert("Failed to load deployment details");
      });
  };

  const handleCloseModal = () => {
    setSelectedDeployment(null);
    setCurrentView("dashboard");
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {currentView === "dashboard" && (
        <DeploymentDashboard
          onCreateDeployment={handleCreateDeployment}
          onTestEndpoint={handleTestEndpoint}
          onStopDeployment={handleStopDeployment}
          onViewMetrics={handleViewMetrics}
        />
      )}

      {currentView === "wizard" && (
        <DeploymentConfigurationWizard
          onDeploy={handleDeploy}
          onCancel={() => setCurrentView("dashboard")}
          availableModels={availableModels}
        />
      )}

      {currentView === "testing" && selectedDeployment && (
        <EndpointTestingInterface
          deploymentId={selectedDeployment.id}
          deploymentName={selectedDeployment.name}
          endpointUrl={selectedDeployment.endpointUrl || ""}
          onClose={handleCloseModal}
        />
      )}

      {currentView === "metrics" && selectedDeployment && (
        <DeploymentMetricsView
          deploymentId={selectedDeployment.id}
          deploymentName={selectedDeployment.name}
          onClose={handleCloseModal}
        />
      )}
    </div>
  );
};
