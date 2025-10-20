from django.test import TestCase


class InventoryDiscoveryTest(TestCase):
    def test_discovery(self):
        # Basic sanity test so test runner picks up the package
        self.assertTrue(True)
