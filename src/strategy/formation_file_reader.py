from pyrusgeom.geom_2d import *
from enum import Enum
from abc import ABC, abstractmethod
import json
from src.strategy.player_role import PlayerRole
        
        
class FormationType(Enum):
    Static = 's'
    DelaunayTriangulation2 = 'D'

class FormationIndexData:
    def __init__(self, ball, players):
        self._ball: list[float] = ball
        self._players: list[list[float]] = players
        
    def ball(self) -> list[float]:
        return self._ball
    
    def players(self) -> list[list[float]]:
        return self._players

class IFormationFileReader(ABC):
    @abstractmethod
    def read_file(self, path) -> list[list[FormationIndexData], dict[int, PlayerRole]]:
        pass
    
class OldStaticFormationFileReader(IFormationFileReader):
    def read_file(self, lines: list[str]) -> list[list[FormationIndexData], dict[int, PlayerRole]]:
        players = {}
        roles = {}
        for i in range(len(lines)):
            if i == 0 or lines[i].startswith('#'):
                continue
            player = lines[i].split()
            players[int(player[0])] = ([float(player[2]), float(player[3])])
            roles[int(player[0])] = PlayerRole(player[1], None, None, None)
        
        return [FormationIndexData(None, players)], roles

class OldDelaunayFormationFileReader(IFormationFileReader):
    def read_file(self, lines: list[str]) -> list[list[FormationIndexData], dict[int, PlayerRole]]:
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
            if lines[i].find('Ball') >= 0:
                indexes.append(self.read_index(i, lines))
            i += 11
        return indexes, roles

    def read_index(self, i: int, lines: list[str]) -> FormationIndexData:
        ball = lines[i].split(' ')
        ball_x = float(ball[1])
        ball_y = float(ball[2])
        ball = [ball_x, ball_y]
        players = {}
        for j in range(1, 12):
            player = lines[i + j].split(' ')
            player_x = float(player[1])
            player_y = float(player[2])
            players[j] = ([player_x, player_y])
        return FormationIndexData(ball, players)
    
class JsonFormationFileReader(IFormationFileReader):
    def read_file(self, lines: list[str]) -> list[list[FormationIndexData], dict[int, PlayerRole]]:
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
        return lines[0].find('{') >= 0
    
    @staticmethod
    def get_method(lines: list[str]) -> FormationType:
        text = ''.join(lines)
        data = json.loads(text)
        if data['method'] == 'Static':
            return FormationType.Static
        return FormationType.DelaunayTriangulation2
        
        
class FormationFileReaderFactory:
    def get_reader(self, lines) -> list[IFormationFileReader, FormationType]:
        if JsonFormationFileReader.is_json(lines):
            return JsonFormationFileReader(), JsonFormationFileReader.get_method(lines)
        if lines[0].find('Static') >= 0:
            return OldStaticFormationFileReader(), FormationType.Static
        return OldDelaunayFormationFileReader(), FormationType.DelaunayTriangulation2
    
    def read_file(self, path) -> list[list[FormationIndexData], dict[int, PlayerRole], FormationType]:
        file = open(path, 'r')
        lines = file.readlines()
        reader, formation_type = self.get_reader(lines)
        indexes, roles = reader.read_file(lines)
        return indexes, roles, formation_type
