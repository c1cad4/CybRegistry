"""Explicit agent registration, with immutable identities within a session."""
from threading import RLock

class Registry:
    def __init__(self):
        self._agents = {}
        self._lock = RLock()
    def register(self, agent):
        with self._lock:
            if agent.id in self._agents:
                raise ValueError('agent already registered')
            self._agents[agent.id] = agent
        return agent
    def get(self, agent_id):
        with self._lock:
            if agent_id not in self._agents:
                raise ValueError('unknown agent')
            return self._agents[agent_id]
    def list(self):
        with self._lock:
            return sorted(self._agents.values(), key=lambda a: a.id)
