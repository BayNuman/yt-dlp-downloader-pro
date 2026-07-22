import unittest
from fastapi.testclient import TestClient
from server.main import app

class TestServer(unittest.TestCase):
    def test_health_check(self):
        """Ensures the health check endpoint returns 200 status code without authentication."""
        with TestClient(app) as client:
            response = client.get("/health")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {"status": "ok", "version": "2.0.0"})

    def test_unauthorized_endpoints(self):
        """Verifies that API endpoints are protected and return 401 when token is missing/invalid."""
        with TestClient(app) as client:
            # 1. No token header
            response = client.get("/api/config/preferences")
            self.assertEqual(response.status_code, 401)

            # 2. Invalid token header
            response = client.get(
                "/api/config/preferences",
                headers={"X-Baynuman-Token": "bad_token_signature"}
            )
            self.assertEqual(response.status_code, 401)

    def test_authorized_endpoints(self):
        """Verifies that endpoints return 200 when authenticated with the valid token."""
        with TestClient(app) as client:
            token = app.state.server.startup_token
            
            # 1. Fetch preferences
            response = client.get(
                "/api/config/preferences",
                headers={"X-Baynuman-Token": token}
            )
            self.assertEqual(response.status_code, 200)
            self.assertIn("output_dir", response.json())

            # 2. Fetch export profiles
            response = client.get(
                "/api/config/profiles",
                headers={"X-Baynuman-Token": token}
            )
            self.assertEqual(response.status_code, 200)
            self.assertIsInstance(response.json(), list)
            # Ensure standard profiles exist in response
            names = [p["name"] for p in response.json()]
            self.assertIn("YouTube Shorts (Max 60s, 9:16 Crop)", names)

    def test_invalid_pydantic_validation(self):
        """Verifies that invalid payloads return 422 Unprocessable Entity status."""
        with TestClient(app) as client:
            token = app.state.server.startup_token
            
            # Post missing required 'url' field
            response = client.post(
                "/api/queue",
                json={"profile": "best"},
                headers={"X-Baynuman-Token": token}
            )
            self.assertEqual(response.status_code, 422)
