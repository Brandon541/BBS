#!/usr/bin/env python3
"""
Web-based BBS Interface
Integrates the secure BBS functionality into the web application
"""

import re
import hashlib
import secrets
import time
import sqlite3
import html
import logging
from datetime import datetime
from typing import Optional, Dict, List, Tuple

# Import BBS classes from the bbs_server module
import sys
import os
sys.path.append('bbs_server')
from secure_bbs import SecurityValidator, RateLimiter, BBSDatabase

class WebBBSSession:
    """Web-based BBS session handler"""
    
    def __init__(self, session_id: str, ip_address: str, database, rate_limiter):
        self.session_id = session_id
        self.ip_address = ip_address
        self.database = database
        self.rate_limiter = rate_limiter
        self.username = None
        self.authenticated = False
        self.current_menu = "login"
        self.last_activity = time.time()
        self.login_attempts = 0
        self.max_login_attempts = 3
        
        # Session timeouts
        self.login_timeout = 300  # 5 minutes to login
        self.idle_timeout = 1800  # 30 minutes idle
        
        # State for multi-step processes
        self.registration_state = {}
        self.temp_data = {}
    
    def is_session_valid(self) -> bool:
        """Check if session is still valid"""
        now = time.time()
        
        # Check idle timeout
        if now - self.last_activity > self.idle_timeout:
            return False
        
        # Check login timeout if not authenticated
        if not self.authenticated and now - self.last_activity > self.login_timeout:
            return False
        
        return True
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = time.time()
    
    def process_input(self, user_input: str) -> Dict:
        """Process user input and return response"""
        self.update_activity()
        
        # Check rate limiting
        if self.rate_limiter.is_rate_limited(self.ip_address):
            return {
                'output': ['Rate limit exceeded. Please slow down.'],
                'prompt': 'Press Enter to continue...',
                'clear_screen': False,
                'menu': self.current_menu
            }
        
        self.rate_limiter.record_command(self.ip_address)
        
        # Validate and sanitize input
        if user_input:
            user_input = SecurityValidator.sanitize_text(user_input, 100)
        
        # Route to appropriate handler based on current menu
        if self.current_menu == "login":
            return self.handle_login(user_input)
        elif self.current_menu == "register":
            return self.handle_registration(user_input)
        elif self.current_menu == "main":
            return self.handle_main_menu(user_input)
        elif self.current_menu == "messages":
            return self.handle_message_area(user_input)
        elif self.current_menu == "users":
            return self.handle_user_list(user_input)
        elif self.current_menu == "help":
            return self.handle_help(user_input)
        elif self.current_menu == "doors":
            return self.handle_door_games(user_input)
        else:
            return self.show_main_menu()
    
    def handle_login(self, user_input: str) -> Dict:
        """Handle login process"""
        if not hasattr(self, 'login_step'):
            self.login_step = 'banner'
        
        if self.login_step == 'banner':
            self.login_step = 'username'
            return {
                'output': [
                    "",
                    "" + "="*60,
                    "             SECURE TEXT BBS - RETRO COMPUTING",
                    "                Connected at " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "" + "="*60,
                    "",
                    "Welcome to a secure, text-only bulletin board system!",
                    "All input is validated and logged for security.",
                    "",
                ],
                'prompt': 'Enter username (3-20 chars, letters/numbers/underscore only):',
                'clear_screen': True,
                'menu': 'login'
            }
        
        elif self.login_step == 'username':
            if not user_input.strip():
                return {
                    'output': ['Username cannot be empty.'],
                    'prompt': 'Enter username:',
                    'clear_screen': False,
                    'menu': 'login'
                }
            
            # Validate username
            valid, msg = SecurityValidator.validate_username(user_input)
            if not valid:
                return {
                    'output': [f'Invalid username: {msg}'],
                    'prompt': 'Enter username:',
                    'clear_screen': False,
                    'menu': 'login'
                }
            
            self.temp_data['username'] = user_input
            self.login_step = 'password'
            return {
                'output': [],
                'prompt': 'Enter password (8+ chars with upper, lower, digit, special):',
                'clear_screen': False,
                'menu': 'login',
                'password_field': True
            }
        
        elif self.login_step == 'password':
            username = self.temp_data.get('username', '')
            password = user_input
            
            if not password:
                return {
                    'output': ['Password cannot be empty.'],
                    'prompt': 'Enter password:',
                    'clear_screen': False,
                    'menu': 'login',
                    'password_field': True
                }
            
            # Check credentials
            if self.database.verify_user(username, password):
                self.username = username
                self.authenticated = True
                self.database.update_login(username)
                self.database.log_login_attempt(username, self.ip_address, True)
                self.rate_limiter.record_login_attempt(self.ip_address, True)
                
                return self.show_main_menu(welcome=True)
            else:
                # Offer registration for new users
                self.login_attempts += 1
                self.database.log_login_attempt(username, self.ip_address, False)
                self.rate_limiter.record_login_attempt(self.ip_address, False)
                
                if self.login_attempts >= self.max_login_attempts:
                    return {
                        'output': [
                            'Too many failed attempts.',
                            'Session terminated for security.'
                        ],
                        'prompt': '',
                        'clear_screen': False,
                        'menu': 'login',
                        'session_ended': True
                    }
                
                self.login_step = 'register_offer'
                return {
                    'output': [
                        'Invalid login.',
                        '',
                        'Would you like to register a new account? (Y/N)'
                    ],
                    'prompt': 'Your choice:',
                    'clear_screen': False,
                    'menu': 'login'
                }
        
        elif self.login_step == 'register_offer':
            response = user_input.upper().strip()
            if response in ['Y', 'YES']:
                # Start registration process
                self.current_menu = 'register'
                self.registration_state = {
                    'step': 'username',
                    'username': self.temp_data.get('username', ''),
                    'password': ''
                }
                return self.handle_registration('')
            else:
                # Return to login
                self.login_step = 'username'
                self.temp_data = {}
                return {
                    'output': [''],
                    'prompt': 'Enter username:',
                    'clear_screen': False,
                    'menu': 'login'
                }
        
        return self.handle_login('')  # Default case
    
    def handle_registration(self, user_input: str) -> Dict:
        """Handle user registration process"""
        step = self.registration_state.get('step', 'username')
        
        if step == 'username':
            if self.registration_state.get('username'):
                # Username already provided from login attempt
                username = self.registration_state['username']
                self.registration_state['step'] = 'password'
                return {
                    'output': [
                        f'Registering username: {username}',
                        '',
                        'Password requirements:',
                        '- At least 8 characters',
                        '- Must contain uppercase and lowercase letters',
                        '- Must contain at least one digit',
                        '- Must contain at least one special character (!@#$%^&*...)',
                    ],
                    'prompt': 'Enter password:',
                    'clear_screen': False,
                    'menu': 'register',
                    'password_field': True
                }
            else:
                return {
                    'output': [
                        'USER REGISTRATION',
                        '=' * 20,
                        '',
                        'Username requirements:',
                        '- 3-20 characters',
                        '- Letters, numbers, and underscores only',
                        '- Must start with a letter',
                    ],
                    'prompt': 'Enter desired username:',
                    'clear_screen': True,
                    'menu': 'register'
                }
        
        elif step == 'password':
            if not user_input:
                return {
                    'output': ['Password cannot be empty.'],
                    'prompt': 'Enter password:',
                    'clear_screen': False,
                    'menu': 'register',
                    'password_field': True
                }
            
            # Validate password
            valid, msg = SecurityValidator.validate_password(user_input)
            if not valid:
                return {
                    'output': [f'Password validation failed: {msg}'],
                    'prompt': 'Enter password:',
                    'clear_screen': False,
                    'menu': 'register',
                    'password_field': True
                }
            
            self.registration_state['password'] = user_input
            self.registration_state['step'] = 'real_name'
            return {
                'output': ['Password accepted.'],
                'prompt': 'Enter your real name (optional, press Enter to skip):',
                'clear_screen': False,
                'menu': 'register'
            }
        
        elif step == 'real_name':
            real_name = SecurityValidator.sanitize_text(user_input or '', SecurityValidator.MAX_REALNAME)
            self.registration_state['real_name'] = real_name
            self.registration_state['step'] = 'location'
            return {
                'output': [],
                'prompt': 'Enter your location (optional, press Enter to skip):',
                'clear_screen': False,
                'menu': 'register'
            }
        
        elif step == 'location':
            location = SecurityValidator.sanitize_text(user_input or '', SecurityValidator.MAX_LOCATION)
            
            # Create the user account
            username = self.registration_state['username']
            password = self.registration_state['password']
            real_name = self.registration_state.get('real_name', '')
            
            if self.database.create_user(username, password, real_name, location):
                self.username = username
                self.authenticated = True
                self.database.update_login(username)
                self.current_menu = 'main'
                
                return {
                    'output': [
                        '',
                        'Registration successful!',
                        f'Welcome to the BBS, {username}!',
                        ''
                    ],
                    'prompt': 'Press Enter to continue to main menu...',
                    'clear_screen': False,
                    'menu': 'register'
                }
            else:
                return {
                    'output': [
                        'Registration failed.',
                        'Username may already be taken.',
                        ''
                    ],
                    'prompt': 'Press Enter to try again...',
                    'clear_screen': False,
                    'menu': 'register'
                }
        
        return self.show_main_menu()
    
    def show_main_menu(self, welcome=False) -> Dict:
        """Display main menu"""
        self.current_menu = 'main'
        
        output = []
        if welcome:
            output.extend([
                '',
                f'Welcome back, {self.username}!',
                ''
            ])
        
        output.extend([
            '',
            "-"*40,
            f"  MAIN MENU - User: {self.username}",
            "-"*40,
            "",
            "  [1] (M)essage Areas",
            "  [2] (D)oor Games",
            "  [3] (U)ser List",
            "  [4] (H)elp",
            "  [5] (T)ime",
            "  [Q]uit",
            "",
        ])
        
        return {
            'output': output,
            'prompt': 'Enter command:',
            'clear_screen': welcome,
            'menu': 'main'
        }
    
    def handle_main_menu(self, user_input: str) -> Dict:
        """Handle main menu commands"""
        if not user_input:
            return self.show_main_menu()
        
        # Validate command
        valid, validated_cmd = SecurityValidator.validate_command(user_input)
        if not valid:
            return {
                'output': [f'Invalid command: {user_input}'],
                'prompt': 'Enter command:',
                'clear_screen': False,
                'menu': 'main'
            }
        
        # Process command
        if validated_cmd in ['Q', 'QUIT', 'EXIT', 'LOGOFF', 'BYE']:
            return {
                'output': [
                    'Thank you for using our BBS.',
                    'Your session has been logged off.',
                    'Goodbye!'
                ],
                'prompt': '',
                'clear_screen': False,
                'menu': 'main',
                'session_ended': True
            }
        elif validated_cmd in ['M', 'MESSAGES', 'MESSAGE', '1']:
            self.current_menu = 'messages'
            return self.handle_message_area('')
        elif validated_cmd in ['D', 'DOORS', 'DOOR', 'GAMES', '2']:
            self.current_menu = 'doors'
            return self.handle_door_games('')
        elif validated_cmd in ['U', 'USERS', 'USER', '3']:
            self.current_menu = 'users'
            return self.handle_user_list('')
        elif validated_cmd in ['H', 'HELP', '?', '4']:
            self.current_menu = 'help'
            return self.handle_help('')
        elif validated_cmd in ['T', 'TIME', '5']:
            return self.show_time()
        else:
            return {
                'output': ['Command not implemented yet.'],
                'prompt': 'Enter command:',
                'clear_screen': False,
                'menu': 'main'
            }
    
    def handle_message_area(self, user_input: str) -> Dict:
        """Handle message area"""
        if not hasattr(self, 'message_area'):
            self.message_area = 'General'
        
        if not hasattr(self, 'message_state'):
            self.message_state = 'menu'
        
        if self.message_state == 'menu':
            return self.show_message_menu(user_input)
        elif self.message_state == 'view':
            return self.handle_view_messages(user_input)
        elif self.message_state == 'post':
            return self.handle_post_message(user_input)
        else:
            self.message_state = 'menu'
            return self.show_message_menu('')
    
    def show_message_menu(self, user_input: str) -> Dict:
        """Show message area main menu"""
        if not user_input:
            return {
                'output': [
                    '',
                    "-"*50,
                    f"  MESSAGE AREAS - {self.message_area}",
                    "-"*50,
                    "",
                    "  [1] General Discussion",
                    "  [2] Gaming Talk",
                    "  [3] Technical Support",
                    "  [4] Announcements (Read Only)",
                    "",
                    "  [R]ead Messages",
                    "  [P]ost New Message",
                    "  [B]ack to Main Menu",
                    "",
                ],
                'prompt': 'Enter choice:',
                'clear_screen': True,
                'menu': 'messages'
            }
        
        if user_input.upper() in ['B', 'BACK']:
            return self.show_main_menu()
        elif user_input in ['1']:
            self.message_area = 'General'
            return self.show_message_menu('')
        elif user_input in ['2']:
            self.message_area = 'Gaming'
            return self.show_message_menu('')
        elif user_input in ['3']:
            self.message_area = 'Technical'
            return self.show_message_menu('')
        elif user_input in ['4']:
            self.message_area = 'Announcements'
            return self.show_message_menu('')
        elif user_input.upper() in ['R', 'READ']:
            self.message_state = 'view'
            return self.handle_view_messages('')
        elif user_input.upper() in ['P', 'POST']:
            if self.message_area == 'Announcements':
                return {
                    'output': ['Announcements area is read-only.'],
                    'prompt': 'Press Enter to continue...',
                    'clear_screen': False,
                    'menu': 'messages'
                }
            self.message_state = 'post'
            self.temp_message = {'step': 'subject'}
            return self.handle_post_message('')
        else:
            return {
                'output': ['Invalid choice.'],
                'prompt': 'Enter choice:',
                'clear_screen': False,
                'menu': 'messages'
            }
    
    def handle_view_messages(self, user_input: str) -> Dict:
        """Handle viewing messages"""
        # Check if we're returning from reading a message or any continue prompt
        if hasattr(self, 'reading_message') and self.reading_message:
            self.reading_message = False
            # Return to message list
            return self.handle_view_messages('')
        
        # Check if returning from posting continuation
        if hasattr(self, 'post_continue') and self.post_continue:
            self.post_continue = False
            self.message_state = 'menu'
            return self.show_message_menu('')
        
        if not user_input:
            # Get messages from database
            try:
                with sqlite3.connect(self.database.db_path) as conn:
                    cursor = conn.execute(
                        "SELECT id, from_user, subject, posted_at FROM messages WHERE message_area = ? ORDER BY posted_at DESC LIMIT 20",
                        (self.message_area,)
                    )
                    messages = cursor.fetchall()
                
                output = [
                    '',
                    "-"*60,
                    f"  MESSAGES - {self.message_area} Discussion",
                    "-"*60,
                    "",
                ]
                
                if messages:
                    output.append(f"{'#':<3} {'From':<15} {'Subject':<25} {'Date':<15}")
                    output.append("-" * 60)
                    
                    for msg_id, from_user, subject, posted_at in messages:
                        # Truncate long subjects
                        if len(subject) > 22:
                            subject = subject[:19] + "..."
                        
                        # Format date
                        try:
                            msg_time = datetime.fromisoformat(posted_at.replace('Z', '+00:00'))
                            date_str = msg_time.strftime("%m/%d %H:%M")
                        except:
                            date_str = "Unknown"
                        
                        output.append(f"{msg_id:<3} {from_user:<15} {subject:<25} {date_str:<15}")
                    
                    output.extend([
                        "",
                        "Enter message number to read, or:",
                    ])
                else:
                    output.append("No messages in this area yet.")
                    output.append("")
                
                output.extend([
                    "[P]ost New Message | [B]ack to Menu",
                    ""
                ])
                
                return {
                    'output': output,
                    'prompt': 'Enter choice:',
                    'clear_screen': True,
                    'menu': 'messages'
                }
            except Exception as e:
                return {
                    'output': [
                        'Error retrieving messages.',
                        '[B]ack to Menu'
                    ],
                    'prompt': 'Enter choice:',
                    'clear_screen': True,
                    'menu': 'messages'
                }
        
        if user_input.upper() in ['B', 'BACK']:
            self.message_state = 'menu'
            return self.show_message_menu('')
        elif user_input.upper() in ['P', 'POST']:
            if self.message_area == 'Announcements':
                return {
                    'output': ['Announcements area is read-only.'],
                    'prompt': 'Press Enter to continue...',
                    'clear_screen': False,
                    'menu': 'messages',
                    'message_continue': True
                }
            self.message_state = 'post'
            self.temp_message = {'step': 'subject'}
            return self.handle_post_message('')
        else:
            # Try to read a specific message
            try:
                msg_id = int(user_input)
                self.reading_message = True
                return self.read_message(msg_id)
            except ValueError:
                return {
                    'output': ['Invalid choice. Enter a message number, P to post, or B to go back.'],
                    'prompt': 'Enter choice:',
                    'clear_screen': False,
                    'menu': 'messages'
                }
    
    def read_message(self, msg_id: int) -> Dict:
        """Read a specific message"""
        try:
            with sqlite3.connect(self.database.db_path) as conn:
                cursor = conn.execute(
                    "SELECT from_user, to_user, subject, body, posted_at FROM messages WHERE id = ? AND message_area = ?",
                    (msg_id, self.message_area)
                )
                message = cursor.fetchone()
            
            if not message:
                return {
                    'output': ['Message not found.'],
                    'prompt': 'Press Enter to continue...',
                    'clear_screen': False,
                    'menu': 'messages',
                    'message_read_continue': True
                }
            
            from_user, to_user, subject, body, posted_at = message
            
            # Format date
            try:
                msg_time = datetime.fromisoformat(posted_at.replace('Z', '+00:00'))
                date_str = msg_time.strftime("%A, %B %d, %Y at %I:%M %p")
            except:
                date_str = "Unknown date"
            
            output = [
                '',
                "=" * 60,
                f"Message #{msg_id} - {self.message_area}",
                "=" * 60,
                "",
                f"From: {from_user}",
                f"To: {to_user}",
                f"Subject: {subject}",
                f"Posted: {date_str}",
                "",
                "-" * 60,
            ]
            
            # Split body into lines if it's long
            body_lines = body.split('\n')
            for line in body_lines:
                # Wrap long lines
                while len(line) > 58:
                    output.append(line[:58])
                    line = line[58:]
                if line:
                    output.append(line)
            
            output.extend([
                "",
                "-" * 60,
                "Press Enter to continue..."
            ])
            
            return {
                'output': output,
                'prompt': '',
                'clear_screen': True,
                'menu': 'messages',
                'message_read_continue': True
            }
        except Exception as e:
            return {
                'output': ['Error reading message.'],
                'prompt': 'Press Enter to continue...',
                'clear_screen': False,
                'menu': 'messages',
                'message_read_continue': True
            }
    
    def handle_post_message(self, user_input: str) -> Dict:
        """Handle posting a new message"""
        if not hasattr(self, 'temp_message'):
            self.temp_message = {'step': 'subject'}
        
        step = self.temp_message.get('step', 'subject')
        
        if step == 'subject':
            if not user_input:
                return {
                    'output': [
                        '',
                        "-" * 50,
                        f"POST NEW MESSAGE - {self.message_area}",
                        "-" * 50,
                        "",
                        "Enter a subject for your message (max 100 characters):",
                        "(Type CANCEL to abort)",
                        ""
                    ],
                    'prompt': 'Subject:',
                    'clear_screen': True,
                    'menu': 'messages'
                }
            
            if user_input.upper() == 'CANCEL':
                self.message_state = 'menu'
                return self.show_message_menu('')
            
            if not user_input.strip():
                return {
                    'output': ['Subject cannot be empty.'],
                    'prompt': 'Subject:',
                    'clear_screen': False,
                    'menu': 'messages'
                }
            
            subject = SecurityValidator.sanitize_text(user_input, 100)
            self.temp_message['subject'] = subject
            self.temp_message['step'] = 'body'
            
            return {
                'output': [
                    f'Subject: {subject}',
                    '',
                    'Enter your message body (max 1000 characters):',
                    '(Type END on a line by itself to finish, or CANCEL to abort)',
                    ''
                ],
                'prompt': 'Message:',
                'clear_screen': False,
                'menu': 'messages'
            }
        
        elif step == 'body':
            if user_input.upper() == 'CANCEL':
                self.message_state = 'menu'
                return self.show_message_menu('')
            
            if user_input.upper() == 'END':
                # Post the message
                return self.post_message_to_db()
            
            # Accumulate message body
            if 'body_lines' not in self.temp_message:
                self.temp_message['body_lines'] = []
            
            line = SecurityValidator.sanitize_text(user_input, 200)
            self.temp_message['body_lines'].append(line)
            
            # Check length limit
            total_length = sum(len(line) for line in self.temp_message['body_lines'])
            if total_length > 1000:
                return {
                    'output': ['Message too long. Type END to finish or CANCEL to abort.'],
                    'prompt': 'Message:',
                    'clear_screen': False,
                    'menu': 'messages'
                }
            
            return {
                'output': [],
                'prompt': 'Message:',
                'clear_screen': False,
                'menu': 'messages'
            }
        
        return self.show_message_menu('')
    
    def post_message_to_db(self) -> Dict:
        """Post the message to the database"""
        try:
            subject = self.temp_message.get('subject', '')
            body_lines = self.temp_message.get('body_lines', [])
            body = '\n'.join(body_lines)
            
            if not subject or not body:
                return {
                    'output': ['Message is incomplete.'],
                    'prompt': 'Press Enter to continue...',
                    'clear_screen': False,
                    'menu': 'messages'
                }
            
            with sqlite3.connect(self.database.db_path) as conn:
                conn.execute(
                    "INSERT INTO messages (from_user, to_user, subject, body, message_area) VALUES (?, ?, ?, ?, ?)",
                    (self.username, 'ALL', subject, body, self.message_area)
                )
            
            self.message_state = 'view'  # Go back to view messages
            self.temp_message = {}
            self.post_continue = True  # Flag for continue handling
            
            return {
                'output': [
                    '',
                    'Message posted successfully!',
                    f'Posted to: {self.message_area}',
                    f'Subject: {subject}',
                    ''
                ],
                'prompt': 'Press Enter to continue...',
                'clear_screen': False,
                'menu': 'messages'
            }
        except Exception as e:
            return {
                'output': [
                    'Error posting message.',
                    'Please try again later.'
                ],
                'prompt': 'Press Enter to continue...',
                'clear_screen': False,
                'menu': 'messages'
            }
    
    def handle_door_games(self, user_input: str) -> Dict:
        """Handle door games menu"""
        if not user_input:
            return {
                'output': [
                    '',
                    "-"*40,
                    "  DOOR GAMES AVAILABLE",
                    "-"*40,
                    "",
                    "  [1] The Pit - Gladiator Combat",
                    "  [2] Galactic Conquest - Space Trading", 
                    "  [3] Hi-Lo Casino - Number Guessing",
                    "",
                    "  [B]ack to Main Menu",
                    "",
                    "Note: Games launch in the main web interface.",
                    "Use the 'Games' section to play door games.",
                ],
                'prompt': 'Enter choice:',
                'clear_screen': True,
                'menu': 'doors'
            }
        
        if user_input.upper() in ['B', 'BACK']:
            return self.show_main_menu()
        elif user_input == '1':
            return {
                'output': [
                    'The Pit - Gladiator Combat Arena',
                    '',
                    'To play this game, visit the main web interface',
                    'and select "The Pit" from the games menu.',
                    '',
                    'This provides the full interactive experience',
                    'with real-time combat and character progression.'
                ],
                'prompt': 'Press Enter to continue...',
                'clear_screen': False,
                'menu': 'doors'
            }
        elif user_input == '2':
            return {
                'output': [
                    'Galactic Conquest - Space Trading Game',
                    '',
                    'To play this game, visit the main web interface',
                    'and select "Galactic Conquest" from the games menu.',
                    '',
                    'Trade across the galaxy and build your fortune!'
                ],
                'prompt': 'Press Enter to continue...',
                'clear_screen': False,
                'menu': 'doors'
            }
        elif user_input == '3':
            return {
                'output': [
                    'Hi-Lo Casino - Number Guessing Game',
                    '',
                    'To play this game, visit the main web interface',
                    'and select "Hi-Lo Casino" from the games menu.',
                    '',
                    'Test your luck and win big!'
                ],
                'prompt': 'Press Enter to continue...',
                'clear_screen': False,
                'menu': 'doors'
            }
        else:
            return {
                'output': ['Invalid selection.'],
                'prompt': 'Enter choice:',
                'clear_screen': False,
                'menu': 'doors'
            }
    
    def handle_user_list(self, user_input: str) -> Dict:
        """Handle user list display"""
        if not user_input:
            # Get user list from database
            try:
                with sqlite3.connect(self.database.db_path) as conn:
                    cursor = conn.execute(
                        "SELECT username, real_name, last_login, login_count FROM users ORDER BY last_login DESC LIMIT 20"
                    )
                    users = cursor.fetchall()
                
                output = [
                    '',
                    "-"*50,
                    "  USER LIST - Recent Visitors",
                    "-"*50,
                    "",
                ]
                
                if users:
                    output.append(f"{'Username':<15} {'Real Name':<20} {'Last Login':<15}")
                    output.append("-" * 50)
                    
                    for username, real_name, last_login, login_count in users:
                        real_name = real_name or "(not provided)"
                        if len(real_name) > 18:
                            real_name = real_name[:15] + "..."
                        
                        if last_login:
                            # Parse the timestamp
                            try:
                                login_time = datetime.fromisoformat(last_login)
                                login_str = login_time.strftime("%Y-%m-%d")
                            except:
                                login_str = "Unknown"
                        else:
                            login_str = "Never"
                        
                        output.append(f"{username:<15} {real_name:<20} {login_str:<15}")
                else:
                    output.append("No users found.")
                
                output.extend([
                    "",
                    "[B]ack to Main Menu",
                ])
                
                return {
                    'output': output,
                    'prompt': 'Enter choice:',
                    'clear_screen': True,
                    'menu': 'users'
                }
            except Exception as e:
                return {
                    'output': [
                        'Error retrieving user list.',
                        '[B]ack to Main Menu'
                    ],
                    'prompt': 'Enter choice:',
                    'clear_screen': True,
                    'menu': 'users'
                }
        
        if user_input.upper() in ['B', 'BACK']:
            return self.show_main_menu()
        
        return self.handle_user_list('')
    
    def handle_help(self, user_input: str) -> Dict:
        """Handle help system"""
        if not user_input:
            return {
                'output': [
                    '',
                    "-"*50,
                    "  HELP - BBS COMMANDS",
                    "-"*50,
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
                    "    - Messages: Read and post messages (coming soon)",
                    "    - Door Games: Information about available games",
                    "    - User List: See who's on the system",
                    "",
                    "  Note: For full game experience, use the main web interface.",
                    "  This BBS interface provides classic text-only navigation.",
                ],
                'prompt': 'Press Enter to continue...',
                'clear_screen': True,
                'menu': 'help'
            }
        
        return self.show_main_menu()
    
    def show_time(self) -> Dict:
        """Display current time"""
        current_time = datetime.now().strftime("%A, %B %d, %Y at %I:%M:%S %p")
        return {
            'output': [
                '',
                f'Current system time: {current_time}',
                ''
            ],
            'prompt': 'Enter command:',
            'clear_screen': False,
            'menu': 'main'
        }

class WebBBSManager:
    """Manages web-based BBS sessions"""
    
    def __init__(self):
        self.database = BBSDatabase("bbs.db")
        self.rate_limiter = RateLimiter()
        self.sessions = {}  # {session_id: WebBBSSession}
        
        # Cleanup old sessions periodically
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # 5 minutes
    
    def cleanup_sessions(self):
        """Remove expired sessions"""
        now = time.time()
        if now - self.last_cleanup < self.cleanup_interval:
            return
        
        expired_sessions = []
        for session_id, session in self.sessions.items():
            if not session.is_session_valid():
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
        
        self.last_cleanup = now
    
    def get_or_create_session(self, session_id: str, ip_address: str) -> WebBBSSession:
        """Get existing session or create new one"""
        self.cleanup_sessions()
        
        if session_id not in self.sessions:
            self.sessions[session_id] = WebBBSSession(
                session_id, ip_address, self.database, self.rate_limiter
            )
        
        return self.sessions[session_id]
    
    def process_input(self, session_id: str, ip_address: str, user_input: str) -> Dict:
        """Process input for a session"""
        session = self.get_or_create_session(session_id, ip_address)
        
        if not session.is_session_valid():
            # Session expired, create new one
            self.sessions[session_id] = WebBBSSession(
                session_id, ip_address, self.database, self.rate_limiter
            )
            session = self.sessions[session_id]
        
        return session.process_input(user_input)
    
    def end_session(self, session_id: str):
        """End a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]

