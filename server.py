# server.py

import socket
import time
import sys
import threading
import os
import json
import select
import google.generativeai as genai
from dotenv import load_dotenv
from queue import Queue
from shared import message, NETWORK_SERVER_PORT, MAX_SERVER_NUM, DELAY, TIMEOUT_TIME

from key_value import KeyValue


keyValue = KeyValue()
networkServer = None
stop_event = threading.Event()
SERVER_NUM = -1

# Consensus Variables
leader = -1

# Represent the maxmimum known ballot by this server
ballot_number = {
    'seq_num': 0,
    'pid': -1,
    'op_num': 0
}

# Server's last accepted value (or leader's current command)
accept_val = -1

# Ballot of server's last accepted value (leader's current ballot)
accept_num = -1

#Used for operations
pending_operations = Queue()
num_leader_promises = 0
num_consensus_accepted = 0
leader_ack = 0

#Used for Storing responses format = {tuple(context_id, query), list(responses)}
response_dict = {}




# ------  SERVER  ------
def connect_server():
    """
    Dakota
    Connect to server.
    Receive initial message from server (expecting SERVER_INIT <num>).
    Parse message to retrieve server number and assign to SERVER_NUM.
    Start listening for incoming messages by calling get_server_message().
    TODO: Implement a method to restore context/kv data in case of a crash.
    """
    global networkServer

    attempt = 0
    max_retries = 5
    interval = 0.5
    while attempt < max_retries:
        try:
            #Connect to the Network Server
            networkServer = socket.socket(socket.AF_INET,socket.SOCK_STREAM)  # Create a TCP socket
            networkServer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            networkServer.connect(('127.0.0.1', NETWORK_SERVER_PORT)) # Connect to the server at localhost on port
            
            print(f"Connected To Network Server on {NETWORK_SERVER_PORT}")
            threading.Thread(target=get_server_message).start()
            break
        except (TimeoutError, ConnectionRefusedError):
            attempt += 1
            if attempt < max_retries:
                time.sleep(interval)
            else:
                print(f"FAILED To Connect to Network Server on {NETWORK_SERVER_PORT}")
                break
    

# def send_server_message(message_type, dest_server, message_args=None):
#     """
#     Dakota
#     Send a message to the specified server with a given message type and arguments.
#     Format message as <destination_server> <SERVER_NUM> <message_type> <args>.
#     Use networkServer to send the formatted message.
#     """

#     #Create uniform message datastructure
#     message_data = {
#         "dest_server": dest_server,
#         "sending_server": SERVER_NUM,
#         "message_type": message_type.value,
#         "args": message_args or {}  # Embed existing message_args here
#     }

#     #Serialize and send message
#     serialized_message = json.dumps(message_data)
#     networkServer.send(serialized_message.encode('utf-8'))  # Convert JSON string to bytes
    
#     print(f"Sending {message_type} to server {dest_server}")

def send_server_message(message_type, dest_server, message_args=None):
    """
    Dakota
    Send a message to the specified server with a given message type and arguments.
    Format message as <destination_server> <SERVER_NUM> <message_type> <args>.
    Use networkServer to send the formatted message.
    """
    # Create uniform message datastructure
    message_data = {
        "dest_server": dest_server,
        "sending_server": SERVER_NUM,
        "message_type": message_type.value,
        "args": message_args or {}  # Embed existing message_args here
    }

    # Serialize and send message
    serialized_message = json.dumps(message_data)
    networkServer.send(serialized_message.encode('utf-8'))  # Convert JSON string to bytes

    if message_type == message.LLM_RESPONSE:
        return  # Skip further processing for this message

    # Extract the simple name from message_type (remove any prefix like "message.")
    simple_message_type = str(message_type).split(".")[-1]

    # Add formatted ballot to the print message if present
    ballot_string = ""
    if message_args and "ballot_number" in message_args:
        ballot_string = ballot_to_string(message_args["ballot_number"])

    # Add accept_val to the print message if present
    accept_val_string = ""
    if message_args and "accept_val" in message_args:
        accept_val = message_args["accept_val"]
        accept_val_string = f"{accept_val}" if accept_val != -1 else "Bottom Bottom"
    
        # Make sure sending server isn't printed for query message
        if accept_val != -1 and accept_val.startswith("query") and "." in accept_val:
            accept_val_string = accept_val_string.split(".", 1)[0]
        else:
            accept_val_string = accept_val_string

    # Format the destination for the print message
    dest_message = "to ALL" if dest_server == -1 else f"to Server {dest_server}"

    # Format and print the message
    print(
        f"Sending {simple_message_type}{f' {ballot_string}' if ballot_string else ''}{f' {accept_val_string}' if accept_val_string else ''} {dest_message}"
    )




def get_server_message():
    """
    Continuously receive messages from other servers or clients.
    Reassemble fragmented messages using a buffer and parse them when complete.
    Based on message type, call the appropriate server function.
    Example: if message_type == "NEW_CONTEXT", call server_new_context().
    """
    buffer = ""  # Buffer to store partial messages

    while not stop_event.is_set():
        try:
            # Receive data from the socket in chunks
            data = networkServer.recv(1024).decode('utf-8')
            if not data:
                print("Server Disconnected")
                break

            buffer += data  # Append received data to the buffer

            while True:
                try:
                    # Attempt to parse a complete JSON object from the buffer
                    message_data, end_idx = json.JSONDecoder().raw_decode(buffer)
                    buffer = buffer[end_idx:].strip()  # Remove the processed message from the buffer

                    # Extract message type and details
                    message_type = message(message_data["message_type"])
                    sending_server = message_data["sending_server"]
                    args = message_data.get("args", {})

                    # Special handling for LLM_RESPONSE: no printing
                    if message_type == message.LLM_RESPONSE:
                        server_llm_response(message_data)
                        continue  # Skip further processing for this message

                    # Extract ballot info if present
                    ballot_string = ""
                    if "ballot_number" in args:
                        ballot_string = ballot_to_string(args["ballot_number"])

                    # Extract accept_val if present
                    accept_val_string = ""
                    if "accept_val" in args:
                        accept_val = args["accept_val"]
                        accept_val_string = f"{accept_val}" if accept_val != -1 else "Bottom Bottom"

                        # Make sure sending server isn't printed for query message
                        if accept_val != -1 and accept_val.startswith("query") and "." in accept_val:
                            accept_val_string = accept_val_string.split(".", 1)[0]

                    # Extract user_message if present
                    user_message = args.get("user_message", "")

                    if user_message and user_message.startswith("query") and "." in user_message:
                            user_message = user_message.split(".", 1)[0]

                    # Format the sending server name
                    sending_server_name = "Network Server" if sending_server == -1 else f"Server {sending_server}"

                    # Format the message and print it
                    simple_message_type = str(message_type).split(".")[-1]  # Extract simple name
                    print(
                        f"Received {simple_message_type}"
                        f"{f' {ballot_string}' if ballot_string else ''}"
                        f"{f' {accept_val_string}' if accept_val_string else ''}"
                        f"{f' {user_message}' if user_message else ''} from {sending_server_name}"
                    )

                    # Call the appropriate function based on message type
                    if message_type == message.SERVER_INIT:
                        server_init_message(message_data)
                    elif message_type == message.SERVER_KILL:
                        server_kill_message()
                    #elif message_type == message.NEW_CONTEXT:
                    #    server_new_context(message_data)
                    #elif message_type == message.CREATE_QUERY:
                    #    server_create_query(message_data)
                    elif message_type == message.PREPARE:
                        server_leader_prepare_message(message_data)
                    elif message_type == message.PROMISE:
                        server_leader_promise_message(message_data)
                    elif message_type == message.LEADER_FORWARD:
                        server_leader_forward_message(message_data)
                    elif message_type == message.LEADER_ACK:
                        server_leader_ack_message(message_data)
                    elif message_type == message.ACCEPT:
                        server_consensus_accept_message(message_data)
                    elif message_type == message.ACCEPTED:
                        server_consensus_accepted_message(message_data)
                    elif message_type == message.DECIDE:
                        server_consensus_decide_message(message_data)
                    elif message_type == message.UPDATE_CONTEXT:
                        server_update_context(message_data)
                except json.JSONDecodeError:
                    # Incomplete JSON message; wait for more data
                    break

        except Exception as e:
            print(f"Exception Thrown Getting Server Message: {e}")
            continue
    networkServer.close()


def server_init_message(message_data):
    """
    Dakota
    Used to asign the server num when connected to the network server
    """
    global SERVER_NUM
    server_num = message_data["args"]["server_num"]
    SERVER_NUM = server_num
    ballot_number["pid"] = server_num

    print(f"Assigned Server Number {SERVER_NUM}")

def server_kill_message():
    """
    Dakota
    Used to asign the server num when connected to the network server
    """
    stop_event.set()


def server_new_context(user_message):
    """
    Nik
    Create a new context using the keyValue object (kv).
    Call kv.create_context() to initialize the context.
    """
    try:
        # Extract the context ID from the received message data
        context_id = user_message.replace("create", "").strip()

        if not context_id:
            print("Error Getting Context_id")
            return
        
        if context_id in keyValue.data:
            print(f"Error: Context ID '{context_id}' already exists. Please use a unique ID.")
            return

        # Create the new context using the keyValue object
        keyValue.create_context(context_id)
        # : Server: Context created successfully on this server.")
        print(f"NEW_CONTEXT {context_id}")

    except Exception as e:
        print(f"Error occurred while processing NEW_CONTEXT: {e}")

def server_create_query(message_data):
    """
    Nik
    Create a query in the specified context.
    Call kv.create_query() to add the query.
    Generate a response by calling query_gemini().
    Send response back to the calling server using send_server_message().
    """
    try:
        # Extract context ID and query string from the message data
        args = message_data.get("args", {})
        user_message, request_server = args.get("accept_val").split(".", 1)
        request_server = int(request_server)

        parts = user_message.split(" ", 2)  # Split into 'query', '<context_id>', and '<query_string>'
        if len(parts) != 3 or parts[0] != "query":
            print("Error: Invalid input format. Use 'query <context_id> <query_string>'")
            return

        context_id, query_string = parts[1].strip(), parts[2].strip()

        if not context_id or not query_string:
            print("Error: Context ID and query cannot be empty.")
            return
        
        # Step 1: Add the query to the specified context
        keyValue.create_query(context_id, query_string)
        # print(f"DEBUG: Server: Query added to context '{context_id}': {query_string}")

        # Step 2: Retrieve the context as a string
        context_string = keyValue.view(context_id)

        if not context_string:
            print(f"Error: Context '{context_id}' not found.")
            return
        
        # Check if the context exists in KeyValue
        if context_id not in keyValue.data:
            print(f"Error: Context ID '{context_id}' does not exist. Please create the context first.")
            return
        
        # Print updated context with query
        print(f"NEW_QUERY on {context_id} with {context_string}")

        # Step 3: Generate a response by querying Gemini
        prompt_answer = ""
        response = query_gemini(context_string + "\n" + prompt_answer)
        if request_server == SERVER_NUM:
            save_response_to_dict(context_id, response)


        # Step 4: Send the response back to the calling server
        response_message = {
            "context_id": context_id,
            "query_string": query_string,
            "response": response
        }
        
        if request_server == SERVER_NUM:
            # print(response)
            pass
        else:
            send_server_message(message.LLM_RESPONSE, request_server, response_message)

    except Exception as e:
        print(f"Error occurred while processing CREATE_QUERY: {e}")

def server_llm_response(message_data):
    """
    Add the received LLM response to the llm_responses collection.
    Print the response for server-side logging.
    """
    
    args = message_data.get("args", {})
    response = args.get("response")
    context_id = args.get("context_id")
    
    #Add responses to datastructure
    save_response_to_dict(context_id, response)
    
def save_response_to_dict(context_id, response):
    """
    Helper Function To Add Response to response_dict
    """
    #Create List if needed
    if (context_id) not in response_dict:
        response_dict[(context_id)] = []
    
    #Get The Candidate Num
    candidate_num = len(response_dict[context_id])

    #Add to response dict and print
    response_dict[context_id].append(response)
    print(f"Context '{context_id}' - Candidate {candidate_num}: {response}")


def server_choose_response(message_data):
    """
    Save the selected answer to the keyValue storage.
    Call kv.save_answer() to persist the answer.
    Send confirmation back to calling server(s) if needed.
    """
    args = message_data.get("args", {})
    user_message= args.get("accept_val")


    parts = user_message.split(" ", 2)  # Split into 'choose', '<context_id>', and '<response_string>'
    if len(parts) != 3 or parts[0] != "choose":
        print("Error: Invalid input format. Use 'choose <context_id> <response>'")
        return

    context_id, response = parts[1].strip(), parts[2].strip()

    if not context_id or not response:
        print("Error: Context ID and query cannot be empty.")
        return

    keyValue.save_answer(context_id, response)

    print(f"CHOSEN ANSWER on {context_id} with {response}")
    


# ------  USER  ------
def get_user_input():
    """
    Dakota
    Take input from the user and call appropriate functions based on input type.
    Example: if user requests a new context, call user_new_context().
    """
    while not stop_event.is_set():
        #user_input = input() # Input message from the user
        if select.select([sys.stdin], [], [], 0.5)[0]:  # Check for input with a timeout
            user_input = sys.stdin.readline().strip()
        else:
            continue
        if user_input.lower() == 'exit':
            stop_event.set()
            if networkServer != None:
                networkServer.close()
            break
        elif user_input.startswith("create"):
            user_new_context(user_input)
        elif user_input.startswith("query"):
            user_input_with_server = f"{user_input}.{SERVER_NUM}"
            user_create_query(user_input_with_server)
        elif user_input.startswith("choose"):
            user_select_answer(user_input)
        elif user_input.startswith("viewall"):
            user_view_all_context()
        elif user_input.startswith("view"):
            user_view_context(user_input)
        else:
            print(f"UNCRECOGNIZED INPUT {user_input}")

def user_new_context(user_message):
    """
    Nik
    Process request to create a new context.
    Call get_consensus() to get agreement from all servers.
    Send message NEW_CONTEXT to all servers via send_server_message().
    Call kv.create_context() to create the context locally.
    """
    # Extract context ID from the user message
    context_id = user_message.replace("create", "").strip()

    if not context_id:
        print("Error: Context ID cannot be empty.")
        return
    

    # Step 1: Get consensus from all servers
    get_consensus(user_message)
    # if not consensus:
    #     print("Consensus failed. Unable to create new context.")
    #     return

    # Step 2: Send NEW_CONTEXT message to all servers (MODIFY TO SEND JSON)
    # Structure the message arguments as JSON
    #message_args = {
    #    "context_id": context_id
    #}

    # Send the message using send_server_message
    #send_server_message(message.NEW_CONTEXT, -1, message_args)

    # Step 3: Create context locally
    #keyValue.create_context(context_id)
    #print(f"New context '{context_id}' created successfully.")

def user_create_query(user_message):
    """
    Nik
    Process request to create a query within an existing context.
    Call get_consensus() for server consensus.
    Send CREATE_QUERY message to all servers via send_server_message().
    Call kv.create_query() locally to create query.
    Obtain response from query_gemini() and add to llm_responses collection.
    Print the response for user.
    """

    # Extract context ID and query string from the user message
    parts = user_message.split(" ", 2)  # Split into 'query', '<context_id>', and '<query_string>'
    if len(parts) != 3 or parts[0] != "query":
        print("Error: Invalid input format. Use 'query <context_id> <query_string>'")
        return

    context_id, query_string = parts[1].strip(), parts[2].strip()


    if not context_id or not query_string:
        print("Error: Context ID and query cannot be empty.")
        return
    
    
    # Clear responses only for the given context_id
    global response_dict
    if context_id in response_dict:
        response_dict[context_id].clear()
    

    # Step 1: Get consensus from all servers
    get_consensus(user_message)
    # if not consensus:
    #     print("Consensus failed. Unable to create new query.")
    #     return

    # Step 2: Send CREATE_QUERY message to all servers (MODIFY TO SEND JSON)
    #message_args = {
    #    "context_id": context_id,
    #     "query_string": query_string
    # }
    # send_server_message(message.CREATE_QUERY, -1, message_args)

    # # Step 3: Create query locally
    # keyValue.create_query(context_id, query_string)

    # # Step 4: Retrieve the context as a string
    # context_string = keyValue.view(context_id)
    # if not context_string:
    #     print(f"Error: Context '{context_id}' not found.")
    #     return

    # # Step 5: Query Gemini
    # prompt_answer = "Answer: "
    # response = query_gemini(context_string + "\n" + prompt_answer)

    # # Step 6: Add the response to local KeyValue storage
    # keyValue.save_answer(context_id, response)

    # # Step 7: Print the response
    # print(f"LLM Response: {response}")

def user_select_answer(user_message):
    """
    Allow user to select an answer from llm_responses using index or identifier.
    Retrieve the selected response from llm_responses.
    Call get_consensus() for server agreement.
    Send SAVE_ANSWER message to all servers via send_server_message().
    Call kv.save_answer() locally to save the chosen answer.
    """
    #Take user_message format 'choose <context_id> <response_number>' and make sure valid and get variables
    parts = user_message.split()

    # Check if the message has the correct format (i.e., 'choose <context_id> <response_number>')
    if len(parts) != 3:
        print("Invalid choose format: must be 'choose context_id response_number")
        return
    try:
        # Extract and convert context_id and response_number to integers
        context_id = parts[1]
        response_number = int(parts[2])

        #Check if context_id in saved answers
        if context_id not in response_dict:
            print(f"Context_id {context_id} not in saved response_dict")
            return

        #Check if valid Response Number
        if response_number < 0 and response_number < len(response_dict[context_id]):
            print(f"Invalide Response Number {response_number}")
            return
        
    except ValueError:
        print("Invalid format. context_id and response_number must be integers.")
    
    #Make have message include selected response
    new_user_message = f"choose {context_id} {response_dict[context_id][response_number]}"
    get_consensus(new_user_message)

def user_view_context(user_message):
    """
    Retrieve and display the data for a specified context.
    Use keyValue.view(context_id) to fetch context details.
    Args:
        user_message (str): The context ID provided by the user.
    """
    # Extract the context ID from the user message
    context_id = user_message.replace("view", "").strip()
    context_data = keyValue.view(context_id)  # Call the KeyValue store's view method

    if not context_data:
        print(f"Context '{context_id}' not found or context is empty.")
        return

    # Print the formatted context data with quotation marks and context ID
    print(f"{context_id} = \"\"\"\n{context_data}\n\"\"\"")

def user_view_all_context():
    """
    Retrieve and display all contexts.
    Use keyValue.view_all() to list all contexts.
    """
    all_contexts = keyValue.view_all()  # Call the KeyValue store's view_all method

    if not all_contexts:
        print("No contexts available.")
        return

    # Format all context data for display
    formatted_output = []
    for context_id, context_data in all_contexts.items():
        formatted_output.append(f"{context_id} = \"\"\"")
        for item in context_data:
            formatted_output.append(f"Query: {item['query']}\nAnswer: {item['answer']}")
        formatted_output.append("\"\"\"")

    print("\n".join(formatted_output))

# ------  CONSENSUS  ------
    
def ballot_to_string(ballot_number):
    """
    Converts a ballot dictionary into a string representation.
    
    Args:
        ballot_number (dict): A dictionary with keys 'seq_num', 'pid', and 'op_num'.
    
    Returns:
        str: The string representation of the ballot in the format "<seq_num, pid, op_num>".
    """
    return f"<{ballot_number['seq_num']}, {ballot_number['pid']}, {ballot_number['op_num']}>" 

    
# --- Election Phase ---
def leader_init():
    
    # print("DEBUG: Leader init")
    if leader == -1:
        start_leader_election()

def start_leader_election():

    # print("DEBUG: Starting Election")
    global num_leader_promises, ballot_number, leader, accept_num, accept_val
    
    num_leader_promises = 0
    
    # Update currently known ballot with your PID to create new ballot
    ballot_number["seq_num"] += 1
    ballot_number["pid"] = SERVER_NUM
    message_args = {
        "ballot_number": ballot_number,
    }
    send_server_message(message.PREPARE, -1, message_args)

    # Wait for all servers to respond with a timeout
    start_time = time.time()  # Record the start time
    while num_leader_promises < MAX_SERVER_NUM - 2:
        time.sleep(0.1)
        if time.time() - start_time > (TIMEOUT_TIME):  # Check if TIMEOUT seconds have elapsed
            print("TIMEOUT: Leader promises not received. Running leader election again.")

            # Restart leader election
            leader_init()
            return

    
    leader = SERVER_NUM
    threading.Thread(target=run_leader).start()

def server_leader_prepare_message(message_data):
    """
    Handle recieving a prepare message from server who wants to be leader
    """

    # Extract context ID and query string from the message data
    global ballot_number
    global accept_val
    global accept_num
    global leader
    args = message_data.get("args", {})
    ballot = args.get("ballot_number")
    sending_server = message_data.get("sending_server")

    # Handle case that non-leader failed and is trying to get context
    if leader == SERVER_NUM:
        message_args = {
            # TODO: Is KeyValue the best way to send all of the context?
            "context": keyValue.to_dict(),  # Serialize the KeyValue object
            "op_num": ballot_number["op_num"],
            "leader": leader
        }
        send_server_message(message.UPDATE_CONTEXT, sending_server, message_args)



    # Return Promise if message seq_num greater than local seq_num, and set local seq_num to new value
    elif ballot["seq_num"] > ballot_number["seq_num"] or (ballot["seq_num"] == ballot_number["seq_num"] and ballot["pid"] == ballot_number["pid"]) or (ballot["seq_num"] == ballot_number["seq_num"] and ballot["pid"] > ballot_number["pid"]):
        # If proposer's op_num is lower, send update their context will up-to-date operations
        if ballot["op_num"] < ballot_number["op_num"]:
            message_args = {
                # TODO: Is KeyValue the best way to send all of the context?
                "context": keyValue.to_dict(),  # Serialize the KeyValue object
                "op_num": ballot_number["op_num"],
                "leader": leader
            }
            send_server_message(message.UPDATE_CONTEXT, sending_server, message_args)

        else:
            # Set maximum known ballot to recieved ballot

            # Set a help flag if acceptor has a lower number of operations completed than leader
            help_needed = ballot["op_num"] > ballot_number["op_num"]
        
            
            ballot_number = ballot
            
            message_args = {
                "ballot_number": ballot_number,
                "accept_val": accept_val,
                "accept_num": accept_num,
                "help": help_needed
            }
            
            # Send a promise to proposer with this server's ballot
            send_server_message(message.PROMISE, sending_server, message_args)



      
def server_update_context(message_data):
    """
    Function called when a server trying to be leader recieves
    UPDATE_CONTEXT because their op_num is lagging behind.
    Replaces its key-value with the sending server's and updates
    op_num.
    """
    global keyValue
    global ballot_number
    global leader
    args = message_data.get("args", {})

    if(args["leader"] != SERVER_NUM):
        leader = args["leader"]

    # Update context and op_num
    ballot_number["op_num"] = args.get("op_num")
    received_data = args.get("context")

    if received_data:
        keyValue = KeyValue.from_dict(received_data)  # Rebuild KeyValue object


    # Restart leader election 
    #TODO: maybe call leader_init instead??
    # start_leader_election()


def server_leader_promise_message(message_data):
    """
    Handle recieving a promise message from a server after sending a prepare.
    Compare their accept_num to yours. If their's is not -1 and is bigger than yours,
    set your accept_val to their accept_val.
    """
    global accept_val
    global accept_num
    args = message_data.get("args", {})
    received_accept_num = args.get("accept_num")
    received_accept_val = args.get("accept_val")

    # Handle case that an acceptor is behind in number of operation by sending them an update context message
    if args.get("help"): 
        message_args = {
                "context": keyValue.to_dict(),  # Serialize the KeyValue object
                "op_num": ballot_number["op_num"],
                "leader": leader
        }
        send_server_message(message.UPDATE_CONTEXT, message_data.get("sending_server"), message_args)
        
    time.sleep(.2)

    if received_accept_num != -1:
        if accept_num == -1:
            accept_num = received_accept_num
            accept_val = received_accept_val
        elif accept_num != -1 and received_accept_num > accept_num:
            accept_num = received_accept_num
            accept_val = received_accept_val

    global num_leader_promises
    num_leader_promises += 1


    # --- Decision Phase ---
# def insert_operation_to_queue(user_message, ballot):

#     #Insert message and ballot to queue
#     pending_operations.put((user_message, ballot))

def insert_operation_to_queue(user_message):

    #Insert message to queue
    pending_operations.put((user_message))

def get_consensus(user_message):
    """
    Implement a method to achieve consensus among servers.
    Communicate with all servers to confirm action or context creation.
    Return consensus result to calling function.
    """
    global leader
    leader_init()

    #If leader add operation to operation queue
    if leader == SERVER_NUM:
        insert_operation_to_queue(user_message)
    #If not send message to leader to do so
    else:
        global leader_ack
        leader_ack = 0
        message_args = {
            "user_message": user_message,
        }
        send_server_message(message.LEADER_FORWARD, leader, message_args)

        #Check To Make Sure Leader Forward Has been Received
        time.sleep(TIMEOUT_TIME)
        if leader_ack == 0:
            print(f"TIMEOUT: Leader Acknowledge Not Received from {leader} for message: {user_message}")
            
            # Assume leader failed, set leader to none
            leader = -1

            # Rerun get consensus with no known leader 
            get_consensus(user_message)
        

def run_leader():

    global num_consensus_accepted
    global accept_val
    global accept_num
    global leader

    while not stop_event.is_set():
        if not pending_operations.empty():

            if accept_val == -1:
                #Pop the next operation
                user_message = pending_operations.get()
                accept_val = user_message

            # Use leader's ballot_number and accept_val
            accept_message_args = {
                "ballot_number": ballot_number,
                "accept_val": accept_val,
            }
            #Send Accept? message to all servers with message
            num_consensus_accepted = 0
            send_server_message(message.ACCEPT, -1, accept_message_args)

            # Wait for all servers to respond with a timeout
            start_time = time.time()  # Record the start time
            while num_consensus_accepted < MAX_SERVER_NUM - 2:
                time.sleep(0.1)
                if time.time() - start_time > (TIMEOUT_TIME):  # Check if TIMEOUT seconds have elapsed
                    print("TIMEOUT: Accepted messages not received, running new leader election again.")
                    leader = -1

                    # Restart leader election
                    leader_init()
                    return
                #If program gets told Kill message, exit gracefully
                if stop_event.is_set():
                    return
            

            #TODO Maybe: Remove from pending operations now??

            #TODO: Op num increment moved to before insertion

            #Broadcast consensus decide
            decide_message_args = {
                "accept_val": accept_val,
            }
            send_server_message(message.DECIDE, -1, decide_message_args)
            
            #Do Operation Locally (mimic message with minimum pieces needed)
            local_decide_message = {
                "args": decide_message_args,
            }
            server_consensus_decide_message(local_decide_message)


def server_leader_forward_message(message_data):
    """
    As the leader, insert recieved message into service queue
    """
    sending_server = message_data.get("sending_server")
    args = message_data.get("args", {})
    user_message = args.get("user_message")
    #ballot = args.get("ballot_number")

    # Don't respond if server doesn't know that it is leader
    if(SERVER_NUM == leader):
        insert_operation_to_queue(user_message) 
        send_server_message(message.LEADER_ACK, sending_server, args)

def server_leader_ack_message(message_data):
    global leader_ack
    leader_ack = 1

def server_consensus_accepted_message(message_data):
    args = message_data.get("args", {})
    
    # Handle case that an acceptor is behind in number of operation by sending them an update context message
    if args.get("help"): 
        message_args = {
                # TODO: Is KeyValue the best way to send all of the context?
                "context": keyValue.to_dict(),  # Serialize the KeyValue object
                "op_num": ballot_number["op_num"],
                "leader": leader
        }
        send_server_message(message.UPDATE_CONTEXT, message_data.get("sending_server"), message_args)
        
    time.sleep(.2)
    global num_consensus_accepted
    num_consensus_accepted += 1

def server_consensus_accept_message(message_data):
    
    global ballot_number
    global accept_val
    global accept_num
    args = message_data.get("args", {})
    ballot = args.get("ballot_number")
    sending_server = message_data.get("sending_server")
    
    # Return Accept if sender has higher ballot than own ballot
    if ballot["seq_num"] > ballot_number["seq_num"] or (ballot["seq_num"] == ballot_number["seq_num"] and ballot["pid"] == ballot_number["pid"]) or (ballot["seq_num"] == ballot_number["seq_num"] and ballot["pid"] > ballot_number["pid"]):
        
        # If proposer's op_num is lower, send own context to update their context with up-to-date operations
        if ballot["op_num"] < ballot_number["op_num"]:
            message_args = {
                # TODO: Is KeyValue the best way to send all of the context?
                "context": keyValue,
                "op_num": ballot_number["op_num"]
            }
            send_server_message(message.UPDATE_CONTEXT, sending_server, message_args)
            ballot_number["seq_num"] = ballot["seq_num"]

        
        # Send an accepted message to proposer otherwise
        else:
            # Server accepts value and logs it in case leader fails
            accept_val = args.get("accept_val")
            accept_num = ballot

            # Set a help flag if acceptor has a lower number of operations completed than leader
            help_needed = ballot["op_num"] > ballot_number["op_num"]
            
            message_args = {
                "ballot_number": ballot_number,
                "accept_val": accept_val,
                "help": help_needed
            }
            send_server_message(message.ACCEPTED, sending_server, message_args)
            
            # Set sending server to leader for future reference
            global leader
            leader = sending_server

            # Set maximum known ballot number to recieved ballot
            ballot_number = ballot


def server_consensus_decide_message(message_data):
    
    #Increment local ballot_number
    ballot_number["op_num"] += 1

    # Reset accept_val and accept_num
    global accept_val
    global accept_num
    accept_val = -1
    accept_num = -1

    args = message_data.get("args", {})
    user_message = args.get("accept_val")
    if user_message.startswith("create"):
        server_new_context(user_message)
    elif user_message.startswith("query"):
        server_create_query(message_data)
    elif user_message.startswith("choose"):
        server_choose_response(message_data)
    else:
        print(f"UNSUPPORTED SERVER CONSENSUS DECIDE MESSAGE: {user_message}")


# ------ GEMINI ------

def setup_gemini():
    # Load environment variables from .env file
    load_dotenv()

    # Configure the Gemini API using the loaded environment variable
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


def query_gemini(context, prompt_answer="Answer: "):
    """
    Query the Gemini LLM with a given context and prompt.
    Args:
        context (str): The context string to send to Gemini.
        prompt_answer (str): The prompt indicating where Gemini should generate a response.
    Returns:
        str: The generated response text from Gemini.
    """
    try:
        # Initialize the Gemini generative model
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        # Generate content using the context and prompt
        response = model.generate_content(context + prompt_answer)
        return response.text  # Return the generated text
    except Exception as e:
        print(f"Error querying Gemini: {e}")
        return "Error querying Gemini API"


if __name__ == "__main__":
    print("Server")
    connect_server()
    threading.Thread(target=get_user_input).start()
    
    while not stop_event.is_set():
        time.sleep(0.5)
        
    sys.stdout.flush()
    sys.exit(0)

    