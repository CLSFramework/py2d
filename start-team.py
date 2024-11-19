import subprocess
import os
import signal
import threading
import logging
import argparse
import check_requirements
from utils.logger_utils import setup_logger
import datetime


# Set up logging
log_dir = os.path.join(os.getcwd(), 'logs', datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
start_team_logger = setup_logger('start-team', log_dir, console_level=logging.DEBUG, file_level=logging.DEBUG, console_format_str='%(message)s')


def run_server_script(args):
    # Start the server.py script as a new process group
    process = subprocess.Popen(
        ['python3', 'server.py', '--rpc-port', args.rpc_port, '--log-dir', log_dir],
        preexec_fn=os.setsid,  # Create a new session and set the process group ID
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT  # Capture stderr and redirect it to stdout
    )
    return process

def run_start_script(args):
    # Start the start.sh script in its own directory as a new process group
    process = subprocess.Popen(
        ['bash', 'start.sh' if not args.debug else 'start-debug.sh', '-t', args.team_name, '--rpc-port', args.rpc_port, '--rpc-type', 'grpc', '-p', args.server_port],
        cwd='scripts/proxy',  # Corrected directory to where start.sh is located
        preexec_fn=os.setsid,  # Create a new session and set the process group ID
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT  # Capture stderr and redirect it to stdout
    )
    return process

def stream_output_to_console(process, prefix):
    # Stream output from the process and log it with a prefix
    for line in iter(process.stdout.readline, b''):
        start_team_logger.debug(f'{prefix} {line.decode().strip()}')
    process.stdout.close()

def stream_output_to_file(process, prefix):
    # Stream output from the process and log it with a prefix
    logger = setup_logger(prefix, log_dir, console_level=None, file_level=logging.DEBUG)
    for line in iter(process.stdout.readline, b''):
        logger.info(line.decode().strip())
        pass
    process.stdout.close()
    
def kill_process_group(process):
    try:
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)  # Send SIGTERM to the process group
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
    parser.add_argument('--server-port', required=False, help='The port of the server', default='6000')
    args = parser.parse_args()
    
    try:
        # Check Python requirements
        start_team_logger.debug("Checking Python requirements...")
        check_requirements.check_requirements()
        
        if args.use_random_port:
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', 0))
                args.rpc_port = str(s.getsockname()[1])
                
        if args.use_random_team:
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
        server_thread = threading.Thread(target=stream_output_to_console, args=(server_process, 'server'))
        start_thread = threading.Thread(target=stream_output_to_file, args=(start_process, 'proxy'))

        server_thread.start()
        start_thread.start()

        # Wait for both threads to finish
        server_thread.join()
        start_thread.join()

    except KeyboardInterrupt:
        start_team_logger.debug("Interrupted! Killing all processes.")
        kill_process_group(server_process)
        kill_process_group(start_process)

    finally:
        # Ensure all processes are killed on exit
        kill_process_group(server_process)
        kill_process_group(start_process)
