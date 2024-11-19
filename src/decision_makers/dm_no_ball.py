from src.interfaces.IDecisionMaker import IDecisionMaker
from src.interfaces.IAgent import IAgent
from pyrusgeom.soccer_math import *
from pyrusgeom.geom_2d import *
from service_pb2 import *
from src.utils.convertor import Convertor
from src.decision_makers.bhv_block import Bhv_Block


class NoBallDecisionMaker(IDecisionMaker):
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
    def __init__(self):
        pass
    
    def make_decision(self, agent: IAgent):
        """
        Make a decision for the agent when it does not have the ball.
        This method determines the best course of action for the agent based on the current state of the game world.
        It considers the positions and reachability of the ball by the agent, teammates, and opponents.
        Args:
            agent (SamplePlayerAgent): The agent making the decision. Must be an instance of SamplePlayerAgent.
        Raises:
            AssertionError: If the agent is not an instance of SamplePlayerAgent.
        Actions:
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
        from src.sample_player_agent import SamplePlayerAgent  # Local import to avoid circular import
        assert isinstance(agent, SamplePlayerAgent)
        # Do tackle TODO: Add Bhv_BasicTackle into idls
        agent.logger.debug(f'------ NoBallDecisionMaker ------')
        wm: WorldModel = agent.wm
        
        self_min = wm.intercept_table.self_reach_steps
        opp_min = wm.intercept_table.first_opponent_reach_steps
        tm_min = wm.intercept_table.first_teammate_reach_steps
        
        if not wm.kickable_teammate_existance and (self_min <= 3 or (self_min <= tm_min and self_min < opp_min + 3)):
            agent.add_action(PlayerAction(body_intercept=Body_Intercept()))
            agent.add_action(PlayerAction(neck_turn_to_ball_or_scan=Neck_TurnToBallOrScan())) # TODO: Add Neck_OffensiveInterceptNeck into idls
            
            agent.logger.debug(f'NoBallDecisionMaker: Body_Intercept')
            return
        
        if opp_min < min(self_min, tm_min):
            bhv_block = Bhv_Block()
            if bhv_block.execute(agent):
                return
            
        target_point = agent.strategy.get_position(wm.self.uniform_number)
        dash_power = 100.0 #TODO: Add dash power calculation
        
        ball_pos = Convertor.convert_rpc_vector2d_to_vector2d(wm.ball.position)
        self_pos = Convertor.convert_rpc_vector2d_to_vector2d(wm.self.position)
        
        ball_dist_from_self = ball_pos.dist(self_pos)
        dist_thr = ball_dist_from_self * 0.1
        if dist_thr < 1.0:
            dist_thr = 1.0
            
        agent.add_action(PlayerAction(body_go_to_point=Body_GoToPoint(target_point=Convertor.convert_vector2d_to_rpc_vector2d(target_point),
                                                                      max_dash_power=dash_power, 
                                                                      distance_threshold=dist_thr)))
        agent.add_action(PlayerAction(body_turn_to_ball=Body_TurnToBall()))
        
        if wm.kickable_opponent_existance and ball_dist_from_self < 18.0:
            agent.add_action(PlayerAction(neck_turn_to_ball=Neck_TurnToBall()))
        else:
            agent.add_action(PlayerAction(neck_turn_to_ball_or_scan=Neck_TurnToBallOrScan(count_threshold=0)))
            
        agent.logger.debug(f'NoBallDecisionMaker: Body_GoToPoint {target_point} {dash_power} {dist_thr} or Body_TurnToBall')
        
        