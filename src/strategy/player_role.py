from enum import Enum


class RoleName(Enum):
    Goalie = "Goalie"
    CenterBack = "CenterBack"
    SideBack = "SideBack"
    DefensiveHalf = "DefensiveHalf"
    OffensiveHalf = "OffensiveHalf"
    SideForward = "SideForward"
    CenterForward = "CenterForward"
    Unknown = "Unknown"
    
class RoleType(Enum):
    G = "G"
    DF = "DF"
    MF = "MF"
    FW = "FW"
    Unknown = "Unknown"
    
class RoleSide(Enum):
    L = "L"
    R = "R"
    C = "C"
    Unknown = "Unknown"

class PlayerRole:
    def __init__(self, name: str, type: str, side: str, pair: int):
        self._name: RoleName = RoleName(name) if name in RoleName.__members__ else RoleName.Unknown
        self._type: RoleType = RoleType(type) if type in RoleType.__members__ else RoleType.Unknown
        self._side: RoleSide = RoleSide(side) if side in RoleSide.__members__ else RoleSide.Unknown
        self._pair: int = pair
        
    @property
    def name(self) -> RoleName:
        return self._name
    
    @property
    def type(self) -> RoleType:
        return self._type
    
    @property
    def side(self) -> RoleSide:
        return self._side
    
    @property
    def pair(self) -> int:
        return self._pair