from src.interfaces.IPositionStrategy import IPositionStrategy
from src.strategy.formation_file import *
from src.interfaces.IAgent import IAgent
from src.strategy.player_role import PlayerRole, RoleName, RoleType, RoleSide
from pyrusgeom.soccer_math import *
from service_pb2 import *
import logging
from src.utils.tools import Tools


class StarterStrategy(IPositionStrategy):
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self._poses: dict[int, Vector2D] = {i: Vector2D(0, 0) for i in range(12)}

    def update(self, agent: IAgent):
        """
        Update the strategy based on the agent's world model.

        Args:
            agent (IAgent): The agent instance.
        """
        wm = agent.wm
        if wm.game_mode_type in [GameModeType.BeforeKickOff, GameModeType.AfterGoal_]:
            self._set_kickoff_positions()
        else:
            ball_pos = self._predict_ball_position(agent)
            self._set_dynamic_positions(ball_pos, agent)
        self._apply_offside_rule(agent)

    def get_position(self, uniform_number: int, agent: IAgent) -> Vector2D:
        """
        Get the position for a given uniform number.

        Args:
            uniform_number (int): The uniform number of the player.
            agent (IAgent): The agent instance.

        Returns:
            Vector2D: The position of the player.
        """
        return self._poses[uniform_number]

    def _set_kickoff_positions(self):
        """
        Set static positions for players during kickoff.
        """
        self._poses = {
            1: Vector2D(-52, 0),
            2: Vector2D(-48, -2),
            3: Vector2D(-48, 2),
            4: Vector2D(-48, -10),
            5: Vector2D(-48, 10),
            6: Vector2D(-48, -20),
            7: Vector2D(-48, 20),
            8: Vector2D(-30, -20),
            9: Vector2D(-30, 0),
            10: Vector2D(-30, 20),
            11: Vector2D(-17, 0),
        }

    def _predict_ball_position(self, agent: IAgent) -> Vector2D:
        """
        Predict the ball position based on the agent's world model.

        Args:
            agent (IAgent): The agent instance.

        Returns:
            Vector2D: The predicted ball position.
        """
        wm = agent.wm
        ball_step = 0
        if wm.game_mode_type == GameModeType.PlayOn or wm.game_mode_type == GameModeType.GoalKick_:
            ball_step = min(1000, wm.intercept_table.first_teammate_reach_steps)
            ball_step = min(ball_step, wm.intercept_table.first_opponent_reach_steps)
            ball_step = min(ball_step, wm.intercept_table.self_reach_steps)

        real_ball_pos = Tools.convert_rpc_vector2d_to_vector2d(wm.ball.position)
        real_ball_vel = Tools.convert_rpc_vector2d_to_vector2d(wm.ball.velocity)
        return inertia_n_step_point(real_ball_pos, real_ball_vel, ball_step, agent.server_params.ball_decay)

    def _set_dynamic_positions(self, ball_pos: Vector2D, agent: IAgent):
        """
        Set dynamic positions for players based on the ball position.

        Args:
            ball_pos (Vector2D): The predicted ball position.
            agent (IAgent): The agent instance.
        """
        min_x_rectangle = [0, -52, -52, -52, -52, -52, -30, -30, -30, 0, 0, 0]
        max_x_rectangle = [0, -48, -10, -10, -10, -10, 15, 15, 15, 50, 50, 50]
        min_y_rectangle = [0, -2, -20, -10, -30, 10, -20, -30, 0, -30, 0, -20]
        max_y_rectangle = [0, 2, 10, 20, -10, 30, 20, 0, 30, 0, 30, 20]

        for i in range(1, 12):
            xx_rectangle = max_x_rectangle[i] - min_x_rectangle[i]
            yy_rectangle = max_y_rectangle[i] - min_y_rectangle[i]
            x_ball = ball_pos.x() + agent.server_params.pitch_half_length
            x_ball /= agent.server_params.pitch_half_length * 2
            y_ball = ball_pos.y() + 34
            y_ball /= agent.server_params.pitch_half_width * 2
            x_pos = xx_rectangle * x_ball + min_x_rectangle[i]
            y_pos = yy_rectangle * y_ball + min_y_rectangle[i]
            self._poses[i] = Vector2D(x_pos, y_pos)

    def _apply_offside_rule(self, agent: IAgent):
        """
        Apply the offside rule to adjust player positions.

        Args:
            agent (IAgent): The agent instance.
            wm: The world model instance.
        """
        wm = agent.wm
        if agent.server_params.use_offside:
            max_x = wm.offside_line_x
            if agent.server_params.kickoff_offside and wm.game_mode_type in [GameModeType.BeforeKickOff, GameModeType.AfterGoal_]:
                max_x = 0
            else:
                mate_step = wm.intercept_table.first_teammate_reach_steps
                if mate_step < 50:
                    trap_pos = inertia_n_step_point(Vector2D(wm.ball.position.x, wm.ball.position.y), Vector2D(wm.ball.velocity.x, wm.ball.velocity.y), mate_step, agent.server_params.ball_decay)
                    max_x = max(max_x, trap_pos.x())
                max_x -= 1.0

            for unum in range(1, 12):
                self._poses[unum].set_x(min(self._poses[unum].x(), max_x))

    s_recover_mode = False

    @staticmethod
    def get_normal_dash_power(agent: IAgent) -> float:
        """
        Get the normal dash power for the agent.

        Args:
            agent (IAgent): The agent instance.

        Returns:
            float: The normal dash power.
        """
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

    def get_offside_line(self):
        """
        Get the offside line position.

        Returns:
            float: The offside line position.
        """
        home_poses_x = sorted(pos.x() for pos in self._poses.values() if pos is not None)
        return home_poses_x[1] if len(home_poses_x) > 1 else (home_poses_x[0] if home_poses_x else 0.0)
