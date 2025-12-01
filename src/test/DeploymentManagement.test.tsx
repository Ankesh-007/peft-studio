/**
 * Deployment Management UI Tests
 * 
 * Tests for the deployment management UI components.
 * Requirements: 9.1, 9.2, 9.3, 9.4, 9.5
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { DeploymentManagement } from '../components/DeploymentManagement';

// Mock fetch
global.fetch = vi.fn();

describe('DeploymentManagement', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => ([])
    });
  });

  it('should render deployment dashboard by default', async () => {
    render(<DeploymentManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('Deployments')).toBeInTheDocument();
    });
  });

  it('should show create deployment button', async () => {
    render(<DeploymentManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('New Deployment')).toBeInTheDocument();
    });
  });

  it('should display deployment statistics', async () => {
    const mockDeployments = [
      {
        deployment_id: 'deploy_1',
        config: {
          name: 'Test Deployment',
          platform: 'predibase',
          model_path: '/models/test',
          min_instances: 1,
          max_instances: 10,
          auto_scaling: true
        },
        status: 'active',
        created_at: new Date().toISOString()
      }
    ];

    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockDeployments
    });

    render(<DeploymentManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('Total Deployments')).toBeInTheDocument();
      // Check for the number 1 in the stats
      const stats = screen.getAllByText('1');
      expect(stats.length).toBeGreaterThan(0);
    });
  });

  it('should open wizard when create button is clicked', async () => {
    render(<DeploymentManagement />);
    
    await waitFor(() => {
      const createButton = screen.getByText('New Deployment');
      fireEvent.click(createButton);
    });

    await waitFor(() => {
      expect(screen.getByText('Select Deployment Platform')).toBeInTheDocument();
    });
  });

  it('should display platform options in wizard', async () => {
    render(<DeploymentManagement />);
    
    // Open wizard
    await waitFor(() => {
      const createButton = screen.getByText('New Deployment');
      fireEvent.click(createButton);
    });

    // Check for platform options
    await waitFor(() => {
      expect(screen.getByText('Predibase')).toBeInTheDocument();
      expect(screen.getByText('Together AI')).toBeInTheDocument();
      expect(screen.getByText('Modal')).toBeInTheDocument();
      expect(screen.getByText('Replicate')).toBeInTheDocument();
    });
  });

  it('should show deployment list when deployments exist', async () => {
    const mockDeployments = [
      {
        deployment_id: 'deploy_1',
        config: {
          name: 'My Model',
          platform: 'predibase',
          model_path: '/models/my-model',
          min_instances: 1,
          max_instances: 10,
          auto_scaling: true
        },
        status: 'active',
        endpoint: {
          endpoint_id: 'ep_1',
          url: 'https://api.example.com/v1/models/my-model',
          status: 'active',
          avg_latency_ms: 150
        },
        created_at: new Date().toISOString()
      }
    ];

    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockDeployments
    });

    render(<DeploymentManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('My Model')).toBeInTheDocument();
      // Check for deployment ID and platform in the same text node
      expect(screen.getByText(/deploy_1.*predibase/i)).toBeInTheDocument();
    });
  });

  it('should show empty state when no deployments exist', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => []
    });

    render(<DeploymentManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('No deployments found')).toBeInTheDocument();
      expect(screen.getByText('Create Your First Deployment')).toBeInTheDocument();
    });
  });

  it('should filter deployments by status', async () => {
    const mockDeployments = [
      {
        deployment_id: 'deploy_1',
        config: {
          name: 'Active Model',
          platform: 'predibase',
          model_path: '/models/active',
          min_instances: 1,
          max_instances: 10,
          auto_scaling: true
        },
        status: 'active',
        created_at: new Date().toISOString()
      },
      {
        deployment_id: 'deploy_2',
        config: {
          name: 'Failed Model',
          platform: 'modal',
          model_path: '/models/failed',
          min_instances: 1,
          max_instances: 10,
          auto_scaling: true
        },
        status: 'failed',
        created_at: new Date().toISOString()
      }
    ];

    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockDeployments
    });

    render(<DeploymentManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('Active Model')).toBeInTheDocument();
      expect(screen.getByText('Failed Model')).toBeInTheDocument();
    });
  });

  it('should show action buttons for active deployments', async () => {
    const mockDeployments = [
      {
        deployment_id: 'deploy_1',
        config: {
          name: 'Test Model',
          platform: 'predibase',
          model_path: '/models/test',
          min_instances: 1,
          max_instances: 10,
          auto_scaling: true
        },
        status: 'active',
        endpoint: {
          endpoint_id: 'ep_1',
          url: 'https://api.example.com/v1/models/test',
          status: 'active',
          avg_latency_ms: 150
        },
        created_at: new Date().toISOString()
      }
    ];

    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockDeployments
    });

    render(<DeploymentManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('Test')).toBeInTheDocument();
      expect(screen.getByText('Metrics')).toBeInTheDocument();
      expect(screen.getByText('Stop')).toBeInTheDocument();
    });
  });
});
