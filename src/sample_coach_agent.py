from abc import ABC
from src.interfaces.IAgent import IAgent
from service_pb2 import *


class SampleCoachAgent(IAgent, ABC):
    def __init__(self):
        super().__init__()
        self.wm: WorldModel = None
        self.first_substitution = True
    
    def update_actions(self, wm:WorldModel) -> CoachActions:
        self.logger.debug(f'update_actions: {wm.cycle}')
        self.wm = wm
        
        actions = CoachActions()
        actions.actions = []
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
        self.add_action(CoachAction(
            do_helios_substitute=DoHeliosSubstitute()
        ))
        
        self.logger.debug(f'actions: {self.actions}')