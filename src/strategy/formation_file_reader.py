from pyrusgeom.geom_2d import *
from enum import Enum
from abc import ABC, abstractmethod
import json
from src.strategy.player_role import PlayerRole

# Enum for formation types
class FormationType(Enum):
    Static = 's'
    DelaunayTriangulation2 = 'D'

# Class to store formation index data
class FormationIndexData:
    def __init__(self, ball, players):
        self._ball: list[float] = ball
        self._players: list[list[float]] = players
        
    def ball(self) -> list[float]:
        """Returns the ball position."""
        return self._ball
    
    def players(self) -> list[list[float]]:
        """Returns the players' positions."""
        return self._players

# Abstract base class for formation file readers
class IFormationFileReader(ABC):
    @abstractmethod
    def read_file(self, lines: list[str]) -> tuple[list[FormationIndexData], dict[int, PlayerRole]]:
        """Reads the formation file and returns formation index data and player roles."""
        pass
    
# Class to read old static formation files
class OldStaticFormationFileReader(IFormationFileReader):
    def read_file(self, lines: list[str]) -> tuple[list[FormationIndexData], dict[int, PlayerRole]]:
        """Reads old static formation files and returns formation index data and player roles."""
        players = {}
        roles = {}
        for i in range(len(lines)):
            if i == 0 or lines[i].startswith('#'):
                continue
            player = lines[i].split()
            players[int(player[0])] = [float(player[2]), float(player[3])]
            roles[int(player[0])] = PlayerRole(player[1], None, None, None)
        
        return [FormationIndexData(None, players)], roles

# Class to read old Delaunay triangulation formation files
class OldDelaunayFormationFileReader(IFormationFileReader):
    def read_file(self, lines: list[str]) -> tuple[list[FormationIndexData], dict[int, PlayerRole]]:
        """Reads old Delaunay triangulation formation files and returns formation index data and player roles."""
        roles = {}
        begin_roles = False
        for i in range(len(lines)):
            if lines[i].startswith('Begin Roles'):
                begin_roles = True
                continue
            if lines[i].startswith('End Roles'):
                break
            if begin_roles:
                player = lines[i].split()
                roles[int(player[0])] = PlayerRole(player[1], None, None, int(player[2]))
        indexes = []
        for i in range(len(lines)):
            if 'Ball' in lines[i]:
                indexes.append(self.read_index(i, lines))
            i += 11
        return indexes, roles

    def read_index(self, i: int, lines: list[str]) -> FormationIndexData:
        """Reads a single formation index from the lines."""
        ball = lines[i].split(' ')
        ball_x = float(ball[1])
        ball_y = float(ball[2])
        ball = [ball_x, ball_y]
        players = {}
        for j in range(1, 12):
            player = lines[i + j].split(' ')
            player_x = float(player[1])
            player_y = float(player[2])
            players[j] = [player_x, player_y]
        return FormationIndexData(ball, players)
    
# Class to read JSON formation files
class JsonFormationFileReader(IFormationFileReader):
    def read_file(self, lines: list[str]) -> tuple[list[FormationIndexData], dict[int, PlayerRole]]:
        """Reads JSON formation files and returns formation index data and player roles."""
        text = ''.join(lines)
        data = json.loads(text)
        roles = {}
        for role in data['role']:
            roles[role['number']] = PlayerRole(role['name'], role['type'], role['side'], role['pair'])
        indexes = []
        for index in data['data']:
            ball = [index['ball']['x'], index['ball']['y']]
            players = {}
            for i in range(1, 12):
                players[i] = [index[str(i)]['x'], index[str(i)]['y']]
            indexes.append(FormationIndexData(ball, players))
        return indexes, roles
    
    @staticmethod
    def is_json(lines: list[str]) -> bool:
        """Checks if the lines represent a JSON file."""
        return '{' in lines[0]
    
    @staticmethod
    def get_method(lines: list[str]) -> FormationType:
        """Gets the formation method from the JSON data."""
        text = ''.join(lines)
        data = json.loads(text)
        if data['method'] == 'Static':
            return FormationType.Static
        return FormationType.DelaunayTriangulation2
        
# Factory class to get the appropriate formation file reader
class FormationFileReaderFactory:
    def get_reader(self, lines: list[str]) -> tuple[IFormationFileReader, FormationType]:
        """Returns the appropriate formation file reader based on the file content."""
        if JsonFormationFileReader.is_json(lines):
            return JsonFormationFileReader(), JsonFormationFileReader.get_method(lines)
        if 'Static' in lines[0]:
            return OldStaticFormationFileReader(), FormationType.Static
        return OldDelaunayFormationFileReader(), FormationType.DelaunayTriangulation2
    
    def read_file(self, path: str) -> tuple[list[FormationIndexData], dict[int, PlayerRole], FormationType]:
        """Reads the formation file and returns formation index data, player roles, and formation type."""
        with open(path, 'r') as file:
            lines = file.readlines()
        reader, formation_type = self.get_reader(lines)
        indexes, roles = reader.read_file(lines)
        return indexes, roles, formation_type
