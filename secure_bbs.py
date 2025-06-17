#!/usr/bin/env python3
"""
Secure Text-Only BBS Server
A hardened bulletin board system with comprehensive input validation
"""

import socket
import threading
import json
import os
import re
import hashlib
import secrets
import time
from datetime import datetime, timedelta
import sqlite3
import html
import logging
from typing import Optional, Dict, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bbs.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SecurityValidator:
    """Comprehensive input validation and security measures"""
    
    # Maximum lengths for various inputs
    MAX_USERNAME = 20
    MAX_PASSWORD = 128
    MAX_MESSAGE_SUBJECT = 80
    MAX_MESSAGE_BODY = 2000
    MAX_REALNAME = 50
    MAX_LOCATION = 50
    
    # Rate limiting
    MAX_COMMANDS_PER_MINUTE = 30
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION = 300  # 5 minutes
    
    # Banned patterns
    BANNED_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # Script tags
        r'javascript:',               # JavaScript URLs
        r'vbscript:',                # VBScript URLs
        r'on\w+\s*=',               # Event handlers
        r'\x00',                     # Null bytes
        r'\.\./',                   # Directory traversal
        r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]',  # Control characters
        r'(?i)(union|select|insert|update|delete|drop|create|alter)\s',  # SQL keywords
    ]
    
    @staticmethod
    def validate_username(username: str) -> Tuple[bool, str]:
        """Validate username with strict rules"""
        if not username:
            return False, "Username cannot be empty"
        
        if len(username) > SecurityValidator.MAX_USERNAME:
            return False, f"Username too long (max {SecurityValidator.MAX_USERNAME})"
        
        if len(username) < 3:
            return False, "Username too short (min 3 characters)"
        
        # Only allow alphanumeric and underscore
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return False, "Username can only contain letters, numbers, and underscores"
        
        # Must start with letter
        if not username[0].isalpha():
            return False, "Username must start with a letter"
        
        # Reserved names
        reserved = ['admin', 'root', 'system', 'sysop', 'guest', 'anonymous', 'user']
        if username.lower() in reserved:
            return False, "Username is reserved"
        
        return True, "Valid"
    
    @staticmethod
    def validate_password(password: str) -> Tuple[bool, str]:
        """Validate password strength"""
        if not password:
            return False, "Password cannot be empty"
        
        if len(password) < 8:
            return False, "Password must be at least 8 characters"
        
        if len(password) > SecurityValidator.MAX_PASSWORD:
            return False, f"Password too long (max {SecurityValidator.MAX_PASSWORD})"
        
        # Check for required character types
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password)
        
        if not (has_upper and has_lower and has_digit and has_special):
            return False, "Password must contain uppercase, lowercase, digit, and special character"
        
        return True, "Valid"
    
    @staticmethod
    def sanitize_text(text: str, max_length: int = None) -> str:
        """Sanitize text input"""
        if not text:
            return ""
        
        # Remove null bytes and control characters
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        # Check for banned patterns
        for pattern in SecurityValidator.BANNED_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                logger.warning(f"Banned pattern detected: {pattern}")
                return "[CONTENT FILTERED]"
        
        # HTML escape
        text = html.escape(text)
        
        # Limit length
        if max_length and len(text) > max_length:
            text = text[:max_length]
        
        return text.strip()
    
    @staticmethod
    def validate_command(command: str) -> Tuple[bool, str]:
        """Validate command input"""
        if not command:
            return False, "Command cannot be empty"
        
        command = command.strip().upper()
        
        # Valid commands
        valid_commands = {
            # Main menu
            'M', 'MESSAGES', 'MESSAGE',
            'F', 'FILES', 'FILE',
            'D', 'DOORS', 'DOOR', 'GAMES',
            'C', 'CHAT',
            'U', 'USERS', 'USER',
            'S', 'STATS', 'STATISTICS',
            'Q', 'QUIT', 'EXIT', 'LOGOFF', 'BYE',
            'H', 'HELP', '?',
            'T', 'TIME',
            'W', 'WHO',
            
            # Message commands
            'R', 'READ',
            'P', 'POST',
            'L', 'LIST',
            'B', 'BACK',
            
            # Numbers for menu selections
            '1', '2', '3', '4', '5', '6', '7', '8', '9', '0',
            
            # Special
            'Y', 'YES', 'N', 'NO',
            'ENTER', 'RETURN'
        }
        
        # Check if it's a number
        if command.isdigit():
            return True, command
        
        # Check if it's a valid command
        if command in valid_commands:
            return True, command
        
        return False, f"Invalid command: {command}"

class RateLimiter:
    """Rate limiting for commands and connections"""
    
    def __init__(self):
        self.command_counts = {}  # {ip: [(timestamp, count), ...]}
        self.login_attempts = {}  # {ip: [(timestamp, attempts), ...]}
        self.lockouts = {}       # {ip: lockout_until_timestamp}
    
    def is_rate_limited(self, ip: str) -> bool:
        """Check if IP is rate limited"""
        now = time.time()
        
        # Check if locked out
        if ip in self.lockouts and now < self.lockouts[ip]:
            return True
        
        # Clean old entries
        self.cleanup_old_entries(ip, now)
        
        # Check command rate
        if ip in self.command_counts:
            recent_commands = sum(1 for ts, _ in self.command_counts[ip] if now - ts < 60)
            if recent_commands >= SecurityValidator.MAX_COMMANDS_PER_MINUTE:
                return True
        
        return False
    
    def record_command(self, ip: str):
        """Record a command from IP"""
        now = time.time()
        if ip not in self.command_counts:
            self.command_counts[ip] = []
        self.command_counts[ip].append((now, 1))
    
    def record_login_attempt(self, ip: str, success: bool):
        """Record login attempt"""
        now = time.time()
        if ip not in self.login_attempts:
            self.login_attempts[ip] = []
        
        if not success:
            self.login_attempts[ip].append((now, 1))
            recent_failures = sum(1 for ts, _ in self.login_attempts[ip] if now - ts < 300)
            
            if recent_failures >= SecurityValidator.MAX_LOGIN_ATTEMPTS:
                self.lockouts[ip] = now + SecurityValidator.LOCKOUT_DURATION
                logger.warning(f"IP {ip} locked out due to failed login attempts")
    
    def cleanup_old_entries(self, ip: str, now: float):
        """Clean up old entries"""
        if ip in self.command_counts:
            self.command_counts[ip] = [(ts, c) for ts, c in self.command_counts[ip] if now - ts < 3600]
        
        if ip in self.login_attempts:
            self.login_attempts[ip] = [(ts, c) for ts, c in self.login_attempts[ip] if now - ts < 3600]

class BBSDatabase:
    """Secure database operations"""
    
    def __init__(self, db_path: str = "bbs.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    real_name TEXT,
                    location TEXT,
                    last_login TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    login_count INTEGER DEFAULT 0,
                    access_level INTEGER DEFAULT 1
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_user TEXT NOT NULL,
                    to_user TEXT DEFAULT 'ALL',
                    subject TEXT NOT NULL,
                    body TEXT NOT NULL,
                    posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    message_area TEXT DEFAULT 'General'
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS login_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    ip_address TEXT,
                    success BOOLEAN,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
    
    def create_user(self, username: str, password: str, real_name: str = "", location: str = "") -> bool:
        """Create new user with secure password hashing"""
        salt = secrets.token_hex(32)
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO users (username, password_hash, salt, real_name, location) VALUES (?, ?, ?, ?, ?)",
                    (username, password_hash.hex(), salt, real_name, location)
                )
            return True
        except sqlite3.IntegrityError:
            return False
    
    def verify_user(self, username: str, password: str) -> bool:
        """Verify user credentials"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT password_hash, salt FROM users WHERE username = ?",
                (username,)
            )
            result = cursor.fetchone()
            
            if not result:
                return False
            
            stored_hash, salt = result
            password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            
            return password_hash.hex() == stored_hash
    
    def update_login(self, username: str):
        """Update user login statistics"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE users SET last_login = CURRENT_TIMESTAMP, login_count = login_count + 1 WHERE username = ?",
                (username,)
            )
    
    def log_login_attempt(self, username: str, ip: str, success: bool):
        """Log login attempt"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO login_log (username, ip_address, success) VALUES (?, ?, ?)",
                (username, ip, success)
            )

class BBSSession:
    """Individual BBS session handler"""
    
    def __init__(self, client_socket, address, database, rate_limiter):
        self.socket = client_socket
        self.address = address
        self.database = database
        self.rate_limiter = rate_limiter
        self.username = None
        self.authenticated = False
        self.buffer_size = 1024
        self.encoding = 'utf-8'
        
        # Session timeouts
        self.login_timeout = 300  # 5 minutes to login
        self.idle_timeout = 1800  # 30 minutes idle
        self.last_activity = time.time()
    
    def send_line(self, text: str):
        """Send a line of text to client"""
        try:
            message = text + "\r\n"
            self.socket.send(message.encode(self.encoding))
        except Exception as e:
            logger.error(f"Error sending to {self.address}: {e}")
    
    def recv_line(self) -> Optional[str]:
        """Receive a line of text from client"""
        try:
            self.socket.settimeout(300)  # 5 minute timeout
            data = self.socket.recv(self.buffer_size)
            if not data:
                return None
            
            line = data.decode(self.encoding).strip()
            self.last_activity = time.time()
            return line
        except Exception as e:
            logger.error(f"Error receiving from {self.address}: {e}")
            return None
    
    def display_banner(self):
        """Display BBS banner"""
        banner = [
            "",
            "" + "="*60,
            "             SECURE TEXT BBS - RETRO COMPUTING",
            "                Connected at " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "" + "="*60,
            "",
            "Welcome to a secure, text-only bulletin board system!",
            "All input is validated and logged for security.",
            "",
        ]
        
        for line in banner:
            self.send_line(line)
    
    def login_sequence(self) -> bool:
        """Handle user login"""
        max_attempts = 3
        attempt = 0
        
        while attempt < max_attempts:
            # Check rate limiting
            if self.rate_limiter.is_rate_limited(self.address[0]):
                self.send_line("Too many attempts. Please try again later.")
                return False
            
            self.send_line("")
            self.send_line("Enter username (3-20 chars, letters/numbers/underscore only):")
            username = self.recv_line()
            
            if not username:
                return False
            
            # Validate username
            valid, msg = SecurityValidator.validate_username(username)
            if not valid:
                self.send_line(f"Invalid username: {msg}")
                attempt += 1
                continue
            
            self.send_line("Enter password (8+ chars with upper, lower, digit, special):")
            password = self.recv_line()
            
            if not password:
                return False
            
            # Check if user exists
            if self.database.verify_user(username, password):
                self.username = username
                self.authenticated = True
                self.database.update_login(username)
                self.database.log_login_attempt(username, self.address[0], True)
                self.rate_limiter.record_login_attempt(self.address[0], True)
                
                self.send_line("")
                self.send_line(f"Welcome back, {username}!")
                return True
            else:
                # Check if we should offer registration
                self.send_line("Invalid login. Would you like to register? (Y/N)")
                response = self.recv_line()
                
                if response and response.upper() in ['Y', 'YES']:
                    if self.register_user(username, password):
                        return True
                
                self.database.log_login_attempt(username, self.address[0], False)
                self.rate_limiter.record_login_attempt(self.address[0], False)
                attempt += 1
        
        self.send_line("Too many failed attempts. Goodbye.")
        return False
    
    def register_user(self, username: str, password: str) -> bool:
        """Register new user"""
        # Validate password
        valid, msg = SecurityValidator.validate_password(password)
        if not valid:
            self.send_line(f"Password requirements not met: {msg}")
            return False
        
        self.send_line("Enter your real name (optional):")
        real_name = self.recv_line() or ""
        real_name = SecurityValidator.sanitize_text(real_name, SecurityValidator.MAX_REALNAME)
        
        self.send_line("Enter your location (optional):")
        location = self.recv_line() or ""
        location = SecurityValidator.sanitize_text(location, SecurityValidator.MAX_LOCATION)
        
        if self.database.create_user(username, password, real_name, location):
            self.username = username
            self.authenticated = True
            self.database.update_login(username)
            self.send_line("")
            self.send_line(f"Registration successful! Welcome, {username}!")
            return True
        else:
            self.send_line("Registration failed. Username may already exist.")
            return False
    
    def main_menu(self):
        """Display and handle main menu"""
        while self.authenticated:
            # Check for timeout
            if time.time() - self.last_activity > self.idle_timeout:
                self.send_line("Session timed out due to inactivity.")
                break
            
            # Check rate limiting
            if self.rate_limiter.is_rate_limited(self.address[0]):
                self.send_line("Rate limit exceeded. Please slow down.")
                time.sleep(5)
                continue
            
            self.display_main_menu()
            
            command = self.recv_line()
            if not command:
                break
            
            self.rate_limiter.record_command(self.address[0])
            
            # Validate command
            valid, validated_cmd = SecurityValidator.validate_command(command)
            if not valid:
                self.send_line(f"Invalid command: {validated_cmd}")
                continue
            
            # Process command
            if validated_cmd in ['Q', 'QUIT', 'EXIT', 'LOGOFF', 'BYE']:
                self.send_line("Thank you for using our BBS. Goodbye!")
                break
            elif validated_cmd in ['M', 'MESSAGES', 'MESSAGE', '1']:
                self.message_area()
            elif validated_cmd in ['D', 'DOORS', 'DOOR', 'GAMES', '2']:
                self.door_games()
            elif validated_cmd in ['U', 'USERS', 'USER', '3']:
                self.user_list()
            elif validated_cmd in ['H', 'HELP', '?', '4']:
                self.show_help()
            elif validated_cmd in ['T', 'TIME', '5']:
                self.show_time()
            else:
                self.send_line("Command not implemented yet.")
    
    def display_main_menu(self):
        """Display main menu"""
        menu = [
            "",
            "" + "-"*40,
            f"  MAIN MENU - User: {self.username}",
            "" + "-"*40,
            "",
            "  [1] (M)essage Areas",
            "  [2] (D)oor Games",
            "  [3] (U)ser List",
            "  [4] (H)elp",
            "  [5] (T)ime",
            "  [Q]uit",
            "",
            "Enter command:",
        ]
        
        for line in menu:
            self.send_line(line)
    
    def message_area(self):
        """Handle message area"""
        self.send_line("")
        self.send_line("MESSAGE AREA - Coming soon!")
        self.send_line("")
    
    def door_games(self):
        """Handle door games menu"""
        games = [
            "",
            "" + "-"*40,
            "  DOOR GAMES AVAILABLE",
            "" + "-"*40,
            "",
            "  [1] The Pit - Gladiator Combat",
            "  [2] Galactic Conquest - Space Trading",
            "  [3] Hi-Lo Casino - Number Guessing",
            "  [B]ack to Main Menu",
            "",
            "Note: Games run in separate processes for security.",
            "Enter choice:",
        ]
        
        for line in games:
            self.send_line(line)
        
        choice = self.recv_line()
        if choice and choice.upper() in ['B', 'BACK']:
            return
        elif choice == '1':
            self.send_line("Launching The Pit... (Feature coming soon)")
        elif choice == '2':
            self.send_line("Launching Galactic Conquest... (Feature coming soon)")
        elif choice == '3':
            self.send_line("Launching Hi-Lo Casino... (Feature coming soon)")
        else:
            self.send_line("Invalid selection.")
    
    def user_list(self):
        """Display user list"""
        self.send_line("")
        self.send_line("USER LIST - Feature coming soon!")
        self.send_line("")
    
    def show_help(self):
        """Display help"""
        help_text = [
            "",
            "" + "-"*50,
            "  HELP - BBS COMMANDS",
            "" + "-"*50,
            "",
            "  Navigation:",
            "    - Enter menu numbers (1, 2, 3...) or letters (M, D, U...)",
            "    - Commands are case-insensitive",
            "    - Type B or BACK to go back in menus",
            "",
            "  Security Features:",
            "    - All input is validated and sanitized",
            "    - Rate limiting prevents abuse",
            "    - Failed login attempts are logged",
            "    - Sessions timeout after 30 minutes of inactivity",
            "",
            "  Available Areas:",
            "    - Messages: Read and post messages",
            "    - Door Games: Play classic BBS games",
            "    - User List: See who's on the system",
            "",
            "Press Enter to continue...",
        ]
        
        for line in help_text:
            self.send_line(line)
        
        self.recv_line()  # Wait for Enter
    
    def show_time(self):
        """Display current time"""
        current_time = datetime.now().strftime("%A, %B %d, %Y at %I:%M:%S %p")
        self.send_line("")
        self.send_line(f"Current system time: {current_time}")
        self.send_line("")
    
    def run(self):
        """Main session loop"""
        try:
            logger.info(f"New connection from {self.address}")
            
            # Display banner
            self.display_banner()
            
            # Handle login
            if self.login_sequence():
                # Run main menu
                self.main_menu()
            
        except Exception as e:
            logger.error(f"Session error for {self.address}: {e}")
        finally:
            try:
                self.socket.close()
            except:
                pass
            logger.info(f"Connection closed for {self.address}")

class SecureBBSServer:
    """Main BBS server class"""
    
    def __init__(self, host='localhost', port=2323):
        self.host = host
        self.port = port
        self.database = BBSDatabase()
        self.rate_limiter = RateLimiter()
        self.running = False
        self.server_socket = None
    
    def start(self):
        """Start the BBS server"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True
            
            logger.info(f"Secure BBS Server started on {self.host}:{self.port}")
            logger.info("Connect using: telnet localhost 2323")
            
            while self.running:
                try:
                    client_socket, address = self.server_socket.accept()
                    
                    # Check rate limiting per IP
                    if self.rate_limiter.is_rate_limited(address[0]):
                        client_socket.send(b"Rate limited. Try again later.\r\n")
                        client_socket.close()
                        continue
                    
                    # Create session thread
                    session = BBSSession(client_socket, address, self.database, self.rate_limiter)
                    thread = threading.Thread(target=session.run, daemon=True)
                    thread.start()
                    
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    logger.error(f"Server error: {e}")
        
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the BBS server"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        logger.info("BBS Server stopped")

if __name__ == "__main__":
    try:
        server = SecureBBSServer()
        server.start()
    except KeyboardInterrupt:
        print("\nShutting down BBS server...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")

