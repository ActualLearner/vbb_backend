"""The OpenAPI schema and Swagger UI are public (ADR-0010).

The schema is not sensitive and the mobile/web teams consume it without
credentials, so both endpoints bypass the global IsAuthenticated default.
"""

from django.test import TestCase
from rest_framework.test import APIClient


class OpenAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_schema_is_public(self):
        resp = self.client.get("/api/schema/")
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertIn("openapi", resp.headers["Content-Type"])

    def test_swagger_ui_is_public(self):
        resp = self.client.get("/api/docs/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"swagger", resp.content.lower())
