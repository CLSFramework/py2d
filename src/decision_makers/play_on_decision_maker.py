from src.interfaces.IDecisionMaker import IDecisionMaker
from src.interfaces.IAgent import IAgent
from src.decision_makers.kick_decision_maker import KickDecisionMaker
from src.decision_makers.move_decision_maker import MoveDecisionMaker


class PlayOnDecisionMaker(IDecisionMaker):
    """
    A decision maker that delegates decisions to either a KickDecisionMaker or a MoveDecisionMaker
    based on whether the agent is in a position to kick the ball.
    Attributes:
        kick_decision_maker (KickDecisionMaker): The decision maker used when the agent can kick the ball.
        move_decision_maker (MoveDecisionMaker): The decision maker used when the agent cannot kick the ball.
    Methods:
        make_decision(agent: IAgent):
            Makes a decision based on the agent's ability to kick the ball.
            Delegates the decision to either kick_decision_maker or move_decision_maker.
    """
    def __init__(self):
        self.kick_decision_maker = KickDecisionMaker()
        self.move_decision_maker = MoveDecisionMaker()
        pass
    
    def make_decision(self, agent: IAgent):
        if agent.wm.self.is_kickable:
            self.kick_decision_maker.make_decision(agent)
        else:
            self.move_decision_maker.make_decision(agent)