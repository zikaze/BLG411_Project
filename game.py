import heapq
import enum
from typing import List, Tuple, Dict, Optional
from copy import deepcopy

from pydantic import BaseModel


class GameRequest(BaseModel):
    """
    Encapsulates a GameRequest. These Requests consist of GameOperations which most be done 
    atomically.
    """
    user_id : int
    user_authcode : Optional[int] = None
    request_id : int
    target_tick : int   # the tick this request is scheduled to take place in.
    operation_target : Optional[int] = None
    operation : str     # the operation or command to call
    operation_args : Dict         # arguments for the operation
        
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
    class Role(enum.IntEnum):
        """
        Represents a User's in-game role.
        """
        USER = 1
        LEADER = 2

    def __init__(self, user_id : int, username : str, authcode : int):
        self.user_id = user_id
        self.name = username
        self.authcode = authcode


class GameObject:
    """
    Represents a in-game object.

    self.operations hold all available in-game operations.
    The signature for an operation should be (self, state: GameState, request : GameRequest) -> GameState
    It returns either the next GameState or None if operation violates in-game rules.
    """
    def __init__(self, object_id):
        self.object_id : int = object_id
        self.operations : dict [str, type(self.__init__)] = {}



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


    class State:
        """
        Represents the state of the game at a given tick.

        These go in between StateChanges so we don't need to rerender everything each time a
        request is made.
        """
        def __init__(self):
            self.objects : dict[int, GameObject] = {}
            self.req_backlog : list[Task] = []
            self.spr_backlog : list[Task] = []
            self.game_phase : Game.Phase = Game.Phase.WAITING
            self.sprint_count : int = 0
            self.users : dict[int, User] = {}

    def __init__(self):
        self.requests : dict[int, list[GameRequest]]
        self.state = Game.State()

    def add_user(self, user : User) -> None:
        """
        Registers a user to a game
        """

        self.state.users[user.user_id] = user


    def make_request(self, request : GameRequest) -> GameUpdate:
        """
        Applies changes given in GameRequest. Returns a GameUpdate that should be sent out to users.
        """
        # Fuck it: just apply every request everytime a new request is made.
        # FIXME This is absolute trash
        result = GameUpdate()
        current_state = deepcopy(self.state)
        times = sorted(self.requests.keys())
        time_i = 0
        times_len = len(times)

        while (time_i < times_len) and (times[time_i] > request.target_tick):
            time = times[time_i]
            if time > request.target_tick:
                break
            
            for req in self.requests[time]:
                current_state = self._apply_request(current_state, req)
            # TODO Assert nonnull value

            time_i = time_i + 1

        current_state = self._apply_request(current_state, request)

        if current_state :
            result.new.append(request)
        else:
            # The change is not applicable.
            result.invalidates.append(request)
            return result

        # Continue applying requests. Anything that violates rules goes in the invalidate pile.
        while time_i < times_len :
            for req in self.requests[time_i]:
                proposed_state = self._apply_request(current_state, req)
                if proposed_state:
                    current_state = proposed_state
                else:
                    result.invalidates.append(req)

            time_i = time_i + 1

        return result



    def _apply_request(self, state: State, request : GameRequest) -> State:
        """
        Apply the Request to this State, return the resulting State. If the request violates any
        in-game rules, None will be returned.
        """
        # 1. If there is a target_id, you arent supposed to handle this. Call target's operation
        #   instead.
        if request.target_id:
            game_obj = state.objects[request.target_id]
            return game_obj.operations[request.operation](state, request)
        
        # 2. If its an operation concerning the game itself then it should be handled here
        # ==== GameOperations concerning the game itself start here ====

        # Operation start_game: starts the game.
        if request.operation == "start_game":
            if state.users[request.user_id].role == User.Role.LEADER:
                new_state = deepcopy(state)
                new_state.game_phase = Game.Phase.PLANNING
                return new_state
            return None

        # TODO Operation: add_user
        # TODO Operation: end_game
        # TODO Probably more Operations

class Task(GameObject):
    """
    Represents a in-game Task.
    """
    @enum.unique
    class Type(enum.IntEnum):
        """
        In-game Task Type.
        """
        SIMPLE = 1
        COMPLICATED = 2
        COMPLEX = 3
        CHAOTIC = 4

    def __init__(self, object_id : int,  task_type: Type, length : int):
        super().__init__(object_id)
        self.task_type = task_type
        self.length = length

    def _gop_add_token(self, state:Game.State, request: GameRequest)-> Game.State or None:
        """
        Adds a user's token to this task.
        """
        if state.users[request.user_id].free_tokens == 0:
            return None

        target = state.objects[request.target_id]
        if not isinstance(target, Task):
            raise ValueError("Given target_id doesnt belong to a task.")
        if target.current_tokens == target.max_tokens:
            return None

        new_state = deepcopy(state)
        target = new_state.objects[request.target_id]
        target.cur_tokens =target.cur_token + 1
        return new_state

class GameList:
    """
    Contains a list of Games associated with the server.
    """
    def __init__(self):
        self.games = [ ]
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

