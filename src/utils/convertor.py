from pyrusgeom.soccer_math import *
from pyrusgeom.geom_2d import *
from service_pb2 import *


class Convertor:
    """Utility class for converting between RPC and internal vector representations"""
    
    @staticmethod
    def convert_rpc_vector2d_to_vector2d(rpc_vector2d: RpcVector2D) -> Vector2D:
        """Convert RPC vector message to internal Vector2D representation
        
        Args:
            rpc_vector2d: Vector from RPC message
        Returns:
            Vector2D: Internal vector representation
        """
        return Vector2D(rpc_vector2d.x, rpc_vector2d.y)

    @staticmethod
    def convert_vector2d_to_rpc_vector2d(vector2d: Vector2D) -> RpcVector2D:
        """Convert internal Vector2D to RPC vector message
        
        Args:
            vector2d: Internal vector representation
        Returns:
            RpcVector2D: Vector in RPC message format
        """
        return RpcVector2D(x=vector2d.x(), y=vector2d.y())