# Coin Collector

A platformer game with persistent leaderboards and user statistics. Collect coins, avoid monsters, and climb the ranks!

## 🌟 Features
- 🔐 User authentication (login/registration)
- 🕹️ Side-scrolling platformer mechanics
- 👾 Monster AI with random movement patterns
- 🏆 Global and personal leaderboards
- ⏱️ Time-based scoring system
- 📊 Player statistics tracking
- 🔄 Real-time game status updates
- 🍪 Session management for game instances

## 🚀 Technologies
- **Backend**: Flask, SQLAlchemy, Flask-Login
- **Frontend**: Pygame (game), Jinja2 templates
- **Database**: SQLite
- **Game Engine**: Pygame

## Database structure 
CREATE TABLE IF NOT EXISTS "user" (  
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,  
    "username" VARCHAR(150) NOT NULL UNIQUE,   
    "password" VARCHAR(150) NOT NULL  
); 

CREATE TABLE IF NOT EXISTS "result" (  
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,  
    "user_id" INTEGER NOT NULL,  
    "result" VARCHAR(20) NOT NULL,  
    "coins" INTEGER NOT NULL,  
    "time" DATETIME,  
    "play_time" INTEGER,  
    FOREIGN KEY("user_id") REFERENCES "user"("id")   
); 

##⚙️ Backend API
**Key Endpoints**
- /submit_result	POST	->	Submit game results with validation
- /check_game_status	GET	-> Chack is the game is running or not 
- /start_game	POST	->	Launches game process with env vars
- /leaderboard	GET	-> SQL ranking query
  
**Security Features** 
- 🔒 Session-based authentication with Flask-Login 
- 🍪 Secure cookie handling for game processes 
- 🛡️ SQL injection prevention via SQLAlchemy ORM 
- 🔑 Password hashing with werkzeug.security 

## 🎮 Gameplay 
**Controls**:  
- ← → Arrow keys: Move character  
- Spacebar: Jump 
- ESC: Quit game 
- F2: Restart game 

**Objectives**: 
- Collect all 5 coins 
- Avoid moving monsters 
- Reach the door after collecting all coins  
- Compete for best time on the leaderboard 

## 📊 Leaderboard System 
Results are ranked using a sorting algorithm: 
- Game outcome priority: Won > Lost > Quit 
- For wins: Fastest completion time 
- For losses/quits: Highest coins collected 
- Secondary sort: Completion time 
