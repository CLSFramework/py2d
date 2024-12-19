from typing import TYPE_CHECKING
from src.interfaces.IDecisionMaker import IDecisionMaker
from pyrusgeom.soccer_math import *
from pyrusgeom.geom_2d import *
from service_pb2 import *


if TYPE_CHECKING:
    from src.sample_player_agent import SamplePlayerAgent

class GoalieDecisionMaker(IDecisionMaker):
    def __init__(self, agent: "SamplePlayerAgent"):
        pass

    def make_decision(self, agent: "SamplePlayerAgent"):
        agent.logger.debug("--- GoalieDecisionMaker ---")
        agent.add_action(PlayerAction(helios_goalie=HeliosGoalie()))