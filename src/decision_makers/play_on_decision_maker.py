from src.interfaces.IDecisionMaker import IDecisionMaker
from src.interfaces.IAgent import IAgent
from src.decision_makers.kick_decision_maker import KickDecisionMaker
from src.decision_makers.move_decision_maker import MoveDecisionMaker


class PlayOnDecisionMaker(IDecisionMaker):
    def __init__(self):
        self.with_ball_decision_maker = KickDecisionMaker()
        self.no_ball_decision_maker = MoveDecisionMaker()
        pass
    
    def make_decision(self, agent: IAgent):
        if agent.wm.self.is_kickable:
            self.with_ball_decision_maker.make_decision(agent)
        else:
            self.no_ball_decision_maker.make_decision(agent)