from typing import TYPE_CHECKING
from src.interfaces.IBehavior import IBehavior
from src.interfaces.IAgent import IAgent
from pyrusgeom.soccer_math import *
from pyrusgeom.geom_2d import *
from service_pb2 import *
from src.behaviors.bhv_shoot import BhvShoot

if TYPE_CHECKING:
    from src.sample_player_agent import SamplePlayerAgent

class BhvKickPlanner(IBehavior):
    """
    Decision maker class for an agent with the ball.

    Methods
    -------
    __init__():
        Initializes the WithBallDecisionMaker instance.

    execute(agent: IAgent):
        Makes a decision for the agent when it has the ball.
        
    _get_helios_offensive_planner():
        Returns an instance of HeliosOffensivePlanner.
        
    _get_planner_evaluation(agent: IAgent):
        Returns an instance of PlannerEvaluation.
        
    _get_planner_evaluation_effector(agent: IAgent):
        Returns an instance of PlannerEvaluationEffector.
        
    _get_opponent_effector(agent: IAgent):
        Determines the opponent effector based on the agent's world model.
    """

    def __init__(self):
        pass

    def execute(self, agent: "SamplePlayerAgent"):
        agent.logger.debug("--- WithBallDecisionMaker ---")

        BhvShoot().execute(agent)
        
        agent.add_action(
            PlayerAction(helios_offensive_planner=self._get_helios_offensive_planner(agent))
        )

    def _get_helios_offensive_planner(self, agent):
        """ Summary
        In this function you can create an instance of HeliosOffensivePlanner and set its attributes.
        The HeliosOffensivePlanner is a message that ask proxy to create a tree and find the best chain of actions and execute the first action of the chain.

        Returns:
            _type_: HeliosOffensivePlanner
        """
        res = HeliosOffensivePlanner(evaluation=self._get_planner_evaluation(agent))
        res.lead_pass = True
        res.direct_pass = True
        res.through_pass = True
        res.simple_pass = True
        res.short_dribble = True
        res.long_dribble = True
        res.simple_shoot = True
        res.simple_dribble = True
        res.cross = True
        
        return res

    def _get_planner_evaluation(self, agent: IAgent):
        return PlannerEvaluation(
            effectors=self._get_planner_evaluation_effector(agent),
        )

    def _get_planner_evaluation_effector(self, agent: IAgent):
        return PlannerEvaluationEffector(
            opponent_effector=self._get_opponent_effector(agent),
        )

    def _get_opponent_effector(self, agent: IAgent):
        wm = agent.wm

        if wm.ball.position.x > 30:
            negetive_effect_by_distance = [-5, -4, -3, -2, -1]
        else:
            negetive_effect_by_distance = [-30, -25, -20, -15, -10, -4, -3, -2, -1]

        return OpponentEffector(
            negetive_effect_by_distance=negetive_effect_by_distance,
            negetive_effect_by_distance_based_on_first_layer=False,
        )
