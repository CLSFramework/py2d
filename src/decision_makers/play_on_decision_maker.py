from src.interfaces.IDecisionMaker import IDecisionMaker
from src.interfaces.IAgent import IAgent
from .kick_decision_maker import WithBallDecisionMaker
from .move_decision_maker import NoBallDecisionMaker


class PlayOnDecisionMaker(IDecisionMaker):
    def __init__(self):
        self.with_ball_decision_maker = WithBallDecisionMaker()
        self.no_ball_decision_maker = NoBallDecisionMaker()
        pass
    
    def make_decision(self, agent: IAgent):
        if agent.wm.self.is_kickable:
            self.with_ball_decision_maker.make_decision(agent)
        else:
            self.no_ball_decision_maker.make_decision(agent)