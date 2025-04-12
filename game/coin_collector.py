import pygame
from random import randint, choice
import requests
import os

# Inizializzazione Pygame
pygame.init()

# Costanti di configurazione
SCREEN_WIDTH = 1900
SCREEN_HEIGHT = 600
FPS = 60
NUM_COINS = 5

# Get session cookie from the ambient
session_cookie_value = os.environ.get('SESSION_COOKIE')

class CoinCollector:
    def __init__(self):
        self.left_pressed = False
        self.right_pressed = False
        self.jump_pressed = False
        
        self.start_time = 0
        self.play_time = 0
        
        self.game_solved = False
        self.game_failed = False
        self.result_sent = False
        self.running = True
        self.is_exiting = False

        self.vel_y = 0
        self.on_ground = True
        self.gravity = 0.5
        self.points = 0

        # Gaming window
        self.window = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.game_font = pygame.font.SysFont("Arial", 24)
        pygame.display.set_caption("Coin Collector")

        self.load_assets() # Load images
        self.reset_game_state() # Reset game
        self.main_loop() # Start game

    # Load images for the game
    def load_assets(self):
        self.rogue = pygame.image.load("./game/rogue.png")
        self.door = pygame.image.load("./game/door.png")
        self.coin_img = pygame.image.load("./game/coin.png")
        self.monster_img = pygame.image.load("./game/monster.png")

        # Dimensions
        self.rogue_rect = self.rogue.get_rect()
        self.door_rect = self.door.get_rect()
        self.coin_size = self.coin_img.get_size()
        self.monster_size = self.monster_img.get_size()

    # Reset game for a new game
    def reset_game_state(self):
        # Set positions
        self.rogue_rect.topleft = (0, SCREEN_HEIGHT - self.rogue_rect.height)
        self.door_rect.topleft = (SCREEN_WIDTH - self.door_rect.width, SCREEN_HEIGHT - self.door_rect.height)
        self.coins = self.generate_elements(self.coin_img, NUM_COINS)
        self.monsters = self.generate_elements(self.monster_img, NUM_COINS, True)

        # Reset for new game
        self.points = 0
        self.result_sent = False
        self.game_solved = False
        self.game_failed = False
        self.is_exiting = False
        self.start_time = pygame.time.get_ticks()
        self.play_time = 0

    def generate_elements(self, img, count, is_monster=False):
        elements = []
        for _ in range(count):
            element = {
                'image': img,
                'pos': [
                    randint(0, SCREEN_WIDTH - img.get_width() - self.door_rect.width),
                    SCREEN_HEIGHT - img.get_height()
                ]
            }
            if is_monster:
                element['vel'] = choice([-2, 2])
            elements.append(element)
        return elements

    # Main loop of the game
    def main_loop(self):
        clock = pygame.time.Clock()
        while self.running:
            self.handle_events()
            self.update_timer()
            if self.game_active:
                self.update_physics()
            self.check_collisions()
            self.update_screen()
            clock.tick(FPS)

    # Update game timer
    def update_timer(self):
        if self.game_active:
            self.play_time = (pygame.time.get_ticks() - self.start_time) // 1000

    # Returns true if the game is active
    @property # the function can be called as a variable of the class (property)
    def game_active(self):
        return not self.game_solved and not self.game_failed

    # Payer's input handling
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.safe_exit()
            
            if event.type == pygame.KEYDOWN:
                self.handle_keydown(event)
            elif event.type == pygame.KEYUP:
                self.handle_keyup(event)

        if self.game_active:
            self.handle_movement() # player can move is the game is active

    # Handle keys down
    def handle_keydown(self, event):
        key_actions = {
            pygame.K_LEFT: lambda: setattr(self, 'left_pressed', True),
            pygame.K_RIGHT: lambda: setattr(self, 'right_pressed', True),
            pygame.K_SPACE: lambda: setattr(self, 'jump_pressed', True),
            pygame.K_ESCAPE: self.safe_exit,
            pygame.K_F2: self.restart_game
        }
        if event.key in key_actions:
            key_actions[event.key]()

    # Handle keys up
    def handle_keyup(self, event):
        key_actions = {
            pygame.K_LEFT: lambda: setattr(self, 'left_pressed', False),
            pygame.K_RIGHT: lambda: setattr(self, 'right_pressed', False),
            pygame.K_SPACE: lambda: setattr(self, 'jump_pressed', False)
        }
        if event.key in key_actions:
            key_actions[event.key]()

    # Side movement
    def handle_movement(self):
        if self.left_pressed and self.rogue_rect.left > 0:
            self.rogue_rect.x -= 5
        if self.right_pressed and self.rogue_rect.right < SCREEN_WIDTH:
            self.rogue_rect.x += 5

    # Jump
    def update_physics(self):
        if self.jump_pressed and self.on_ground:
            self.vel_y = -15
            self.on_ground = False

        self.rogue_rect.y += self.vel_y
        self.vel_y += self.gravity

        # Handle vertical collisions
        if self.rogue_rect.bottom >= SCREEN_HEIGHT:
            self.rogue_rect.bottom = SCREEN_HEIGHT
            self.vel_y = 0
            self.on_ground = True
        elif self.rogue_rect.top < 0:
            self.rogue_rect.top = 0
            self.vel_y = 0

    # Handle collisions
    def check_collisions(self):
        if self.game_active:
            self.check_coin_collisions()
            self.check_monster_collisions()
            self.check_victory_condition()

    # Gather coins (through collision)
    def check_coin_collisions(self):
        remaining_coins = []
        for coin in self.coins:
            coin_rect = pygame.Rect(*coin['pos'], *self.coin_size) # * breaks the tuple in all it's elements
            if coin_rect.colliderect(self.rogue_rect):
                self.points += 1
            else:
                remaining_coins.append(coin)
        self.coins = remaining_coins

    def check_monster_collisions(self):
        for monster in self.monsters:
            monster_rect = pygame.Rect(*monster['pos'], *self.monster_size)
            if monster_rect.colliderect(self.rogue_rect):
                self.game_failed = True
                self.send_result('lost')
                return

    def check_victory_condition(self):
        if self.points == NUM_COINS and self.rogue_rect.colliderect(self.door_rect):
            self.game_solved = True
            self.send_result('won')

    def update_screen(self):
        self.window.fill((56, 58, 102))  # Background
        
        # Platform
        pygame.draw.rect(self.window, (102, 51, 0), (0, SCREEN_HEIGHT-10, SCREEN_WIDTH, 10))
        
        self.draw_elements()
        self.draw_ui()
        
        # Ending messages
        if self.game_failed:
            self.draw_text_center("You lose!")
        elif self.game_solved:
            self.draw_text_center("Congratulations, you won!")
        
        pygame.display.flip()

    def draw_elements(self):
        # Coins
        for coin in self.coins:
            self.window.blit(coin['image'], coin['pos'])
        
        # Monsters
        for monster in self.monsters:
            self.window.blit(monster['image'], monster['pos'])
            # Move monster
            monster['pos'][0] += monster.get('vel', 0)
            # Casual changing direction
            if randint(0, 100) < 2:
                monster['vel'] = choice([-2, 2])
            # Turn back when at the border
            if monster['pos'][0] < 0 or monster['pos'][0] > SCREEN_WIDTH - self.monster_size[0]:
                monster['vel'] *= -1
        
        self.window.blit(self.rogue, self.rogue_rect)
        self.window.blit(self.door, self.door_rect)

    def draw_ui(self):
        minutes = self.play_time // 60
        seconds = self.play_time % 60
        time_text = f"Time: {minutes:02d}:{seconds:02d}"
        
        texts = [
            ("F2 - New Game", 50),
            ("ESC - Exit", SCREEN_WIDTH//2 - 50),
            (f"Coins: {self.points}/{NUM_COINS}", SCREEN_WIDTH - 300),
            (time_text, SCREEN_WIDTH - 200)
        ]
        for text, x in texts:
            surface = self.game_font.render(text, True, (255, 0, 0))
            self.window.blit(surface, (x, 20))

    def draw_text_center(self, text):
        surface = self.game_font.render(text, True, (255, 0, 0))
        text_rect = surface.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
        self.window.blit(surface, text_rect)

    def safe_exit(self):
        if not self.is_exiting:
            self.is_exiting = True
            self.send_result('quit')
            self.running = False

    def restart_game(self):
        self.send_result('quit')
        self.reset_game_state()

    def send_result(self, result_type):
        if not self.result_sent:
            self.result_sent = True
            send_result(result_type, self.points, self.play_time)

# Send game results to server
def send_result(result, coins, play_time):
    url = "http://localhost:5000/submit_result"
    headers = {"Content-Type": "application/json"}
    data = {
        "result": result,
        "coins": coins,
        "play_time": play_time
    }

    try:
        # Create a new session to handle cookies and requests
        session = requests.Session()
        if session_cookie_value:
            session.cookies.set('session', session_cookie_value, path='/') # assign cookie
        
        response = session.post(url, json=data, headers=headers, timeout=1)
        
        if response.status_code == 200:
            print("Success")
        else:
            print("Error", response.text)
        
        # Delay to avoids more requests
        pygame.time.delay(150)
        
    except Exception as e:
        print("Connection error", str(e))


if __name__ == "__main__":
    CoinCollector().main_loop()