# constants.py

from enum import Enum

class message(Enum):
    """
    Used To Unify the type of message being sent
    """
    SERVER_INIT = 1
    SERVER_KILL = 2
    
    PREPARE = 3
    PROMISE = 4

    LEADER_FORWARD = 5
    LEADER_ACK = 6

    ACCEPT = 7
    ACCEPTED = 8
    DECIDE = 9

    LLM_RESPONSE = 10

    # Used to update context and op_num
    UPDATE_CONTEXT = 11


NETWORK_SERVER_PORT = 9000
MAX_SERVER_NUM = 3

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
        if PREPARE:
            "ballot_number": dictionary
        if PROMISE:
            "ballot_number": dictionary

        if LEADER_FORWARD:
            "user_message": string
        if LEADER_ACK:
            "user_message": string
        if ACCEPT:
            "ballot_number": dictionary
        if ACCEPTED:
            "ballot_number": dictionary
        if DECIDE:
            "user_message": string
            "request_server": int   //Original server that made the response
        if LLM_RESPONSE:
            "context_id": int
            "query_string": string
            "response": string
        if UPDATE_CONTEXT:
            "context": KeyValue
            "op_num": int



"""