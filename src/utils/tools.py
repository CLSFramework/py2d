import pyrusgeom.soccer_math as smath
from pyrusgeom.soccer_math import *
from pyrusgeom.geom_2d import *
from pyrusgeom.vector_2d import Vector2D
from pyrusgeom.angle_deg import AngleDeg
from src.interfaces.IAgent import IAgent
import math
from service_pb2 import PlayerType, Player, GameModeType, ServerParam, RpcVector2D
from copy import deepcopy as copy

class Tools:
    """Utility class containing helper methods for soccer simulation calculations"""

    @staticmethod
    def inertia_final_point(playerType: PlayerType, position: Vector2D, velocity: Vector2D) -> Vector2D:
        """Calculate final position after inertia movement
        
        Args:
            playerType: Player type parameters
            position: Current position
            velocity: Current velocity
        Returns:
            Vector2D: Final position after decay
        """
        return smath.inertia_final_point(position, velocity, playerType.player_decay)
        
    @staticmethod
    def ball_move_step(first_ball_speed, ball_move_dist, ball_decay):
        return int(math.ceil(calc_length_geom_series(first_ball_speed, ball_move_dist, ball_decay)) + 1.0e-10)
    
    @staticmethod
    def first_ball_speed(ball_move_dist: float, total_step: int, ball_decay: float):
        return calc_first_term_geom_series(ball_move_dist, ball_decay, total_step)
        
    @staticmethod
    def predict_kick_count(agent: IAgent, kicker_uniform_number, first_ball_speed, ball_move_angle: AngleDeg):
        """Predict number of kicks needed to achieve target ball movement
        
        Args:
            agent: Agent instance
            kicker_uniform_number: Uniform number of kicking player
            first_ball_speed: Initial ball speed
            ball_move_angle: Target angle for ball movement
        Returns:
            int: Predicted number of kicks needed
        """
        if agent.wm.game_mode_type not in [GameModeType.PlayOn, GameModeType.PenaltyKick_]:
            return 1

        if kicker_uniform_number == agent.wm.self.uniform_number and agent.wm.self.is_kickable:
            max_vel = Tools.calc_max_velocity(ball_move_angle, agent.wm.self.kick_rate, Tools.convert_rpc_vector2d_to_vector2d(agent.wm.ball.velocity), agent.server_params)
            if max_vel.r() >= first_ball_speed:
                return 1
        if first_ball_speed > 2.5:
            return 3
        elif first_ball_speed > 1.5:
            return 2
        return 1
    
    @staticmethod
    def calc_max_velocity(target_angle: AngleDeg,
                      krate,
                      ball_vel: Vector2D,
                      sp: ServerParam):
        ball_speed_max2 = sp.ball_speed_max ** 2
        max_accel = min(sp.max_power * krate,
                        sp.ball_accel_max)

        desired_ray = Ray2D(Vector2D(0.0, 0.0), target_angle)
        next_reachable_circle = Circle2D(ball_vel, max_accel)

        num = next_reachable_circle.intersection(desired_ray)
        if len(num) == 0:
            return Vector2D(0.0, 0.0)
        
        vel1 = num[0]
        
        if len(num) == 1:
            if vel1.r2() > ball_speed_max2:
                # next inertia ball point is within reachable circle.
                if next_reachable_circle.contains(Vector2D(0.0, 0.0)):
                    # can adjust angle at least
                    vel1.set_length(sp.ball_speed_max)

                else:
                    # failed
                    vel1.assign(0.0, 0.0)

            return vel1

        vel2 = num[1]
        #
        # num == 2
        #   ball reachable circle does not contain the current ball pos.

        length1 = vel1.r2()
        length2 = vel2.r2()

        if length1 < length2:
            vel1, vel2 = vel2, vel1
            length1, length2 = length2, length1

        if length1 > ball_speed_max2:
            if length2 > ball_speed_max2:
                # failed
                vel1.assign(0.0, 0.0)

            else:
                vel1.set_length(sp.ball_speed_max)

        return vel1
    
    @staticmethod
    def estimate_min_reach_cycle(player_pos: Vector2D, player_speed_max, target_first_point: Vector2D, target_move_angle: AngleDeg):
        target_to_player: Vector2D = (player_pos - target_first_point).rotated_vector(-target_move_angle)
        if target_to_player.x() < -1.0:
            return -1
        else:
            return max( 1, int(target_to_player.abs_y() / player_speed_max))
    
    @staticmethod    
    def inertia_point(initial_pos: Vector2D, initial_vel: Vector2D, n_step: int, player_decay: float):
        return smath.inertia_n_step_point(initial_pos, initial_vel, n_step, player_decay)
    
    @staticmethod
    def convert_rpc_vector2d_to_vector2d(rpc_vector2d: RpcVector2D) -> Vector2D:
        """Convert RPC vector message to internal Vector2D representation
        
        Args:
            rpc_vector2d: Vector from RPC message
        Returns:
            Vector2D: Internal vector representation
        """
        return Vector2D(rpc_vector2d.x, rpc_vector2d.y)

    @staticmethod
    def convert_vector2d_to_rpc_vector2d(vector2d: Vector2D) -> RpcVector2D:
        """Convert internal Vector2D to RPC vector message
        
        Args:
            vector2d: Internal vector representation
        Returns:
            RpcVector2D: Vector in RPC message format
        """
        return RpcVector2D(x=vector2d.x(), y=vector2d.y())
    
    @staticmethod
    def estimate_virtual_dash_distance(player: Player, real_speed_max: float):
        pos_count = min(10, player.pos_count, player.seen_pos_count)
        max_speed = real_speed_max * 0.8

        d = 0.
        for i in range(pos_count):
            d += max_speed * math.exp(-(i**2)/15)

        return d
    
    @staticmethod
    def update_dash_distance_table(pt: PlayerType, agent: IAgent):
        sp: ServerParam = agent.server_params
        agent.memory.dash_distance_tables[pt.id] = [0] * 50
        speed = 0.0
        reach_dist = 0.0
        accel = sp.max_dash_power * pt.dash_power_rate * pt.effort_max
        for counter in range(50):
            if speed + accel > pt.player_speed_max:
                accel = pt.player_speed_max - speed
            
            speed += accel
            reach_dist += speed
            agent.memory.dash_distance_tables[pt.id][counter] = reach_dist
            speed *= pt.player_decay
            
    @staticmethod
    def cycles_to_reach_distance(agent: IAgent, player: Player, dash_dist: float):
        if dash_dist <= 0.001:
            return 0
        player_type = agent.get_player_type(player.type_id)
        dash_distance_table = agent.memory.dash_distance_tables[player_type.id]
        
        it = next((i for i, dist in enumerate(dash_distance_table) if dist >= dash_dist - 0.001), len(dash_distance_table))

        if it < len(dash_distance_table):
            return it + 1

        rest_dist = dash_dist - dash_distance_table[-1]
        cycle = len(dash_distance_table)

        cycle += math.ceil(rest_dist / player_type.real_speed_max)

        return cycle
        
    @staticmethod
    def predict_player_turn_cycle(sp: ServerParam, ptype: PlayerType, player_body: AngleDeg, player_speed, target_dist,
                                  target_angle: AngleDeg, dist_thr, use_back_dash):
        n_turn = 0
        angle_diff = (target_angle - player_body).abs()

        if use_back_dash and target_dist < 5.0 and angle_diff > 90.0 and sp.min_dash_power < -sp.max_dash_power + 1.0:
            angle_diff = abs( angle_diff - 180.0 )

        turn_margin = 180.0
        if dist_thr < target_dist:
            turn_margin = max( 15.0, AngleDeg.asin_deg( dist_thr / target_dist ) )

        speed = float(player_speed)
        while angle_diff > turn_margin:
            angle_diff -= Tools.effective_turn( sp.max_moment, speed, ptype.inertia_moment )
            speed *= ptype.player_decay
            n_turn += 1

        return n_turn
    
    @staticmethod
    def effective_turn(command_moment, speed, inertia_moment):
        return command_moment / (1.0 + inertia_moment * speed)
    
    @staticmethod
    def get_nearest_teammate(agent: IAgent, position: Vector2D):
        players = agent.wm.teammates
        best_player = None
        min_dist2 = 1000
        for player in players:
            player_position = Tools.convert_rpc_vector2d_to_vector2d(player.position)
            d2 = player_position.dist2( position )
            if d2 < min_dist2:
                min_dist2 = d2
                best_player = player

        return best_player
    
    @staticmethod
    def predict_opponent_reach_step(agent: IAgent, opponent: Player, first_ball_pos: Vector2D, first_ball_vel: Vector2D,
                                    ball_move_angle: AngleDeg, receive_point: Vector2D, max_cycle, description):
        """Predict cycles needed for opponent to reach ball
        
        Args:
            agent: Agent instance
            opponent: Opponent player
            first_ball_pos: Initial ball position
            first_ball_vel: Initial ball velocity
            ball_move_angle: Ball movement angle
            receive_point: Target receiving position
            max_cycle: Maximum cycles to consider
            description: Movement description
        Returns:
            tuple: (cycles needed, final ball position)
        """
        sp = agent.server_params

        penalty_area = Rect2D(Vector2D(sp.their_penalty_area_line_x, -sp.penalty_area_half_width ),
                                Size2D(sp.penalty_area_length, sp.penalty_area_half_width * 2.0))
        CONTROL_AREA_BUF = 0.15

        opp_pos = Vector2D(opponent.position.x, opponent.position.y)
        opp_vel = Vector2D(opponent.velocity.x, opponent.velocity.y)
        ptype:PlayerType = agent.get_type(opponent.type_id)
        min_cycle = Tools.estimate_min_reach_cycle(opp_pos, ptype.real_speed_max, first_ball_pos,
                                                   ball_move_angle)

        if min_cycle < 0:
            return 1000, None

        for cycle in range(max(1, min_cycle), max_cycle + 1):
            ball_pos = smath.inertia_n_step_point(first_ball_pos, first_ball_vel, cycle, sp.ball_decay)
            control_area = sp.catchable_area if opponent.is_goalie and penalty_area.contains(ball_pos) else ptype.kickable_area

            inertia_pos = Tools.inertia_point(opp_pos, opp_vel, cycle, ptype.player_decay)
            target_dist = inertia_pos.dist(ball_pos)

            dash_dist = target_dist
            if description == 'T' \
                and first_ball_vel.x() > 2.\
                and ( receive_point.x() > agent.wm.offside_line_x or receive_point.x() > 30.):
                pass
            else:
                dash_dist -= Tools.estimate_virtual_dash_distance(opponent, ptype.real_speed_max)
            if dash_dist - control_area - CONTROL_AREA_BUF < 0.001:
                return cycle, ball_pos

            if description == 'T' \
                and first_ball_vel.x() > 2.\
                and ( receive_point.x() > agent.wm.offside_line_x or receive_point.x() > 30.):

                dash_dist -= control_area
            else:
                if receive_point.x() < 25.:
                    dash_dist -= control_area + 0.5
                else:
                    dash_dist -= control_area + 0.2

            if dash_dist > ptype.real_speed_max * (cycle + min(opponent.pos_count, 5)):
                continue

            n_dash = Tools.cycles_to_reach_distance(dash_dist, ptype.real_speed_max)
            if n_dash > cycle + opponent.pos_count:
                continue

            n_turn = 0
            if opponent.body_direction_count > 1:
                n_turn = Tools.predict_player_turn_cycle(sp, ptype, AngleDeg(opponent.body_direction), opp_vel.r(),
                                                         target_dist,
                                                         (ball_pos - inertia_pos).th(), control_area, True)

            n_step = n_turn + n_dash if n_turn == 0 else n_turn + n_dash + 1

            bonus_step = 0
            if opponent.is_tackling:
                bonus_step = -5
            if n_step - bonus_step <= cycle:
                return cycle, ball_pos
        return 1000, None

    @staticmethod
    def exist_opponent_in(agent: IAgent, region: Region2D) -> bool:
        """Check if any opponent is within a given region
        
        Args:
            agent: Agent instance
            region: Region to check
        Returns:
            bool: True if any opponent is within the region, False otherwise
        """
        return any(region.contains(Vector2D(opp.position.x, opp.position.y)) for opp in agent.wm.opponents)
    
    def swap(x, y):
        return (copy(y), copy(x))
    
    @staticmethod
    def get_opponents_from_self(agent: IAgent) -> list[Player]:
        """Get list of opponents sorted by distance from self
        
        Args:
            agent: Agent instance
        Returns:
            list[Player]: Sorted list of opponent players
        """
        # Copy the list of opponents, excluding invalid entries
        opponents = [copy(opp) for opp in agent.wm.opponents if opp and opp.uniform_number >= 0]
        
        # Sort the copied list by distance from self
        opponents.sort(key=lambda opp: opp.dist_from_self)
        
        return opponents
    
    @staticmethod
    def get_teammates_from_self(agent: IAgent) -> list[Player]:
        """Get list of teammates sorted by distance from self
        
        Args:
            agent: Agent instance
        Returns:
            list[Player]: Sorted list of teammate players
        """
        # Copy the list of teammates, excluding invalid entries
        teammates = [copy(tm) for tm in agent.wm.teammates if tm and tm.uniform_number != agent.wm.self.uniform_number and tm.uniform_number >= 0]
        
        # Sort the copied list by distance from self
        teammates.sort(key=lambda tm: tm.dist_from_self)
        
        return teammates
    
    @staticmethod
    def get_opponents_from_ball(agent: IAgent) -> list[Player]:
        """Get list of opponents sorted by distance from ball
        
        Args:
            agent: Agent instance
        Returns:
            list[Player]: Sorted list of opponent players
        """
        # Copy the list of opponents, excluding invalid entries
        opponents = [copy(opp) for opp in agent.wm.opponents if opp and opp.uniform_number != agent.wm.self.uniform_number and opp.uniform_number >= 0]
        
        # Sort the copied list by distance from the ball
        opponents.sort(key=lambda opp: opp.dist_from_ball)
        
        return opponents
    
    @staticmethod
    def get_dash_power_to_keep_speed(agent: IAgent, speed: float, effort: float) -> float:
        """Calculate the dash power needed to maintain a given speed
        
        Args:
            agent: Agent instance
            speed: Desired speed to maintain
            effort: Effort level
        Returns:
            float: Required dash power
        """
        player_type: PlayerType = agent.player_types[agent.wm.self.id]
        return speed * ((1.0 - player_type.player_decay) / (player_type.dash_power_rate * effort))
    
    @staticmethod
    def get_teammate_nearest_to_self(agent: IAgent, with_goalie: bool) -> Player:
        """Get the teammate player nearest to the agent itself
        
        Args:
            agent: Agent instance
            with_goalie: Whether to include the goalie in the search
        Returns:
            Player: Teammate player nearest to the agent itself
        """
        teammates = [tm for tm in agent.wm.teammates if tm and tm.uniform_number != agent.wm.self.uniform_number and (with_goalie or tm.uniform_number != agent.wm.our_goalie_uniform_number)]
        return min(teammates, key=lambda tm: tm.dist_from_self, default=None)
    
    @staticmethod
    def get_opponent_nearest_to_self(agent: IAgent) -> Player:
        """Get the opponent player nearest to the agent itself
        
        Args:
            agent: Agent instance
        Returns:
            Player: Opponent player nearest to the agent itself
        """
        return min(agent.wm.opponents, key=lambda opp: opp.dist_from_self, default=None)
    
    @staticmethod
    def get_teammate_nearest_to(agent: IAgent, point: Vector2D) -> Player:
        """Get the teammate player nearest to a given point
        
        Args:
            agent: Agent instance
            point: Target point
        Returns:
            Player: Teammate player nearest to the given point
        """
        point_vec = Vector2D(point.x, point.y) if isinstance(point, RpcVector2D) else point
        teammates = [tm for tm in agent.wm.teammates if tm and tm.uniform_number != agent.wm.self.uniform_number]
        nearest_tm = min(teammates, key=lambda i: Vector2D(i.position.x, i.position.y).dist(point_vec), default=None)
        return nearest_tm
    
    @staticmethod
    def get_opponent_nearest_to(agent: IAgent, point: Vector2D) -> Player:
        """Get the opponent player nearest to a given point
        
        Args:
            agent: Agent instance
            point: Target point
        Returns:
            Player: Opponent player nearest to the given point
        """
        point_vec = Vector2D(point.x, point.y)
        opponents = [opponent for opponent in agent.wm.opponents if opponent]
        nearest_opp = min(opponents, key=lambda i: Vector2D(i.position.x, i.position.y).dist(point_vec), default=None)
        return nearest_opp
    
    @staticmethod
    def get_inertia_final_point(initial_pos: Vector2D, initial_vel: Vector2D, decay: float) -> Vector2D:
        """Calculate the final position of an object given its initial position, velocity, and decay factor
        
        Args:
            initial_pos: Initial position of the object
            initial_vel: Initial velocity of the object
            decay: Decay factor
        Returns:
            Vector2D: Final position of the object
        """
        return initial_pos + Tools.get_inertia_final_travel(initial_vel, decay)
    
    @staticmethod
    def get_inertia_final_travel(initial_vel: Vector2D, decay: float) -> Vector2D:
        """Calculate the final travel distance of an object given its initial velocity and decay factor
        
        Args:
            initial_vel: Initial velocity of the object
            decay: Decay factor
        Returns:
            Vector2D: Final travel distance
        """
        return initial_vel / (1.0 - decay)
    
    @staticmethod
    def calc_first_term_geom_series_last(last_term: float, total_sum: float, ratio: float) -> float:
        """Calculate the first term of a geometric series given the last term, sum, and ratio
        
        Args:
            last_term: The last term of the series
            total_sum: The sum of the series
            ratio: The common ratio of the series
        Returns:
            float: The first term of the series
        """
        if math.isclose(last_term, 0.0, abs_tol=0.001):
            return total_sum * (1.0 - ratio)
        
        inverse_ratio = 1.0 / ratio
        tmp = 1.0 + total_sum * (inverse_ratio - 1.0) / last_term
        
        if tmp < 0.001:
            return last_term
        
        return last_term * pow(inverse_ratio, math.log(tmp) / math.log(inverse_ratio))
    
    @staticmethod
    def get_teammates_from_ball(agent: IAgent) -> list[Player]:
        """Get list of teammates sorted by distance from ball
        
        Args:
            agent: Agent instance
        Returns:
            list[Player]: Sorted list of teammate players
        """
        tms = [copy(tm) for tm in agent.wm.teammates if tm and tm.uniform_number != agent.wm.self.uniform_number and tm.uniform_number >= 0]
        tms.sort(key=lambda tm: tm.dist_from_ball)
        return tms
    
    @staticmethod
    def calculate_ball_inertia_final_point(initial_pos: Vector2D, initial_vel: Vector2D, ball_decay: float) -> Vector2D:
        """Calculate the final position of the ball after inertia movement
        
        Args:
            initial_pos: Initial position of the ball
            initial_vel: Initial velocity of the ball
            ball_decay: Ball decay factor
        Returns:
            Vector2D: Final position of the ball
        """
        return initial_pos + inertia_final_travel(initial_vel, ball_decay)
    
    @staticmethod
    def get_opponent_goalie(agent: IAgent) -> Player:
        """Get the opponent goalie
        
        Args:
            agent: Agent instance
        Returns:
            Player: Opponent goalie player
        """
        return next((opponent for opponent in agent.wm.opponents if opponent.uniform_number == agent.wm.their_goalie_uniform_number), None)
