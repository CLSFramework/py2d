
from src.interfaces.IAgent import IAgent
from src.utils.convertor import Convertor
from pyrusgeom.geom_2d import *
from pyrusgeom.soccer_math import *
from service_pb2 import *
from src.interfaces.IBehavior import IBehavior


class BhvTackle(IBehavior):
    def __init__(self):
        pass
    
    def execute(self, agent: IAgent) -> bool:
        agent.logger.debug("BhvTackle.execute")
        from src.sample_player_agent import SamplePlayerAgent  # Local import to avoid circular import
        assert isinstance(agent, SamplePlayerAgent)
        agent.add_action(PlayerAction(helios_basic_tackle=HeliosBasicTackle(min_prob=0.8, body_thr=100.0)))