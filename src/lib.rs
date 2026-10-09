//! In-memory registry of agent public identities and declared capabilities.
//! Registration is not proof of ownership; authentication must happen upstream.
use std::collections::{BTreeMap, BTreeSet};

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct AgentRecord {
    pub id: String,
    pub public_key: [u8; 32],
    pub capabilities: BTreeSet<String>,
}

#[derive(Default)]
pub struct Registry {
    agents: BTreeMap<String, AgentRecord>,
}

#[derive(Debug, PartialEq, Eq)]
pub enum RegistryError {
    EmptyId,
    DuplicateId,
    EmptyCapability,
}

impl Registry {
    pub fn register(&mut self, record: AgentRecord) -> Result<(), RegistryError> {
        if record.id.trim().is_empty() {
            return Err(RegistryError::EmptyId);
        }
        if record.capabilities.iter().any(|s| s.trim().is_empty()) {
            return Err(RegistryError::EmptyCapability);
        }
        if self.agents.contains_key(&record.id) {
            return Err(RegistryError::DuplicateId);
        }
        self.agents.insert(record.id.clone(), record);
        Ok(())
    }

    pub fn get(&self, id: &str) -> Option<&AgentRecord> {
        self.agents.get(id)
    }

    pub fn capable(&self, capability: &str) -> Vec<&AgentRecord> {
        self.agents
            .values()
            .filter(|record| record.capabilities.contains(capability))
            .collect()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn agent(id: &str) -> AgentRecord {
        AgentRecord {
            id: id.into(),
            public_key: [7; 32],
            capabilities: BTreeSet::from(["research".into()]),
        }
    }

    #[test]
    fn registers_and_discovers_agent() {
        let mut registry = Registry::default();
        registry.register(agent("a")).unwrap();
        assert_eq!(registry.capable("research").len(), 1);
        assert!(registry.get("a").is_some());
    }

    #[test]
    fn prevents_duplicate_id() {
        let mut registry = Registry::default();
        registry.register(agent("a")).unwrap();
        assert_eq!(
            registry.register(agent("a")),
            Err(RegistryError::DuplicateId)
        );
    }

    #[test]
    fn rejects_empty_id() {
        let mut registry = Registry::default();
        assert_eq!(registry.register(agent("")), Err(RegistryError::EmptyId));
    }
}
