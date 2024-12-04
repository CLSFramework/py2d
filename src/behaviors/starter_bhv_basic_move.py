from src.interfaces.IAgent import IAgent
from service_pb2 import PlayerAction, Body_Intercept, Body_GoToPoint, Body_TurnToBall
from strategy.starter_strategy import Strategy
from src.behaviors.starter_bhv_basic_tackle import BhvBasicTackle

class BhvBasicMove():
    
    def __init__(self):
        pass
    
    def Decision(agent: IAgent):
        # Player action without ball
        
        wm = agent.wm
        actions = [] # actions will be queued here
        
        actions += [tackle] if (tackle := BhvBasicTackle(0.8, 80).Decision(agent)) is not None else []
        
        actions += [tackle] if (tackle := BhvBasicTackle(0.8, 80).Decision(agent)) is not None else []
        
        self_min = wm.intercept_table.self_reach_steps
        mate_min = wm.intercept_table.first_teammate_reach_steps
        opp_min = wm.intercept_table.first_opponent_reach_steps
        our_min = min(self_min, mate_min)
        
        if mate_min > 1 and (self_min <= 3 or (self_min <= mate_min and self_min < opp_min + 3)):
            actions.append(PlayerAction(body_intercept=Body_Intercept()))
            
        if our_min < opp_min:
            pass
            # Do offensive move like unmark or possitioning
        else:
            pass
            # Do defensive move like mark or block
        home_pos = Strategy.get_home_pos(agent, wm.self.uniform_number)
        
        dash_power = Strategy.get_normal_dash_power(agent)
        dist_thr = wm.ball.dist_from_self * 0.1
        dist_thr = max(dist_thr, 1.0)
        
        actions.append(PlayerAction(body_go_to_point=Body_GoToPoint(target_point=home_pos, distance_threshold=0, max_dash_power=dash_power)))
        actions.append(PlayerAction(body_turn_to_ball=Body_TurnToBall(cycle=1)))
        return actions