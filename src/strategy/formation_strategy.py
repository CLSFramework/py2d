from src.interfaces.IPositionStrategy import IPositionStrategy
from src.strategy.formation_file import *
from src.interfaces.IAgent import IAgent
from enum import Enum
from pyrusgeom.soccer_math import *
from service_pb2 import *
import logging


class Situation(Enum):
    OurSetPlay_Situation = 0,
    OppSetPlay_Situation = 1,
    Defense_Situation = 2,
    Offense_Situation = 3,
    PenaltyKick_Situation = 4

class Formation:
    def __init__(self, path):
        self.before_kick_off_formation: FormationFile = FormationFile(f'{path}/before_kick_off.conf')
        self.defense_formation: FormationFile = FormationFile(f'{path}/defense_formation.conf')
        self.offense_formation: FormationFile = FormationFile(f'{path}/offense_formation.conf')
        self.goalie_kick_opp_formation: FormationFile = FormationFile(f'{path}/goalie_kick_opp_formation.conf')
        self.goalie_kick_our_formation: FormationFile = FormationFile(f'{path}/goalie_kick_our_formation.conf')
        self.kickin_our_formation: FormationFile = FormationFile(f'{path}/kickin_our_formation.conf')
        self.setplay_opp_formation: FormationFile = FormationFile(f'{path}/setplay_opp_formation.conf')
        self.setplay_our_formation: FormationFile = FormationFile(f'{path}/setplay_our_formation.conf')
        
class FormationStrategy(IPositionStrategy):
    def __init__(self):
        self.formations: dict[str, Formation] = {}
        self.formations['4-3-3'] = Formation('src/formations/4-3-3')
        self.selected_formation_name = '4-3-3'
        
        self._poses: dict[int, Vector2D] = {(i, Vector2D(0, 0)) for i in range(11)}
        self.current_situation = Situation.Offense_Situation
        self.current_formation_file: FormationFile = self._get_current_formation().offense_formation

    def _get_current_formation(self) -> Formation:
        return self.formations[self.selected_formation_name]
    
    def _set_formation(self, wm: WorldModel):
        self.selected_formation_name = '4-3-3'
        
    def update(self, agent: IAgent):
        logger = agent.logger
        logger.debug(f'---- update strategy ----')
        
        wm: WorldModel = agent.wm
        
        self._set_formation(wm)
        
        tm_min = wm.intercept_table.first_teammate_reach_steps
        opp_min = wm.intercept_table.first_opponent_reach_steps
        self_min = wm.intercept_table.self_reach_steps
        all_min = min(tm_min, opp_min, self_min)
        current_ball_pos = Vector2D(wm.ball.position.x, wm.ball.position.y)
        current_ball_vel = Vector2D(wm.ball.velocity.x, wm.ball.velocity.y)
        ball_pos = inertia_n_step_point(current_ball_pos, current_ball_vel, all_min, 0.96) #todo use server param ball decay
        

        if True: #todo wm.game_mode().type() is GameModeType.PlayOn:
            thr = 0
            if ball_pos.x() > 0:
                thr += 1
            if wm.self.uniform_number > 6:
                thr += 1
            if min(tm_min, self_min) < opp_min + thr:
                self.current_situation = Situation.Offense_Situation
            else:
                self.current_situation = Situation.Defense_Situation
        else:
            pass
            # if wm.game_mode().is_penalty_kick_mode():
            #     self.current_situation = Situation.PenaltyKick_Situation
            # elif wm.game_mode().is_our_set_play(wm.our_side()):
            #     self.current_situation = Situation.OurSetPlay_Situation
            # else:
            #     self.current_situation = Situation.OppSetPlay_Situation

        if True: #ToDo wm.game_mode().type() is GameModeType.PlayOn:
            if self.current_situation is Situation.Offense_Situation:
                self.current_formation_file = self._get_current_formation().offense_formation
            else:
                self.current_formation_file = self._get_current_formation().defense_formation

        # elif wm.game_mode().type() in [GameModeType.BeforeKickOff, GameModeType.AfterGoal_Left,
        #                                GameModeType.AfterGoal_Right]:
        #     self.current_formation_file = self.before_kick_off_formation

        # elif wm.game_mode().type() in [GameModeType.GoalKick_Left, GameModeType.GoalKick_Right, GameModeType.GoalieCatchBall_Left, GameModeType.GoalieCatchBall_Right]: # Todo add Goal Catch!!
        #     if wm.game_mode().is_our_set_play(wm.our_side()):
        #         self.current_formation_file = self.goalie_kick_our_formation
        #     else:
        #         self.current_formation_file = self.goalie_kick_opp_formation

        # else:
        #     if wm.game_mode().is_our_set_play(wm.our_side()):
        #         if wm.game_mode().type() in [GameModeType.KickIn_Right, GameModeType.KickIn_Left,
        #                                      GameModeType.CornerKick_Right, GameModeType.CornerKick_Left]:
        #             self.current_formation_file = self.kickin_our_formation
        #         else:
        #             self.current_formation_file = self.setplay_our_formation
        #     else:
        #         self.current_formation_file = self.setplay_opp_formation

        self.current_formation_file.update(ball_pos)
        self._poses = self.current_formation_file.get_poses()

        logger.debug(f'{self._poses=}')
        # if self.current_formation_file is self.before_kick_off_formation or wm.game_mode().type() in \
        #         [GameModeType.KickOff_Left, GameModeType.KickOff_Right]:
        #     for pos in self._poses:
        #         pos._x = min(pos.x(), -0.5)
        # else:
        #     pass # Todo add offside line
        #     # for pos in self._poses:
        #     #     pos._x = math.min(pos.x(), )
    
    def get_position(self, uniform_number):
        return self._poses[uniform_number]
    
    def get_offside_line(self):
        home_poses_x = [pos.x() for pos in self._poses.values()]
        home_poses_x.sort()
        if len(home_poses_x) > 1:
            return home_poses_x[1]
        elif len(home_poses_x) == 1:
            return home_poses_x[0]
        else:
            return 0.0