from typing import TYPE_CHECKING
import math
from src.interfaces.IAgent import IAgent
from service_pb2 import *
from pyrusgeom.vector_2d import Vector2D
#from src.setplay.BhvGoToPlacedBall import BhvGoToPlacedBall
from src.behaviors.bhv_starter_pass import BhvStarterPass
from src.utils.tools import Tools
import math
from pyrusgeom.soccer_math import *
#from src.setplay.BhvSetPlay import BhvSetPlay
from src.strategy.starter_strategy import StarterStrategy
from src.utils.convertor import Convertor

if TYPE_CHECKING:
    from src.sample_player_agent import SamplePlayerAgent
class BhvStarterSetPlayKickIn:

    def __init__(self):
        pass
    def execute(self, agent: IAgent) -> bool:
        from src.behaviors.starter_setplay.bhv_starter_setplay import BhvStarterSetPlay
        setplay = BhvStarterSetPlay()

        if setplay.is_kicker(agent):
            return self.do_kick(agent)
        else:
            return self.do_move(agent)

        return []

    def do_kick(self, agent: IAgent):
        from src.behaviors.starter_setplay.bhv_starter_go_to_placed_ball import BhvStarterGoToPlacedBall
        wm = agent.wm
        actions = []
        # Go to the kick position
        ball_place_angle = -90.0 if wm.ball.position.y > 0.0 else 90.0
        go_to_placed_ball = BhvStarterGoToPlacedBall(ball_place_angle)
        actions += go_to_placed_ball.execute(agent)

        # Wait
        wait = self.do_kick_wait(agent)
        if wait != []:
            actions += wait
            return actions

        # Kick
        max_ball_speed = wm.self.kick_rate * agent.server_params.max_power

        # Pass
        passer = BhvStarterPass()
        actions.append(passer.execute(agent))

        # Kick to the nearest teammate
        ball_position = Vector2D(wm.ball.position.x, wm.ball.position.y)
        receiver: Player = Tools.GetTeammateNearestTo(agent, ball_position)
        if receiver and receiver.dist_from_ball < 10.0 and abs(receiver.position.x) < agent.server_params.pitch_half_length and abs(receiver.position.y) < agent.server_params.pitch_half_width:

            target_point = Vector2D(receiver.inertia_final_point.x, receiver.inertia_final_point.y)
            target_point.set_x(target_point.x() + 0.5)
            ball_move_dist = ball_position.dist(target_point)
            ball_reach_step = math.ceil(calc_length_geom_series(max_ball_speed, ball_move_dist, agent.server_params.ball_decay))
            ball_speed = 0.0

            if ball_reach_step > 3:
                ball_speed = calc_first_term_geom_series(ball_move_dist, agent.server_params.ball_decay, ball_reach_step)
            else:
                ball_speed = Tools.calc_first_term_geom_series_last(1.4, ball_move_dist, agent.server_params.ball_decay)
                ball_reach_step = math.ceil(calc_length_geom_series(ball_speed, ball_move_dist, agent.server_params.ball_decay))

            ball_speed = min(ball_speed, max_ball_speed)
            actions.append(PlayerAction(body_kick_one_step=Body_KickOneStep(target_point=Convertor.convert_vector2d_to_rpc_vector2d(target_point), first_speed=ball_speed, force_mode=False)))
            return actions

        # Clear
        # Turn to ball
        if abs(wm.ball.angle_from_self - wm.self.body_direction) > 1.5:
            actions.append(PlayerAction(body_turn_to_ball=Body_TurnToBall(cycle=1)))
            return actions

        # Advance ball
        if wm.self.position.x < 20.0:
            actions.append(PlayerAction(body_advance_ball=Body_AdvanceBall()))
            return actions

        # Kick to the opponent side corner

        target_point = Vector2D(agent.server_params.pitch_half_length - 2.0,
                                (agent.server_params.pitch_half_width - 5.0) * (1.0 - (wm.self.position.x / agent.server_params.pitch_half_length)))

        if wm.self.position.y < 0.0:
            target_point.set_y(target_point.y() * -1.0)
        
        # Enforce one step kick
        actions.append(PlayerAction(body_kick_one_step=Body_KickOneStep(target_point=Convertor.convert_vector2d_to_rpc_vector2d(target_point), first_speed=agent.server_params.ball_speed_max, force_mode=False)))

        return actions
    

    def do_kick_wait(self, agent: IAgent):
        from src.behaviors.starter_setplay.bhv_starter_setplay import BhvStarterSetPlay
        setplay = BhvStarterSetPlay()
        wm = agent.wm

        real_set_play_count = wm.cycle - wm.last_set_play_start_time
        actions = []
        if real_set_play_count >= agent.server_params.drop_ball_time - 5:
            return []
        if setplay.is_delaying_tactics_situation(agent):
            actions.append(PlayerAction(body_turn_to_point=Body_TurnToPoint(target_point=RpcVector2D(x=0, y=0), cycle=2)))
            return actions

        if not Tools.TeammatesFromBall(agent):
            actions.append(PlayerAction(body_turn_to_point=Body_TurnToPoint(target_point=RpcVector2D(x=0, y=0), cycle=2)))
            return actions

        if wm.set_play_count <= 3:
            actions.append(PlayerAction(body_turn_to_ball=Body_TurnToBall(cycle=1)))
            return actions

        if wm.set_play_count >= 15 and wm.see_time == wm.cycle and wm.self.stamina > agent.server_params.stamina_max * 0.6:
            return []

        if wm.see_time != wm.cycle or wm.self.stamina < agent.server_params.stamina_max * 0.9:
            actions.append(PlayerAction(body_turn_to_ball=Body_TurnToBall(cycle=1)))
            return actions

        return actions

    def do_move(self, agent: "SamplePlayerAgent"):
        from src.behaviors.starter_setplay.bhv_starter_setplay import BhvStarterSetPlay
        setplay = BhvStarterSetPlay()
        wm = agent.wm
        actions = []
        ball_position = Vector2D(wm.ball.position.x, wm.ball.position.y)
        target = Convertor.convert_vector2d_to_rpc_vector2d(agent.strategy.get_position(wm.self.uniform_number, agent))
        target_point = Vector2D(target.x, target.y)
        avoid_opponent = False
        
        if wm.self.stamina > agent.server_params.stamina_max * 0.9:
            nearest_opp = Tools.GetOpponentNearestToSelf(agent)
            nearest_opp_pos = Vector2D(nearest_opp.position.x, nearest_opp.position.y)
            
            if nearest_opp and nearest_opp_pos.dist(target_point) < 3.0:
                add_vec = ball_position - target_point
                add_vec.set_length(3.0)

                time_val = wm.cycle % 60
                if time_val < 20:
                    pass
                elif time_val < 40:
                    target_point += add_vec.rotated_vector(90.0)
                else:
                    target_point += add_vec.rotated_vector(-90.0)

                target_point.set_x(min(max(-agent.server_params.pitch_half_length, target_point.x()), agent.server_params.pitch_half_length))
                target_point.set_y (min(max(-agent.server_params.pitch_half_width, target_point.y()), agent.server_params.pitch_half_width))
                avoid_opponent = True
        dash_power = setplay.get_set_play_dash_power(agent)
        dist_thr = wm.ball.dist_from_self * 0.07
        dist_thr = max(dist_thr, 1.0)
        tm = Tools.TeammatesFromBall(agent)
        if tm:
            kicker_ball_dist = tm[0].dist_from_ball
        else:
            1000
        
        actions.append(PlayerAction(body_go_to_point=Body_GoToPoint(target_point=Convertor.convert_vector2d_to_rpc_vector2d(target_point), distance_threshold=dist_thr, max_dash_power=dash_power)))
            # Already there
        if kicker_ball_dist > 1.0:
            actions.append(PlayerAction(turn=Turn(relative_direction=120)))
        else:
            actions.append(PlayerAction(body_turn_to_ball=Body_TurnToBall(cycle=1)))
        self_position = Vector2D(wm.self.position.x, wm.self.position.y)
        self_velocity = Vector2D(wm.self.velocity.x, wm.self.velocity.y)
        my_inertia = Tools.inertia_final_point(agent.player_types[wm.self.id], self_position, self_velocity)
        wait_dist_buf = (10.0 if avoid_opponent else ball_position.dist(target_point) * 0.2 + 6.0)

        if my_inertia.dist(target_point) > wait_dist_buf or wm.self.stamina < agent.server_params.stamina_max * 0.7:
            if not wm.self.stamina_capacity == 0:
                #TODO actions.append(Say(wait_request_message=WaitRequestMessage()))
                pass

        ''''if kicker_ball_dist > 3.0:
            agent.setViewAction(ViewWide())
            agent.setNeckAction(NeckScanField())
        elif wm.ball().distFromSelf() > 10.0 or kicker_ball_dist > 1.0:
            agent.setNeckAction(NeckTurnToBallOrScan(0))
        else:
            agent.setNeckAction(NeckTurnToBall())''' #TODO
            
        return actions
