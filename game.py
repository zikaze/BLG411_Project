import heapq
import enum
from typing import List, Tuple, Dict, Optional

from pydantic import BaseModel

class GameOperation(BaseModel):
    """
    A specific action taken by a user within the game. Putting one of their Tokens on a Task for example

    Used in GameRequest.
    """
    target_tick : int   # the tick this request is scheduled to take place in.
    operation : str     # the operation or command to call
    args : Dict         # arguments for the operation

# Note on target_ids: All user-alterable things in a game (ie. the Tasks, Chatbox, Noteboard) 
# have a unique id assigned to them, and these ids are used in commands when referencing them.
# Tasks start at id 1000. Everything else gets a constant predetermined value.

# | id  | Interactable          |
# |:---:|:--------------------- |
# | 10  | Product Backlog       |
# | 11  | Sprint Backlog        |
# |     |                       |
# |     |                       |
# |     |                       |
# |     |                       |
# |     |                       |
# |     |                       |

class GameRequest(BaseModel):
    """
    Encapsulates a GameRequest. These Requests consist of GameOperations which most be done atomically.
    """
    user_id : int
    user_authcode : Optional[int] = None
    request_id : int
    operations : Optional[List[GameOperation]] = None


class GameUpdate(BaseModel):
    """
    Sent by the Game to users to inform them of newly approved GameRequests, and if this decision
    invalidates any of the previously approved GRequests.
    """
    new : Optional[List[GameRequest]] = []
    invalidates : Optional[List[GameRequest]] = []


class User:
    """
    A User. Has an id, username, and a randomly assigned authcode.
    """
    def __init__(self, user_id : int, username : str, authcode : int):
        self.user_id = user_id
        self.name = username
        self.authcode = authcode

class Task:
    """
    A in-game Task.
    """
    @enum.unique
    class Type(enum.IntEnum):
        SIMPLE = 1
        COMPLICATED = 2
        COMPLEX = 3
        CHAOTIC = 4

    def __init__(self, task_type: Type, length : int):
        self.task_type = task_type
        self.length = length


class Game:
    """
    Represents a Game instance. GameRequests go in, game state updates, GameUpdates come out.
    """
    class Phase(enum.IntEnum):
        """
        Represents current phase of the game.
        WAITING indicates game hasn't yet started.
        Rest are directly from the game specs.
        """
        WAITING = 0
        PLANNING = 1
        SPRINT = 2
        RETROSPECTIVE = 3
    def __init__(self):
        self.users : dict[int, User] = {}
        self.req_backlog : list[Task] = []
        self.spr_backlog : list[Task] = []
        self.game_phase : Game.Phase = Game.Phase.WAITING
        self.sprint_count : int = 0

    def add_user(self, user : User) -> None:
        """
        Registers a user to a game
        """
        self.users[user.user_id] = user

    def make_request(self, request : GameRequest) -> GameUpdate:
        """
        Applies changes given in GameRequest. Returns a GameUpdate that should be sent out to users.
        """
        pass

class GameList:
    """
    Contains a list of Games associated with the server.
    """
    def __init__(self):
        self.games = []
        self.free_indexes = [] # A heap containing previously freed indexes.
        self.largest_index_in_use = 0

    def insert_game(self, game : Game) -> int:
        """
        Inserts a new Game into the GameList. Returns the id/index of the game in games.
        """
        index = int()
        if len(self.free_indexes) != 0:
            # Use one of the previously freed indexes.
            index = heapq.heappop(self.free_indexes)
        else:
            # No free indexes mean we gotta allocate a new one
            index = len(self.games)
            self.largest_index_in_use = index

        self.games.insert(index, game)
        return index

    def free_game(self, index : int) -> None:
        """
        Removes the game by the given id/index from the list, and frees its slot.
        """
        # 1: If the index isn't the rightmost one,
        #    it cannot expose a None sequence.
        #    Just remove, push it as freed and exit.
        if index != self.largest_index_in_use:
            self.games[index] = None
            heapq.heappush(self.games, index)
            return

        # If we are here, it means we are about to remove the tail of the array.
        # we need to check and clean any neighboring free slots from the games array.

        # 2 : Remove trailing None sequence from the games array.
        i = index-1
        while(i>0 and (i in self.free_indexes)):
            self.free_indexes.pop(i)
            i -= 1

        del self.games[i+1:]

