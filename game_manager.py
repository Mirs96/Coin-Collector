import os
import subprocess

class GameManager:
    def __init__(self, game_path):
        self.game_path = game_path
        self.process = None
        self._game_active = False

    @property
    def is_game_active(self):
        if self.process and self.process.poll() is not None:
            self._game_active = False
        return self._game_active

    def start_game(self, session_cookie):
        if self.is_game_active:
            return False, "The game is already running!"
            
        try:
            env = os.environ.copy()
            env['SESSION_COOKIE'] = session_cookie
            self.process = subprocess.Popen(["python", self.game_path], env=env)
            self._game_active = True
            return True, "The game is running!"
        except Exception as e:
            return False, str(e)

    def cleanup(self):
        if self.process:
            try:
                self.process.terminate()
            except:
                pass
            self.process = None
        self._game_active = False