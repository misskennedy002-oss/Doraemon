
const API = "http://127.0.0.1:8000";

let currentConversationId = null;
let isSending = false;
let token = sessionStorage.getItem("doraemon_token");

const authScreen = document.getElementById("authScreen");
const app = document.getElementById("app");

const loginForm = document.getElementById("loginForm");
const registerForm = document.getElementById("registerForm");

const showLoginButton = document.getElementById("showLoginButton");
const showRegisterButton = document.getElementById("showRegisterButton");

const authMessage = document.getElementById("authMessage");

const form = document.getElementById("chatForm");
const input = document.getElementById("messageInput");
const messages = document.getElementById("messages");
const sendButton = document.getElementById("sendButton");

const historyList = document.getElementById("historyList");
const logoutButton = document.getElementById("logoutButton");


function showLogin() {
    loginForm.hidden = false;
    registerForm.hidden = true;

    showLoginButton.classList.add("active");
    showRegisterButton.classList.remove("active");

    authMessage.textContent = "";
}


function showRegister() {
    loginForm.hidden = true;
    registerForm.hidden = false;

    showRegisterButton.classList.add("active");
    showLoginButton.classList.remove("active");

    authMessage.textContent = "";
}


showLoginButton.addEventListener("click", showLogin);
showRegisterButton.addEventListener("click", showRegister);


// API REQUEST HELPER
async function apiRequest(path, options = {}) {

    const headers = {
        ...(options.headers || {})
    };

    if (token) {
        headers.Authorization = `Bearer ${token}`;
    }

    if (options.body) {
        headers["Content-Type"] = "application/json";
    }

    const response = await fetch(API + path, {
        ...options,
        headers
    });

    if (response.status === 401 && token) {
        handleSessionExpired();
        throw new Error("Your session has expired. Please log in again.");
    }

    return response;
}


// AUTHENTICATION
async function authenticate(endpoint, username, password) {

    authMessage.textContent = "Please wait...";
    authMessage.className = "auth-message";

    try {

        const response = await fetch(API + endpoint, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                username,
                password
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Authentication failed");
        }

        token = data.token;

        sessionStorage.setItem("doraemon_token", token);

        await startApplication(data.username);

    } catch (error) {

        authMessage.textContent = error.message;
        authMessage.className = "auth-message error";

    }
}


// LOGIN
loginForm.addEventListener("submit", async (event) => {

    event.preventDefault();

    const username = document.getElementById("loginUsername").value.trim();
    const password = document.getElementById("loginPassword").value;

    await authenticate(
        "/api/auth/login",
        username,
        password
    );

});


// REGISTRATION
registerForm.addEventListener("submit", async (event) => {

    event.preventDefault();

    const username = document.getElementById("registerUsername").value.trim();
    const password = document.getElementById("registerPassword").value;

    await authenticate(
        "/api/auth/register",
        username,
        password
    );

});


// START APPLICATION
async function startApplication(username) {

    authScreen.hidden = true;
    app.hidden = false;

    document.getElementById("currentUsername").textContent =
        "Logged in as " + username;

    currentConversationId = null;

    messages.innerHTML = `
        <div class="welcome">
            <h1>Hey! I'm Doraemon.</h1>
            <p>What can I help you with today?</p>
        </div>
    `;

    await loadConversations();
}


// CHECK EXISTING SESSION
async function checkSession() {

    if (!token) {
        authScreen.hidden = false;
        app.hidden = true;
        return;
    }

    try {

        const response = await apiRequest("/api/auth/me");

        if (!response.ok) {
            throw new Error("Session invalid");
        }

        const user = await response.json();

        await startApplication(user.username);

    } catch (error) {

        if (token) {
            token = null;
            sessionStorage.removeItem("doraemon_token");
        }

        authScreen.hidden = false;
        app.hidden = true;

    }
}


// SESSION EXPIRED
function handleSessionExpired() {

    token = null;

    sessionStorage.removeItem("doraemon_token");

    currentConversationId = null;

    app.hidden = true;
    authScreen.hidden = false;

    authMessage.textContent = "Session expired. Please log in again.";
    authMessage.className = "auth-message error";
}


// LOGOUT
logoutButton.addEventListener("click", async () => {

    if (isSending) {
        alert("Please wait until the current response finishes.");
        return;
    }

    try {

        await apiRequest("/api/auth/logout", {
            method: "POST"
        });

    } catch (error) {

        console.error(error);

    }

    token = null;

    sessionStorage.removeItem("doraemon_token");

    currentConversationId = null;

    app.hidden = true;
    authScreen.hidden = false;

    showLogin();

    loginForm.reset();
    registerForm.reset();

});


// ADD MESSAGE
function addMessage(text, sender) {

    document.querySelector(".welcome")?.remove();

    const element = document.createElement("div");

    element.className = `message ${sender}`;
    element.textContent = text;

    messages.appendChild(element);

    messages.scrollTop = messages.scrollHeight;

    return element;
}



// LOAD CHAT HISTORY
async function loadConversations() {

    try {

        const response = await apiRequest("/api/conversations");

        if (!response.ok) {
            throw new Error("History unavailable");
        }

        const conversations = await response.json();

        historyList.innerHTML = "";

        conversations.forEach(conversation => {

            const item = document.createElement("div");
            item.className = "history-item";

            if (conversation.id === currentConversationId) {
                item.classList.add("active");
            }

            const title = document.createElement("span");
            title.className = "history-title";
            title.textContent = conversation.title;

            const deleteButton = document.createElement("button");
            deleteButton.className = "delete-chat-button";
            deleteButton.type = "button";
            deleteButton.textContent = "🗑";
            deleteButton.title = "Delete conversation";
            deleteButton.setAttribute(
                "aria-label",
                `Delete ${conversation.title}`
            );

            deleteButton.addEventListener("click", (event) => {
                event.stopPropagation();
                deleteConversation(conversation.id);
            });

            item.appendChild(title);
            item.appendChild(deleteButton);

            item.addEventListener("click", () => {
                openConversation(conversation.id);
            });

            historyList.appendChild(item);

        });

    } catch (error) {

        console.error(error);

    }
}


// DELETE CONVERSATION
async function deleteConversation(id) {

    if (isSending) {
        alert("Please wait until the current response finishes.");
        return;
    }

    const confirmed = confirm(
        "Are you sure you want to delete this conversation? This cannot be undone."
    );

    if (!confirmed) return;

    try {

        const response = await apiRequest(
            `/api/conversations/${id}`,
            {
                method: "DELETE"
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Could not delete conversation");
        }

        if (currentConversationId === id) {
            currentConversationId = null;

            messages.innerHTML = `
                <div class="welcome">
                    <h1>Hey! I'm Doraemon.</h1>
                    <p>What can I help you with today?</p>
                </div>
            `;
        }

        await loadConversations();

    } catch (error) {

        alert(error.message);
        console.error(error);

    }
}



// OPEN CONVERSATION
async function openConversation(id) {

    if (isSending) return;

    try {

        const response = await apiRequest(
            `/api/conversations/${id}`
        );

        if (!response.ok) {
            throw new Error("Could not load chat");
        }

        const history = await response.json();

        currentConversationId = id;

        messages.innerHTML = "";

        history.forEach(message => {

            addMessage(
                message.content,
                message.role === "user" ? "user" : "bot"
            );

        });

        await loadConversations();

    } catch (error) {

        alert(error.message);

    }
}


// SEND MESSAGE
form.addEventListener("submit", async (event) => {

    event.preventDefault();

    if (isSending) return;

    const userMessage = input.value.trim();

    if (!userMessage) return;

    isSending = true;
    sendButton.disabled = true;

    addMessage(userMessage, "user");

    input.value = "";

    const loading = addMessage(
        "Doraemon is thinking...",
        "bot"
    );

    try {

        const controller = new AbortController();

        const timeout = setTimeout(
            () => controller.abort(),
            300000
        );

        let response;

        try {

            response = await apiRequest("/api/chat", {

                method: "POST",

                body: JSON.stringify({
                    message: userMessage,
                    conversation_id: currentConversationId
                }),

                signal: controller.signal

            });

        } finally {

            clearTimeout(timeout);

        }

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Backend error");
        }

        currentConversationId = data.conversation_id;

        loading.textContent =
            data.reply || "Empty response received.";

        await loadConversations();

    } catch (error) {

        loading.textContent =
            error.name === "AbortError"
                ? "Request timed out. Please try again."
                : "Error: " + error.message;

        console.error(error);

    } finally {

        isSending = false;
        sendButton.disabled = false;

        input.focus();

    }

});


// NEW CHAT
function clearChat() {

    if (isSending) return;

    currentConversationId = null;

    messages.innerHTML = `
        <div class="welcome">
            <h1>Hey! I'm Doraemon.</h1>
            <p>What can I help you with today?</p>
        </div>
    `;

    loadConversations();

}


// INITIALIZE
checkSession();
