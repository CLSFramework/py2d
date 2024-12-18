from typing import TYPE_CHECKING
from src.interfaces.IAgent import IAgent
from src.utils.tools import Tools
from pyrusgeom.geom_2d import *
from pyrusgeom.soccer_math import *
from service_pb2 import *
from src.interfaces.IBehavior import IBehavior

if TYPE_CHECKING:
    from src.sample_player_agent import SamplePlayerAgent

class BhvTackle(IBehavior):
    def __init__(self):
        pass
    
    def execute(self, agent: "SamplePlayerAgent"):
        agent.logger.debug("BhvTackle.execute")
        agent.add_action(PlayerAction(helios_basic_tackle=HeliosBasicTackle(min_prob=0.8, body_thr=100.0)))