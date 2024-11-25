import subprocess
import os
import signal
import threading
import logging
import argparse
import check_requirements
from utils.logger_utils import setup_logger
import datetime
import multiprocessing
from server import main
import random

# Set up logging
log_dir = None
start_team_logger = None

def run_server_script(args):
    # Define a wrapper function to pass the arguments to the main function
    def server_main():
        import sys
        sys.argv = ['server.py', '--rpc-port', str(args.rpc_port), '--log-dir', log_dir]
        if args.disable_log_file:
            sys.argv += ['--disable-log-file']
        main()

    # Start the main function as a new process
    process = multiprocessing.Process(target=server_main)
    process.start()
    return process

def run_start_script(args):
    # Start the start.sh script in its own directory as a new process group
    arguments = ['bash']
    if args.player or args.coach or args.goalie:
        arguments += ['start-agent.sh', '--coach' if args.coach else '--goalie' if args.goalie else '--player']
    else:
        arguments += ['start.sh' if not args.debug else 'start-debug.sh']
        
    arguments += ['-t', args.team_name, 
         '--rpc-port', args.rpc_port, '--rpc-type', 'grpc', 
         '-p', args.server_port, '-h', args.server_host]
        
    process = subprocess.Popen(
        arguments,
        cwd='scripts/proxy',  # Corrected directory to where start.sh is located
        preexec_fn=os.setsid,  # Create a new session and set the process group ID
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT  # Capture stderr and redirect it to stdout
    )
    return process

stop_thread = threading.Event()

def stream_output_to_file(process, name, args):
    # Stream output from the process and log it to a file with the given name
    f = None if args.disable_log_file else open(f"{log_dir}/{name}.log", "a")
    while not stop_thread.is_set():
        output = process.stdout.readline()
        if output:
            if f:
                f.write(output.decode())
                f.flush()
            else:
                print(output.decode())
        else:
            break
    process.stdout.close()
    
def kill_process_group(process):
    try:
        start_team_logger.debug(f"Killing process group with PID: {process.pid}")
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)  # Send SIGTERM to the process group
    except ProcessLookupError:
        pass  # The process might have already exited

def kill_rpc_server_process(process):
    try:
        start_team_logger.debug(f"Killing process with PID: {process.pid}")
        os.kill(process.pid, signal.SIGTERM)  # Send SIGTERM to the specific process
    except ProcessLookupError:
        pass  # The process might have already exited

    
if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(description='Run server and team scripts.')
    parser.add_argument('-t', '--team_name', required=False, help='The name of the team', default='CLS')
    parser.add_argument('--rpc-port', required=False, help='The port of the server', default='50051')
    parser.add_argument('-d', '--debug', required=False, help='Enable debug mode', default=False, action='store_true')
    parser.add_argument('--use-random-port', required=False, help='Use a random port for the server', default=False, action='store_true')
    parser.add_argument('--use-random-name', required=False, help='Use a random team name', default=False, action='store_true')
    parser.add_argument('--server-host', required=False, help='The host of the server', default='localhost')
    parser.add_argument('--server-port', required=False, help='The port of the server', default='6000')
    parser.add_argument('--close-server', required=False, help='Close the server', default=False, action='store_true')
    parser.add_argument('--player', required=False, help='Use coach instead of proxy', default=False, action='store_true')
    parser.add_argument('--coach', required=False, help='Use coach instead of proxy', default=False, action='store_true')
    parser.add_argument('--goalie', required=False, help='Use goalie instead of proxy', default=False, action='store_true')
    parser.add_argument('--disable-log-file', required=False, help='Disable logging to a file', default=False, action='store_true')
    parser.add_argument('--log-dir', required=False, help='The directory to store logs', default=None)
    args = parser.parse_args()
    
    # Set up logging
    if not args.log_dir:
        log_dir = os.path.join(os.getcwd(), 'logs', f"{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_{random.randint(100000, 999999)}")
    else:
        log_dir = args.log_dir
    start_team_logger = setup_logger('start-team', log_dir, console_level=logging.DEBUG, file_level=logging.DEBUG if not args.disable_log_file else None, console_format_str='%(message)s')

    start_team_logger.debug(f"Arguments: {args=}")
    
    try:
        if args.use_random_port:
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', 0))
                args.rpc_port = str(s.getsockname()[1])
            start_team_logger.debug(f"Using random port: {args.rpc_port}")
                
        if args.use_random_name:
            import random
            import string
            args.team_name = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        
        # Run the server.py script first
        server_process = run_server_script(args)
        start_team_logger.debug(f"Started server.py process with PID: {server_process.pid}")
        
        # Run the start.sh script after server.py with the given arguments
        start_process = run_start_script(args)
        start_team_logger.debug(f"Started start.sh process with PID: {start_process.pid} with team name {args=}")

        # Monitor both processes and log their outputs
        start_team_logger.debug("Monitoring processes...")
        
        start_thread = threading.Thread(target=stream_output_to_file, args=(start_process, 'proxy', args))
        start_thread.start()
        
        def signal_handler(sig, frame):
            start_team_logger.info('Received signal to terminate. Cleaning up...')
            kill_rpc_server_process(server_process)
            server_process.join()
            
            start_team_logger.debug(f"server.py ended with PID: {server_process.pid}")
            
            kill_process_group(start_process)
            start_process.wait()
            
            start_team_logger.debug(f"start.sh ended with PID: {start_process.pid}")
            
            stop_thread.set()
        
            start_thread.join()
            start_team_logger.debug("start_thread has finished.")
            
            start_team_logger.info('All processes have been killed.')
            raise KeyboardInterrupt
            # os._exit(0)
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

        # Wait for both threads to finish
        start_thread.join()
        start_team_logger.debug("server_thread has finished.")
        
        if args.close_server:
            kill_rpc_server_process(server_process)
            start_team_logger.debug("Server has been closed.")
            
        # wait for server process to finish
        server_process.join()
        start_team_logger.debug("server.py has finished.")
        
        start_team_logger.info("Both processes have exited.")
    except KeyboardInterrupt:
        start_team_logger.debug("Interrupted! Killing all processes.")
        kill_rpc_server_process(server_process)
        kill_process_group(start_process)

    finally:
        # Ensure all processes are killed on exit
        start_team_logger.debug("Final Cleaning up...")
        kill_rpc_server_process(server_process)
        kill_process_group(start_process)
