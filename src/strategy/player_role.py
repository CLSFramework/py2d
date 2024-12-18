from enum import Enum

class RoleName(Enum):
    """
    Enum class representing different role names for players.
    """
    Goalie = "Goalie"
    CenterBack = "CenterBack"
    SideBack = "SideBack"
    DefensiveHalf = "DefensiveHalf"
    OffensiveHalf = "OffensiveHalf"
    SideForward = "SideForward"
    CenterForward = "CenterForward"
    Unknown = "Unknown"
    
class RoleType(Enum):
    """
    Enum class representing different role types for players.
    """
    G = "G"
    DF = "DF"
    MF = "MF"
    FW = "FW"
    Unknown = "Unknown"
    
class RoleSide(Enum):
    """
    Enum class representing different role sides for players.
    """
    L = "L"
    R = "R"
    C = "C"
    Unknown = "Unknown"

class PlayerRole:
    """
    Class representing a player's role in the game.

    Attributes:
        _name (RoleName): The name of the role.
        _type (RoleType): The type of the role.
        _side (RoleSide): The side of the role.
        _pair (int): The pair number of the role.
    """
    def __init__(self, name: str, type: str, side: str, pair: int):
        """
        Initialize a PlayerRole instance.

        Args:
            name (str): The name of the role.
            type (str): The type of the role.
            side (str): The side of the role.
            pair (int): The pair number of the role.
        """
        self._name: RoleName = RoleName(name) if name in RoleName.__members__ else RoleName.Unknown
        self._type: RoleType = RoleType(type) if type in RoleType.__members__ else RoleType.Unknown
        self._side: RoleSide = RoleSide(side) if side in RoleSide.__members__ else RoleSide.Unknown
        self._pair: int = pair
        
    @property
    def name(self) -> RoleName:
        """
        Get the name of the role.

        Returns:
            RoleName: The name of the role.
        """
        return self._name
    
    @property
    def type(self) -> RoleType:
        """
        Get the type of the role.

        Returns:
            RoleType: The type of the role.
        """
        return self._type
    
    @property
    def side(self) -> RoleSide:
        """
        Get the side of the role.

        Returns:
            RoleSide: The side of the role.
        """
        return self._side
    
    @property
    def pair(self) -> int:
        """
        Get the pair number of the role.

        Returns:
            int: The pair number of the role.
        """
        return self._pair