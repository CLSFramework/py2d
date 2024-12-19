from typing import TYPE_CHECKING
from src.interfaces.IBehavior import IBehavior
from src.interfaces.IAgent import IAgent
import math
from service_pb2 import *
from pyrusgeom.vector_2d import Vector2D
from pyrusgeom.segment_2d import Segment2D
from pyrusgeom.circle_2d import Circle2D
from pyrusgeom.angle_deg import AngleDeg
from src.utils.tools import Tools
from src.strategy.starter_strategy import StarterStrategy
from src.utils.tools import Tools
from src.behaviors.starter_setplay.bhv_starter_setplay_kickoff import BhvStarterSetPlayKickOff
from src.behaviors.starter_setplay.bhv_starter_their_goal_kick_move import BhvStarterTheirGoalKickMove
from src.behaviors.starter_setplay.bhv_starter_setplay_freekick import BhvStarterSetPlayFreeKick
from src.behaviors.starter_setplay.bhv_starter_setplay_goal_kick import BhvStarterSetPlayGoalKick
from src.behaviors.starter_setplay.bhv_starter_setplay_kickin import BhvStarterSetPlayKickIn
from src.behaviors.starter_setplay.bhv_starter_setplay_indirect_freekick import BhvStarterSetPlayIndirectFreeKick

if TYPE_CHECKING:
    from src.sample_player_agent import SamplePlayerAgent
    
class BhvStarterSetPlay(IBehavior):
    def __init__(self):
        self.setplay_kickoff = BhvStarterSetPlayKickOff()
        self.their_goal_kick_move = BhvStarterTheirGoalKickMove()
        self.setplay_freekick = BhvStarterSetPlayFreeKick()
        self.setplay_goal_kick = BhvStarterSetPlayGoalKick()
        self.setplay_kickin = BhvStarterSetPlayKickIn()
        self.setplay_indirect_freekick = BhvStarterSetPlayIndirectFreeKick()

    def execute(self, agent: "SamplePlayerAgent"):
        agent.logger.debug("BhvStarterSetPlay.execute")
        wm = agent.wm
        if wm.self.is_goalie:
            if wm.game_mode_type != GameModeType.BackPass_ and wm.game_mode_type != GameModeType.IndFreeKick_:
                agent.add_action(PlayerAction(bhv_goalie_free_kick=bhv_goalieFreeKick())) #TODO
                return True
            else:
                self.setplay_indirect_freekick.execute(agent)
                return True

        if wm.game_mode_type == GameModeType.KickOff_:
            if wm.game_mode_side == wm.our_side:
                return self.setplay_kickoff.execute(agent)
            else:
                return self.doBasicTheirSetPlayMove(agent)


        if wm.game_mode_type in [GameModeType.KickIn_, GameModeType.CornerKick_]:
            if wm.game_mode_side == wm.our_side:
                return self.setplay_kickin.execute(agent)
            else:
                return self.doBasicTheirSetPlayMove(agent)

        if wm.game_mode_type == GameModeType.GoalKick_:
            if wm.game_mode_side == wm.our_side:
                return self.setplay_goal_kick.execute(agent)
            else:
                return self.their_goal_kick_move.execute(agent)

        if wm.game_mode_type in [GameModeType.BackPass_, GameModeType.IndFreeKick_]:
            return self.setplay_indirect_freekick.execute(agent)

        if wm.game_mode_type in [GameModeType.FoulCharge_, GameModeType.FoulPush_]:
            if (wm.ball.position.x < agent.server_params.our_penalty_area_line_x + 1.0 and abs(wm.ball.position.y) < agent.server_params.penalty_area_half_width + 1.0):
                return self.setplay_indirect_freekick.execute(agent)
            elif (wm.ball.position.x > agent.server_params.their_penalty_area_line_x - 1.0 and
                  abs(wm.ball.position.y) < agent.server_params.penalty_area_half_width + 1.0):
                return self.setplay_indirect_freekick.execute(agent)

        if wm.is_our_set_play:
            return self.setplay_freekick.execute(agent)
        else:
            return self.doBasicTheirSetPlayMove(agent)

    def get_set_play_dash_power(self, agent: "SamplePlayerAgent"):
        wm = agent.wm
        if not wm.is_our_set_play:
            target_point = agent.strategy.get_position(wm.self.uniform_number, agent)
            if target_point.x() > wm.self.position.x:
                if (wm.ball.position.x < -30.0 and
                        target_point.x() < wm.ball.position.x):
                    return wm.self.get_safety_dash_power
                rate = 0.0
                if wm.self.stamina > agent.server_params.stamina_max * 0.8:
                    rate = 1.5 * wm.self.stamina / agent.server_params.stamina_max
                else:
                    rate = 0.9 * (wm.self.stamina -  agent.server_params.recover_dec_thr) /  agent.server_params.stamina_max
                    rate = max(0.0, rate)
                return (agent.player_types[wm.self.id].stamina_inc_max * wm.self.recovery * rate)
        return wm.self.get_safety_dash_power

    def can_go_to(self, agent: IAgent, count, wm, ball_circle: Circle2D, target_point:Vector2D) -> bool:
        wm = agent.wm
        self_position = Vector2D(wm.self.position.x, wm.self.position.y)
        
        move_line = Segment2D(self_position, target_point)
        n_intersection = ball_circle.intersection(move_line)

        num = str(count)

        if n_intersection == 0:
            return True
        
        if n_intersection == 1:
            angle = Vector2D(target_point - self_position).th()
            if abs(angle - wm.ball.angle_from_self) > 80.0:
                return True
        return False

    def get_avoid_circle_point(self, wm, target_point,agent:IAgent):
        SP = agent.server_params
        wm = agent.wm
        avoid_radius = SP.center_circle_r + agent.player_types[wm.self.id].player_size
        ball_position = Vector2D(wm.ball.position.x, wm.ball.position.y)
        ball_circle = Circle2D(ball_position, avoid_radius)
        if self.can_go_to(agent,-1, wm, ball_circle, target_point):
            return target_point
        self_position = Vector2D(wm.self.position.x, wm.self.position.y)
        target_angle = Vector2D(target_point - self_position).th()
        ball_target_angle = Vector2D(target_point - ball_position).th()
        ball_ang = AngleDeg(wm.ball.angle_from_self)
        ball_is_left = ball_ang.is_left_of(target_angle)
        ANGLE_DIVS = 6
        subtargets = []
        angle_step = 1 if ball_is_left else -1
        count = 0
        a = angle_step
        for i in range(1, ANGLE_DIVS):
            angle = ball_target_angle + (180.0 / ANGLE_DIVS) * a
            new_target = Vector2D(ball_position + Vector2D.from_polar(avoid_radius + 1.0, angle))

            if abs(new_target.x()) > SP.pitch_half_length + SP.pitch_margin - 1.0 or abs(new_target.y()) > SP.pitch_half_width + SP.pitch_margin - 1.0: #TODO pith_margin
                break
            if self.can_go_to(agent, count, wm, ball_circle, new_target):
                return new_target
            a += angle_step
            count += 1
        a = -angle_step
        for i in range(1, ANGLE_DIVS * 2):
            angle = ball_target_angle + (180.0 / ANGLE_DIVS) * a
            new_target = Vector2D(ball_position + Vector2D.from_polar(avoid_radius + 1.0, angle))

            if abs(new_target.x()) > SP.pitch_half_length + SP.pitch_margin - 1.0 or abs(new_target.y()) > SP.pitch_half_width + SP.pitch_margin - 1.0:
                break
            if self.can_go_to(agent, count, wm, ball_circle, new_target):
                return new_target
            a -= angle_step
            count += 1
        return target_point

    def is_kicker(self, agent: "SamplePlayerAgent"):
        wm = agent.wm
        min_dist = 10000.0
        unum = 0
        ball_position = Vector2D(wm.ball.position.x, wm.ball.position.y)
        for i in range(1, 12):
            if i == wm.our_goalie_uniform_number and wm.game_mode_type == GameModeType.GoalieCatch_:
                h_p:RpcVector2D = wm.teammates[wm.our_goalie_uniform_number - 1].position
            elif i == wm.our_goalie_uniform_number:
                continue
            else:
                h_p:RpcVector2D = Tools.convert_vector2d_to_rpc_vector2d(agent.strategy.get_position(i, agent))
            home_pos = Vector2D(h_p.x, h_p.y)
            if(home_pos.dist(ball_position) < min_dist):
                min_dist = home_pos.dist(ball_position)
                unum = i
        if wm.self.uniform_number == unum:
            return True
        return False   
        '''teammates_from_ball = Tools.TeammatesFromBall(agent)
        wm = agent.wm
        ball_position = Vector2D(wm.ball.position.x, wm.ball.position.y)
        if wm.game_mode_type == GameModeType.GoalieCatch_ and wm.game_mode_side == wm.our_side and not wm.self.is_goalie:
            return False
        kicker_unum = 0
        min_dist2 = 100000.0
        second_kicker_unum = 0
        second_min_dist2 = 100000.0
        for unum in range(1, 12):
            if unum == wm.our_goalie_uniform_number:
                continue
            h_p:RpcVector2D = Strategy.get_home_pos(agent, unum)
            home_pos = Vector2D(h_p.x, h_p.y)
            if not home_pos.is_valid():
                continue
            d2 = home_pos.dist2(ball_position)
            if d2 < second_min_dist2:
                second_kicker_unum = unum
                second_min_dist2 = d2
                if second_min_dist2 < min_dist2:
                    second_kicker_unum, kicker_unum = kicker_unum, second_kicker_unum
                    second_min_dist2, min_dist2 = min_dist2, second_min_dist2

        kicker = None
        second_kicker = None
        if kicker_unum != 0:
            print ('unum', kicker_unum)
            kicker = wm.teammates[kicker_unum]
        if second_kicker_unum != 0:
            second_kicker = wm.teammates[second_kicker_unum]
        if not kicker:
            if teammates_from_ball and teammates_from_ball[0].dist_from_ball < wm.ball.dist_from_self * 0.9:
                return False

            return True
        print('kicker unum: ', kicker.uniform_number)
        print('second is_kicker', second_kicker.uniform_number)
        if kicker and second_kicker and (kicker.uniform_number == wm.self.uniform_number or second_kicker.uniform_number == wm.self.uniform_number):
            if math.sqrt(min_dist2) < math.sqrt(second_min_dist2) * 0.95:
                return kicker.uniform_number == wm.self.uniform_number
            elif kicker.dist_from_ball < second_kicker.dist_from_ball * 0.95:
                return kicker.uniform_number == wm.self.uniform_number
            elif second_kicker.dist_from_ball < kicker.dist_from_ball * 0.95:
                return second_kicker.uniform_number == wm.self.uniform_number
            
            elif teammates_from_ball and teammates_from_ball[0].dist_from_ball < wm.self.dist_from_ball * 0.95:
                return False
            else:
                return True
        return kicker.uniform_number == wm.self.uniform_number'''

    def is_delaying_tactics_situation(self, agent: IAgent):
        wm = agent.wm
        real_set_play_count = wm.cycle - wm.last_set_play_start_time
        wait_buf = 15 if wm.game_mode_type == GameModeType.GoalKick_ else 2
        if real_set_play_count >= agent.server_params.drop_ball_time - wait_buf:
            return False
        our_score = wm.left_team_score if wm.our_side == Side.LEFT else wm.right_team_score
        opp_score = wm.right_team_score if wm.our_side == Side.LEFT else wm.left_team_score
        '''if wm.audioMemory().recoveryTime().cycle >= wm.cycle - 10:
            if our_score > opp_score:
                return True''' #TODO audio memory
        cycle_thr = max(0, agent.server_params.nr_normal_halfs * (agent.server_params.half_time * 10) - 500)
        if wm.cycle < cycle_thr:
            return False
        if our_score > opp_score and our_score - opp_score <= 1:
            return True
        return False

    def doBasicTheirSetPlayMove(self, agent: "SamplePlayerAgent"):
        wm = agent.wm
        target_point = agent.strategy.get_position(wm.self.uniform_number, agent)
        ball_position = Vector2D(wm.ball.position.x, wm.ball.position.y)
        dash_power = self.get_set_play_dash_power(agent)
        ball_to_target = Vector2D(target_point - ball_position)
        if ball_to_target.r() < 11.0:
            xdiff = math.sqrt(math.pow(11.0, 2) - math.pow(ball_to_target.y(), 2))
            target_point.set_x(wm.ball.position.x - xdiff)
            if target_point.x() < -45.0:
                target_point = ball_position
                target_point += ball_to_target.set_length_vector(11.0)
                
        if wm.game_mode_type == GameModeType.KickOff_ and agent.server_params.kickoff_offside:
            target_point.set_x(min(-1.0e-5, target_point.x()))

        adjusted_point = self.get_avoid_circle_point(wm, target_point,agent)
        dist_thr = wm.ball.dist_from_self * 0.1
        if dist_thr < 0.7:
            dist_thr = 0.7
        self_velocity = Vector2D(wm.self.velocity.x, wm.self.velocity.y)
        self_position = Vector2D(wm.self.position.x, wm.self.position.y)
        if adjusted_point != target_point and ball_position.dist(target_point) > 10.0 and Tools.inertia_final_point(agent.player_types[wm.self.id], self_position, self_velocity).dist(adjusted_point) < dist_thr:
            adjusted_point = target_point
        agent.add_action(PlayerAction(body_go_to_point=Body_GoToPoint(target_point=Tools.convert_vector2d_to_rpc_vector2d(adjusted_point), distance_threshold=dist_thr, max_dash_power=dash_power)))
        body_angle = wm.ball.angle_from_self
        if body_angle < 0.0:
            body_angle -= 90.0
        else:
            body_angle += 90.0
            agent.add_action(PlayerAction(body_turn_to_angle=Body_TurnToAngle(angle=body_angle)))
        return True