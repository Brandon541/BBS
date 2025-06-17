// BBS Terminal Interface JavaScript

let bbsSocket = null;
let isConnected = false;
let sessionStartTime = null;
let currentUser = null;
let isPasswordField = false;

// DOM elements
const statusElement = document.getElementById('bbs-status');
const outputElement = document.getElementById('bbs-output');
const inputElement = document.getElementById('bbs-input');
const promptElement = document.getElementById('bbs-prompt');
const userElement = document.getElementById('bbs-user');
const sessionTimeElement = document.getElementById('session-time');
const connectBtn = document.getElementById('bbs-connect-btn');
const disconnectBtn = document.getElementById('bbs-disconnect-btn');
const clearBtn = document.getElementById('bbs-clear-btn');

function initializeBBS() {
    // Initialize Socket.IO connection
    bbsSocket = io();
    
    // Set up event listeners
    setupBBSSocketEvents();
    setupBBSUIEvents();
    
    // Update UI state
    updateBBSStatus('Disconnected', 'red');
    updateSessionTime();
    setInterval(updateSessionTime, 1000); // Update every second
}

function setupBBSSocketEvents() {
    bbsSocket.on('connect', () => {
        console.log('Connected to BBS server');
        updateBBSStatus('Connected', 'green');
        connectBtn.disabled = false;
    });
    
    bbsSocket.on('disconnect', () => {
        console.log('Disconnected from BBS server');
        updateBBSStatus('Disconnected', 'red');
        isConnected = false;
        updateBBSUIState();
    });
    
    bbsSocket.on('bbs_output', (data) => {
        console.log('BBS output received:', data);
        handleBBSOutput(data);
    });
    
    bbsSocket.on('bbs_error', (data) => {
        console.error('BBS error:', data);
        addBBSOutput(`Error: ${data.message}`);
    });
}

function setupBBSUIEvents() {
    // Connect button
    connectBtn.addEventListener('click', () => {
        connectToBBS();
    });
    
    // Disconnect button
    disconnectBtn.addEventListener('click', () => {
        disconnectFromBBS();
    });
    
    // Clear screen button
    clearBtn.addEventListener('click', () => {
        clearBBSScreen();
    });
    
    // Input field - handle Enter key
    inputElement.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendBBSInput();
        }
    });
    
    // Auto-focus input when connected
    inputElement.addEventListener('focus', () => {
        if (isPasswordField) {
            inputElement.type = 'password';
        }
    });
    
    inputElement.addEventListener('blur', () => {
        inputElement.type = 'text';
    });
}

function connectToBBS() {
    if (!bbsSocket) {
        addBBSOutput('Error: Not connected to server');
        return;
    }
    
    updateBBSStatus('Connecting...', 'orange');
    addBBSOutput('Connecting to BBS...');
    
    // Send connect request
    bbsSocket.emit('bbs_connect');
    
    // Mark as connecting
    isConnected = true;
    sessionStartTime = new Date();
    updateBBSUIState();
}

function disconnectFromBBS() {
    if (bbsSocket) {
        bbsSocket.emit('bbs_disconnect');
    }
    
    isConnected = false;
    currentUser = null;
    sessionStartTime = null;
    updateBBSStatus('Disconnected', 'red');
    updateBBSUser('Not connected');
    updateBBSUIState();
    
    addBBSOutput('\nDisconnected from BBS.');
    inputElement.value = '';
    inputElement.placeholder = 'Connect to BBS to begin...';
    inputElement.disabled = true;
}

function sendBBSInput() {
    const input = inputElement.value;
    if (!isConnected) {
        return;
    }
    
    // Allow empty input for "Press Enter to continue" scenarios
    const isEmptyInput = !input.trim();
    
    // Echo input to output (unless it's a password or empty)
    if (!isEmptyInput) {
        if (!isPasswordField) {
            addBBSOutput(`> ${input}`);
        } else {
            addBBSOutput(`> ${'*'.repeat(input.length)}`);
        }
    } else {
        // For empty input (continuation), just add a blank line
        addBBSOutput('');
    }
    
    // Send to server
    bbsSocket.emit('bbs_input', {
        input: input
    });
    
    // Clear input
    inputElement.value = '';
    inputElement.type = 'text';
    isPasswordField = false;
}

function handleBBSOutput(data) {
    // Handle clear screen
    if (data.clear_screen) {
        clearBBSScreen();
    }
    
    // Add output lines
    if (data.output && data.output.length > 0) {
        data.output.forEach(line => {
            addBBSOutput(line);
        });
    }
    
    // Update prompt
    if (data.prompt) {
        promptElement.textContent = data.prompt;
        inputElement.placeholder = data.prompt;
    }
    
    // Handle password field
    if (data.password_field) {
        isPasswordField = true;
        inputElement.placeholder = inputElement.placeholder + ' (hidden)';
    }
    
    // Handle session end
    if (data.session_ended) {
        setTimeout(() => {
            disconnectFromBBS();
        }, 2000);
        return;
    }
    
    // Handle message reading continuation
    // When showing a message, user just needs to press Enter to continue
    // This is handled by the normal input processing
    
    // Enable input if we're waiting for it
    if (isConnected) {
        inputElement.disabled = false;
        inputElement.focus();
    }
    
    // Extract username from successful login
    if (data.menu === 'main' && data.output) {
        const welcomeMsg = data.output.find(line => line.includes('Welcome back,'));
        if (welcomeMsg) {
            const match = welcomeMsg.match(/Welcome back, ([^!]+)!/);
            if (match) {
                updateBBSUser(match[1]);
            }
        }
        
        // Also check for new user welcome
        const newUserMsg = data.output.find(line => line.includes('Welcome to the BBS,'));
        if (newUserMsg) {
            const match = newUserMsg.match(/Welcome to the BBS, ([^!]+)!/);
            if (match) {
                updateBBSUser(match[1]);
            }
        }
    }
}

function addBBSOutput(text) {
    if (!outputElement) return;
    
    // Create new line element
    const line = document.createElement('div');
    line.textContent = text;
    line.className = 'bbs-line';
    
    // Add timestamp for debugging
    line.setAttribute('data-timestamp', new Date().toISOString());
    
    // Append to output
    outputElement.appendChild(line);
    
    // Auto-scroll to bottom
    outputElement.scrollTop = outputElement.scrollHeight;
}

function clearBBSScreen() {
    if (outputElement) {
        outputElement.innerHTML = '';
    }
}

function updateBBSStatus(status, color) {
    if (!statusElement) return;
    
    statusElement.textContent = status;
    statusElement.style.color = getBBSStatusColor(color);
}

function getBBSStatusColor(color) {
    const colors = {
        'green': '#00ff41',
        'red': '#ff4444',
        'orange': '#ffaa00',
        'blue': '#0066ff'
    };
    return colors[color] || '#e0e0e0';
}

function updateBBSUser(username) {
    if (userElement) {
        userElement.textContent = username;
        currentUser = username;
    }
}

function updateSessionTime() {
    if (!sessionTimeElement) return;
    
    if (sessionStartTime) {
        const now = new Date();
        const elapsed = Math.floor((now - sessionStartTime) / 1000);
        const minutes = Math.floor(elapsed / 60);
        const seconds = elapsed % 60;
        sessionTimeElement.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
    } else {
        sessionTimeElement.textContent = '--';
    }
}

function updateBBSUIState() {
    if (connectBtn) {
        connectBtn.disabled = isConnected;
    }
    
    if (disconnectBtn) {
        disconnectBtn.disabled = !isConnected;
    }
    
    if (inputElement) {
        if (isConnected) {
            inputElement.disabled = false;
            inputElement.placeholder = 'Enter command...';
            inputElement.focus();
        } else {
            inputElement.disabled = true;
            inputElement.placeholder = 'Connect to BBS to begin...';
        }
    }
}

// Handle page unload
window.addEventListener('beforeunload', () => {
    if (bbsSocket && isConnected) {
        bbsSocket.emit('bbs_disconnect');
    }
});

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    updateBBSStatus('Initializing...', 'orange');
    updateBBSUIState();
});

