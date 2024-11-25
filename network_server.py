# network_server.py

from shared import message, NETWORK_SERVER_PORT
from key_value import KeyValue
import threading
import sys
import time
import socket


# Global Variables
global server_running
stop_event = threading.Event()


socket_info = [
    [1, 2, 3],  # Socket numbers
    [None, None, None],  # Sockets (initially null)
    [  # Link status (tuple for each connection)
        [(2, 1), (3, 1)],  # Links for socket 1 (server, status)
        [(1, 1), (3, 1)],  # Links for socket 2 (server, status)
        [(1, 1), (2, 1)],  # Links for socket 3 (server, status)
    ]
]

# Setup socket information data structure
def setup_socket_info():
    """
    Pseudocode:
    - Initialize socket_info 2D array
    - Set all sockets to None initially
    """

# Simulate user input for server control
def get_user_input():
    """
    Pseudocode:
    - Continuously accept user input in a loop
    - Handle commands like fail_link, fix_link, fail_Node, etc.
    """
    while not stop_event.is_set():
        user_input = input() # Input message from the user
        if user_input.lower() == 'exit':
            stop_event.set()
            for soc in socket_info[1]:
                if soc != None:
                    soc.close()
            break
        elif user_input.startswith("failLink"):
            fail_link(user_input)
        elif user_input.startswith("fixLink"):
            fix_link(user_input)
        elif user_input.startswith("failNode"):
            fail_node(user_input)
        else:
            print(f"UNCRECOGNIZED INPUT {user_input}")

# Fail a link between two servers
def fail_link(user_message):
    """
    Pseudocode:
    - Find the tuple for src and dest in socket_info[2]
    - Set the link status to 0 for both directions
    """
    print("TODO")

# Fix a link between two servers
def fix_link(user_message):
    """
    Pseudocode:
    - Find the tuple for src and dest in socket_info[2]
    - Set the link status to 1 for both directions
    """
    print("TODO")

# Fail a node
def fail_node(user_message):
    """
    Pseudocode:
    - Set socket associated with node_num to None in socket_info[1]
    - Set all links to/from the node to 0 (inactive) in socket_info[2]
    """
    print("TODO")

# Start the server and listen for connections
def run_server():
    """
    Dakota
    Pseudocode:
    - Setup server and port
    - While server is running:
        - Accept incoming connections
        - Assign a socket number and store it
        - Send server initialization confirmation
    """
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Create a TCP socket
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', NETWORK_SERVER_PORT))  # Bind to all interfaces
    server.listen(5) # Start listening for connections
    server.settimeout(1)  # Set a timeout of 1 second for accepting connections
    print(f"Server started on port {NETWORK_SERVER_PORT}")

    count = 0
    while not stop_event.is_set():
        try:
            server_socket, addr = server.accept() # Accept client connections
            
            socket_info[1][count] = server_socket

            count +=1

            print(f"Accepted connection from {addr} as Server {count}")

            # Create a new thread
            server_handler = threading.Thread(target=get_server_message,args=(server_socket,))
            server_handler.start() # Start the new thread            
           
        except socket.timeout:
            #Timeout enabled so that will be nonblocking
            continue

# Handle incoming server messages
def get_server_message(server):
    """
    Dakota
    Pseudocode:
    - Wait for server messages
    - Process messages based on their content
    """

# Forward messages to appropriate destinations
def forward_server_message(message):
    """
    Dakota
    Pseudocode:
    - Check destination server status
    - If dest_server == -1, forward to all except origin_server
    - Otherwise, forward to the specified destination
    """

# Check the status of links and nodes
def check_status():
    """
    Pseudocode:
    - Periodically check link and node statuses
    - Print or log any changes in status
    """

# Main function to run the server
def main():
    """
    Pseudocode:
    - Setup socket information
    - Start server and user input threads
    """

if __name__ == "__main__":
    print("Network Server")
    setup_socket_info()
    threading.Thread(target=run_server).start()
    threading.Thread(target=get_user_input).start()

    while not stop_event.is_set():
        time.sleep(0.5)

    sys.stdout.flush()
    sys.exit(0)