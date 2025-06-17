// BBS Door Games - JavaScript Interface

let socket = null;
let currentGameId = null;
let isConnected = false;
let playerName = null;

// DOM elements
const statusElement = document.getElementById('status');
const outputElement = document.getElementById('output');
const inputElement = document.getElementById('input');
const promptElement = document.getElementById('prompt');
const playerNameElement = document.getElementById('player-name');
const connectBtn = document.getElementById('connect-btn');
const disconnectBtn = document.getElementById('disconnect-btn');

function initializeGame(gameId) {
    currentGameId = gameId;
    
    // Initialize Socket.IO connection
    socket = io();
    
    // Set up event listeners
    setupSocketEvents();
    setupUIEvents();
    
    // Enable connect button
    connectBtn.disabled = false;
    
    // Add welcome message
    addToOutput('Welcome! Enter your name and click Connect to begin.');
}

function setupSocketEvents() {
    socket.on('connect', () => {
        console.log('Connected to server');
        updateStatus('Connected', 'green');
    });
    
    socket.on('disconnect', () => {
        console.log('Disconnected from server');
        updateStatus('Disconnected', 'red');
        isConnected = false;
        updateUIState();
    });
    
    socket.on('connected', (data) => {
        console.log('Server acknowledgment:', data.status);
    });
    
    socket.on('game_started', (data) => {
        console.log('Game started:', data);
        playerName = data.player_name;
        isConnected = true;
        updatePlayerInfo(playerName);
        updateUIState();
        
        // Clear input and set placeholder for game commands
        inputElement.value = '';
        inputElement.placeholder = 'Enter command...';
        inputElement.focus();
    });
    
    socket.on('game_output', (data) => {
        console.log('Game output received:', data);
        
        // Add each output line
        if (data.output && data.output.length > 0) {
            data.output.forEach(line => {
                addToOutput(line.text);
            });
        }
        
        // Update prompt
        if (data.prompt) {
            promptElement.textContent = data.prompt;
        }
        
        // Check if game ended
        if (data.game_state === 'ended') {
            addToOutput('\n--- Game Ended ---');
            addToOutput('You can disconnect or start a new game.');
        }
    });
    
    socket.on('error', (data) => {
        console.error('Game error:', data);
        addToOutput(`Error: ${data.message}`);
    });
}

function setupUIEvents() {
    // Connect button
    connectBtn.addEventListener('click', () => {
        const name = inputElement.value.trim();
        if (!name) {
            alert('Please enter your name first!');
            inputElement.focus();
            return;
        }
        
        connectToGame(name);
    });
    
    // Disconnect button
    disconnectBtn.addEventListener('click', () => {
        disconnectFromGame();
    });
    
    // Input field - handle Enter key
    inputElement.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            if (!isConnected) {
                // If not connected, treat as name input
                connectBtn.click();
            } else {
                // If connected, send as game input
                sendGameInput();
            }
        }
    });
    
    // Auto-focus input
    inputElement.focus();
}

function connectToGame(name) {
    if (!socket || !currentGameId) {
        addToOutput('Error: Game not properly initialized.');
        return;
    }
    
    updateStatus('Connecting...', 'orange');
    addToOutput(`Connecting as ${name}...`);
    
    socket.emit('start_game', {
        game_id: currentGameId,
        player_name: name
    });
}

function disconnectFromGame() {
    if (socket) {
        socket.disconnect();
    }
    
    isConnected = false;
    playerName = null;
    updateStatus('Disconnected', 'red');
    updatePlayerInfo('Not connected');
    updateUIState();
    
    addToOutput('\nDisconnected from game.');
    inputElement.value = '';
    inputElement.placeholder = 'Enter your name to begin...';
}

function sendGameInput() {
    const input = inputElement.value.trim();
    if (!input || !isConnected) {
        return;
    }
    
    // Echo the input to the output
    addToOutput(`> ${input}`);
    
    // Send to server
    socket.emit('game_input', {
        input: input
    });
    
    // Clear input
    inputElement.value = '';
}

function addToOutput(text) {
    if (!outputElement) return;
    
    // Create new line element
    const line = document.createElement('div');
    line.textContent = text;
    
    // Append to output
    outputElement.appendChild(line);
    
    // Auto-scroll to bottom
    outputElement.scrollTop = outputElement.scrollHeight;
}

function updateStatus(status, color) {
    if (!statusElement) return;
    
    statusElement.textContent = status;
    statusElement.style.color = getStatusColor(color);
}

function getStatusColor(color) {
    const colors = {
        'green': '#00ff41',
        'red': '#ff4444',
        'orange': '#ffaa00',
        'blue': '#0066ff'
    };
    return colors[color] || '#e0e0e0';
}

function updatePlayerInfo(name) {
    if (playerNameElement) {
        playerNameElement.textContent = name;
    }
}

function updateUIState() {
    if (connectBtn) {
        connectBtn.disabled = isConnected;
    }
    
    if (disconnectBtn) {
        disconnectBtn.disabled = !isConnected;
    }
    
    if (inputElement) {
        inputElement.disabled = false;
        if (isConnected) {
            inputElement.placeholder = 'Enter command...';
        } else {
            inputElement.placeholder = 'Enter your name to begin...';
        }
    }
}

// Handle page unload
window.addEventListener('beforeunload', () => {
    if (socket && isConnected) {
        socket.disconnect();
    }
});

// Initialize connection status
document.addEventListener('DOMContentLoaded', () => {
    updateStatus('Disconnected', 'red');
    updateUIState();
});

