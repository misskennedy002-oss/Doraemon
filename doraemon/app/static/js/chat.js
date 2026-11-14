const chatBox = document.getElementById('chat-box');
const form = document.getElementById('chat-form');
const input = document.getElementById('user-input');

function appendMessage(text, role) {
    const div = document.createElement('div');
    div.className = `message ${role}`;
    div.textContent = text;
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
    return div;
}

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const message = input.value.trim();
    if (!message) return;
    
    input.value = '';
    appendMessage(message, 'user');
    const botDiv = appendMessage('', 'bot');
    form.querySelector('button').disabled = true;

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: message }) // Removed session_id here
        });

        if (!response.ok) {
            botDiv.textContent = 'Error: could not reach server.';
            return;
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n\n');
            buffer = lines.pop(); // keep incomplete part

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = line.slice(6);
                    if (data === '[DONE]') continue;
                    botDiv.textContent += data;
                    chatBox.scrollTop = chatBox.scrollHeight;
                }
            }
        }
    } catch (err) {
        botDiv.textContent = 'Error: ' + err.message;
    } finally {
        form.querySelector('button').disabled = false;
        input.focus();
    }
});