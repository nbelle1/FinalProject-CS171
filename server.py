# server.py

import socket
import time
import sys
import threading
from shared import message
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
    print("TODO")

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
    print("TODO")

def server_new_context():
    """
    Nik
    Create a new context using the keyValue object (kv).
    Call kv.create_context() to initialize the context.
    """
    print("TODO")

def server_create_query():
    """
    Nik
    Create a query in the specified context.
    Call kv.create_query() to add the query.
    Generate a response by calling query_gemini().
    Send response back to the calling server using send_server_message().
    """
    print("TODO")

def server_llm_response():
    """
    Add the received LLM response to the llm_responses collection.
    Print the response for server-side logging.
    """
    print("TODO")

def server_save_answer():
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
    print("TODO")

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
    Nik
    Retrieve and display the data for a specified context.
    Use kv.view(context_id) to fetch context details.
    """
    print("TODO")

def user_view_all_context(user_message):
    """
    Nik
    Retrieve and display all contexts.
    Use kv.view_all() to list all contexts.
    """
    print("TODO")


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
    threading.Thread(target=get_server_message).start()
    threading.Thread(target=get_user_input).start()

    while not stop_event.is_set():
        time.sleep(0.5)
        
    sys.stdout.flush()
    sys.exit(0)

    