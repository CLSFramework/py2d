from typing import TYPE_CHECKING
from src.interfaces.IBehavior import IBehavior
import numpy as np
from src.interfaces.IAgent import IAgent
from src.utils.tools import Tools
from pyrusgeom.vector_2d import Vector2D
from pyrusgeom.angle_deg import AngleDeg
from pyrusgeom.line_2d import Line2D
from pyrusgeom.ray_2d import Ray2D
from pyrusgeom.size_2d import Size2D
from pyrusgeom.rect_2d import Rect2D
from src.behaviors.starter.bhv_starter_dribble import BhvStarterDribble
from src.behaviors.starter.bhv_starter_go_to_placed_ball import BhvStarterGoToPlacedBall
from service_pb2 import *
from src.utils.tools import Tools
from src.behaviors.starter.bhv_starter_clearball import BhvStarterClearBall

if TYPE_CHECKING:
    from src.sample_player_agent import SamplePlayerAgent

class BhvStarterPenalty(IBehavior):
    def __init__(self):
        pass
    
    def execute(self, agent: "SamplePlayerAgent"):
        agent.logger.debug("BhvStarterPenalty.execute")
        wm = agent.wm
        state = wm.penalty_kick_state
        actions = []
        if wm.game_mode_type == GameModeType.PenaltySetup_:
            if state.current_taker_side == wm.our_side:
                if state.is_kick_taker:
                    actions += self.do_kicker_setup(agent)
                    
            else:
                if wm.self.is_goalie:
                    actions += self.do_goalie_setup(agent)
                    

        elif wm.game_mode_type == GameModeType.PenaltyReady_:
            if state.current_taker_side == wm.our_side:
                if state.is_kick_taker:
                    actions += self.do_kicker_ready(agent)
                    
            else:
                if wm.self.is_goalie:
                    actions += self.do_goalie_setup(agent)
                    

        elif wm.game_mode_type == GameModeType.PenaltyTaken_:
            if state.current_taker_side == wm.our_side:
                if state.is_kick_taker:
                    actions += self.do_kicker(agent)
                    
            else:
                if wm.self.is_goalie:
                    actions += self.do_goalie(agent)
                    

        elif wm.game_mode_type in [GameModeType.PenaltyScore_, GameModeType.PenaltyMiss_]:
            if state.current_taker_side == wm.our_side:
                if wm.self.is_goalie:
                    actions += self.do_goalie_setup(agent)
                    

        elif wm.game_mode_type in [GameModeType.PenaltyOnfield_, GameModeType.PenaltyFoul_]:
            pass  


        if wm.self.is_goalie:
            actions += self.do_goalie_wait(agent)
        else:
            actions += self.do_kicker_wait(agent)
            
        for i in actions:
            if i is not None:
                agent.add_action(i)
    

    def do_kicker_wait(self, agent: IAgent) -> bool:
        actions = []
        dist_step = (9.0 + 9.0) / 12
        wait_pos = Vector2D(-2.0, -9.8 + dist_step * agent.wm.self.uniform_number)

        actions.append(PlayerAction(body_go_to_point=Body_GoToPoint(target_point=Tools.convert_vector2d_to_rpc_vector2d(wait_pos), distance_threshold=0.3, max_dash_power=agent.server_params.max_dash_power)))
            

        return actions

    def do_kicker_setup(self, agent: IAgent):
        actions = []
        goal_c = Vector2D(agent.server_params.pitch_half_length,0)
        opp_goalie = Tools.get_opponent_goalie(agent)
        place_angle = 0.0
        go_to_placed_ball = BhvStarterGoToPlacedBall(place_angle)
        go_to_placed_ball = go_to_placed_ball.execute(agent)
        if go_to_placed_ball == []:
            actions.append(PlayerAction(body_turn_to_point=Body_TurnToPoint(target_point=Tools.convert_vector2d_to_rpc_vector2d(goal_c), cycle=2)))
        else:
            for i in go_to_placed_ball:
                if not i == None:
                    actions.append(i)
        return actions

    def do_kicker_ready(self, agent: IAgent):
        actions = []
        wm = agent.wm
        state = wm.penalty_kick_state

        if wm.self.stamina < agent.server_params.stamina_max - 10.0 and (wm.cycle - state.cycle > agent.server_params.pen_ready_wait - 3):
            actions += self.do_kicker_setup(agent)

        if not wm.self.is_kickable:
            actions += self.do_kicker_setup(agent)

        actions += self.do_kicker(agent)
        return actions

    def do_kicker(self, agent: IAgent):
        actions = []
        if not agent.server_params.pen_allow_mult_kicks:
            actions += self.do_one_kick_shoot(agent)

        wm = agent.wm

        if not wm.self.is_kickable:
            actions.append(PlayerAction(body_intercept=Body_Intercept()))
            actions.append(PlayerAction(body_go_to_point=Body_GoToPoint(target_point=wm.ball.position, distance_threshold=0.4, max_dash_power=agent.server_params.max_dash_power)))
            
        actions += self.do_shoot(agent)
        actions += self.do_dribble(agent)
        
        return actions

    def do_one_kick_shoot(self, agent: IAgent):
        actions = []
        wm = agent.wm
        ball_vel = Tools.convert_rpc_vector2d_to_vector2d(wm.ball.velocity)
        ball_speed = ball_vel.r()
        if not agent.server_params.pen_allow_mult_kicks and ball_speed > 0.3:
            return []

        if not agent.wm.self.is_kickable:
            actions.append(PlayerAction(body_go_to_point=Body_GoToPoint(target_point=wm.ball.position, distance_threshold=0.4, max_dash_power=agent.server_params.max_dash_power)))
            return []

        if abs(agent.wm.ball.angle_from_self - agent.wm.self.body_direction) > 3.0:
            actions.append(PlayerAction(body_turn_to_ball=Body_TurnToBall(cycle=2)))
            opp_goalie = Tools.get_opponent_goalie(agent)
            if opp_goalie:
                actions.append(PlayerAction(neck_turn_to_point=Neck_TurnToPoint(target_point=opp_goalie.position)))
            else:
                goal_c = RpcVector2D(x=agent.server_params.pitch_half_length, y=0)
                actions.append(PlayerAction(neck_turn_to_point=Neck_TurnToPoint(target_point=goal_c)))
            return []

        shoot_point = Vector2D(agent.server_params.pitch_half_length, 0)
        opp_goalie = Tools.get_opponent_goalie(agent)
        if opp_goalie:
            shoot_point.set_y(((agent.server_params.goal_width)/2.0) - 1.0)
            if abs(opp_goalie.position.y) > 0.5:
                if opp_goalie.position.y > 0.0:
                    shoot_point.set_y(shoot_point.y()*-1.0) 
        actions.append(PlayerAction(body_kick_one_step=Body_KickOneStep(target_point=Tools.convert_vector2d_to_rpc_vector2d(shoot_point), first_speed=agent.server_params.ball_speed_max)))

        return actions

    def do_shoot(self, agent: IAgent):
        actions = []
        wm = agent.wm
        state = wm.penalty_kick_state

        if wm.cycle - state.cycle > agent.server_params.pen_taken_wait - 25:
            actions += self.do_one_kick_shoot(agent)

        shot_point = Vector2D(0, 0)
        shot_speed = 0.0
        if self.get_shoot_target(agent, shot_point, shot_speed):
            actions.append(PlayerAction(body_smart_kick=Body_SmartKick(target_point=Tools.convert_vector2d_to_rpc_vector2d(shot_point), first_speed=shot_speed, first_speed_threshold=shot_speed * 0.96, max_steps=2)))

        return actions

    def get_shoot_target(self, agent: IAgent, point: Vector2D, first_speed: float) -> bool:
        wm = agent.wm
        SP = agent.server_params
        ball_position = Tools.convert_rpc_vector2d_to_vector2d(wm.ball.position)
        if Vector2D(agent.server_params.pitch_half_length,0).dist2(ball_position) > 35.0 ** 2:
            return False

        opp_goalie = Tools.get_opponent_goalie(agent)
        if not opp_goalie:
            if point: point.assign(Vector2D(agent.server_params.pitch_half_length,0))
            if first_speed: first_speed = SP.ball_speed_max
            return True

        best_l_or_r = 0
        best_speed = SP.ball_speed_max + 1.0
        post_buf = 1.0 + min(2.0, (SP.pitch_half_length - abs(wm.self.position.x)) * 0.1)

        shot_l = Vector2D(SP.pitch_half_length, -(SP.goal_width)/2 + post_buf)
        shot_r = Vector2D(SP.pitch_half_length, (SP.goal_width)/2 - post_buf)

        angle_l = Vector2D(shot_l - ball_position).th()
        angle_r = Vector2D(shot_r - ball_position).th()

        goalie_max_speed = 1.0
        goalie_dist_buf = goalie_max_speed * min(5, opp_goalie.pos_count) + SP.catch_area_l + 0.2
        goalie_next_pos = Tools.convert_rpc_vector2d_to_vector2d(opp_goalie.position) + Tools.convert_rpc_vector2d_to_vector2d(opp_goalie.velocity)

        for i in range(2):
            target = shot_l if i == 0 else shot_r
            angle = angle_l if i == 0 else angle_r

            dist2goal = ball_position.dist(target)
            tmp_first_speed = (dist2goal + 5.0) * (1.0 - SP.ball_decay)
            tmp_first_speed = max(1.2, tmp_first_speed)

            over_max = False
            while not over_max:
                if tmp_first_speed > SP.ball_speed_max:
                    over_max = True
                    tmp_first_speed = SP.ball_speed_max

                ball_pos = Tools.convert_rpc_vector2d_to_vector2d(wm.ball.position)
                ball_vel = Vector2D.polar2vector(tmp_first_speed, angle)
                ball_pos += ball_vel
                ball_vel *= SP.ball_decay

                goalie_can_reach = False
                cycle = 0.0
                while abs(ball_pos.x()) < SP.pitch_half_length:
                    if goalie_next_pos.dist(ball_pos) < goalie_max_speed * cycle + goalie_dist_buf:
                        goalie_can_reach = True
                        break

                    ball_pos += ball_vel
                    ball_vel *= SP.ball_decay
                    cycle += 1.0

                if not goalie_can_reach:
                    if tmp_first_speed < best_speed:
                        best_l_or_r = i
                        best_speed = tmp_first_speed
                    break

                tmp_first_speed += 0.4

        if best_speed <= SP.ball_speed_max:
            if point: point = (shot_l if best_l_or_r == 0 else shot_r)
            if first_speed: first_speed = best_speed
            return True

        return False

    def do_dribble(self, agent: IAgent):
        actions = []
        CONTINUAL_COUNT = 20
        wm = agent.wm
        S_target_continual_count = CONTINUAL_COUNT
        selfpos = Tools.convert_rpc_vector2d_to_vector2d(wm.self.position)
        SP = agent.server_params
        wm = agent.wm
        goal_c = Vector2D(agent.server_params.pitch_half_length,0)
        penalty_abs_x = SP.their_penalty_area_line_x
        opp_goalie = Tools.get_opponent_goalie(agent)
        goalie_max_speed = 1.0
        my_abs_x = abs(selfpos.x())
        opp_goalie_pos = Tools.convert_rpc_vector2d_to_vector2d(opp_goalie.position)
        goalie_dist = opp_goalie_pos.dist(selfpos) - goalie_max_speed * min(5, opp_goalie.pos_count) if opp_goalie else 200.0
        goalie_abs_x = abs(opp_goalie.position.x) if opp_goalie else 200.0

        base_target_abs_y = (SP.goal_width)/2 + 4.0
        drib_target = goal_c
        drib_dashes = 6

        if my_abs_x < penalty_abs_x - 3.0 and goalie_dist > 10.0:
            pass
        else:
            if goalie_abs_x > my_abs_x:
                if goalie_dist < 4.0:
                    if S_target_continual_count == 1:
                        S_target_continual_count = -CONTINUAL_COUNT
                    elif S_target_continual_count == -1:
                        S_target_continual_count = CONTINUAL_COUNT
                    elif S_target_continual_count > 0:
                        S_target_continual_count -= 1
                    else:
                        S_target_continual_count += 1
                if S_target_continual_count > 0:
                    if selfpos.y() < -base_target_abs_y + 2.0:
                        drib_target.set_y(  base_target_abs_y  )
                    else:
                        drib_target.set_y(  -base_target_abs_y  )
                else:
                    if selfpos.y() > base_target_abs_y - 2.0:
                        drib_target.set_y(  -base_target_abs_y  )
                    else:
                        drib_target.set_y(  base_target_abs_y  )

                drib_target.set_x(  goalie_abs_x + 1.0)
                drib_target.set_x( min(max(penalty_abs_x - 2.0, drib_target.x()), SP.pitch_half_length - 4.0))

                dashes = (selfpos.dist(drib_target) * 0.8 / SP.player_speed_max)
                drib_dashes = int(dashes)
                drib_dashes = min(max(1, drib_dashes), 6)

        if opp_goalie and goalie_dist < 5.0:
            drib_angle = Vector2D(drib_target - selfpos).th()
            goalie_angle = Vector2D(Tools.convert_rpc_vector2d_to_vector2d(opp_goalie.position) - selfpos).th()
            drib_dashes = 6
            if (drib_angle - goalie_angle).abs() < 80.0:
                drib_target = selfpos + Vector2D.polar2vector(10.0, goalie_angle + (1 if selfpos.y() > 0 else -1) * 55.0)

        target_rel = drib_target - selfpos
        buf = 2.0
        if drib_target.abs_x() < penalty_abs_x:
            buf += 2.0

        if target_rel.abs_x() < 5.0 and (not opp_goalie or Tools.convert_rpc_vector2d_to_vector2d(opp_goalie.position).dist(drib_target) > target_rel.r() - buf):
            if (target_rel.th() - wm.self.body_direction).abs() < 5.0:
                first_speed = Tools.calc_first_term_geom_series_last(0.5, target_rel.r(), SP.ball_decay)
                first_speed = min(first_speed, SP.ball_speed_max)
                actions.append(PlayerAction(body_smart_kick=Body_SmartKick(target_point=Tools.convert_vector2d_to_rpc_vector2d(drib_target), first_speed=first_speed, first_speed_threshold=first_speed * 0.96, max_steps=3)))
            else:
                actions.append(PlayerAction(body_turn_to_point=Body_TurnToPoint(target_point=Tools.convert_vector2d_to_rpc_vector2d(drib_target), cycle=2)))

        else:
            dribble = BhvStarterDribble()
            actions.append(dribble.execute(agent))

        return actions

    def do_goalie_wait(self, agent: IAgent):
        return [PlayerAction(body_turn_to_ball=Body_TurnToBall(cycle=2))]

    def do_goalie_setup(self, agent: IAgent):
        actions = []
        our_team_goal_line_x = Vector2D(-agent.server_params.pitch_half_length, 0)
        move_point = Vector2D(our_team_goal_line_x + agent.server_params.pen_max_goalie_dist_x - 0.1, 0.0)
        actions.append(PlayerAction(body_go_to_point=Body_GoToPoint(target_point=Tools.convert_vector2d_to_rpc_vector2d(move_point), distance_threshold=0.5, max_dash_power=agent.server_params.max_dash_power)))

        if abs(agent.wm.self.body_direction) > 2.0:
            actions.append(PlayerAction(body_turn_to_point=Body_TurnToPoint(target_point=RpcVector2D(x=0, y=0), cycle=2)))
        return actions

    def do_goalie(self, agent: IAgent):
        actions = []
        SP = agent.server_params
        wm = agent.wm

        our_penalty = Rect2D(Vector2D(-SP.pitch_half_length, -SP.penalty_area_half_width + 1.0), Size2D(SP.penalty_area_length - 1.0, (SP.penalty_area_half_width)*2 - 2.0))

        if wm.ball.dist_from_self < SP.catchable_area - 0.05 and our_penalty.contains(Tools.convert_vector2d_to_rpc_vector2d(wm.ball.position)):
            actions.append(PlayerAction(catch=Catch()))

        if wm.self.is_kickable:
            clear_ball = BhvStarterClearBall()
            actions.append(clear_ball.execute(agent))

        if not SP.pen_allow_mult_kicks:
            if pow(Tools.convert_rpc_vector2d_to_vector2d(wm.ball.velocity).r(), 2) < 0.01 and abs(wm.ball.position.x) < SP.pitch_half_length - SP.pen_dist_x - 1.0:
                actions += self.do_goalie_setup(agent)

            if Tools.convert_rpc_vector2d_to_vector2d(wm.ball.velocity).r2() > 0.01: 
                actions += self.do_goalie_slide_chase(agent)

        actions += self.do_goalie_basic_move(agent)
        return actions

    def do_goalie_basic_move(self, agent: IAgent):
        actions = []
        SP = agent.server_params
        wm = agent.wm
        ballpos = Tools.convert_rpc_vector2d_to_vector2d(wm.ball.position)
        ballvel = Tools.convert_rpc_vector2d_to_vector2d(wm.ball.velocity)
        our_penalty = Rect2D(Vector2D(-SP.pitch_half_length, -SP.penalty_area_half_width + 1.0), Size2D(SP.penalty_area_length - 1.0, (SP.penalty_area_half_width)*2 - 2.0))

        self_min = wm.intercept_table.self_reach_steps
        move_pos = Tools.inertia_point(ballpos, ballvel, self_min, agent.server_params.ball_decay)

        if our_penalty.contains(move_pos):
            if wm.intercept_table.first_opponent_reach_steps < wm.intercept_table.self_reach_steps or wm.intercept_table.self_reach_steps <= 4:
                actions.append(PlayerAction(body_intercept=Body_Intercept()))

        my_pos = Tools.convert_rpc_vector2d_to_vector2d(wm.self.position)
        ball_pos = Tools.convert_rpc_vector2d_to_vector2d(Tools.get_opponents_from_ball(agent)[0].position) + Tools.convert_rpc_vector2d_to_vector2d(Tools.get_opponents_from_ball(agent)[0].velocity) if wm.kickable_opponent_existance else Tools.inertia_point(ballpos, ballvel, 3, SP.ball_decay)
        move_pos = self.get_goalie_move_pos(agent, ball_pos, my_pos)
        
        actions.append(PlayerAction(body_go_to_point=Body_GoToPoint(target_point=Tools.convert_vector2d_to_rpc_vector2d(move_pos), distance_threshold=0.5, max_dash_power=SP.max_dash_power)))
        face_angle = wm.ball.angle_from_self
        face_angle += 90.0 if AngleDeg(wm.ball.angle_from_self).is_left_of(AngleDeg(wm.self.body_direction)) else -90.0 
        actions.append(PlayerAction(body_turn_to_angle=Body_TurnToAngle(angle=face_angle)))
        return actions

    def get_goalie_move_pos(self, agent: IAgent, ball_pos: Vector2D, my_pos: Vector2D) -> Vector2D:
        SP = agent.server_params
        min_x = -SP.pitch_half_length + SP.catch_area_l * 0.9

        if ball_pos.x < -49.0:
            return Vector2D(min_x, ball_pos.y()) if ball_pos.abs_y() < (SP.goal_width)/2 else Vector2D(min_x, np.sign(ball_pos.y()) * ((SP.goal_width)/2))

        goal_l = Vector2D(-SP.pitch_half_length, -((SP.goal_width)/2))
        goal_r = Vector2D(-SP.pitch_half_length, ((SP.goal_width)/2))

        ball2post_angle_l = Vector2D(goal_l - ball_pos).th()
        ball2post_angle_r = Vector2D(goal_r - ball_pos).th()

        line_dir = AngleDeg.bisect(ball2post_angle_r, ball2post_angle_l)
        line_mid = Line2D(ball_pos, line_dir)
        goal_line = Line2D(goal_l, goal_r)

        intersection = goal_line.intersection(line_mid)
        if intersection.is_valid():
            line_l = Line2D(ball_pos, goal_l)
            line_r = Line2D(ball_pos, goal_r)

            alpha = AngleDeg.atan2_deg(((SP.goal_width)/2), SP.penalty_area_length() - 2.5)
            dist_from_goal = ((line_l.dist(intersection) + line_r.dist(intersection)) * 0.5) / np.sin(alpha)

            if dist_from_goal <= ((SP.goal_width)/2):
                dist_from_goal = ((SP.goal_width)/2)

            if (ball_pos - intersection).r() + 1.5 < dist_from_goal:
                dist_from_goal = (ball_pos - intersection).r() + 1.5

            position_error = line_dir - (intersection - my_pos).th()
            danger_angle = 21.0
            if position_error.abs() > danger_angle:
                dist_from_goal *= (1.0 - ((position_error.abs() - danger_angle) / (180.0 - danger_angle)) * 0.5)

            result = intersection
            add_vec = ball_pos - intersection
            add_vec.set_length(dist_from_goal)
            result += add_vec
            if result.x() < min_x:
                result.set_x(  min_x  )
            return result
        else:
            if ball_pos.x() > 0.0:
                return Vector2D(min_x, goal_l.y())
            elif ball_pos.x() < 0.0:
                return Vector2D(min_x, goal_r.y())
            else:
                return Vector2D(min_x, 0.0)

    def do_goalie_slide_chase(self, agent: IAgent):
        actions = []
        wm = agent.wm

        if abs(90.0 - wm.self.body_direction) > 2.0:
            face_point = Vector2D(wm.self.position.x, 100.0)
            face_point.set_y(  -100.0 if wm.self.body_direction < 0.0 else 100.0  )
            actions.append(PlayerAction(body_turn_to_point=Body_TurnToPoint(target_point=Tools.convert_vector2d_to_rpc_vector2d(face_point), cycle=2)))

        ball_ray = Ray2D(Tools.convert_rpc_vector2d_to_vector2d(wm.ball.position), Tools.convert_rpc_vector2d_to_vector2d(wm.ball.velocity).th())
        ball_line = Line2D(ball_ray.origin(), ball_ray.dir())
        my_line = Line2D(wm.self.position, wm.self.body_direction)

        intersection = my_line.intersection(ball_line)
        if not intersection.is_valid() or not ball_ray.in_right_dir(intersection):
            actions.append(PlayerAction(body_intercept=Body_Intercept(save_recovery=False)))

        if wm.self.position.dist(intersection) < agent.server_params.catch_area_l * 0.7:
            actions.append(PlayerAction(body_stop_dash=Body_StopDash(save_recovery=False)))
        self_position = Tools.convert_rpc_vector2d_to_vector2d(wm.self.position)
        angle = Vector2D(intersection - self_position).th()
        dash_power = agent.server_params.max_dash_power()
        if (angle - AngleDeg(wm.self.body_direction)).abs() > 90.0:
            dash_power = agent.server_params.min_dash_power
        actions.append(PlayerAction(dash=Dash(dash_power)))
        return actions
