# constants.py

from enum import Enum

class message(Enum):
    SERVER_INIT = 1
    SERVER_KILL = 2
    NEW_CONTEXT = 3
    CREATE_QUERY = 4
    LLM_RESPONSE = 5
    SAVE_ANSWER = 6
