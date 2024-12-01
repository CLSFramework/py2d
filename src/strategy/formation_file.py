from scipy.spatial import Delaunay
from pyrusgeom.geom_2d import *
from pyrusgeom.soccer_math import min_max
import logging
from src.strategy.formation_file_reader import FormationFileReaderFactory, FormationType
from src.strategy.player_role import PlayerRole

class FormationFile:
    def __init__(self, path, logger: logging.Logger):
        self._logger = logger
        self._balls = []
        self._players = []
        self._triangles = []
        self._formation_type = FormationType.Static
        self._target_players = {}
        self._path = path
        self._roles: dict[int, PlayerRole] = {}
        self.read_file(path)
        self.calculate()

    def read_file(self, path):
        indexes, self._roles, self._formation_type = FormationFileReaderFactory().read_file(path)
        
        if self._formation_type == FormationType.Static:
            data = indexes[0]
            players = data.players()
            for i in range(1, 12):
                self._target_players[i] = Vector2D(float(players[i][0]), float(players[i][1]))
        else:
            for index in indexes:
                self._balls.append(index.ball())
                self._players.append(index.players())

    def calculate(self):
        if self._formation_type == FormationType.Static:
            return
        self._tri = Delaunay(self._balls).simplices
        for tri in self._tri:
            tmp = [Triangle2D(Vector2D(self._balls[tri[0]][0], self._balls[tri[0]][1]),
                                    Vector2D(self._balls[tri[1]][0], self._balls[tri[1]][1]),
                                    Vector2D(self._balls[tri[2]][0], self._balls[tri[2]][1])), tri[0], tri[1], tri[2]]
            self._triangles.append(tmp)

    def update(self, B:Vector2D):
        # SP = ServerParam.i()
        if self._formation_type == FormationType.Static:
            return
        ids = []
        
        point = B.copy()
        if point.abs_x() > 52.5: #todo SP.pitch_half_length():
            point._x = min_max(-52.5, point.x(), 52.5) #todo 
        if point.abs_y() > 34.0: #SP.pitch_half_width():
            point._y = min_max(-34.0, point.y(), +34.0) #todo
        
        for tri in self._triangles:
            if tri[0].contains(point):
                ids = [tri[1], tri[2], tri[3]]
                break
        Pa = Vector2D(self._balls[ids[0]][0], self._balls[ids[0]][1])
        Pb = Vector2D(self._balls[ids[1]][0], self._balls[ids[1]][1])
        Pc = Vector2D(self._balls[ids[2]][0], self._balls[ids[2]][1])
        lineProj = Line2D(p1=Pb, p2=Pc).projection(B)
        m1 = Pb.dist(lineProj)
        n1 = Pc.dist(lineProj)
        m2 = Pa.dist(B)
        n2 = lineProj.dist(B)

        self._target_players.clear()
        for p in range(1, 12):
            OPa = Vector2D(self._players[ids[0]][p][0], self._players[ids[0]][p][1])
            OPb = Vector2D(self._players[ids[1]][p][0], self._players[ids[1]][p][1])
            OPc = Vector2D(self._players[ids[2]][p][0], self._players[ids[2]][p][1])
            OI = (OPc - OPb)
            OI *= (m1 / (m1 + n1))
            OI += OPb
            OB = (OI - OPa)
            OB *= (m2 / (m2 + n2))
            OB += OPa
            self._target_players[p] = OB

    def get_pos(self, unum):
        return self._target_players[unum]

    def get_poses(self):
        return self._target_players
    
    def get_role(self, unum) -> PlayerRole:
        return self._roles[unum]

    def __repr__(self):
        return self._path

# f = Formation('base/formations-dt/before-kick-off.conf')
# debug_print(len(f._balls))
# debug_print(len(f._players))
# debug_print(f._formation_type)
# f.update(Vector2D(20, 16))
# debug_print(f._formation_type)
# debug_print(f._target_players)
