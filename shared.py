# constants.py

from enum import Enum

class message(Enum):
    """
    Used To Unify the type of message being sent
    """
    SERVER_INIT = 1
    SERVER_KILL = 2
    NEW_CONTEXT = 3
    CREATE_QUERY = 4
    LLM_RESPONSE = 5
    SAVE_ANSWER = 6

NETWORK_SERVER_PORT = 9000


"""
JSON Format:

message_data
    "dest_server": int
    "sending_server": int 
    "message_type": int
    "args":
        if SERVER_INIT:
            "server_num": int
        if SERVER_KILL:
        if NEW_CONTEXT:
        if CREATE_QUERY:
            "context_id": int
            "query_string": string
        if LLM_RESPONSE:
        if SAVE_ANSWER




"""