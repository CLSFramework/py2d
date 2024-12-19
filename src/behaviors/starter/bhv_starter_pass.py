from typing import TYPE_CHECKING
from src.interfaces.IBehavior import IBehavior
from pyrusgeom.soccer_math import *
from pyrusgeom.geom_2d import *
from src.utils.tools import Tools
from service_pb2 import *


if TYPE_CHECKING:
    from src.sample_player_agent import SamplePlayerAgent


class BhvStarterPass(IBehavior):
    def __init__(self):
        pass

    def execute(self, agent: "SamplePlayerAgent") -> bool:
        # Log the execution of the behavior
        agent.logger.debug("BhvStarterPass.execute")
        
        # Get the world model from the agent
        wm = agent.wm
        
        # Initialize the list of potential pass targets
        targets: list[Vector2D] = self.get_candidates(agent)
        
        # Get the best pass target
        best_target = self.get_best_candidate(agent, targets)

        # If there is a valid pass target, execute the pass action
        if best_target is not None:
            first_speed = 2.5 if wm.game_mode_type == GameModeType.PlayOn else 2.7
            first_speed_threshold = (
                2.5 if wm.game_mode_type == GameModeType.PlayOn else 0.0
            )
            max_steps = 3 if wm.game_mode_type == GameModeType.PlayOn else 1

            # Log the pass action
            agent.add_log_message(
                LoggerLevel.PASS,
                f": Passing to {best_target}",
                agent.wm.self.position.x,
                agent.wm.self.position.y - 2,
                "\033[31m",
            )
            agent.add_log_text(LoggerLevel.PASS, f": Passing to {best_target}")
            agent.logger.debug(f"Passing to {best_target}")
            
            # Add the pass action to the agent's action list
            agent.add_action(
                PlayerAction(
                    body_smart_kick=Body_SmartKick(
                        target_point=Tools.convert_vector2d_to_rpc_vector2d(
                            best_target
                        ),
                        first_speed=first_speed,
                        first_speed_threshold=first_speed_threshold,
                        max_steps=max_steps,
                    )
                )
            )
            return True

        # Return False if no valid pass targets are found
        return False
    
    def get_candidates(self, agent: "SamplePlayerAgent") -> list[Vector2D]:
        """
        Identify potential pass targets for the agent.
        This function evaluates the positions of the agent's teammates and determines
        which ones are valid pass targets based on several criteria, such as distance
        from the ball, distance from the agent, and offside position. It also checks
        for the presence of opponents in the passing path.
        Args:
            agent (SamplePlayerAgent): The agent for which to find pass targets.
        Returns:
            list[Vector2D]: A list of valid pass target positions as Vector2D objects.
        """
        # Get the world model from the agent
        wm = agent.wm
        
        # Initialize the list of potential pass targets
        targets: list[Vector2D] = []
        
        # Get the positions of the ball and the agent
        ball_pos = Vector2D(wm.ball.position.x, wm.ball.position.y)
        self_pos = Vector2D(wm.self.position.x, wm.self.position.y)
        
        # Iterate over teammates to find valid pass targets
        for teammate in wm.teammates:
            if (
                teammate == None
                or teammate.uniform_number == wm.self.uniform_number
                or teammate.uniform_number < 0
            ):
                continue
            
            tm_pos = Vector2D(teammate.position.x, teammate.position.y)
            
            # Check if the teammate is too far from the ball
            if tm_pos.dist(ball_pos) > 30.0:
                continue
            
            # Check if the teammate is too close to the agent
            if self_pos.dist(tm_pos) < 2.0:
                continue
            
            # Check if the teammate is offside
            if tm_pos.x() > wm.offside_line_x - 0.5:
                continue
            
            # Define a sector to check for opponents
            check_root = Sector2D(
                ball_pos,
                1.0,
                tm_pos.dist(ball_pos) + 3.0,
                (tm_pos - ball_pos).th().degree() - 15.0,
                (tm_pos - ball_pos).th().degree() + 15.0,
            )
            
            # Check if there are no opponents in the sector
            if not Tools.exist_opponent_in(agent, check_root):
                targets.append(tm_pos)
        
        # Return the list of valid pass targets
        return targets

    def get_best_candidate(self, agent: "SamplePlayerAgent", targets: list[Vector2D]) -> Union[Vector2D, None]:
        """
        Determine the best candidate target from a list of targets for the given agent.
        Args:
            agent (SamplePlayerAgent): The agent for which the best candidate target is being determined.
            targets (list[Vector2D]): A list of potential target positions represented as Vector2D objects.
        Returns:
            Union[Vector2D, None]: The best candidate target based on the highest x-coordinate value, 
                                   or None if the targets list is empty.
        """
        # Get the world model from the agent
        wm = agent.wm
        
        if len(targets) == 0:
            return None
        
        # Initialize the best pass target
        best_target: Vector2D = max(targets, key=lambda target: target.x())
        
        # Return the best pass target
        return best_target