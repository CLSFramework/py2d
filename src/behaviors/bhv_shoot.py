from typing import TYPE_CHECKING
from src.interfaces.IAgent import IAgent
from src.utils.tools import Tools
from pyrusgeom.geom_2d import *
from pyrusgeom.soccer_math import *
from service_pb2 import *
from src.interfaces.IBehavior import IBehavior

if TYPE_CHECKING:
    from src.sample_player_agent import SamplePlayerAgent

class BhvShoot(IBehavior):
    def __init__(self):
        pass
    
    def execute(self, agent: "SamplePlayerAgent"):
        agent.logger.debug("BhvShoot.execute")
        # To enable this behavior, you need to set ignore_shootInPreprocess to True in the sample_player_agent.py
        # Otherwise, the proxy will execute shoot action automatically.
        
        agent.add_action(PlayerAction(helios_shoot=HeliosShoot()))