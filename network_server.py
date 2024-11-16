# network_server.py

from shared import message
from key_value import KeyValue

# Global Variables
global server_running
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

# Fail a link between two servers
def fail_link(src, dest):
    """
    Pseudocode:
    - Find the tuple for src and dest in socket_info[2]
    - Set the link status to 0 for both directions
    """

# Fix a link between two servers
def fix_link(src, dest):
    """
    Pseudocode:
    - Find the tuple for src and dest in socket_info[2]
    - Set the link status to 1 for both directions
    """

# Fail a node
def fail_Node(node_num):
    """
    Pseudocode:
    - Set socket associated with node_num to None in socket_info[1]
    - Set all links to/from the node to 0 (inactive) in socket_info[2]
    """

# Start the server and listen for connections
def start_server():
    """
    Pseudocode:
    - Setup server and port
    - While server is running:
        - Accept incoming connections
        - Assign a socket number and store it
        - Send server initialization confirmation
    """

# Handle incoming server messages
def get_server_message():
    """
    Pseudocode:
    - Wait for server messages
    - Process messages based on their content
    """

# Forward messages to appropriate destinations
def forward_server_message(message):
    """
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