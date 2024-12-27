from abc import ABC
from src.decision_makers.decision_maker import DecisionMaker
from src.interfaces.IAgent import IAgent
from src.strategy.formation_strategy import FormationStrategy
from src.strategy.starter_strategy import StarterStrategy
from service_pb2 import *


class SamplePlayerAgent(IAgent, ABC):
    """
    A sample player agent implementation that handles decision making and strategy execution.
    Inherits from IAgent and implements required abstract methods.
    """
    def __init__(self, logger) -> None:
        """
        Initialize the player agent with required components.
        
        Args:
            logger: Logger instance for debug/info messages
        """
        super().__init__(logger)
        self.logger.info('SamplePlayerAgent created')
        
        # Flag to switch between starter mode and major mode
        self.use_starter_code = False
        
        # Initialize core components
        self.decision_maker = DecisionMaker(self)
        self.strategy = self._initialize_strategy()
        self.wm: WorldModel = None
    
    def _initialize_strategy(self):
        """
        Initialize the strategy based on the use_starter_code flag.
        
        Returns:
            Strategy: Initialized strategy instance
        """
        if self.use_starter_code:
            return StarterStrategy(self.logger)
        return FormationStrategy(self.logger)
    
    def update_actions(self, wm: WorldModel):
        """
        Update agent actions based on the current world model state.
        
        Args:
            wm (WorldModel): Current world model containing game state
        """
        self.logger.debug(f'update_actions: {wm.cycle}')
        self.wm = wm
        self.actions.clear()
        self.strategy.update(self)
        self.decision_maker.make_decision(self)
        self.logger.debug(f'actions: {self.actions}')
    
    def get_strategy(self):
        """
        Get the current strategy instance being used by the agent.
        
        Returns:
            Strategy: Current strategy instance (FormationStrategy or StarterStrategy)
        """
        return self.strategy
    
    def get_actions(self) -> PlayerActions:
        """
        Get the list of player actions to be executed
        """
        
        res = PlayerActions()
        res.actions.extend(self.actions)
        
        if self.use_starter_code:
            res.ignore_doHeardPassRecieve = True
            res.ignore_doIntention = True
            res.ignore_shootInPreprocess = True
        else:
            pass
            # res.ignore_shootInPreprocess = True
        return res