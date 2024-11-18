from src.interfaces.IDecisionMaker import IDecisionMaker
from .dm_play_on import PlayOnDecisionMaker
from .dm_set_play import SetPlayDecisionMaker
from src.interfaces.IAgent import IAgent
from service_pb2 import *


class DecisionMaker(IDecisionMaker):
    def __init__(self):
        self.play_on_decision_maker = PlayOnDecisionMaker()
        self.set_play_decision_maker = SetPlayDecisionMaker()
    
    def make_decision(self, agent: IAgent):
        if agent.wm.self.is_goalie:
            agent.add_action(PlayerAction(helios_goalie=HeliosGoalie()))
        else:
            if agent.wm.game_mode_type == GameModeType.PlayOn:
                self.play_on_decision_maker.make_decision(agent)
            elif agent.wm.is_penalty_kick_mode:
                agent.add_action(PlayerAction(helios_penalty=HeliosPenalty()))
            else:
                agent.add_action(PlayerAction(helios_set_play=HeliosSetPlay()))