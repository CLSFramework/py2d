from typing import TYPE_CHECKING
from src.interfaces.IDecisionMaker import IDecisionMaker
from .play_on_decision_maker import PlayOnDecisionMaker
from .set_play_decision_maker import SetPlayDecisionMaker
from .penalty_decision_maker import PenaltyDecisionMaker
from .goalie_decision_maker import GoalieDecisionMaker
from service_pb2 import *

if TYPE_CHECKING:
    from src.sample_player_agent import SamplePlayerAgent
    
class DecisionMaker(IDecisionMaker):
    """
    DecisionMaker is responsible for making decisions for an agent based on the current game state.
    Attributes:
        play_on_decision_maker (PlayOnDecisionMaker): Handles decisions during the 'PlayOn' game mode.
        set_play_decision_maker (SetPlayDecisionMaker): Handles decisions during set plays.
        penalty_decision_maker (PenaltyDecisionMaker): Handles decisions during penalty kicks.
        goalie_decision_maker (GoalieDecisionMaker): Handles decisions for goalies.
    Methods:
        __init__():
            Initializes the DecisionMaker with specific decision makers for different game modes.
        make_decision(agent: IAgent):
            Makes a decision for the given agent based on its role and the current game mode.
            If the agent is a goalie, it adds a goalie action using goalie_decision_maker.
            If the game mode is 'PlayOn', it delegates the decision to play_on_decision_maker.
            If the game mode is a penalty kick, it adds a penalty action using penalty_decision_maker.
            Otherwise, it adds a set play action using set_play_decision_maker.
    """
    def __init__(self, agent: "SamplePlayerAgent"):
        self.play_on_decision_maker = PlayOnDecisionMaker(agent)
        self.set_play_decision_maker = SetPlayDecisionMaker(agent)
        self.penalty_decision_maker = PenaltyDecisionMaker(agent)
        self.goalie_decision_maker = GoalieDecisionMaker(agent)
    
    def make_decision(self, agent: "SamplePlayerAgent"):
        if agent.wm.self.is_goalie:
            self.goalie_decision_maker.make_decision(agent)
        elif agent.wm.game_mode_type == GameModeType.PlayOn:
            self.play_on_decision_maker.make_decision(agent)
        elif agent.wm.is_penalty_kick_mode:
            self.penalty_decision_maker.make_decision(agent)
        else:
            self.set_play_decision_maker.make_decision(agent)