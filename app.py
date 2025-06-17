#!/usr/bin/env python3
"""
BBS Door Games Web Interface
A web-based interface for classic BBS door games
"""

from flask import Flask, render_template, request, session, jsonify, redirect, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room
import json
import os
import threading
import time
import uuid
from datetime import datetime

# Import our game classes
import sys
sys.path.append('games')

# Import BBS functionality
from bbs_web import WebBBSManager

app = Flask(__name__)
app.config['SECRET_KEY'] = 'bbs-door-games-secret-key-change-in-production'
socketio = SocketIO(app, cors_allowed_origins="*")

# Store active game sessions
active_sessions = {}
player_data_dir = "player_data"

# Initialize BBS manager
bbs_manager = WebBBSManager()

if not os.path.exists(player_data_dir):
    os.makedirs(player_data_dir)

class WebGameSession:
    """Base class for web-based game sessions"""
    def __init__(self, session_id, player_name, game_type):
        self.session_id = session_id
        self.player_name = player_name
        self.game_type = game_type
        self.output_buffer = []
        self.waiting_for_input = False
        self.input_prompt = ""
        self.game_state = "menu"
        self.last_activity = datetime.now()
    
    def add_output(self, text):
        """Add text to output buffer"""
        self.output_buffer.append({
            'text': text,
            'timestamp': datetime.now().isoformat()
        })
        self.last_activity = datetime.now()
    
    def get_output(self):
        """Get and clear output buffer"""
        output = self.output_buffer.copy()
        self.output_buffer.clear()
        return output
    
    def set_input_prompt(self, prompt):
        """Set the current input prompt"""
        self.input_prompt = prompt
        self.waiting_for_input = True

@app.route('/')
def index():
    """Main page showing available games"""
    games = [
        {
            'id': 'the_pit',
            'name': 'The Pit',
            'description': 'Gladiator Combat Arena - Fight monsters, gain experience, and climb the ranks!',
            'genre': 'Combat/RPG',
            'difficulty': 'Medium'
        },
        {
            'id': 'galactic_conquest',
            'name': 'Galactic Conquest',
            'description': 'Space Trading Game - Buy low, sell high, and rule the galaxy!',
            'genre': 'Trading/Strategy',
            'difficulty': 'Hard'
        },
        {
            'id': 'hilo_casino',
            'name': 'Hi-Lo Casino',
            'description': 'Number Guessing Game - Guess the number, win big!',
            'genre': 'Casino/Luck',
            'difficulty': 'Easy'
        }
    ]
    return render_template('index.html', games=games)

@app.route('/game/<game_id>')
def game_page(game_id):
    """Game interface page"""
    valid_games = ['the_pit', 'galactic_conquest', 'hilo_casino']
    if game_id not in valid_games:
        return redirect(url_for('index'))
    
    game_info = {
        'the_pit': {
            'name': 'The Pit',
            'description': 'Gladiator Combat Arena'
        },
        'galactic_conquest': {
            'name': 'Galactic Conquest',
            'description': 'Space Trading Game'
        },
        'hilo_casino': {
            'name': 'Hi-Lo Casino',
            'description': 'Number Guessing Game'
        }
    }
    
    return render_template('game.html', 
                         game_id=game_id, 
                         game_info=game_info[game_id])

@app.route('/bbs')
def bbs_page():
    """BBS interface page"""
    return render_template('bbs.html')

@app.route('/about')
def about():
    """About page with BBS history"""
    return render_template('about.html')

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f"Client connected: {request.sid}")
    emit('connected', {'status': 'Connected to BBS Door Games'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    session_id = request.sid
    if session_id in active_sessions:
        del active_sessions[session_id]
    print(f"Client disconnected: {session_id}")

@socketio.on('start_game')
def handle_start_game(data):
    """Start a new game session"""
    session_id = request.sid
    game_id = data.get('game_id')
    player_name = data.get('player_name', 'Anonymous')
    
    # Create new game session
    game_session = WebGameSession(session_id, player_name, game_id)
    active_sessions[session_id] = game_session
    
    # Start the appropriate game
    if game_id == 'the_pit':
        start_pit_game(session_id, player_name)
    elif game_id == 'galactic_conquest':
        start_galactic_game(session_id, player_name)
    elif game_id == 'hilo_casino':
        start_hilo_game(session_id, player_name)
    
    emit('game_started', {'game_id': game_id, 'player_name': player_name})

@socketio.on('game_input')
def handle_game_input(data):
    """Handle input from the game interface"""
    session_id = request.sid
    user_input = data.get('input', '')
    
    if session_id not in active_sessions:
        emit('error', {'message': 'No active game session'})
        return
    
    game_session = active_sessions[session_id]
    
    # Process input based on game type
    if game_session.game_type == 'the_pit':
        process_pit_input(session_id, user_input)
    elif game_session.game_type == 'galactic_conquest':
        process_galactic_input(session_id, user_input)
    elif game_session.game_type == 'hilo_casino':
        process_hilo_input(session_id, user_input)

# BBS Socket Handlers
@socketio.on('bbs_input')
def handle_bbs_input(data):
    """Handle input from the BBS interface"""
    session_id = request.sid
    user_input = data.get('input', '')
    ip_address = request.environ.get('REMOTE_ADDR', '127.0.0.1')
    
    try:
        response = bbs_manager.process_input(session_id, ip_address, user_input)
        emit('bbs_output', response)
    except Exception as e:
        print(f"BBS error: {e}")
        emit('bbs_error', {'message': 'BBS system error'})

@socketio.on('bbs_connect')
def handle_bbs_connect():
    """Handle BBS connection"""
    session_id = request.sid
    ip_address = request.environ.get('REMOTE_ADDR', '127.0.0.1')
    
    try:
        # Get initial BBS screen
        response = bbs_manager.process_input(session_id, ip_address, '')
        emit('bbs_output', response)
    except Exception as e:
        print(f"BBS connection error: {e}")
        emit('bbs_error', {'message': 'Failed to connect to BBS'})

@socketio.on('bbs_disconnect')
def handle_bbs_disconnect():
    """Handle BBS disconnection"""
    session_id = request.sid
    bbs_manager.end_session(session_id)

def start_pit_game(session_id, player_name):
    """Start The Pit game"""
    game_session = active_sessions[session_id]
    game_session.add_output("\n" + "="*60)
    game_session.add_output("               THE PIT - GLADIATOR ARENA")
    game_session.add_output("               Fight! Survive! Conquer!")
    game_session.add_output("="*60)
    game_session.add_output(f"\nWelcome, {player_name}!")
    game_session.add_output("\nThis is a simplified web version of The Pit.")
    game_session.add_output("Available commands: fight, stats, shop, quit")
    game_session.set_input_prompt("Enter command: ")
    
    # Send initial output
    emit_game_output(session_id)

def process_pit_input(session_id, user_input):
    """Process input for The Pit game"""
    game_session = active_sessions[session_id]
    cmd = user_input.lower().strip()
    
    if cmd == 'fight':
        game_session.add_output("\n🗡️  You enter the arena!")
        game_session.add_output("A goblin appears! You strike it down!")
        game_session.add_output("🎉 Victory! You gain 25 experience and 15 gold!")
    elif cmd == 'stats':
        game_session.add_output("\n📊 GLADIATOR STATS")
        game_session.add_output(f"Name: {game_session.player_name}")
        game_session.add_output("Level: 1 | Health: 100/100")
        game_session.add_output("Gold: 115 | Wins: 1")
    elif cmd == 'shop':
        game_session.add_output("\n🏪 WEAPON SHOP")
        game_session.add_output("1. Iron Sword - 50 gold")
        game_session.add_output("2. Leather Armor - 40 gold")
        game_session.add_output("(Shop functionality simplified for web demo)")
    elif cmd == 'quit':
        game_session.add_output("\n👋 Thanks for playing The Pit!")
        game_session.game_state = "ended"
    else:
        game_session.add_output(f"\nUnknown command: {user_input}")
        game_session.add_output("Available: fight, stats, shop, quit")
    
    if game_session.game_state != "ended":
        game_session.set_input_prompt("Enter command: ")
    
    emit_game_output(session_id)

def start_galactic_game(session_id, player_name):
    """Start Galactic Conquest game"""
    game_session = active_sessions[session_id]
    game_session.add_output("\n" + "="*60)
    game_session.add_output("           GALACTIC CONQUEST - SPACE TRADER")
    game_session.add_output("         Buy Low, Sell High, Rule the Galaxy!")
    game_session.add_output("="*60)
    game_session.add_output(f"\nWelcome, Captain {player_name}!")
    game_session.add_output("You start with 2000 credits on Earth.")
    game_session.add_output("\nCommands: trade, travel, status, quit")
    game_session.set_input_prompt("Enter command: ")
    
    emit_game_output(session_id)

def process_galactic_input(session_id, user_input):
    """Process input for Galactic Conquest"""
    game_session = active_sessions[session_id]
    cmd = user_input.lower().strip()
    
    if cmd == 'trade':
        game_session.add_output("\n📊 EARTH MARKET")
        game_session.add_output("Food: 8 credits | Medicine: 45 credits")
        game_session.add_output("(Trading simplified for web demo)")
    elif cmd == 'travel':
        game_session.add_output("\n🚀 DESTINATIONS")
        game_session.add_output("1. Mars (5 fuel) - Minerals, Machinery")
        game_session.add_output("2. Alpha Centauri (15 fuel) - Electronics")
        game_session.add_output("(Travel simplified for web demo)")
    elif cmd == 'status':
        game_session.add_output("\n💰 CAPTAIN STATUS")
        game_session.add_output(f"Captain: {game_session.player_name}")
        game_session.add_output("Credits: 2,000 | Location: Earth")
        game_session.add_output("Fuel: 100/100 | Cargo: 0/50")
    elif cmd == 'quit':
        game_session.add_output("\n👋 Safe travels, Captain!")
        game_session.game_state = "ended"
    else:
        game_session.add_output(f"\nUnknown command: {user_input}")
        game_session.add_output("Available: trade, travel, status, quit")
    
    if game_session.game_state != "ended":
        game_session.set_input_prompt("Enter command: ")
    
    emit_game_output(session_id)

def start_hilo_game(session_id, player_name):
    """Start Hi-Lo Casino game"""
    game_session = active_sessions[session_id]
    game_session.add_output("\n" + "="*60)
    game_session.add_output("              HI-LO CASINO - NUMBER GUESSING")
    game_session.add_output("              Guess the number, win big!")
    game_session.add_output("="*60)
    game_session.add_output(f"\nWelcome to the casino, {player_name}!")
    game_session.add_output("You start with 1,000 credits.")
    game_session.add_output("\nCommands: play, stats, rules, quit")
    game_session.set_input_prompt("Enter command: ")
    
    emit_game_output(session_id)

def process_hilo_input(session_id, user_input):
    """Process input for Hi-Lo Casino"""
    game_session = active_sessions[session_id]
    cmd = user_input.lower().strip()
    
    if cmd == 'play':
        game_session.add_output("\n🎲 NEW GAME")
        game_session.add_output("I'm thinking of a number between 1 and 100")
        game_session.add_output("Bet: 100 credits (simplified for demo)")
        game_session.add_output("\nThe number was 42! You won 300 credits!")
    elif cmd == 'stats':
        game_session.add_output("\n📈 PLAYER STATISTICS")
        game_session.add_output(f"Player: {game_session.player_name}")
        game_session.add_output("Credits: 1,300 | Games: 1 | Wins: 1")
        game_session.add_output("Win Rate: 100% | Streak: 1")
    elif cmd == 'rules':
        game_session.add_output("\n📜 GAME RULES")
        game_session.add_output("1. Choose difficulty (affects payout)")
        game_session.add_output("2. Place your bet")
        game_session.add_output("3. Guess the secret number")
        game_session.add_output("4. Win based on difficulty and speed")
    elif cmd == 'quit':
        game_session.add_output("\n👋 Thanks for playing Hi-Lo Casino!")
        game_session.game_state = "ended"
    else:
        game_session.add_output(f"\nUnknown command: {user_input}")
        game_session.add_output("Available: play, stats, rules, quit")
    
    if game_session.game_state != "ended":
        game_session.set_input_prompt("Enter command: ")
    
    emit_game_output(session_id)

def emit_game_output(session_id):
    """Send game output to client"""
    if session_id not in active_sessions:
        return
    
    game_session = active_sessions[session_id]
    output = game_session.get_output()
    
    socketio.emit('game_output', {
        'output': output,
        'prompt': game_session.input_prompt,
        'waiting_for_input': game_session.waiting_for_input,
        'game_state': game_session.game_state
    }, room=session_id)

if __name__ == '__main__':
    print("Starting BBS Door Games Web Server...")
    print("Visit http://localhost:5001 to play!")
    socketio.run(app, debug=True, host='0.0.0.0', port=5001)

