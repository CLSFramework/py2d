from typing import TYPE_CHECKING
from src.interfaces.IPositionStrategy import IPositionStrategy
from src.strategy.formation_file import *
from src.interfaces.IAgent import IAgent
from src.strategy.player_role import PlayerRole, RoleName, RoleType, RoleSide
from enum import Enum
from pyrusgeom.soccer_math import *
from service_pb2 import *
import logging
from src.strategy.formation import Formation

if TYPE_CHECKING:
    from src.sample_player_agent import SamplePlayerAgent

class Situation(Enum):
    """
    Enum class representing different game situations in a 2D soccer simulation.
    """
    OurSetPlay_Situation = 0
    OppSetPlay_Situation = 1
    Defense_Situation = 2
    Offense_Situation = 3
    PenaltyKick_Situation = 4

class FormationStrategy(IPositionStrategy):
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.formations: dict[str, Formation] = {}
        self._poses: dict[int, Vector2D] = {i: Vector2D(0, 0) for i in range(11)}
        self.current_situation = Situation.Offense_Situation
        self.selected_formation_name = '4-3-3-cyrus-base'
        
        self._read_formations()
        self.current_formation_file: FormationFile = self._get_current_formation().offense_formation

    def _read_formations(self):
        """
        Read and initialize formations from configuration files.
        """
        self.formations['4-3-3'] = Formation('src/formations/4-3-3', self.logger)
        self.formations['4-3-3-cyrus-base'] = Formation('src/formations/4-3-3-cyrus-base', self.logger)
        self.formations['4-3-3-helios-base'] = Formation('src/formations/4-3-3-helios-base', self.logger)
        
    def _get_current_formation(self) -> Formation:
        """
        Get the current formation based on the selected formation name.

        Returns:
            Formation: The current formation instance.
        """
        return self.formations[self.selected_formation_name]
    
    def _set_formation(self, wm: WorldModel):
        """
        Set the formation based on the world model state.

        Args:
            wm (WorldModel): The current world model.
        """
        self.selected_formation_name = '4-3-3-cyrus-base'  # Example: '4-3-3', '4-3-3-cyrus-base', '4-3-3-helios-base'
        
    def update(self, agent: 'SamplePlayerAgent'):
        """
        Update the strategy based on the agent's world model.

        Args:
            agent (SamplePlayerAgent): The agent instance.
        """
        logger = agent.logger
        logger.debug('---- update strategy ----')
        
        wm: WorldModel = agent.wm
        self._set_formation(wm)
        
        tm_min = wm.intercept_table.first_teammate_reach_steps
        opp_min = wm.intercept_table.first_opponent_reach_steps
        self_min = wm.intercept_table.self_reach_steps
        all_min = min(tm_min, opp_min, self_min)
        current_ball_pos = Vector2D(wm.ball.position.x, wm.ball.position.y)
        current_ball_vel = Vector2D(wm.ball.velocity.x, wm.ball.velocity.y)
        ball_pos = inertia_n_step_point(current_ball_pos, current_ball_vel, all_min, 0.96)  # todo: use server param ball decay

        self._determine_situation(wm, ball_pos, tm_min, opp_min, self_min)
        self._update_formation_file(ball_pos)
        self._adjust_positions(wm)
                
        logger.debug(f'{self._poses=}')
        
    def _determine_situation(self, wm: WorldModel, ball_pos: Vector2D, tm_min: int, opp_min: int, self_min: int):
        """
        Determine the current game situation based on the world model.

        Args:
            wm (WorldModel): The current world model.
            ball_pos (Vector2D): The current ball position.
            tm_min (int): First teammate reach steps.
            opp_min (int): First opponent reach steps.
            self_min (int): Self reach steps.
        """
        if wm.game_mode_type is GameModeType.PlayOn:
            thr = 0
            if ball_pos.x() > 0:
                thr += 1
            if wm.self.uniform_number > 6:
                thr += 1
            if min(tm_min, self_min) < opp_min + thr:
                self.current_situation = Situation.Offense_Situation
            else:
                self.current_situation = Situation.Defense_Situation
        elif wm.game_mode_type is GameModeType.PenaltyKick_:
            self.current_situation = Situation.PenaltyKick_Situation
        elif wm.game_mode_type is not GameModeType.PlayOn and wm.game_mode_side is wm.our_side:
            self.current_situation = Situation.OurSetPlay_Situation
        else:
            self.current_situation = Situation.OppSetPlay_Situation

    def _update_formation_file(self, ball_pos: Vector2D):
        """
        Update the current formation file based on the current situation.

        Args:
            ball_pos (Vector2D): The current ball position.
        """
        if self.current_situation is Situation.Offense_Situation:
            self.current_formation_file = self._get_current_formation().offense_formation
        elif self.current_situation is Situation.Defense_Situation:
            self.current_formation_file = self._get_current_formation().defense_formation
        elif self.current_situation is Situation.OurSetPlay_Situation:
            self.current_formation_file = self._get_current_formation().setplay_our_formation
        elif self.current_situation is Situation.OppSetPlay_Situation:
            self.current_formation_file = self._get_current_formation().setplay_opp_formation
        elif self.current_situation is Situation.PenaltyKick_Situation:
            self.current_formation_file = self._get_current_formation().before_kick_off_formation
        else:
            self.current_formation_file = self._get_current_formation().before_kick_off_formation

        self.current_formation_file.update(ball_pos)
        self._poses = self.current_formation_file.get_poses()

    def _adjust_positions(self, wm: WorldModel):
        """
        Adjust player positions based on the game mode and offside line.

        Args:
            wm (WorldModel): The current world model.
        """
        if wm.game_mode_type in [GameModeType.BeforeKickOff, GameModeType.AfterGoal_]:
            for pos in self._poses.values():
                pos._x = min(pos.x(), -0.5)
        else:
            offside_line = wm.offside_line_x
            for pos in self._poses.values():
                pos._x = min(pos.x(), offside_line - 0.5)
    
    def get_position(self, uniform_number, agent: IAgent = None) -> Vector2D:
        """
        Get the position for a given uniform number.

        Args:
            uniform_number (int): The uniform number of the player.
            agent (IAgent, optional): The agent instance.

        Returns:
            Vector2D: The position of the player.
        """
        return self._poses[uniform_number]
    
    def get_role_name(self, uniform_number) -> RoleName:
        """
        Get the role name for a given uniform number.

        Args:
            uniform_number (int): The uniform number of the player.

        Returns:
            RoleName: The role name of the player.
        """
        return self.current_formation_file.get_role(uniform_number).name
    
    def get_role_type(self, uniform_number) -> RoleType:
        """
        Get the role type for a given uniform number.

        Args:
            uniform_number (int): The uniform number of the player.

        Returns:
            RoleType: The role type of the player.
        """
        return self.current_formation_file.get_role(uniform_number).type
    
    def get_role_side(self, uniform_number) -> RoleSide:
        """
        Get the role side for a given uniform number.

        Args:
            uniform_number (int): The uniform number of the player.

        Returns:
            RoleSide: The role side of the player.
        """
        return self.current_formation_file.get_role(uniform_number).side
    
    def get_role_pair(self, uniform_number) -> int:
        """
        Get the role pair for a given uniform number.

        Args:
            uniform_number (int): The uniform number of the player.

        Returns:
            int: The role pair of the player.
        """
        return self.current_formation_file.get_role(uniform_number).pair
    
    def get_role(self, uniform_number) -> PlayerRole:
        """
        Get the role for a given uniform number.

        Args:
            uniform_number (int): The uniform number of the player.

        Returns:
            PlayerRole: The role of the player.
        """
        return self.current_formation_file.get_role(uniform_number)
    
    def get_offside_line(self) -> float:
        """
        Get the offside line position.

        Returns:
            float: The offside line position.
        """
        home_poses_x = [pos.x() for pos in self._poses.values()]
        home_poses_x.sort()
        if len(home_poses_x) > 1:
            return home_poses_x[1]
        elif len(home_poses_x) == 1:
            return home_poses_x[0]
        else:
            return 0.0