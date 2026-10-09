import unittest
from types import SimpleNamespace
from cybregistry import Registry
class RegistryTests(unittest.TestCase):
    def test_duplicate_identity_preserves_original(self):
        registry=Registry();first=SimpleNamespace(id='keeper')
        registry.register(first)
        with self.assertRaises(ValueError):registry.register(SimpleNamespace(id='keeper'))
        self.assertIs(registry.get('keeper'),first)
    def test_missing_agent(self):
        with self.assertRaises(ValueError):Registry().get('missing')
