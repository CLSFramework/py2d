from typing import TYPE_CHECKING
from src.interfaces.IDecisionMaker import IDecisionMaker
from pyrusgeom.soccer_math import *
from pyrusgeom.geom_2d import *
from service_pb2 import *
from src.utils.tools import Tools
from src.behaviors.bhv_block import Bhv_Block
from src.behaviors.bhv_tackle import BhvTackle
from src.behaviors.starter.bhv_starter_tackle import BhvStarterTackle


if TYPE_CHECKING:
    from src.sample_player_agent import SamplePlayerAgent
    
class MoveDecisionMaker(IDecisionMaker):
    """
    A decision maker class for an agent when it does not have the ball.
    Methods
    -------
    __init__():
        Initializes the NoBallDecisionMaker instance.
    make_decision(agent):
        Makes a decision for the agent based on the current world model state.
        The decision includes actions like intercepting the ball, blocking opponents,
        moving to a strategic position, and turning towards the ball.
        Parameters:
        agent (SamplePlayerAgent): The agent for which the decision is being made.
    """
    def __init__(self, agent: "SamplePlayerAgent"):
        self.bhv_tackle = BhvTackle() if not agent.use_starter_code else BhvStarterTackle(0.8, 80)
        self.bhv_block = Bhv_Block()
    
    def make_decision(self, agent: "SamplePlayerAgent"):
        """
        Make a decision for the agent when it does not have the ball.
        This method determines the best course of action for the agent based on the current state of the game world.
        It considers the positions and reachability of the ball by the agent, teammates, and opponents.
        Args:
            agent (SamplePlayerAgent): The agent making the decision. Must be an instance of SamplePlayerAgent.
        Raises:
            AssertionError: If the agent is not an instance of SamplePlayerAgent.
        Actions:
            - If can tackle the ball, the player will execute the helios basic tackle action and ignore other actions.
            - If no teammate can kick the ball and the agent can reach the ball within 3 steps or before any opponent:
                - Adds Body_Intercept and Neck_TurnToBallOrScan actions to the agent.
            - If an opponent can reach the ball before the agent and teammates:
                - Executes Bhv_Block behavior.
            - Otherwise:
                - Adds Body_GoToPoint and Body_TurnToBall actions to the agent.
                - If an opponent can kick the ball and is within 18 units of distance:
                    - Adds Neck_TurnToBall action.
                - Otherwise:
                    - Adds Neck_TurnToBallOrScan action with a count threshold of 0.
        Logging:
            - Logs debug information about the decisions made.
        """
        agent.logger.debug(f'------ NoBallDecisionMaker ------')
        wm: WorldModel = agent.wm
        
        self.bhv_tackle.execute(agent)
        
        self_min = wm.intercept_table.self_reach_steps
        opp_min = wm.intercept_table.first_opponent_reach_steps
        tm_min = wm.intercept_table.first_teammate_reach_steps
        
        if not wm.kickable_teammate_existance and (self_min <= 3 or (self_min <= tm_min and self_min < opp_min + 3)):
            agent.add_action(PlayerAction(body_intercept=Body_Intercept()))
            agent.add_action(PlayerAction(neck_offensive_intercept_neck=Neck_OffensiveInterceptNeck()))
            
            agent.logger.debug(f'NoBallDecisionMaker: Body_Intercept')
            return
        
        if opp_min < min(self_min, tm_min):
            if self.bhv_block.execute(agent):
                return
            
        target_point = agent.strategy.get_position(wm.self.uniform_number, agent)
        dash_power = MoveDecisionMaker.get_normal_dash_power(agent)
        
        ball_pos = Tools.convert_rpc_vector2d_to_vector2d(wm.ball.position)
        self_pos = Tools.convert_rpc_vector2d_to_vector2d(wm.self.position)
        
        ball_dist_from_self = ball_pos.dist(self_pos)
        dist_thr = ball_dist_from_self * 0.1
        if dist_thr < 1.0:
            dist_thr = 1.0
            
        agent.add_action(PlayerAction(body_go_to_point=Body_GoToPoint(target_point=Tools.convert_vector2d_to_rpc_vector2d(target_point),
                                                                      max_dash_power=dash_power, 
                                                                      distance_threshold=dist_thr)))
        agent.add_action(PlayerAction(body_turn_to_ball=Body_TurnToBall()))
        
        if wm.kickable_opponent_existance and ball_dist_from_self < 18.0:
            agent.add_action(PlayerAction(neck_turn_to_ball=Neck_TurnToBall()))
        else:
            agent.add_action(PlayerAction(neck_turn_to_ball_or_scan=Neck_TurnToBallOrScan(count_threshold=0)))
            
        agent.logger.debug(f'NoBallDecisionMaker: Body_GoToPoint {target_point} {dash_power} {dist_thr} or Body_TurnToBall')
        
    s_recover_mode = False
    
    @staticmethod
    def get_normal_dash_power(agent: "SamplePlayerAgent") -> float:
        """
        Get the normal dash power for the agent based on the current world model state.
        This method calculates the normal dash power for the agent based on the stamina level, ball position, and other factors.
        Args:
            agent (SamplePlayerAgent): The agent for which the dash power is being calculated
        Returns:
            float: The normal dash power for the agent.
        """
        wm = agent.wm
        
        player_type: PlayerType = agent.player_types[wm.self.type_id]
        sp: ServerParam = agent.server_params
        
        if wm.self.stamina_capacity < 0.01:
            return min(sp.max_dash_power, wm.self.stamina + player_type.extra_stamina)
        
        self_min = wm.intercept_table.self_reach_steps
        mate_min = wm.intercept_table.first_teammate_reach_steps
        opp_min = wm.intercept_table.first_opponent_reach_steps
        
        if wm.self.stamina_capacity < 0.01:
            MoveDecisionMaker.s_recover_mode = False
        elif wm.self.stamina < sp.stamina_max * 0.5:
            MoveDecisionMaker.s_recover_mode = True
        elif wm.self.stamina > sp.stamina_max * 0.7:
            MoveDecisionMaker.s_recover_mode = False
        
        dash_power = sp.max_dash_power
        my_inc = player_type.stamina_inc_max * wm.self.recovery
        
        if wm.our_defense_line_x > wm.self.position.x and wm.ball.position.x < wm.our_defense_line_x + 20.0:
            agent.logger.debug(f'NoBallDecisionMaker: correct DF line. keep max power')
            dash_power = sp.max_dash_power
        elif MoveDecisionMaker.s_recover_mode:
            dash_power = my_inc - 25.0
            if dash_power < 0.0:
                dash_power = 0.0
            agent.logger.debug(f'NoBallDecisionMaker: recovering')
        elif wm.kickable_teammate_existance and wm.ball.dist_from_self < 20.0:
            dash_power = min(my_inc * 1.1, sp.max_dash_power)
            agent.logger.debug(f'NoBallDecisionMaker: exist kickable teammate. dash_power={dash_power}')
        elif wm.self.position.x > wm.offside_line_x:
            dash_power = sp.max_dash_power
            agent.logger.debug(f'NoBallDecisionMaker: in offside area. dash_power={dash_power}')
        elif wm.ball.position.x > 25.0 and wm.ball.position.x > wm.self.position.x + 10.0 and self_min < opp_min - 6 and mate_min < opp_min - 6:
            dash_power = bound(sp.max_dash_power * 0.1, my_inc * 0.5, sp.max_dash_power)
            agent.logger.debug(f'NoBallDecisionMaker: opponent ball dash_power={dash_power}')
        else:
            dash_power = min(my_inc * 1.7, sp.max_dash_power)
            agent.logger.debug(f'NoBallDecisionMaker: normal mode dash_power={dash_power}')
            
        return dash_power
