from abc import ABC
from src.interfaces.IAgent import IAgent
from service_pb2 import *


class SampleCoachAgent(IAgent, ABC):
    """
    A sample coach agent implementation that handles team substitutions and tactics.
    Inherits from IAgent and implements required abstract methods.
    """
    def __init__(self, logger) -> None:
        """
        Initialize the coach agent.
        
        Args:
            logger: Logger instance for debug/info messages
        """
        super().__init__(logger)
        self.logger.info('SampleCoachAgent created')
        self.wm: WorldModel = None
        self.first_substitution = True
    
    def update_actions(self, wm:WorldModel) -> CoachActions:
        """
        Update coach actions based on the current world model state.
        Currently implements basic Helios substitution strategy.
        
        Args:
            wm (WorldModel): Current world model containing game state
            
        Returns:
            CoachActions: List of coach actions to be executed
        """
        self.logger.debug(f'update_actions: {wm.cycle}')
        self.wm = wm
        
        self.actions.clear()
        self.add_action(CoachAction(
            do_helios_substitute=DoHeliosSubstitute()
        ))
        # actions = CoachActions()
        # actions.actions = []
        # if (wm.cycle == 0
        #     and self.first_substitution
        #     and self.playerParams is not None
        #     and len(self.playerTypes.keys()) == self.playerParams.player_types):
            
        #     self.first_substitution = False
        #     for i in range(11):
        #         actions.actions.append(
        #             CoachAction(
        #                 change_player_types=ChangePlayerType(
        #                 uniform_number=i+1,
        #                 type=i
        #                 )
        #             )
        #         )

        # actions.append(
        #     CoachAction(
        #         do_helios_substitute=DoHeliosSubstitute()
        #     )
        # )
        # self.add_action(CoachAction(
        #     do_helios_substitute=DoHeliosSubstitute()
        # ))
        
        self.logger.debug(f'actions: {self.actions}')
        
    def get_actions(self) -> CoachActions:
        """
        Get the list of coach actions to be executed
        """
        
        return CoachActions(actions=self.actions)