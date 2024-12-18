from typing import TYPE_CHECKING
from src.interfaces.IBehavior import IBehavior
from pyrusgeom.soccer_math import *
from pyrusgeom.geom_2d import *
from src.utils.tools import Tools
from service_pb2 import *


if TYPE_CHECKING:
    from src.sample_player_agent import SamplePlayerAgent

class BhvStarterPass(IBehavior):
    def __init__(self):
        pass

    def execute(self, agent: "SamplePlayerAgent") -> bool:
        wm = agent.wm
        targets: list[Vector2D] = []
        ball_pos = Vector2D(wm.ball.position.x, wm.ball.position.y)
        self_pos = Vector2D(wm.self.position.x, wm.self.position.y)
        for teammate in wm.teammates:
            if teammate == None or teammate.uniform_number == wm.self.uniform_number or teammate.uniform_number < 0:
                continue
            tm_pos = Vector2D(teammate.position.x, teammate.position.y)
            if tm_pos.dist(ball_pos) > 30.0 :
                continue
            if self_pos.dist(tm_pos) < 2.0:
                continue
            check_root = Sector2D(ball_pos, 1.0, tm_pos.dist(ball_pos) + 3.0, (tm_pos - ball_pos).th().degree() - 15.0, (tm_pos - ball_pos).th().degree() + 15.0)
            if not Tools.exist_opponent_in(agent, check_root):
                targets.append(tm_pos)
                
        if len(targets) > 0:
            best_target: Vector2D = targets[0]
            for target in targets:
                if target.x() > best_target.x():
                    best_target = target
            if wm.game_mode_type == GameModeType.PlayOn:
                agent.add_action(PlayerAction(body_smart_kick=Body_SmartKick(target_point=Tools.convert_vector2d_to_rpc_vector2d(best_target), first_speed=2.5, first_speed_threshold=2.5, max_steps=3)))
            else :
                agent.add_action(PlayerAction(body_smart_kick=Body_SmartKick(target_point=Tools.convert_vector2d_to_rpc_vector2d(best_target), first_speed=2.7, first_speed_threshold=2.5, max_steps=1)))
            return True
        
        return False
                
