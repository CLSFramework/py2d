import logging
from src.strategy.formation_file import FormationFile

class Formation:
    """
    A class to manage different soccer formations for various game situations.

    Attributes:
        before_kick_off_formation (FormationFile): Formation used before the kick-off.
        defense_formation (FormationFile): Formation used during defense.
        offense_formation (FormationFile): Formation used during offense.
        goalie_kick_opp_formation (FormationFile): Formation used when the opponent's goalie kicks.
        goalie_kick_our_formation (FormationFile): Formation used when our goalie kicks.
        kickin_our_formation (FormationFile): Formation used during our team's kick-in.
        setplay_opp_formation (FormationFile): Formation used during the opponent's set play.
        setplay_our_formation (FormationFile): Formation used during our team's set play.

    Args:
        path (str): The path to the directory containing the formation configuration files.
        logger (logging.Logger): Logger instance for logging formation-related information.
    """
    def __init__(self, path, logger: logging.Logger):
        self.logger = logger
        self.path = path
        self._initialize_formations()

    def _initialize_formations(self):
        """
        Initialize formation files for different game situations.
        """
        self.before_kick_off_formation = self._create_formation_file('before-kick-off.conf')
        self.defense_formation = self._create_formation_file('defense-formation.conf')
        self.offense_formation = self._create_formation_file('offense-formation.conf')
        self.goalie_kick_opp_formation = self._create_formation_file('goalie-kick-opp-formation.conf')
        self.goalie_kick_our_formation = self._create_formation_file('goalie-kick-our-formation.conf')
        self.kickin_our_formation = self._create_formation_file('kickin-our-formation.conf')
        self.setplay_opp_formation = self._create_formation_file('setplay-opp-formation.conf')
        self.setplay_our_formation = self._create_formation_file('setplay-our-formation.conf')

    def _create_formation_file(self, filename: str) -> FormationFile:
        """
        Create a FormationFile instance for a given filename.

        Args:
            filename (str): The name of the formation configuration file.

        Returns:
            FormationFile: The created FormationFile instance.
        """
        return FormationFile(f'{self.path}/{filename}', self.logger)
