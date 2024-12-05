# constants.py

from enum import Enum

class message(Enum):
    """
    Used To Unify the type of message being sent
    """
    SERVER_INIT = 1
    SERVER_KILL = 2
    
    LEADER_PREPARE = 3
    LEADER_PROMISE = 4
    LEADER_ACCEPT = 5

    CONSENSUS_PROPOSE = 6
    CONSENSUS_ACCEPT = 7
    CONSENSUS_ACCEPTED = 8
    CONSENSUS_DECIDE = 9

    LLM_RESPONSE = 10
    SAVE_ANSWER = 11


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
        if LEADER_PREPARE:
            "ballot_number": dictionary
        if LEADER_PROMISE:
        if LEADER_ACCEPT:

        if CONSENSUS_PROPOSE:
            "user_message": string
            "ballot_message":string
        if CONSENSUS_ACCEPT:
            "ballot_number": dictionary
        if CONSENSUS_ACCEPTED:
        if CONSENSUS_DECIDE:
            "user_message": string
        if LLM_RESPONSE:
            "context_id": int
            "query_string": string
            "response": string
            "request_server": int   //Original server that made the response



"""