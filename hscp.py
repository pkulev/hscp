import requests
import logging

log = logging.getLogger(__name__)

class AuthError(Exception):
    """Exception to raise when authentification has failed"""
    pass

class InvalidName(Exception):
    """Exception to raise when nickname can't be found"""
    pass

class TokenUnavailable(Exception):
    """Exception to raise when token isn't set"""
    pass

class HyScoresClient:
    def __init__(self, url, app:str, timeout:int = 30, user_agent:str = None):
        self.url = url
        self.session = requests.Session()
        self.timeout = max(timeout, 0)
        self.app = app

        self.user_agent = user_agent
        self._token = None 

    @property
    def user_agent(self):
        return self._user_agent

    @user_agent.setter
    def user_agent(self, val:str):
        self._user_agent = val
        self.session.headers.update({"user-agent": self._user_agent})

    @property
    def token(self):
        return self._token
    
    @token.setter
    def token(self, val:str):
        self._token = val
        self.session.headers.update({"x-access-tokens": self._token})

    def register(self, username:str, password:str, endpoint:str = "/register") -> bool:
        return self.session.post(
            self.url+endpoint, 
            timeout=self.timeout, 
            auth = (username, password),
            json={"app": self.app},
        ).json().get("result", False)

    def login(self, username:str, password:str, endpoint:str = "/login"):
        result = self.session.post(
            self.url+endpoint, 
            timeout=self.timeout, 
            auth = (username, password),
            json={"app": self.app},
        ).json().get("result", None)
        if result:
            token = result.get("token", None)
            if token:
                self.token = token
                return
        
        raise AuthError

    def require_token(func:callable):
        def inner(self, *args, **kwargs):
            if not self.token:
                raise TokenUnavailable

            return func(self, *args, **kwargs)
        return inner

    @require_token
    def get_scores(self, endpoint:str = "/scores") -> list:
        return self.session.get(
            self.url+endpoint, 
            timeout=self.timeout, 
            json={"app": self.app},
        ).json()["result"]

    @require_token
    def get_score(self, nickname:str, endpoint:str = "/score") -> dict:
        result = self.session.get(
            self.url+endpoint, 
            timeout=self.timeout, 
            json={
                "app": self.app,
                "nickname": nickname,
            },
        ).json()["result"]
        if type(result) is dict:
            return result
        else:
            raise InvalidName

    # #TODO: maybe add ability to attach custom data, besides score?
    @require_token
    def post_score(self, nickname:str, score:int, endpoint:str = "/score") -> bool:
        return self.session.post(
            self.url+endpoint, 
            timeout=self.timeout, 
            json={
                "app": self.app,
                "nickname": nickname,
                "score": score,
            },
        ).json()["result"]

    @require_token
    def logout(self):
        self.token = None
