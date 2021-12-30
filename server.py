import os

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse
from jinja2 import Environment as JnEnv, FileSystemLoader as JnFileSystemLoader, select_autoescape
import random
from game import *


app = FastAPI()

jinja_env = JnEnv(
                    loader=JnFileSystemLoader(f'{os.path.dirname(__file__)}/templates/'),
                    autoescape=select_autoescape('html')
                 )
GameList = GameList()


@app.get('/', response_class=HTMLResponse)
def get_homepage():
    """
    Returns the home page.

    Homepage has a single button, which redirects the user to /create_game in order to create
    the game.
    """
    return jinja_env.get_template(name='index.html').render()

@app.get('/tutorial', response_class=HTMLResponse)
def get_tutorial():
    """
    Returns the tutorial page.
    """
    return jinja_env.get_template(name='tutorial1.html').render()


@app.get('/create_game', response_class=RedirectResponse)
def create_game():
    """
    Creates a new Game object, then redirects user to /join/{room_id}.
    """
    game1 = Game()
    index = GameList.insert_game(game1)

    return RedirectResponse(url=app.url_path_for("join_game",room_id=index))


@app.get('/join/{room_id}')
def join_game(room_id : int):
    """
    Registers a user to a game, then redirects user to /game/{room_id}.

    If game does not exist, redirects to /?invalidroom=1
    """
    id = random.randint(9, 1000000000)
    while GameList.games[room_id].users[id] == None:
        id = random.randint(9,1000000000)
    user1 = User()
    user1.id = id
    user1.name = 'Player{}'.format(len(GameList.games[room_id].users)+1)
    user1.authcode = random.randint(1000000,9999999)
    GameList.games[room_id].add_user(user1)
    if(GameList.games[room_id] != None):
        return RedirectResponse(url=app.url_path_for("get_homepage",room_id_valid = 0))


@app.get('/game/{room_id}', response_class=HTMLResponse)
def get_game(room_id:int):
    """
    Returns the page with all the game stuff on it.
    user_id, user_authcode and room_id will be integrated into the page with a Jinja template.

    After being received, the page must connect to /game_ws/{room_id}/{user_id} to send and 
    receive game requests.
    """
    pass


@app.get('/game_ws/{room_id}/{user_id}')
def game_ws(room_id:int , user_id:int):
    """
    The websocket for user-game pair. Game requests come and leave from here. All game requests
    must be sent with a user_authcode to validate that it is infact the user who sent the request.

    It basically is a middle man between the users and Game.make_request()
    """
    pass

