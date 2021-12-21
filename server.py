import os
import heapq

from typing import List, Tuple, Dict, Optional
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from jinja2 import Environment as JnEnv, FileSystemLoader as JnFileSystemLoader, select_autoescape


class GameOperation(BaseModel):
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
    user_id : int
    user_passcode : Optional[int] = None
    request_id : int
    operations : Optional[List[GameOperation]] = None


class GameUpdate(BaseModel):
    new : Optional[List[GameRequest]] = []
    invalidates : Optional[List[GameRequest]] = []


class User:
    user_id : int
    username : str
    user_passcode : int

class Task:
    pass

class Game:
    users : List[User]
    req_backlog : List[Task]
    spr_backlog : List[Task]
    game_phase : int
    sprint_count : int

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

        self.games[index] = game
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



app = FastAPI()

jinja_env = JnEnv(
                    loader=JnFileSystemLoader(f'{os.path.dirname(__file__)}/templates/'), 
                    autoescape=select_autoescape('html')
                 )

@app.get('/', response_class=HTMLResponse)
def get_homepage():
    """
    Returns the home page.

    Homepage has a single button, which redirects the user to /create_game in order to create
    the game.
    """
    return jinja_env.get_template(name='index.html').render()

@app.get('/tutorial')
def get_tutorial():
    """
    Returns the tutorial page.
    """
    return jinja_env.get_template(name='tutorial1.html').render()


@app.get('/create_game')
def create_game():
    """
    Creates a new Game object, then redirects user to /join/{room_id}.
    """
    pass


@app.get('/join/{room_id}')
def join_game(room_id : int):
    """
    Registers a user to a game, then redirects user to /game/{room_id}.

    If game does not exist, redirects to /?invalidroom=1
    """

    pass


@app.get('/game/{room_id}', response_class=HTMLResponse)
def get_game(room_id:int):
    """
    Returns the page with all the game stuff on it.
    user_id, user_passcode and room_id will be integrated into the page with a Jinja template.

    After being received, the page must connect to /game_ws/{room_id}/{user_id} to send and 
    receive game requests.
    """
    pass


@app.get('/game_ws/{room_id}/{user_id}')
def game_ws(room_id:int , user_id:int):
    """
    The websocket for user-game pair. Game requests come and leave from here. All game requests
    must be sent with a user_passcode to validate that it is infact the user who sent the request.

    It basically is a middle man between the users and Game.make_request()
    """
    pass

