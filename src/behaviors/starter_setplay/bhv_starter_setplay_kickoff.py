from src.interfaces.IAgent import IAgent
#from src.setplay.BhvGoToPlacedBall import BhvGoToPlacedBall
#from src.setplay.BhvSetPlay import BhvSetPlay
from service_pb2 import *
from pyrusgeom.vector_2d import Vector2D
from src.utils.tools import Tools
#from src.setplay.BhvGoToPlacedBall import BhvGoToPlacedBall
from src.strategy.starter_strategy import StarterStrategy
from src.utils.convertor import Convertor

class BhvStarterSetPlayKickOff:
    def __init__(self):
        pass
    
    def execute(agent: IAgent):
        wm = agent.wm
        teammates = Tools.TeammatesFromBall(agent)

        if not teammates or teammates[0].dist_from_self > wm.self.dist_from_ball:
            return BhvStarterSetPlayKickOff.do_kick(agent)
        else:
            return BhvStarterSetPlayKickOff.do_move(agent)

        return []

    def do_kick(agent: IAgent):
        # Go to the ball position
        actions = []
        from src.behaviors.starter_setplay.bhv_starter_go_to_placed_ball import BhvStarterGoToPlacedBall
        actions += BhvStarterGoToPlacedBall(0.0).execute(agent)
        
        # Wait
        actions += BhvStarterSetPlayKickOff.do_kick_wait(agent)
            
        
        # Kick
        wm = agent.wm
        max_ball_speed = agent.server_params.max_power * wm.self.kick_rate

        target_point = Vector2D()
        ball_speed = max_ball_speed

        # Teammate not found
        if not Tools.TeammatesFromSelf(agent):
            target_point.assign(agent.server_params.pitch_half_length, (-1 + 2 * (wm.cycle % 2)) * 0.8 * agent.server_params.goal_width / 2)
        else:
            teammate = Tools.TeammatesFromSelf(agent)[0]
            dist = teammate.dist_from_self

            if dist > 35.0:
                # Too far
                target_point.assign(agent.server_params.pitch_half_length, (-1 + 2 * (wm.cycle % 2)) * 0.8 * agent.server_params.goal_width)
            else:
                target_point = Vector2D(teammate.inertia_final_point.x, teammate.inertia_final_point.y)
                #target_point = teammate.inertia_final_point
                ball_speed = min(max_ball_speed,
                                 Tools.calc_first_term_geom_series_last(1.8, dist, agent.server_params.ball_decay))

        ball_position = Vector2D(wm.ball.position.x, wm.ball.position.y)
        ball_vel = Vector2D.polar2vector(ball_speed, Vector2D(target_point - ball_position).th())
        ball_next = ball_position + ball_vel
        self_position = Vector2D(wm.self.position.x, wm.self.position.y)
        while self_position.dist(ball_next) < agent.player_types[agent.wm.self.id].kickable_area + 0.2:
            ball_vel.set_length(ball_speed + 0.1)
            ball_speed += 0.1
            ball_next = ball_position + ball_vel

        ball_speed = min(ball_speed, max_ball_speed)


        # Enforce one step kick
        actions.append(PlayerAction(body_smart_kick=Body_SmartKick(target_point=Convertor.convert_vector2d_to_rpc_vector2d(target_point), first_speed=ball_speed, first_speed_threshold=ball_speed * 0.96, max_steps=1)))
        return actions
        
    def do_kick_wait(agent: IAgent) -> bool:
        actions = []
        wm = agent.wm
        real_set_play_count = int(wm.cycle - wm.last_set_play_start_time)

        if real_set_play_count >= agent.server_params.drop_ball_time - 5:
            return []
        from src.behaviors.starter_setplay.bhv_starter_setplay import BhvStarterSetPlay
        if BhvStarterSetPlay.is_delaying_tactics_situation(agent):
            actions.append(PlayerAction(body_turn_to_angle=Body_TurnToAngle(angle=180)))
            return actions
            
        if abs(wm.self.body_direction) < 175.0:
            actions.append(PlayerAction(body_turn_to_angle=Body_TurnToAngle(angle=180)))
            return actions

        if not Tools.TeammatesFromBall(agent):
            actions.append(PlayerAction(body_turn_to_angle=Body_TurnToAngle(angle=180)))
            return actions

        if len(Tools.TeammatesFromSelf(agent)) < 9:
            actions.append(PlayerAction(body_turn_to_angle=Body_TurnToAngle(angle=180)))
            return actions

        if wm.see_time != wm.cycle or wm.self.stamina < agent.server_params.stamina_max * 0.9:
            actions.append(PlayerAction(body_turn_to_angle=Body_TurnToAngle(angle=180)))
            return actions
        return actions

    def do_move(agent: IAgent):
        wm = agent.wm
        actions = []
        target = StarterStrategy.get_position(agent, wm.self.uniform_number)
        target_point = Vector2D(target.x, target.y)
        target_point.set_x(min(-0.5, target_point.x()))
        from src.behaviors.starter_setplay.bhv_starter_setplay import BhvStarterSetPlay
        dash_power = BhvStarterSetPlay.get_set_play_dash_power(agent)
        dist_thr = wm.ball.dist_from_self * 0.07
        if dist_thr < 1.0:
            dist_thr = 1.0
        actions.append(PlayerAction(body_go_to_point=Body_GoToPoint(target_point=Convertor.convert_vector2d_to_rpc_vector2d(target_point), distance_threshold=dist_thr, max_dash_power=dash_power)))
        actions.append(PlayerAction(body_turn_to_ball=Body_TurnToBall(cycle=1)))
        
        return actions
