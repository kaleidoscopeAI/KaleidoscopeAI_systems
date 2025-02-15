const socket = io();

// Handle file upload
function handleUpload() {
    const fileInput = document.getElementById('dataFile');
    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('file', file);

    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if(data.error) throw new Error(data.error);
        updateVisualization(data.visualization);
        document.getElementById('uploadStatus').textContent = data.message;
    })
    .catch(error => {
        document.getElementById('uploadStatus').textContent = error.message;
    });
}

// Handle chat messages
function sendMessage() {
    const input = document.getElementById('userInput');
    const message = input.value.trim();
    if(message) {
        socket.emit('message', message);
        addMessage(message, 'user');
        input.value = '';
    }
}

// Socket listeners
socket.on('connect', () => {
    console.log('Connected to server');
});

socket.on('response', (data) => {
    addMessage(data.content, 'ai');
});

socket.on('visualization', (data) => {
    updateVisualization(data.url);
});

// Helper functions
function addMessage(content, sender) {
    const chatHistory = document.getElementById('chatHistory');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    messageDiv.textContent = content;
    chatHistory.appendChild(messageDiv);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

function updateVisualization(url) {
    fetch(url)
        .then(response => response.text())
        .then(html => {
            const vizPane = document.getElementById('cubeVisualization');
            vizPane.innerHTML = html;
        });
}
