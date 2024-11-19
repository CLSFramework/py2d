from pyrusgeom.soccer_math import *
from pyrusgeom.geom_2d import *
from service_pb2 import *


class Convertor:
    @staticmethod
    def convert_rpc_vector2d_to_vector2d(rpc_vector2d: RpcVector2D) -> Vector2D:
        return Vector2D(rpc_vector2d.x, rpc_vector2d.y)

    @staticmethod
    def convert_vector2d_to_rpc_vector2d(vector2d: Vector2D) -> RpcVector2D:
        return RpcVector2D(x=vector2d.x(), y=vector2d.y())