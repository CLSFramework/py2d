from abc import ABC
from src.interfaces.IAgent import IAgent


class IBehavior(ABC):
    def execute(self, agent: IAgent):
        pass