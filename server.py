from typing import List, Tuple, Dict
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class GameOperation(BaseModel):
    target_tick : int   # the tick this request is scheduled to take place in.
    operation : str     # the operation or command to call
    args : Dict         # arguments for the operation

# Note on target_ids: All user-alterable things in a game (ie. the Tasks, Chatbox, Noteboard) have a unique assigned to them, and these ids are used in commands when referencing them.
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


class Game:
    users : List[User]
    req_backlog : List[Task]
    spr_backlog : List[Task]
    game_phase : int
    sprint_count : int

    def make_request(request : GameRequest) -> GameUpdate:
        """
        Applies changes given in GameRequest. Returns a GameUpdate that should be sent out to users.
        """
        pass

game_list = []

@app.get('/')
def get_homepage():
    """
    Returns the home page.

    Homepage has a single button, which redirects the user to /create_game in order to create the game.
    """
    pass


@app.get('/create_game')
def create_game():
    """
    Creates a new Game object, then redirects user to /join/{room_id}.
    """
    pass


@app.get('/join_game/{room_id}')
def join_game(room_id : int):
    """
    Registers a user to a game, then redirects user to /game/{room_id}.

    If game does not exist, redirects to /?invalidroom=1
    """
    pass


@app.get('/game/{room_id}')
def get_game(room_id:int):
    """
    Returns the page with all the game stuff on it. user_id, user_passcode and room_id will be integrated into the page with a Jinja template.

    After being received, the page must connect to /game_ws/{room_id}/{user_id} to send and receive game requests.
    """
    pass


@app.get('/game_ws/{room_id}/{user_id}')
def game_ws(room_id:int , user_id:int):
    """
    The websocket for user-game pair. Game requests come and leave from here. All game requests must be sent with a user_passcode to validate that it is infact the user who sent the request.

    It basically is a middle man between the users and Game.make_request()
    """
    pass

