# Secure Text-Only BBS Server

A hardened, text-only bulletin board system with comprehensive security features.

## 🔒 Security Features

### Input Validation
- **Username validation**: 3-20 characters, alphanumeric + underscore, must start with letter
- **Password strength**: Minimum 8 chars with uppercase, lowercase, digit, and special character
- **Command validation**: Only predefined commands are accepted
- **Text sanitization**: HTML escaping, control character removal, pattern filtering
- **Length limits**: All inputs have maximum length restrictions

### Authentication & Access Control
- **Secure password hashing**: PBKDF2 with SHA-256 and random salts (100,000 iterations)
- **Rate limiting**: Max 30 commands per minute, 5 login attempts per IP
- **Account lockout**: 5-minute lockout after failed login attempts
- **Session timeouts**: 5-minute login timeout, 30-minute idle timeout
- **Login logging**: All login attempts logged with IP addresses

### Abuse Prevention
- **Banned patterns**: Protection against XSS, SQL injection, directory traversal
- **Control character filtering**: Removes null bytes and control characters
- **Reserved usernames**: Prevents use of system account names
- **Connection limiting**: Rate limiting per IP address

### Data Security
- **SQLite database**: Parameterized queries prevent SQL injection
- **Secure tokens**: Cryptographically secure random salt generation
- **Input encoding**: UTF-8 encoding with proper error handling
- **Buffer limits**: Fixed buffer sizes prevent overflow attacks

## 🚀 Getting Started

### Prerequisites
- Python 3.6 or higher
- Standard library only (no external dependencies)

### Starting the Server

```bash
# Basic startup
python3 start_bbs.py

# Custom host and port
python3 start_bbs.py --host 0.0.0.0 --port 2323

# Enable debug logging
python3 start_bbs.py --debug
```

### Connecting to the BBS

```bash
# Using telnet
telnet localhost 2323

# Using netcat
nc localhost 2323

# Using PuTTY (Windows)
# Set connection type to "Raw" or "Telnet"
# Host: localhost, Port: 2323
```

## 📋 BBS Features

### User Management
- **Registration**: New users can register with validated credentials
- **Authentication**: Secure login with rate limiting
- **User database**: SQLite database stores user information
- **Access levels**: Foundation for future permission systems

### Menu System
- **Main menu**: Navigate with numbers or letter commands
- **Message areas**: (Coming soon) Read and post messages
- **Door games**: Launch classic BBS games
- **User list**: View system users
- **Help system**: Comprehensive command help
- **Time display**: Current system time

### Security Monitoring
- **Comprehensive logging**: All activities logged to `bbs.log`
- **Failed login tracking**: Automatic IP lockout for abuse
- **Command validation**: Only safe commands accepted
- **Session monitoring**: Automatic timeout for inactive sessions

## 🛡️ Security Architecture

### Input Validation Layers
1. **Length validation**: All inputs checked against maximum lengths
2. **Character validation**: Allowed character sets enforced
3. **Pattern validation**: Regex patterns detect malicious content
4. **Content sanitization**: HTML escaping and character filtering
5. **Command validation**: Whitelist of allowed commands only

### Rate Limiting System
- **Per-IP tracking**: Separate limits for commands and login attempts
- **Sliding window**: Time-based counters with automatic cleanup
- **Escalating responses**: Warnings → delays → temporary bans
- **Automatic recovery**: Limits reset after time periods

### Database Security
- **Parameterized queries**: All SQL uses parameter binding
- **Connection management**: Proper connection handling and cleanup
- **Transaction isolation**: Database operations properly isolated
- **Schema validation**: Table structure enforced at startup

## 📂 File Structure

```
bbs_server/
├── secure_bbs.py      # Main BBS server implementation
├── start_bbs.py       # Server startup script
├── README.md          # This documentation
├── bbs.db            # SQLite database (created automatically)
└── bbs.log           # Server log file (created automatically)
```

## 🔧 Configuration

### Server Settings
- **Host**: Default `localhost`, configurable via `--host`
- **Port**: Default `2323`, configurable via `--port`
- **Logging**: INFO level, file and console output

### Security Settings (in `SecurityValidator` class)
- `MAX_USERNAME = 20`: Maximum username length
- `MAX_PASSWORD = 128`: Maximum password length
- `MAX_COMMANDS_PER_MINUTE = 30`: Command rate limit
- `MAX_LOGIN_ATTEMPTS = 5`: Login attempts before lockout
- `LOCKOUT_DURATION = 300`: Lockout duration in seconds

### Session Settings (in `BBSSession` class)
- `login_timeout = 300`: Time to complete login (5 minutes)
- `idle_timeout = 1800`: Session idle timeout (30 minutes)
- `buffer_size = 1024`: Network buffer size

## 🚨 Security Considerations

### Network Security
- **Plaintext protocol**: Communications are not encrypted
- **Local use recommended**: Designed for localhost/LAN use
- **Firewall protection**: Use firewall rules for internet exposure
- **VPN recommended**: Use VPN for remote access

### System Security
- **Non-privileged port**: Default port 2323 doesn't require root
- **File permissions**: Ensure database and log files have proper permissions
- **Process isolation**: Run as non-root user
- **Resource limits**: Consider ulimit settings for production use

## 🔍 Monitoring & Logging

### Log Levels
- **INFO**: Normal operations, connections, logins
- **WARNING**: Security events, rate limiting, failed attempts
- **ERROR**: System errors, network issues, database problems

### Log Format
```
2024-01-01 12:00:00,000 - INFO - New connection from ('127.0.0.1', 54321)
2024-01-01 12:00:05,123 - WARNING - IP 127.0.0.1 locked out due to failed login attempts
```

### Database Monitoring
- **Login log table**: Track all authentication attempts
- **User activity**: Last login times and counts
- **Security events**: Failed attempts and lockouts

## 🎮 Future Enhancements

### Planned Features
- **Message system**: Full bulletin board functionality
- **File areas**: Upload and download capabilities
- **Door game integration**: Direct integration with Python games
- **Chat system**: Real-time user communication
- **Admin tools**: User management and system administration

### Security Enhancements
- **TLS encryption**: Secure communications option
- **CAPTCHA system**: Additional bot protection
- **IP whitelisting**: Restrict access to known good IPs
- **Audit trails**: Enhanced logging and monitoring
- **Intrusion detection**: Automated threat detection

## 📞 Classic BBS Experience

This BBS recreates the authentic experience of 1980s-1990s bulletin board systems:
- **Text-only interface**: Pure ASCII art and text menus
- **Command-driven navigation**: Type commands or menu numbers
- **Turn-based interactions**: Classic BBS gameplay mechanics
- **User community**: Shared message boards and high scores
- **Door games**: External game programs launched from the BBS

Connect with `telnet localhost 2323` and experience computing history with modern security!

---

*"In memory of 1200 baud modems and late-night bulletin board sessions"*

