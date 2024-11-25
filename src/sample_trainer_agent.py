from abc import ABC
from src.interfaces.IAgent import IAgent
from service_pb2 import *


class SampleTrainerAgent(IAgent, ABC):
    def __init__(self, logger) -> None:
        super().__init__(logger)
        self.logger.info('SampleTrainerAgent created')
        self.wm: WorldModel = None
        self.first_substitution = True
    
    def update_actions(self, wm:WorldModel):
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
        if isinstance(params, ServerParam):
            self.serverParams = params
        elif isinstance(params, PlayerParam):
            self.playerParams = params
        elif isinstance(params, PlayerType):
            self.playerTypes[params.id] = params
        else:
            raise Exception("Unknown params type")