from abc import ABC
from src.interfaces.IAgent import IAgent
from service_pb2 import *


class SampleTrainerAgent(IAgent, ABC):
    """
    A sample trainer agent implementation that handles training scenarios and ball control.
    Inherits from IAgent and implements required abstract methods.
    """
    def __init__(self, logger) -> None:
        """
        Initialize the trainer agent.
        
        Args:
            logger: Logger instance for debug/info messages
        """
        super().__init__(logger)
        self.logger.info('SampleTrainerAgent created')
        self.wm: WorldModel = None
        self.first_substitution = True
    
    def update_actions(self, wm:WorldModel):
        """
        Update trainer actions based on the current world model state.
        Periodically moves ball to center position every 100 cycles.
        
        Args:
            wm (WorldModel): Current world model containing game state
        """
        self.logger.debug(f'update_actions: {wm.cycle}')
        self.wm = wm
        
        actions = TrainerActions()
        actions.actions = []
        
        if self.wm.cycle % 100 == 0:
            actions.actions.append(
                TrainerAction(
                    do_move_ball=DoMoveBall(
                        position=RpcVector2D(
                            x=0,
                            y=0
                        ),
                        velocity=RpcVector2D(
                            x=0,
                            y=0
                        ),
                    )
                )
            )
        self.logger.debug(f'actions: {self.actions}')
    
    def set_params(self, params):
        """
        Set various game parameters for the trainer.
        
        Args:
            params: Can be ServerParam, PlayerParam, or PlayerType
            
        Raises:
            Exception: If parameter type is unknown
        """
        if isinstance(params, ServerParam):
            self.serverParams = params
        elif isinstance(params, PlayerParam):
            self.playerParams = params
        elif isinstance(params, PlayerType):
            self.playerTypes[params.id] = params
        else:
            raise Exception("Unknown params type")
        
    def get_actions(self) -> TrainerActions:
        """
        Get the list of coach actions to be executed
        """
        
        return TrainerActions(actions=self.actions)