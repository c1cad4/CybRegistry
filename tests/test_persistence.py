from dataclasses import dataclass
from pathlib import Path
import tempfile
from concurrent.futures import ThreadPoolExecutor
import unittest

from cybregistry import Registry


@dataclass(frozen=True)
class TestAgent:
    id: str
    capabilities: tuple
    def __post_init__(self):
        if not self.id or not self.capabilities:
            raise ValueError('invalid agent')


class PersistenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'data' / 'registry.sqlite3'

    def registry(self):
        return Registry(self.path, TestAgent)

    def test_agents_and_permissions_survive_restart(self):
        self.registry().register(TestAgent('reader', ('memory.recall',)))
        restored = self.registry().get('reader')
        self.assertEqual(restored.capabilities, ('memory.recall',))
        self.assertEqual([a.id for a in self.registry().list()], ['reader'])

    def test_duplicate_registration_cannot_change_permissions(self):
        self.registry().register(TestAgent('reader', ('memory.recall',)))
        with self.assertRaisesRegex(ValueError, 'already registered'):
            self.registry().register(TestAgent('reader', ('memory.remember',)))
        self.assertEqual(self.registry().get('reader').capabilities, ('memory.recall',))

    def test_instances_observe_new_registrations(self):
        first, second = self.registry(), self.registry()
        first.register(TestAgent('new', ('memory.recall',)))
        self.assertEqual(second.get('new').id, 'new')

    def test_concurrent_duplicate_has_exactly_one_winner(self):
        first, second = self.registry(), self.registry()
        def register(registry):
            try:
                registry.register(TestAgent('reader', ('memory.recall',)))
                return True
            except ValueError:
                return False
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(sorted(pool.map(register, [first, second])), [False, True])
        self.assertEqual(len(self.registry().list()), 1)

    def test_invalid_agent_does_not_leave_a_record(self):
        registry = self.registry()
        class Invalid:
            id = 'bad'
            capabilities = ()
        with self.assertRaises(ValueError):
            registry.register(Invalid())
        self.assertEqual(registry.list(), [])

    def test_persistence_requires_a_factory_and_file(self):
        with self.assertRaises(ValueError):
            Registry(self.path)
        with self.assertRaises(ValueError):
            Registry(':memory:', TestAgent)
