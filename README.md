# BBS Door Games Collection

A complete recreation of classic Bulletin Board System (BBS) door games with both modern web interface and authentic text-only BBS server. Experience the golden age of computing with games that capture the spirit of the 1980s and 1990s BBS era.

## 🎮 Two Ways to Play

### 1. Modern Web Interface

Play in your browser with a retro terminal interface:

- Real-time WebSocket gameplay
- Responsive design for desktop and mobile
- Authentic green-on-black terminal styling
- **Start**: `python3 app.py` → visit <http://localhost:5001>

### 2. Authentic BBS Experience

Connect via telnet for the true 1980s experience:

- Text-only interface with ASCII art
- Secure hardened server with input validation
- Rate limiting and abuse prevention
- **Start**: `cd bbs_server && python3 start_bbs.py` → `telnet localhost 2323`

## 🕹️ Games Included

### **The Pit** - Gladiator Combat Game

Fight monsters in the arena, gain experience, and climb the ranks!

- Turn-based combat system
- Character progression and equipment
- Multiple monster types with scaling difficulty

### **Galactic Conquest** - Space Trading Game

Trade goods across the galaxy, upgrade your ship, and build your fortune!

- Multi-planet trading simulation
- Dynamic market prices
- Ship upgrades and cargo management
- Random events and space encounters

### **Hi-Lo Casino** - Number Guessing Game

Guess the number, win big with multiple difficulty levels!

- Variable difficulty settings with different payouts
- Streak bonuses and statistics tracking
- Credit exchange system

## 🔒 Security Features (BBS Server)

- **Input Validation**: Comprehensive sanitization against XSS, SQL injection, directory traversal
- **Authentication**: PBKDF2 password hashing with 100,000 iterations
- **Rate Limiting**: 30 commands/minute, 5 login attempts per IP
- **Session Security**: Automatic timeouts, secure token generation
- **Comprehensive Logging**: All activities logged for security monitoring

## 🚀 Quick Start

### Web Interface

```bash
# Install dependencies
pip install -r requirements.txt

# Start web server
python3 app.py

# Visit in browser
open http://localhost:5001
```

### BBS Server

```bash
# Start BBS (no dependencies needed)
cd bbs_server
python3 start_bbs.py

# Connect via telnet
telnet localhost 2323
```

### Standalone Games

```bash
# Play games directly in terminal
cd games
python3 the_pit.py
python3 galactic_conquest.py
python3 hilo_casino.py
```

## 📁 Project Structure

```
bbs-door-games/
├── games/                    # Standalone Python games
│   ├── the_pit.py
│   ├── galactic_conquest.py
│   └── hilo_casino.py
├── bbs_server/              # Secure BBS server
│   ├── secure_bbs.py       # Main BBS implementation
│   ├── start_bbs.py        # Server startup script
│   └── README.md           # BBS documentation
├── templates/               # Web interface HTML
├── static/                  # CSS and JavaScript
├── app.py                   # Flask web application
├── requirements.txt         # Web dependencies
└── player_data/            # Saved game data
```

## 🎯 Game Features

- **Persistent Player Data**: Progress saved between sessions across all interfaces
- **Classic BBS Aesthetics**: Authentic ASCII art and retro text interfaces
- **Turn-based Gameplay**: Traditional BBS door game mechanics
- **Multiple Difficulty Levels**: Scaling challenges and rewards
- **Statistics Tracking**: Win/loss records, high scores, and achievements
- **Daily Turn Limits**: Authentic BBS-style play restrictions

## 🌐 Technology Stack

### Web Interface

- **Backend**: Python 3.9+ with Flask and Socket.IO
- **Frontend**: HTML5, CSS3, JavaScript with WebSocket communication
- **Styling**: Retro terminal theme with CSS animations
- **Real-time**: WebSocket-based game interaction

### BBS Server

- **Pure Python**: No external dependencies, standard library only
- **Network**: Raw TCP socket server with telnet protocol
- **Database**: SQLite with parameterized queries
- **Security**: Multiple layers of input validation and rate limiting

## 🛡️ Security Architecture

The BBS server implements enterprise-grade security:

1. **Input Validation**: Whitelist-based command validation
2. **Authentication**: Secure password hashing with salt
3. **Rate Limiting**: Per-IP command and login attempt limits
4. **Session Management**: Automatic timeouts and secure tokens
5. **Abuse Prevention**: Pattern detection and automatic bans
6. **Comprehensive Logging**: Full audit trail of all activities

## 📞 Historical Context

BBS door games were external programs that ran on bulletin board systems. Players would "dial in" using modems to access these digital communities. Door games were often the main attraction, featuring:

- **Limited daily turns** to encourage regular visits
- **Persistent game worlds** that evolved over time
- **Competition between users** through high scores and rankings
- **Text-based interfaces** optimized for slow modem connections

This project recreates that authentic experience while adding modern security and web accessibility.

## 🎨 Screenshots

### Web Interface

- Modern browser-based terminal interface
- Real-time gameplay with WebSocket communication
- Mobile-responsive design

### BBS Interface

- Authentic text-only experience
- ASCII art and classic menu systems
- Telnet connectivity for true retro feel

## 🤝 Contributing

We welcome contributions! Ideas for new games:

- **Legend of the Red Dragon (LORD)** - Fantasy adventure with romance
- **Trade Wars 2002** - Multi-player space conquest
- **Usurper** - Dark fantasy with unique graphics
- **Global Wars** - Military strategy and conquest
- **Yankee Trader** - Historical commodity trading

## 📜 License

This project is open source and available under the MIT License.

---

### 🎭 "Remember when the internet was 40 characters wide?"

*A nostalgic journey back to the golden age of bulletin board systems*

**Connect today**: `telnet localhost 2323` or visit <http://localhost:5001>
