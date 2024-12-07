# network_server.py

import sys
import time
import socket
import json
from shared import message, NETWORK_SERVER_PORT, MAX_SERVER_NUM
import threading



# Global Variables
global server_running
stop_event = threading.Event()
lock = threading.Lock()

socket_info = [
    [None, None, None],  # Sockets (initially null)
    [
        #Link status [Sending][Receiving]
        [1, 1, 1],  # Status of links from server 1
        [1, 1, 1],  # Status of links from server 2
        [1, 1, 1],  # Status of links from server 3
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
            for soc in socket_info[0]:
                if soc != None:
                    soc.close()
            break
        elif user_input.startswith("failLink"):
            fail_link(user_input)
        elif user_input.startswith("fixLink"):
            fix_link(user_input)
        elif user_input.startswith("failNode"):
            fail_node(user_input)
        elif user_input.startswith("status"):
            print_socket_status()
        else:
            print(f"UNCRECOGNIZED INPUT {user_input}")

# Fail a link between two servers
def fail_link(user_message):
    """
    Pseudocode:
    - Find the tuple for src and dest in socket_info[1]
    - Set the link status to 0 for both directions
    """
    valid, result = decode_link_user_message(user_message)
    if not valid:
        print(f"Error: {result}")
        return
    
    #Set Link To False
    socket_info[1][result[0]][result[1]] = 0
    print(f"Failed Link src={result[0]}, dest={result[1]}")

# Fix a link between two servers
def fix_link(user_message):
    """
    Pseudocode:
    - Find the tuple for src and dest in socket_info[1]
    - Set the link status to 1 for both directions
    """
    valid, result = decode_link_user_message(user_message)
    if not valid:
        print(f"Error: {result}")
        return
    
    #Set Link To True
    socket_info[1][result[0]][result[1]] = 1
    print(f"Fixed Link src={result[0]}, dest={result[1]}")

def print_socket_status():
    print("Sockets:")
    # Print socket information
    for i, soc in enumerate(socket_info[0], start=1):
        status = "None" if soc is None else str(soc)
        print(f"  Socket {i-1}: {status}")
    
    print("\nLink Status Matrix:")
    # Print the link status matrix
    matrix = socket_info[1]
    print("    " + " ".join(f"S{i}" for i in range(len(matrix))))  # Header row
    for i, row in enumerate(matrix):
        row_status = "  ".join(str(status) for status in row)
        print(f"S{i}: {row_status}")


def decode_link_user_message(user_message):
    """
    Helper message to deconde link
    """
    # Split the message into parts
    parts = user_message.split()
    
    # Validate message format
    if len(parts) != 3:
        return False, "Invalid message format. Use: failLink <src> <dest>"
    
    try:
        # Parse src and dest as integers
        src = int(parts[1])
        dest = int(parts[2])
    except ValueError:
        return False, "Source and destination must be integers."
    
    # Validate src and dest
    if src == dest:
        return False, "Source and destination cannot be the same."
    if not (0 <= src <= MAX_SERVER_NUM and 0 <= dest <= MAX_SERVER_NUM):
        return False, f"Source and destination must be between 0 and {MAX_SERVER_NUM}."
    
    return True, (src, dest)
    

# Fail a node
def fail_node(user_message):
    """
    Pseudocode:
    - Set socket associated with node_num to None in socket_info[0]
    - Set all links to/from the node to 0 (inactive) in socket_info[1]
    """
    _, dest_server = user_message.split()

    message_data = {
        "dest_server": int(dest_server),
        "sending_server": -1,
        "message_type": message.SERVER_KILL.value,
    }
    
    server_message = json.dumps(message_data)
    forward_server_message(server_message)
    
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

    while not stop_event.is_set():
        try:
            
            server_socket, addr = server.accept() # Accept client connections

            #Add connected socket to first available socket in socket_info
            for count, soc in enumerate(socket_info[0]):
                if soc is None:
                    # Add socket to socket_info at the correct index
                    socket_info[0][count] = server_socket
                    print(f"Accepted connection from {addr} as Server {count}")
                    #Sleep to enable server to setup message_handling
                    time.sleep(0.1)
                    
                    #Send Server Server_Init message with ServerNum
                    message_data = {
                        "dest_server": -1,
                        "sending_server": -1,
                        "message_type": message.SERVER_INIT.value,
                        "args": {
                            "server_num": count
                        }
                    }
                    
                    # Serialize to JSON
                    serialized_message = json.dumps(message_data)
                    server_socket.send(serialized_message.encode('utf-8'))  # Convert JSON string to bytes

                    break

            # Create a new thread
            server_handler = threading.Thread(target=get_server_message,args=(server_socket,))
            server_handler.start() # Start the new thread            
           
        except socket.timeout:
            #Timeout enabled so that will be nonblocking
            continue

# Handle incoming server messages
# def get_server_message(server):
#     """
#     Dakota
#     Pseudocode:
#     - Wait for server messages
#     - Process messages based on their content
#     """
#     while not stop_event.is_set():
#         try:
#             server_message = server.recv(1024).decode('utf-8') #Receive server response
#             if not server_message:
#                 print("Server Disconnected")
#                 break
#             threading.Thread(target=forward_server_message, args=(server_message,)).start()
#         except socket.error:
#             continue

def get_server_message(server):
    """
    Continuously receive and buffer messages from a server.
    Ensure fragmented messages are reassembled before processing.
    """
    buffer = ""  # Buffer to store incomplete messages

    while not stop_event.is_set():
        try:
            # Receive data in chunks
            data = server.recv(1024).decode('utf-8')
            if not data:
                raise socket.error()
            
            buffer += data  # Append received data to the buffer

            while True:
                try:
                    # Attempt to parse a complete JSON object
                    message_data, end_idx = json.JSONDecoder().raw_decode(buffer)
                    buffer = buffer[end_idx:].strip()  # Remove processed message from buffer

                    # Process the complete message in a separate thread
                    threading.Thread(target=forward_server_message, args=(json.dumps(message_data),)).start()
                except json.JSONDecodeError:
                    # If parsing fails, wait for more data
                    break

        except socket.error:
            print("Server Disconnected")
            break
            #continue



# Forward messages to appropriate destinations
def forward_server_message(server_message):
    """
    Dakota
    Pseudocode:
    - Check destination server status
    - If dest_server == -1, forward to all except origin_server
    - Otherwise, forward to the specified destination
    Message format <destination server> <rest of message>
    """
    #Required Interval Between Message Passing
    time.sleep(1)
    try:
        #Lock to protect prints and sending messages
        with lock:
            #Get Json Datastructure from message
            message_data = json.loads(server_message)

            #Determine destination server number from message_data
            dest_server_num = message_data["dest_server"]
            sending_server = message_data["sending_server"]
            message_type = message_data["message_type"]
            
            #if server number is -1 send message to all except sender
            if dest_server_num == -1:
                for count, soc in enumerate(socket_info[0]):
                    if count != sending_server and check_forward_connection(soc, sending_server, count, message_type):
                        soc.send(server_message.encode('utf-8'))
                
            #else send to specific server_num
            else:
                #Get socket from socket_info and server_num
                dest_server = socket_info[0][dest_server_num]
                if check_forward_connection(dest_server, sending_server, dest_server_num, message_type):
                    dest_server.send(server_message.encode('utf-8'))

            #If sending Kill message close connection to server
            if message_type is message.SERVER_KILL.value:
                #print(f"Failed Node {dest_server_num}")
                socket_info[0][dest_server_num].close()
                socket_info[0][dest_server_num] = None

    except Exception as e:
        # Print the error along with the message that caused it
        print(f"FAILED FORWARDING MESSAGE: {server_message}")
        print(f"ERROR: {e}")

def check_forward_connection(dest_soc, src, dest, message_type):
    if dest_soc is None:
        print(f"Broken Node {src} to {dest} for {message(message_type)}")
        return False
    #Check if Link is down
    elif socket_info[1][src][dest] == 0:
        print(f"Broken Link {src} to {dest} for {message(message_type)}")
        return False
    #Forward Message
    else:
        print(f"Forwarding From Server {src} to Server {dest}: {message(message_type)}")
        #print(f"Forwarding From Server {src} to Server {'ALL' if dest_server_num == -1 else dest_server_num}: {message(message_type)}")

        return True

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