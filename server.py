# server.py

import socket
import time
import sys
import threading
from shared import message, NETWORK_SERVER_PORT
from key_value import KeyValue


keyValue = KeyValue()
networkServer = None
stop_event = threading.Event()

SERVER_NUM = -1

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
    

def send_server_message(message_type, destination_server, args):
    """
    Dakota
    Send a message to the specified server with a given message type and arguments.
    Format message as <SERVER_NUM> <destination_server> <message_type> <args>.
    Use networkServer to send the formatted message.
    """
    print("TODO")

def get_server_message():
    """
    Dakota
    Continuously receive messages from other servers or clients.
    Parse incoming message to identify message type.
    Based on message type, call the appropriate server function.
    Example: if message_type == "NEW_CONTEXT", call server_new_context().
    """
    while not stop_event.is_set():
        try:
            server_message = networkServer.recv(1024).decode('utf-8') #Receive server response
            if not server_message:
                print("Server Disconnected")
                break

            #Get message Type from Message
            message_type = message(int(server_message.split()[2]))

            #Start function based on message type
            if message_type == message.SERVER_INIT:
                server_init_message(server_message)
            elif message_type == message.NEW_CONTEXT:
                server_new_context(server_message)
            elif message_type == message.CREATE_QUERY:
                server_create_query(server_message)
            elif message_type == message.LLM_RESPONSE:
                server_llm_response(server_message)
            elif message_type == message.SAVE_ANSWER:
                server_save_answer(server_message)
        except Exception:
            continue
    print("TODO")

def server_init_message(server_message):
    """
    Used to asign the server num when connected to the network server
    """
    global SERVER_NUM
    server_num = server_message.split()[3]
    SERVER_NUM = server_num
    print(f"Assigned Server Number {SERVER_NUM}")

def server_new_context(server_message):
    """
    Nik
    Create a new context using the keyValue object (kv).
    Call kv.create_context() to initialize the context.
    """
    print("TODO")

def server_create_query(server_message):
    """
    Nik
    Create a query in the specified context.
    Call kv.create_query() to add the query.
    Generate a response by calling query_gemini().
    Send response back to the calling server using send_server_message().
    """
    print("TODO")

def server_llm_response(server_message):
    """
    Add the received LLM response to the llm_responses collection.
    Print the response for server-side logging.
    """
    print("TODO")

def server_save_answer(server_message):
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
            user_view_all_context(user_input)
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
    print("TODO")

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
    print("TODO")

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
        print(f"Context '{context_id}' not found.")
        return

    # Format the context data for display
    formatted_output = [f"Query: {item['query']}\nAnswer: {item['answer']}" for item in context_data]
    print(f"{context_id} = \"\"\"\n" + "\n".join(formatted_output) + "\n\"\"\"")

def user_view_all_context(user_message):
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
def get_consensus():
    """
    Implement a method to achieve consensus among servers.
    Communicate with all servers to confirm action or context creation.
    Return consensus result to calling function.
    """
    print("TODO")


# ------ GEMINI ------
def query_gemini():
    """
    Nik
    Send a query to the Gemini LLM and receive a response.
    Return response to calling function.
    """
    print("TODO")


if __name__ == "__main__":
    print("Server")
    connect_server()
    threading.Thread(target=get_user_input).start()

    while not stop_event.is_set():
        time.sleep(0.5)
        
    sys.stdout.flush()
    sys.exit(0)

    