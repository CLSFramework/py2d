from src.interfaces.IPositionStrategy import IPositionStrategy
from src.strategy.formation_file import *
from src.interfaces.IAgent import IAgent
from src.strategy.player_role import PlayerRole, RoleName, RoleType, RoleSide
from pyrusgeom.soccer_math import *
from service_pb2 import *
import logging
from src.utils.convertor import Convertor


class StarterStrategy():
    def __init__(self):
        pass

    def update(self, agent: IAgent):
        raise NotImplementedError("StarterStrategy.update not implemented")
        pass
        
    def get_position(agent: IAgent, uniform_number: int) -> RpcVector2D:
        wm = agent.wm
        if wm.game_mode_type in [GameModeType.BeforeKickOff, GameModeType.AfterGoal_]:
            kick_off_position = [None] * 12
            kick_off_position[1] = RpcVector2D(x=-52, y=0)
            kick_off_position[2] = RpcVector2D(x=-30, y=-10)
            kick_off_position[3] = RpcVector2D(x=-30, y=10)
            kick_off_position[4] = RpcVector2D(x=-30, y=-20)
            kick_off_position[5] = RpcVector2D(x=-30, y=20)
            kick_off_position[6] = RpcVector2D(x=-17, y=0)
            kick_off_position[7] = RpcVector2D(x=-15, y=-15)
            kick_off_position[8] = RpcVector2D(x=-15, y=15)
            kick_off_position[9] = RpcVector2D(x=-11, y=0)
            kick_off_position[10] = RpcVector2D(x=-5, y=-20)
            kick_off_position[11] = RpcVector2D(x=-5, y=20)
            return kick_off_position[uniform_number]
        ball_step = 0
        if wm.game_mode_type == GameModeType.PlayOn or wm.game_mode_type == GameModeType.GoalKick_:
            ball_step = min(1000, wm.intercept_table.first_teammate_reach_steps)
            ball_step = min(ball_step, wm.intercept_table.first_opponent_reach_steps)
            ball_step = min(ball_step, wm.intercept_table.self_reach_steps)
        
        real_ball_pos = Vector2D(wm.ball.position.x, wm.ball.position.y)
        real_ball_vel = Vector2D(wm.ball.velocity.x, wm.ball.velocity.y)
        ball_pos = inertia_n_step_point(real_ball_pos, real_ball_vel, ball_step, agent.server_params.ball_decay)
        
        
        positions = [None] * 12
        min_x_rectangle = [0, -52, -52, -52, -52, -52, -30, -30, -30,   0,  0,   0]
        max_x_rectangle = [0, -48, -10, -10, -10, -10,  15,  15,  15,  50, 50,  50]
        min_y_rectangle = [0,  -2, -20, -10, -30,  10, -20, -30,   0, -30,  0, -20]
        max_y_rectangle = [0,   2,  10,  20, -10,  30,  20,   0,  30,   0, 30,  20]
        
        for i in range (1, 12):
            xx_rectangle = max_x_rectangle[i] - min_x_rectangle[i]
            yy_rectangle = max_y_rectangle[i] - min_y_rectangle[i]
            x_ball = ball_pos.x() + agent.server_params.pitch_half_length
            x_ball /= agent.server_params.pitch_half_length * 2
            y_ball = ball_pos.y() + 34
            y_ball /= agent.server_params.pitch_half_width * 2
            x_pos = xx_rectangle * x_ball + min_x_rectangle[i]
            y_pos = yy_rectangle * y_ball + min_y_rectangle[i]
            positions[i] = RpcVector2D(x=x_pos, y=y_pos)
        
        if agent.server_params.use_offside:
            max_x = wm.offside_line_x
            if agent.server_params.kickoff_offside and wm.game_mode_type in [GameModeType.BeforeKickOff, GameModeType.AfterGoal_]:
                max_x = 0
                
            else:
                mate_step = wm.intercept_table.first_teammate_reach_steps
                if mate_step < 50:
                    trap_pos = inertia_n_step_point(real_ball_pos, real_ball_vel, mate_step, agent.server_params.ball_decay)
                    max_x = max(max_x, trap_pos.x())
                max_x -= 1.0
                
            for unum in range(1, 12):
                positions[unum].x = min(positions[unum].x, max_x)
    
        return positions[uniform_number]
            
            
    s_recover_mode = False
    
    @staticmethod
    def get_normal_dash_power(agent: IAgent) -> float:
        wm = agent.wm
        if wm.self.stamina_capacity == 0:
            return min(agent.server_params.max_dash_power, wm.self.stamina + agent.player_types[agent.wm.self.id].extra_stamina)
        self_min = wm.intercept_table.self_reach_steps
        mate_min = wm.intercept_table.first_teammate_reach_steps
        opp_min = wm.intercept_table.first_opponent_reach_steps
        # Check recover mode
        if wm.self.stamina_capacity == 0:
            StarterStrategy.s_recover_mode = False
        elif wm.self.stamina < agent.server_params.stamina_max * 0.5:
            StarterStrategy.s_recover_mode = True
        elif wm.self.stamina > agent.server_params.stamina_max * 0.7:
            StarterStrategy.s_recover_mode = False
        # Initialize dash_power with max_dash_power
        dash_power = agent.server_params.max_dash_power
        my_inc = (agent.player_types[agent.wm.self.id].stamina_inc_max * wm.self.recovery)
        if wm.our_defense_line_x > wm.self.position.x and wm.ball.position.x < wm.our_defense_line_x + 20.0:
            dash_power = agent.server_params.max_dash_power
        elif StarterStrategy.s_recover_mode:
            dash_power = my_inc - 25.0  # Preferred recovery value
            dash_power = max(dash_power, 0)
        elif mate_min <= 1 and wm.ball.dist_from_self < 20.0:
            dash_power = min(my_inc * 1.1, agent.server_params.max_dash_power)
            
        elif wm.self.position.x > wm.offside_line_x:
            dash_power = agent.server_params.max_dash_power
        elif wm.ball.position.x > 25.0 and wm.ball.position.x > wm.self.position.x + 10.0 and self_min < opp_min - 6 and mate_min < opp_min - 6:
            dash_power = bound(agent.server_params.max_dash_power * 0.1, my_inc * 0.5, agent.server_params.max_dash_power)
        else:
            dash_power = min(my_inc * 1.7, agent.server_params.max_dash_power)
        return dash_power