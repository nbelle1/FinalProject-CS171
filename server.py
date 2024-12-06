# server.py

import socket
import time
import sys
import threading
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from queue import Queue
from shared import message, NETWORK_SERVER_PORT, MAX_SERVER_NUM

from key_value import KeyValue


keyValue = KeyValue()
networkServer = None
stop_event = threading.Event()
SERVER_NUM = -1

# Consensus Variables
leader = -1
ballot_number = {
    'seq_num': 0,
    'pid': -1,
    'op_num': 0
}
pending_operations = Queue()
num_leader_promises = 0
num_consensus_accepted = 0




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
    

def send_server_message(message_type, dest_server, message_args=None):
    """
    Dakota
    Send a message to the specified server with a given message type and arguments.
    Format message as <destination_server> <SERVER_NUM> <message_type> <args>.
    Use networkServer to send the formatted message.
    """

    #Create uniform message datastructure
    message_data = {
        "dest_server": dest_server,
        "sending_server": SERVER_NUM,
        "message_type": message_type.value,
        "args": message_args or {}  # Embed existing message_args here
    }

    #Serialize and send message
    serialized_message = json.dumps(message_data)
    networkServer.send(serialized_message.encode('utf-8'))  # Convert JSON string to bytes
    
    print(f"Sent {message_type} to server {dest_server}")



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

                    # Get message type and process it
                    message_type = message(message_data["message_type"])
                    print(f"Received {message_type}")

                    # Call the appropriate function based on message type
                    if message_type == message.SERVER_INIT:
                        server_init_message(message_data)
                    #elif message_type == message.NEW_CONTEXT:
                    #    server_new_context(message_data)
                    #elif message_type == message.CREATE_QUERY:
                    #    server_create_query(message_data)
                    elif message_type == message.LEADER_PREPARE:
                        server_leader_prepare_message(message_data)
                    elif message_type == message. LEADER_PROMISE:
                        server_leader_promise_message()
                    elif message_type == message.LEADER_ACCEPT:
                        server_leader_accept_message(message_data)
                    elif message_type == message.CONSENSUS_PROPOSE:
                        server_consensus_propose_message(message_data)
                    elif message_type == message.CONSENSUS_ACCEPT:
                        server_consensus_accept_message(message_data)
                    elif message_type == message.CONSENSUS_ACCEPTED:
                        server_consensus_accepted_message()
                    elif message_type == message.CONSENSUS_DECIDE:
                        server_consensus_decide_message(message_data)
                    elif message_type == message.LLM_RESPONSE:
                        server_llm_response(message_data)
                    elif message_type == message.SAVE_ANSWER:
                        server_save_answer(message_data)
                except json.JSONDecodeError:
                    # Incomplete JSON message; wait for more data
                    break

        except Exception as e:
            print(f"Exception Thrown Getting Server Message: {e}")
            continue
    print("TODO")


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

        # Create the new context using the keyValue object
        keyValue.create_context(context_id)
        print(f"Context '{context_id}' created successfully on this server.")

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
        user_message = args.get("user_message")
        request_server = args.get("request_server")

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
        print(f"Server: Query added to context '{context_id}': {query_string}")

        # Step 2: Retrieve the context as a string
        context_string = keyValue.view(context_id)
        if not context_string:
            print(f"Error: Context '{context_id}' not found.")
            return

        # Step 3: Generate a response by querying Gemini
        prompt_answer = "Answer: "
        response = query_gemini(context_string + "\n" + prompt_answer)
        print(f"Server: Generated response for context '{context_id}': {response}")

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
    print(response)

def server_save_answer(message_data):
    """
    Save the selected answer to the keyValue storage.
    Call kv.save_answer() to persist the answer.
    Send confirmation back to calling server(s) if needed.
    """
    print("TODO")


# ------  USER  ------
def get_user_input():
    """
    Dakota
    Take input from the user and call appropriate functions based on input type.
    Example: if user requests a new context, call user_new_context().
    """
    while not stop_event.is_set():
        user_input = input() # Input message from the user
        if user_input.lower() == 'exit':
            stop_event.set()
            if networkServer != None:
                networkServer.close()
            break
        elif user_input.startswith("create"):
            user_new_context(user_input)
        elif user_input.startswith("query"):
            user_create_query(user_input)
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
    print("TODO")

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
    # --- Election Phase ---
def leader_init():
    
    print("Leader init")
    if leader == -1:
        start_leader_election()

def start_leader_election():

    print("Starting Election")
    global num_leader_promises, ballot_number, leader
    
    num_leader_promises = 0
    ballot_number["seq_num"] += 1
    message_args = {
        "ballot_number": ballot_number,
    }
    send_server_message(message.LEADER_PREPARE, -1, message_args)
    while num_leader_promises < MAX_SERVER_NUM - 1:
        time.sleep(0.1)
        #TODO: TIMOUT FOR FAILURE
    send_server_message(message.LEADER_ACCEPT, -1)
    leader = SERVER_NUM
    threading.Thread(target=run_leader).start()

def server_leader_prepare_message(message_data):

    # Extract context ID and query string from the message data
    args = message_data.get("args", {})
    ballot = args.get("ballot_number")
    sending_server = message_data.get("sending_server")

    #Return Promise if message seq_num greater than local seq_num, and set local seq_num to new value
    if ballot["seq_num"] > ballot_number["seq_num"]:
        send_server_message(message.LEADER_PROMISE, sending_server)
        ballot_number["seq_num"] = ballot["seq_num"]
        


def server_leader_promise_message():

    global num_leader_promises
    num_leader_promises += 1


def server_leader_accept_message(message_data):

    global leader
    leader = message_data.get("sending_server")

    # --- Decision Phase ---
def insert_operation_to_queue(user_message, ballot):

    #Insert message and ballot to queue
    pending_operations.put((user_message, ballot))

def get_consensus(user_message):
    """
    Implement a method to achieve consensus among servers.
    Communicate with all servers to confirm action or context creation.
    Return consensus result to calling function.
    """
    leader_init()

    #TODO: Increment local ballot_number (Right Spot?)
    ballot_number["op_num"] += 1

    #If leader add operation to operation queue
    if leader == SERVER_NUM:
        insert_operation_to_queue(user_message, ballot_number)
    #If not send message to leader to do so
    else:
        message_args = {
            "user_message": user_message,
            "ballot_number": ballot_number,
        }
        send_server_message(message.CONSENSUS_PROPOSE, leader, message_args)

def run_leader():

    global num_consensus_accepted

    while not stop_event.is_set():
        if not pending_operations.empty():
            #Pop the next operation
            user_message, ballot = pending_operations.get()
            accept_message_args = {
                "ballot_number": ballot,
            }
            #Send Accept? message to all servers with message
            num_consensus_accepted = 0
            send_server_message(message.CONSENSUS_ACCEPT, -1, accept_message_args)

            #Wait for all servers to respond
            while num_consensus_accepted < MAX_SERVER_NUM - 1:
                time.sleep(0.1)
                #TODO: TIMOUT FOR FAILURE

            #TODO Maybe: Remove from pending operations now??

            #TODO: Op num increment moved to before insertion

            #Broadcast consensus decide
            decide_message_args = {
                "user_message": user_message,
                "request_server": ballot["pid"]
            }
            send_server_message(message.CONSENSUS_DECIDE, -1, decide_message_args)
            
            #Do Operation Locally (mimic message with minium pieces needed)
            local_decide_message = {
                "sending_server": SERVER_NUM,
                "args": decide_message_args,
            }
            server_consensus_decide_message(local_decide_message)


def server_consensus_propose_message(message_data):
        
    args = message_data.get("args", {})
    user_message = args.get("user_message")
    ballot = args.get("ballot_number")

    insert_operation_to_queue(user_message, ballot)

def server_consensus_accepted_message():

    global num_consensus_accepted
    num_consensus_accepted += 1

def server_consensus_accept_message(message_data):

    args = message_data.get("args", {})
    ballot = args.get("ballot_number")
    sending_server = message_data.get("sending_server")

    if ballot["op_num"] >= ballot_number["op_num"]:
        send_server_message(message.CONSENSUS_ACCEPTED, sending_server)
        #TODO: Might have to clarify what ballot talking about
    else:
        print(f"Consensus Rejected: incoming ballot op_num {ballot["op_num"]} < server ballot op_num {ballot_number["op_num"]}")


def server_consensus_decide_message(message_data):

    args = message_data.get("args", {})
    user_message = args.get("user_message")
    if user_message.startswith("create"):
        server_new_context(user_message)
    elif user_message.startswith("query"):
        server_create_query(message_data)
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

    