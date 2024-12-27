from typing import TYPE_CHECKING
from typing import Union
from abc import ABC, abstractmethod
from typing import Union
from service_pb2 import *
import logging
from src.utils.memory import Memory


if TYPE_CHECKING:
    from src.utils.tools import Tools

class IAgent(ABC):
    def __init__(self, logger) -> None:
        super().__init__()
        self.wm: Union[WorldModel, None] = None
        self.actions: list[Union[PlayerAction, CoachAction, TrainerAction]] = []
        self.server_params: Union[ServerParam, None] = None
        self.player_params: Union[PlayerParam, None] = None
        self.player_types: dict[PlayerType] = {}
        self.debug_mode: bool = False
        self.memory: Memory = Memory()
        self.logger: logging.Logger = logger

    def set_server_params(self, server_param: ServerParam):
        self.server_params = server_param
    
    def set_player_params(self, player_param: PlayerParam):
        self.player_params = player_param
        
    def set_player_types(self, player_type: PlayerType):
        self.player_types[player_type.id] = player_type
        from src.utils.tools import Tools
        Tools.update_dash_distance_table(player_type, self)
        
    def get_player_type(self, id: int) -> PlayerType:
        if id < 0:
            id = 0
        return self.player_types[id]

    @abstractmethod
    def update_actions(self, wm: WorldModel):
        pass

    # @abstractmethod
    # def get_strategy(self) -> IPositionStrategy:
    #     pass

    def set_debug_mode(self, debug_mode: bool):
        self.debug_mode = debug_mode

    def add_log_text(self, level: LoggerLevel, message: str):
        if not self.debug_mode:
            return
        self.add_action(PlayerAction(
            log=Log(
                add_text=AddText(
                    level=level,
                    message=message
                )
            )
        ))

    def add_log_message(self, level: LoggerLevel, message: str, x, y, color):
        if not self.debug_mode:
            return
        self.add_action(PlayerAction(
            log=Log(
                add_message=AddMessage(
                    level=level,
                    message=message,
                    position=RpcVector2D(x=x, y=y),
                    color=color,
                )
            )
        ))

    def add_log_circle(self, level: LoggerLevel, center_x: float, center_y: float, radius: float, color: str,
                       fill: bool):
        if not self.debug_mode:
            return
        self.add_action(PlayerAction(
            log=Log(
                add_circle=AddCircle(
                    level=level,
                    center=RpcVector2D(x=center_x, y=center_y),
                    radius=radius,
                    color=color,
                    fill=fill
                )
            )
        ))
        
    def add_log_line(self, level: LoggerLevel, start_x: float, start_y: float, end_x: float, end_y: float, color: str):
        if not self.debug_mode:
            return
        self.add_action(PlayerAction(
            log=Log(
                add_line=AddLine(
                    level=level,
                    start=RpcVector2D(x=start_x, y=start_y),
                    end=RpcVector2D(x=end_x, y=end_y),
                    color=color,
                )
            )
        )
        )

    def add_action(self, action: Union[PlayerAction, CoachAction, TrainerAction]):
        self.actions.append(action)
    
    @abstractmethod
    def get_actions(self) -> Union[PlayerActions, CoachActions, TrainerActions]:
        pass