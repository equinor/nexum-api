import uuid
import asyncio
from collections import defaultdict
from contextlib import asynccontextmanager
import threading

class ScenarioQueueManager:
    scenario_locks: dict[uuid.UUID, asyncio.Lock] = {}

    def add_scenario_lock(self, scenario_id: uuid.UUID):
        self.scenario_locks[scenario_id] = asyncio.Lock()

    def aquire_scenario_lock(self, scenario_id: uuid.UUID) -> asyncio.Lock:
        lock = self.scenario_locks.get(scenario_id)
        if lock is None:
            self.add_scenario_lock(scenario_id)
            lock = self.scenario_locks.get(scenario_id)
            if lock is None:
                raise Exception("Scenario lock could not be aquired")
        return lock




