import pyrusgeom.soccer_math as smath
from pyrusgeom.soccer_math import *
from pyrusgeom.geom_2d import *
from pyrusgeom.vector_2d import Vector2D
from pyrusgeom.angle_deg import AngleDeg
from src.interfaces.IAgent import IAgent
import math
from service_pb2 import PlayerType, Player, GameModeType, ServerParam, RpcVector2D
from copy import copy

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
            max_vel = Tools.calc_max_velocity(ball_move_angle, agent.wm.self.kick_rate, Tools.vector2d_message_to_vector2d(agent.wm.ball.velocity), agent.server_params)
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
    def vector2d_message_to_vector2d(v: Vector2D):
        return Vector2D(v.x, v.y)
    
    @staticmethod
    def estimate_virtual_dash_distance(player: Player, real_speed_max: float):
        pos_count = min(10, player.pos_count, player.seen_pos_count)
        max_speed = real_speed_max * 0.8

        d = 0.
        for i in range(pos_count):
            d += max_speed * math.exp(-(i**2)/15)

        return d
    
    @staticmethod
    def cycles_to_reach_distance(dash_dist, real_speed_max):
        if dash_dist <= 0.001:
            return 0
        return int(math.ceil(dash_dist / real_speed_max))
        # todo: implement this
        # ddc = 0
        # for dd in self._dash_distance_table:
        #     if dash_dist <= dd:
        #         return ddc
        #     ddc += 1

        # cycle = len(self._dash_distance_table)
        # rest_dist = dash_dist - self._dash_distance_table[cycle - 1]
        # cycle += int(math.ceil(rest_dist / self.real_speed_max()))
        # return cycle
        
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
            player_position = Tools.vector2d_message_to_vector2d(player.position)
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

    def ExistOpponentIn(agent: IAgent, region: Region2D):
        for i in agent.wm.opponents:
            if region.contains(Vector2D(i.position.x, i.position.y)):
                return True
    
    def swap(x, y):
        return (copy(y), copy(x))
    
    def OpponentsFromSelf(agent: IAgent) -> list[Player]:
        """Get list of opponents sorted by distance from self
        
        Args:
            agent: Agent instance
        Returns:
            list[Player]: Sorted list of opponent players
        """
        opp = agent.wm.opponents
        for i in opp:
            if i == None or i.uniform_number == agent.wm.self.uniform_number or i.uniform_number < 0:
                opp.remove(i)
        for i in range(0, len(opp)):
            for j in range(i + 1, len(opp)):
                if opp[i].dist_from_self > opp[j].dist_from_self:
                    Tools.swap(opp[i], opp[j])
        return opp
    
    def TeammatesFromSelf(agent: IAgent) -> list[Player]:
        """Get list of teammates sorted by distance from self
        
        Args:
            agent: Agent instance
        Returns:
            list[Player]: Sorted list of teammate players
        """
        tms = agent.wm.teammates
        for i in tms:
            if i == None or i.uniform_number == agent.wm.self.uniform_number or i.uniform_number < 0:
                tms.remove(i)
        for i in range(0, len(tms)):
            for j in range(i + 1, len(tms)):
                if tms[i].dist_from_self > tms[j].dist_from_self:
                    Tools.swap(tms[i], tms[j])
        return tms
    
    def OpponentsFromBall(agent: IAgent):
        """Get list of opponents sorted by distance from ball
        
        Args:
            agent: Agent instance
        Returns:
            list[Player]: Sorted list of opponent players
        """
        opp = agent.wm.opponents
        for i in opp:
            if i == None or i.uniform_number == agent.wm.self.uniform_number or i.uniform_number < 0:
                opp.remove(i)
        for i in range(0, len(opp)):
            for j in range(i + 1, len(opp)):
                if opp[i].dist_from_ball > opp[j].dist_from_ball:
                    Tools.swap(opp[i], opp[j])
        return opp
    
    def GetDashPowerToKeepSpeed(agent: IAgent, speed: float, effort: float):
        return speed * ((1.0 - agent.player_types[agent.wm.self.id].player_decay) / (agent.player_types[agent.wm.self.id].dash_power_rate * effort))
    
    def GetTeammateNearestToSelf(agent: IAgent, with_goalie: bool) -> Player:
        nearest_dist = 1000000.0
        nearest_tm = None
        for i in agent.wm.teammates:
            if i.uniform_number == agent.wm.self.uniform_number:
                continue
            if with_goalie == False and i.uniform_number == agent.wm.our_goalie_uniform_number:
                continue
            dist = i.dist_from_self
            if dist < nearest_dist:
                nearest_dist = dist
                nearest_tm = i
        return nearest_tm
    
    def GetOpponentNearestToSelf(agent: IAgent) -> Player:
        nearest_dist = 1000000.0
        nearest_opp = None
        for i in agent.wm.opponents:
            dist = i.dist_from_self
            if dist < nearest_dist:
                nearest_dist = dist
                nearest_opp = i
        return nearest_opp
    
    def GetTeammateNearestTo(agent: IAgent, point: Vector2D) -> Player:
        nearest_dist = 1000000.0
        nearest_tm = None
        for i in agent.wm.teammates:
            if i.uniform_number == agent.wm.self.uniform_number:
                continue
            i_pos = Vector2D(i.position.x, i.position.y)
            dist = i_pos.dist(point)
            if dist < nearest_dist:
                nearest_dist = dist
                nearest_tm = i
        return nearest_tm
    
    def GetOpponentNearestTo(agent: IAgent, point: Vector2D) -> Player:
        point_vec = Vector2D(point.x, point.y)
        nearest_dist = 1000000.0
        nearest_opp = None
        for i in agent.wm.opponents:
            i_pos = Vector2D(i.position.x, i.position.y)
            dist = i_pos.dist(point_vec)
            if dist < nearest_dist:
                nearest_dist = dist
                nearest_opp = i
        return nearest_opp
    
    def InertiaFinalPoint(initial_pos: Vector2D, initial_vel: Vector2D, decay: float):
        return initial_pos + Tools.InertiaFinalTravel(initial_vel, decay)
    
    def InertiaFinalTravel(initial_vel: Vector2D, decay: float):
        return initial_vel / (1.0 - decay)
    
    def calc_first_term_geom_series_last(last_term: float, sum: float, r: float):
        if math.fabs(last_term) < 0.001:
            return sum * (1.0 - r)
        inverse = 1.0 / r
        tmp = 1.0 + sum * (inverse - 1.0) / last_term
        if tmp < 0.001:
            return last_term
        return last_term * pow(inverse, math.log(tmp) / math.log(inverse))
    
    def TeammatesFromBall(agent: IAgent):

        tms = agent.wm.teammates
        for i in tms:
            if i == None or i.uniform_number == agent.wm.self.uniform_number or i.uniform_number < 0:
                tms.remove(i)
        for i in range(0, len(tms)):
            for j in range(i + 1, len(tms)):
                if tms[i].dist_from_ball > tms[j].dist_from_ball:
                    Tools.swap(tms[i], tms[j])
        return tms
    
    def BallInertiaFinalPoint(initial_pos: Vector2D, initial_vel: Vector2D, ball_decay: float):
        return Vector2D(initial_pos) + inertia_final_travel(initial_vel, ball_decay)
    
    def OpponentGoalie(agent: IAgent) -> Player:
        for i in agent.wm.opponents:
            if i.uniform_number == agent.wm.their_goalie_uniform_number : 
                return i