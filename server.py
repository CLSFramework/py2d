from concurrent import futures
from time import sleep
import service_pb2_grpc as pb2_grpc
import service_pb2 as pb2
from typing import Union
from multiprocessing import Manager, Lock
from utils.logger_utils import setup_logger
import logging
import grpc
import argparse
import datetime
from src.interfaces.IAgent import IAgent
from src.sample_coach_agent import SampleCoachAgent
from src.sample_player_agent import SamplePlayerAgent
from src.sample_trainer_agent import SampleTrainerAgent


console_logging_level = logging.INFO
file_logging_level = logging.DEBUG

main_logger = None
log_dir = None


class GrpcAgent:
    def __init__(self, agent_type, uniform_number, logger) -> None:
        self.agent_type: pb2.AgentType = agent_type
        self.uniform_number: int = uniform_number
        self.agent: IAgent = None
        self.logger: logging.Logger = logger
        if self.agent_type == pb2.AgentType.PlayerT:
            self.agent = SamplePlayerAgent()
        elif self.agent_type == pb2.AgentType.CoachT:
            self.agent = SampleCoachAgent()
        elif self.agent_type == pb2.AgentType.TrainerT:
            self.agent = SampleTrainerAgent()
        self.agent.set_logger(self.logger)
        self.debug_mode: bool = False
        
    
    def GetAction(self, state: pb2.State):
        self.logger.debug(f"================================= cycle={state.world_model.cycle}.{state.world_model.stoped_cycle} =================================")
        # self.logger.debug(f"State: {state}")
        try:
            if self.agent_type == pb2.AgentType.PlayerT:
                return self.GetPlayerActions(state)
            elif self.agent_type == pb2.AgentType.CoachT:
                return self.GetCoachActions(state)
            elif self.agent_type == pb2.AgentType.TrainerT:
                return self.GetTrainerActions(state)
        except Exception as e:
            self.logger.error(f"Error in GetAction: {e}")
            import traceback
            traceback.print_exc()
            return pb2.PlayerActions()
        
    def GetPlayerActions(self, state: pb2.State):
        self.agent.update_actions(state.world_model)
        res = pb2.PlayerActions()
        res.actions.extend(self.agent.get_actions())
        return res
    
    def GetBestPlannerAction(self, request: pb2.BestPlannerActionRequest) -> int:
        self.logger.debug(f"GetBestPlannerAction cycle:{request.state.world_model.cycle} pairs:{len(request.pairs)} unum:{request.state.register_response.uniform_number}")
        best_index = max(request.pairs.items(), key=lambda x: x[1].evaluation)[0]
        best_action = request.pairs[best_index].action
        
        while best_action.parent_index and best_action.parent_index > 0:
            best_action = request.pairs[best_action.parent_index].action
        
        res = pb2.BestPlannerActionResponse(index=best_action.index)
        return res
    
    def GetCoachActions(self, state: pb2.State):
        self.agent.update_actions(state.world_model)
        return pb2.CoachActions(actions=self.agent.get_actions())
    
    def GetTrainerActions(self, state: pb2.State):
        self.agent.update_actions(state.world_model)
        return pb2.TrainerActions(actions=self.agent.get_actions())
    
    def SetServerParams(self, server_params: pb2.ServerParam):
        self.logger.debug(f"Server params received unum {server_params.register_response.uniform_number}")
        self.agent.set_server_params(server_params)
        
    def SetPlayerParams(self, player_params: pb2.PlayerParam):
        self.logger.debug(f"Player params received unum {player_params.register_response.uniform_number}")
        self.agent.set_player_params(player_params)
        
    def SetPlayerType(self, player_type: pb2.PlayerType):
        self.logger.debug(f"Player type received unum {player_type.register_response.uniform_number}")
        self.agent.set_player_types(player_type)
        
class GameHandler(pb2_grpc.GameServicer):
    def __init__(self, shared_lock, shared_number_of_connections) -> None:
        self.agents: dict[int, GrpcAgent] = {}
        self.shared_lock = shared_lock
        self.shared_number_of_connections = shared_number_of_connections

    def GetPlayerActions(self, state: pb2.State, context):
        main_logger.debug(f"GetPlayerActions unum {state.register_response.uniform_number} at {state.world_model.cycle}")
        res = self.agents[state.register_response.client_id].GetAction(state)
        return res

    def GetCoachActions(self, state: pb2.State, context):
        main_logger.debug(f"GetCoachActions coach at {state.world_model.cycle}")
        res = self.agents[state.register_response.client_id].GetAction(state)
        return res

    def GetTrainerActions(self, state: pb2.State, context):
        main_logger.debug(f"GetTrainerActions trainer at {state.world_model.cycle}")
        res = self.agents[state.register_response.client_id].GetAction(state)
        return res

    def SendServerParams(self, serverParams: pb2.ServerParam, context):
        main_logger.debug(f"Server params received unum {serverParams.register_response.uniform_number}")
        self.agents[serverParams.register_response.client_id].SetServerParams(serverParams)
        res = pb2.Empty()
        return res

    def SendPlayerParams(self, playerParams: pb2.PlayerParam, context):
        main_logger.debug(f"Player params received unum {playerParams.register_response.uniform_number}")
        self.agents[playerParams.register_response.client_id].SetPlayerParams(playerParams)
        res = pb2.Empty()
        return res

    def SendPlayerType(self, playerType: pb2.PlayerType, context):
        main_logger.debug(f"Player type received unum {playerType.register_response.uniform_number}")
        self.agents[playerType.register_response.client_id].SetPlayerType(playerType)
        res = pb2.Empty()
        return res

    def SendInitMessage(self, initMessage: pb2.InitMessage, context):
        main_logger.debug(f"Init message received unum {initMessage.register_response.uniform_number}")
        self.agents[initMessage.register_response.client_id].debug_mode = initMessage.debug_mode
        res = pb2.Empty()
        return res

    def Register(self, register_request: pb2.RegisterRequest, context):
        with self.shared_lock:
            main_logger.info(f"received register request from team_name: {register_request.team_name} "
                f"unum: {register_request.uniform_number} "
                f"agent_type: {register_request.agent_type}")
            self.shared_number_of_connections.value += 1
            main_logger.info(f"Number of connections {self.shared_number_of_connections.value}")
            team_name = register_request.team_name
            uniform_number = register_request.uniform_number
            agent_type = register_request.agent_type
            register_response = pb2.RegisterResponse(client_id=self.shared_number_of_connections.value,
                                    team_name=team_name,
                                    uniform_number=uniform_number,
                                    agent_type=agent_type)
            logger = setup_logger(f"agent{register_response.uniform_number}_{register_response.client_id}", log_dir)
            self.agents[self.shared_number_of_connections.value] = GrpcAgent(agent_type, uniform_number, logger)
        return register_response

    def SendByeCommand(self, register_response: pb2.RegisterResponse, context):
        main_logger.debug(f"Bye command received unum {register_response.uniform_number}")
        # with shared_lock:
        self.agents.pop(register_response.client_id)
            
        res = pb2.Empty()
        return res
    
    def GetBestPlannerAction(self, pairs: pb2.BestPlannerActionRequest, context):
        main_logger.debug(f"GetBestPlannerAction cycle:{pairs.state.world_model.cycle} pairs:{len(pairs.pairs)} unum:{pairs.register_response.uniform_number}")
        res = self.agents[pairs.register_response.client_id].GetBestPlannerAction(pairs)
        return res
    

def serve(port, shared_lock, shared_number_of_connections):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=22))
    game_service = GameHandler(shared_lock, shared_number_of_connections)
    pb2_grpc.add_GameServicer_to_server(game_service, server)
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    main_logger.info(f"Starting server on port {port}")
    
    server.wait_for_termination()
    

def main():
    global main_logger, log_dir
    parser = argparse.ArgumentParser(description='Run play maker server')
    parser.add_argument('-p', '--rpc-port', required=False, help='The port of the server', default=50051)
    parser.add_argument('-l', '--log-dir', required=False, help='The directory of the log file', 
                        default=f'logs/{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}')
    args = parser.parse_args()
    log_dir = args.log_dir
    main_logger = setup_logger("pmservice", log_dir, console_level=console_logging_level, file_level=file_logging_level)
    main_logger.info("Starting server")
    manager = Manager()
    shared_lock = Lock()  # Create a Lock for synchronization
    shared_number_of_connections = manager.Value('i', 0)
    
    serve(args.rpc_port, shared_lock, shared_number_of_connections)
    
if __name__ == '__main__':
    main()
    
