from abc import ABC
from src.decision_makers.decision_maker import DecisionMaker
from src.interfaces.IAgent import IAgent
from src.strategy.formation_strategy import FormationStrategy
from service_pb2 import *


class SamplePlayerAgent(IAgent, ABC):
    def __init__(self):
        super().__init__()
        self.decision_maker = DecisionMaker()
        self.strategy = FormationStrategy()
        self.wm: WorldModel = None
    
    def update_actions(self, wm:WorldModel):
        self.logger.debug(f'update_actions: {wm.cycle}')
        self.wm = wm
        self.actions.clear()
        self.strategy.update(wm)
        self.decision_maker.make_decision(self)
        self.logger.debug(f'actions: {self.actions}')
    
    def get_strategy(self):
        return self.strategy