"""
Integration tests for Cost Calculator API endpoints

Tests the FastAPI endpoints for cost calculation.
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestCostCalculatorAPI:
    """Test suite for Cost Calculator API endpoints"""
    
    def test_calculate_cost_estimates_endpoint(self):
        """Test POST /api/cost/estimate endpoint"""
        response = client.post(
            "/api/cost/estimate",
            json={
                "training_time_hours": 2.0,
                "gpu_name": "RTX 4090",
                "num_gpus": 1,
                "electricity_rate_per_kwh": 0.15,
                "region": "US",
                "utilization": 0.85
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify all required fields are present
        assert "gpu_hours" in data
        assert "electricity_cost_usd" in data
        assert "carbon_footprint_kg" in data
        assert "total_energy_kwh" in data
        assert "formatted" in data
        
        # Verify values are reasonable
        assert data["gpu_hours"] == 2.0
        assert data["electricity_cost_usd"] > 0
        assert data["carbon_footprint_kg"] > 0
        assert data["total_energy_kwh"] > 0
    
    def test_calculate_cost_estimates_multi_gpu(self):
        """Test cost estimates with multiple GPUs"""
        response = client.post(
            "/api/cost/estimate",
            json={
                "training_time_hours": 1.0,
                "gpu_name": "A100",
                "num_gpus": 4,
                "electricity_rate_per_kwh": 0.15,
                "region": "US"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # GPU hours should be 4 (1 hour × 4 GPUs)
        assert data["gpu_hours"] == 4.0
    
    def test_get_default_electricity_rate(self):
        """Test GET /api/cost/electricity-rate/{region} endpoint"""
        response = client.get("/api/cost/electricity-rate/US")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "region" in data
        assert "electricity_rate_per_kwh" in data
        assert data["region"] == "US"
        assert data["electricity_rate_per_kwh"] == 0.14
    
    def test_get_default_electricity_rate_unknown_region(self):
        """Test electricity rate with unknown region"""
        response = client.get("/api/cost/electricity-rate/UNKNOWN")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return default rate
        assert data["electricity_rate_per_kwh"] == 0.15
    
    def test_get_carbon_intensity(self):
        """Test GET /api/cost/carbon-intensity/{region} endpoint"""
        response = client.get("/api/cost/carbon-intensity/US")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "region" in data
        assert "carbon_intensity_g_per_kwh" in data
        assert data["region"] == "US"
        assert data["carbon_intensity_g_per_kwh"] == 386
    
    def test_get_carbon_intensity_clean_grid(self):
        """Test carbon intensity for clean grid region"""
        response = client.get("/api/cost/carbon-intensity/FR")
        
        assert response.status_code == 200
        data = response.json()
        
        # France has low carbon intensity (nuclear)
        assert data["carbon_intensity_g_per_kwh"] == 57
    
    def test_get_gpu_power_profile(self):
        """Test GET /api/cost/gpu-power/{gpu_name} endpoint"""
        response = client.get("/api/cost/gpu-power/RTX 4090")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "model_name" in data
        assert "tdp_watts" in data
        assert "avg_power_watts" in data
        assert "idle_power_watts" in data
        
        assert data["model_name"] == "RTX 4090"
        assert data["tdp_watts"] == 450
        assert data["avg_power_watts"] == 400
        assert data["idle_power_watts"] == 50
    
    def test_get_gpu_power_profile_unknown_gpu(self):
        """Test GPU power profile with unknown GPU"""
        response = client.get("/api/cost/gpu-power/Unknown GPU")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return default profile
        assert data["model_name"] == "default"
        assert data["tdp_watts"] == 300
    
    def test_cost_estimates_with_different_regions(self):
        """Test that carbon footprint varies by region"""
        # US region
        response_us = client.post(
            "/api/cost/estimate",
            json={
                "training_time_hours": 1.0,
                "gpu_name": "RTX 4090",
                "num_gpus": 1,
                "electricity_rate_per_kwh": 0.15,
                "region": "US"
            }
        )
        
        # France region (cleaner grid)
        response_fr = client.post(
            "/api/cost/estimate",
            json={
                "training_time_hours": 1.0,
                "gpu_name": "RTX 4090",
                "num_gpus": 1,
                "electricity_rate_per_kwh": 0.15,
                "region": "FR"
            }
        )
        
        assert response_us.status_code == 200
        assert response_fr.status_code == 200
        
        data_us = response_us.json()
        data_fr = response_fr.json()
        
        # France should have lower carbon footprint
        assert data_fr["carbon_footprint_kg"] < data_us["carbon_footprint_kg"]
        
        # But same energy consumption
        assert abs(data_fr["total_energy_kwh"] - data_us["total_energy_kwh"]) < 0.01
    
    def test_cost_estimates_formatted_output(self):
        """Test that formatted output is present and correct"""
        response = client.post(
            "/api/cost/estimate",
            json={
                "training_time_hours": 2.5,
                "gpu_name": "A100",
                "num_gpus": 2,
                "electricity_rate_per_kwh": 0.20,
                "region": "EU"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        formatted = data["formatted"]
        
        # Check all formatted fields exist
        assert "gpu_hours" in formatted
        assert "electricity_cost" in formatted
        assert "carbon_footprint" in formatted
        assert "energy_consumption" in formatted
        assert "electricity_rate" in formatted
        assert "carbon_intensity" in formatted
        assert "confidence" in formatted
        
        # Check formatting
        assert "GPU hours" in formatted["gpu_hours"]
        assert "$" in formatted["electricity_cost"]
        assert "kg CO₂" in formatted["carbon_footprint"]
        assert "kWh" in formatted["energy_consumption"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
