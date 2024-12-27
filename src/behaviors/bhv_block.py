from typing import TYPE_CHECKING
from src.interfaces.IAgent import IAgent
from src.utils.tools import Tools
from pyrusgeom.geom_2d import *
from pyrusgeom.soccer_math import *
from service_pb2 import *
from src.interfaces.IBehavior import IBehavior

if TYPE_CHECKING:
    from src.sample_player_agent import SamplePlayerAgent

class Bhv_Block(IBehavior):
    """
    Bhv_Block is a behavior class that determines whether an agent should block the ball based on the predicted future positions of the ball and the players.
    Methods
    -------
    __init__():
        Initializes the Bhv_Block instance.
    execute(agent):
        Executes the block behavior for the agent. Predicts the future position of the ball and checks if the agent or any teammate can block it within a certain number of cycles.
    _get_final_target(agent):
        Returns the final target position for the agent.
    _get_average_dribble_speed(agent):
        Returns the average dribble speed of the agent.
    _calculate_block_cycles(future_ball_pos, player):
        Calculates the number of cycles required for a player to block the ball at a future position.
    """
    def __init__(self):
        pass
    
    def execute(self, agent: "SamplePlayerAgent") -> bool:
        """
            Executes the block behavior for the agent. Predicts the future position of the ball and checks if the agent or any teammate can block it within a certain number of cycles.
            Parameters:
                agent (IAgent): The agent executing the behavior.
            Returns:
                bool: True if the agent or a teammate can block the ball, False otherwise.
            Actions:
                - Find the predicted future position of the ball based on the current ball position, velocity, and opponent reach steps.
                - Calculate the first cycle that the agent or a teammate can block the ball.
                - If the agent can block the ball, add a Body_GoToPoint action to the agent.
        """
        agent.logger.debug(f'------ Bhv_Block ------')
        wm = agent.wm
        sp = agent.server_params
        
        opp_min = wm.intercept_table.first_opponent_reach_steps
        current_ball_pos = Tools.convert_rpc_vector2d_to_vector2d(wm.ball.position)
        current_ball_vel = Tools.convert_rpc_vector2d_to_vector2d(wm.ball.velocity)
        intercept_pos: Vector2D = inertia_n_step_point(current_ball_pos, current_ball_vel, opp_min, sp.ball_decay)
        target_pos = self._get_final_target(agent)
        dribble_vel = Vector2D.from_polar(self._get_average_dribble_speed(agent), (target_pos - intercept_pos).th())
        home_pos_offside_line_x = agent.strategy.get_offside_line()
        
        future_ball_pos = intercept_pos
        
        for cycle in range(opp_min + 1, opp_min + 40):
            future_ball_pos += dribble_vel
            
            if future_ball_pos.abs_x() > sp.pitch_half_length:
                agent.logger.debug(f'Bhv_Block: False: future_ball_pos.abs_x() > sp.pitch_half_length')
                return False
            
            if future_ball_pos.abs_y() > sp.pitch_half_width:
                agent.logger.debug(f'Bhv_Block: False: future_ball_pos.abs_y() > sp.pitch_half_width')
                return False
            
            if wm.self.uniform_number <= 5:
                # Defender should not block the ball if it is too far from the offside line
                if future_ball_pos.x() > home_pos_offside_line_x + 10.0:
                    continue
                
            for our_player in wm.our_players_dict.values():
                if our_player.is_goalie:
                    continue
                block_cycles = self._calculate_block_cycles(future_ball_pos, our_player)
                if block_cycles <= cycle:
                    if wm.self.uniform_number == our_player.uniform_number:
                        agent.logger.debug(f'Bhv_Block: True: I can block in {cycle} in {future_ball_pos=}')
                        agent.add_action(PlayerAction(body_go_to_point=Body_GoToPoint(target_point=Tools.convert_vector2d_to_rpc_vector2d(future_ball_pos),
                                                                                      max_dash_power=100.0,
                                                                                      distance_threshold=0.5)))
                        agent.add_action(PlayerAction(neck_turn_to_ball_or_scan=Neck_TurnToBallOrScan(count_threshold=0)))
                        agent.add_log_circle(LoggerLevel.BLOCK, future_ball_pos.x(), future_ball_pos.y(), 0.5, 'red', True)
                        return True
                    else:
                        agent.logger.debug(f'Bhv_Block: False: tm {our_player.uniform_number} can block in {block_cycles} in {future_ball_pos=}')
                        return False
            
        return False
    
    def _get_final_target(self, agent: IAgent) -> Vector2D:
        """
        Returns the final target position for the agent.
        Parameters:
            agent (IAgent): The agent executing the behavior.
        Returns:
            Vector2D: The final target position.
        """
        return Vector2D(-agent.server_params.pitch_half_length, 0)
    
    def _get_average_dribble_speed(self, agent: IAgent) -> float:
        """
        Returns the average dribble speed of the agent.
        Parameters:
            agent (IAgent): The agent executing the behavior.
        Returns:
            float: The average dribble speed.
        """
        return 0.7
    
    def _calculate_block_cycles(self, future_ball_pos: Vector2D, player: Player) -> int:
        """
        Calculates the number of cycles required for a player to block the ball at a future position.
        Parameters:
            future_ball_pos (Vector2D): The predicted future position of the ball.
            player (Player): The player attempting to block the ball.
        Returns:
            int: The number of cycles required for the player to block the ball.
        """
        player_pos = Tools.convert_rpc_vector2d_to_vector2d(player.position)
        distance = future_ball_pos.dist(player_pos)
        return int(distance)