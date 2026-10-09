"""Explicit agent registration with optional durable SQLite identities."""
from contextlib import contextmanager
import json
from pathlib import Path
import sqlite3
from threading import RLock

class Registry:
    def __init__(self, database=None, agent_factory=None):
        self._agents = {}
        self._lock = RLock()
        self.database = str(database) if database is not None else None
        self.agent_factory = agent_factory
        if self.database is not None:
            if not callable(agent_factory):
                raise ValueError('persistent registry requires an agent factory')
            if self.database == ':memory:':
                raise ValueError('persistent registry requires a file database')
            Path(self.database).parent.mkdir(parents=True, exist_ok=True)
            with self._connect() as db:
                db.execute('CREATE TABLE IF NOT EXISTS registered_agents('
                           'id TEXT PRIMARY KEY, capabilities TEXT NOT NULL)')

    @contextmanager
    def _connect(self):
        db = sqlite3.connect(self.database, timeout=10)
        try:
            with db:
                yield db
        finally:
            db.close()

    def _restore(self, record):
        return self.agent_factory(record[0], tuple(json.loads(record[1])))

    def register(self, agent):
        with self._lock:
            if self.database is not None:
                # Validate the persisted identity through the same factory used
                # on restart, before committing anything to the database.
                restored = self.agent_factory(agent.id, tuple(agent.capabilities))
                try:
                    with self._connect() as db:
                        db.execute('INSERT INTO registered_agents(id, capabilities) VALUES (?, ?)',
                                   (restored.id, json.dumps(restored.capabilities)))
                except sqlite3.IntegrityError as error:
                    raise ValueError('agent already registered') from error
                return restored
            if agent.id in self._agents:
                raise ValueError('agent already registered')
            self._agents[agent.id] = agent
        return agent
    def get(self, agent_id):
        with self._lock:
            if self.database is not None:
                with self._connect() as db:
                    record = db.execute('SELECT id, capabilities FROM registered_agents WHERE id=?', (agent_id,)).fetchone()
                if record is None:
                    raise ValueError('unknown agent')
                return self._restore(record)
            if agent_id not in self._agents:
                raise ValueError('unknown agent')
            return self._agents[agent_id]
    def list(self):
        with self._lock:
            if self.database is not None:
                with self._connect() as db:
                    records = db.execute('SELECT id, capabilities FROM registered_agents ORDER BY id').fetchall()
                return [self._restore(record) for record in records]
            return sorted(self._agents.values(), key=lambda a: a.id)
