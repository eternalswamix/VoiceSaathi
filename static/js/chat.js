const chatBox = document.getElementById("chat-box");
const welcomePanel = document.getElementById("welcomePanel");
let currentUser = null;
let currentChatId = null;
let isSending = false;

function escapeHTML(value) {
    return String(value).replace(/[&<>"']/g, (char) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    }[char]));
}

async function loadCurrentUser() {
    try {
        const res = await fetch("/auth/me");
        if (!res.ok) throw new Error("Not logged in");
        const data = await res.json();
        currentUser = data.user;
        updateAuthUI();
    } catch {
        currentUser = null;
        updateAuthUI();
    }
}

async function loadGeminiKeyStatus() {
    const status = document.getElementById("geminiKeyStatus");
    if (!status) return;

    try {
        const res = await fetch("/settings/gemini-key");
        const data = await res.json();
        if (data.session_key) {
            status.textContent = data.masked || "Saved";
            status.className = "text-xs text-slate-300";
        } else if (data.has_key) {
            status.textContent = ".env key";
            status.className = "text-xs text-neutral-500";
        } else {
            status.textContent = "Not set";
            status.className = "text-xs text-neutral-600";
        }
    } catch {
        status.textContent = "Unknown";
        status.className = "text-xs text-neutral-600";
    }
}

async function saveGeminiKey() {
    const input = document.getElementById("geminiKeyInput");
    const apiKey = input?.value.trim();
    if (!apiKey) {
        alert("Gemini API key paste karo");
        return;
    }

    const res = await fetch("/settings/gemini-key", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ api_key: apiKey })
    });

    if (!res.ok) {
        alert("Gemini API key save nahi hui");
        return;
    }

    if (input) input.value = "";
    loadGeminiKeyStatus();
}

async function clearGeminiKey() {
    await fetch("/settings/gemini-key", { method: "DELETE" });
    loadGeminiKeyStatus();
}

function updateAuthUI() {
    const signIn = document.getElementById("googleSignIn");
    const badge = document.getElementById("userBadge");
    const email = document.getElementById("userEmail");
    const input = document.getElementById("user-input");

    if (currentUser) {
        signIn?.classList.add("hidden");
        badge?.classList.remove("hidden");
        badge?.classList.add("flex");
        if (email) email.textContent = currentUser.email || currentUser.name || "Signed in";
        if (input) {
            input.disabled = false;
            input.placeholder = "Message VoiceSaathi...";
        }
        loadChats();
    } else {
        signIn?.classList.remove("hidden");
        badge?.classList.add("hidden");
        badge?.classList.remove("flex");
        if (input) {
            input.disabled = true;
            input.placeholder = "Sign in with Google to start...";
        }
        renderChatList([]);
    }
}

async function handleGoogleCredential(response) {
    const res = await fetch("/auth/google", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ credential: response.credential })
    });

    if (!res.ok) {
        alert("Google login failed");
        return;
    }

    const data = await res.json();
    currentUser = data.user;
    updateAuthUI();
}

function initGoogleLogin() {
    if (!window.google || !window.GOOGLE_CLIENT_ID) {
        setTimeout(initGoogleLogin, 200);
        return;
    }

    google.accounts.id.initialize({
        client_id: window.GOOGLE_CLIENT_ID,
        callback: handleGoogleCredential
    });

    const signIn = document.getElementById("googleSignIn");
    if (signIn) {
        google.accounts.id.renderButton(signIn, {
            theme: "outline",
            size: "medium",
            type: "standard"
        });
    }
}

async function logout() {
    await fetch("/auth/logout", { method: "POST" });
    currentUser = null;
    currentChatId = null;
    clearChat();
    updateAuthUI();
}

async function loadChats() {
    const list = document.getElementById("chat-list");
    if (!currentUser || !list) return;

    list.innerHTML = `<div class="min-w-64 text-sm text-neutral-500 rounded-xl border border-neutral-900 p-3">Loading chats...</div>`;

    try {
        const res = await fetch("/chats");
        if (!res.ok) throw new Error("Unable to load chats");
        const chats = await res.json();
        renderChatList(chats || []);
    } catch (err) {
        console.error(err);
        list.innerHTML = `<div class="min-w-64 text-sm text-red-300 rounded-xl border border-red-950 bg-red-950/20 p-3">Chat history load nahi hui.</div>`;
    }
}

function renderChatList(chats) {
    const list = document.getElementById("chat-list");
    if (!list) return;

    if (!currentUser) {
        list.innerHTML = `<div class="min-w-64 text-sm text-neutral-500 rounded-xl border border-dashed border-neutral-900 p-3">Sign in to sync chat history.</div>`;
        return;
    }

    if (!chats.length) {
        list.innerHTML = `<div class="min-w-64 text-sm text-neutral-500 rounded-xl border border-dashed border-neutral-900 p-3">No chats yet. Start a new conversation.</div>`;
        return;
    }

    list.innerHTML = chats.map((chat) => {
        const title = escapeHTML(chat.title || "Untitled chat");
        const active = chat.id === currentChatId;
        return `
            <button type="button" onclick="loadChat('${escapeHTML(chat.id)}')" class="min-w-56 max-w-64 text-left rounded-xl border px-3 py-3 transition md:min-w-0 md:max-w-none ${active ? "border-neutral-600 bg-neutral-900 text-white" : "border-neutral-900 bg-black hover:bg-neutral-950 hover:border-neutral-700 text-slate-200"}">
                <span class="block truncate text-sm font-semibold">${title}</span>
                <span class="block mt-1 text-xs text-neutral-600">Open chat</span>
            </button>
        `;
    }).join("");
}

async function createNewChat() {
    if (!currentUser) {
        alert("Sign in with Google to start");
        return;
    }

    try {
        const res = await fetch("/chat/new", { method: "POST" });
        if (!res.ok) throw new Error("Unable to create chat");
        const chat = await res.json();
        currentChatId = chat.id;
        clearChat();
        setActiveTitle(chat.title || "New conversation");
        await loadChats();
        toggleSidebar(false);
    } catch (err) {
        console.error(err);
        alert("New chat create nahi hui");
    }
}

async function loadChat(chatId) {
    if (!currentUser) return;

    try {
        const res = await fetch(`/chat/${encodeURIComponent(chatId)}`);
        if (!res.ok) throw new Error("Unable to open chat");
        const messages = await res.json();
        currentChatId = chatId;
        clearChat(false);
        messages.forEach((message) => {
            if (message.sender === "user") addUserMsg(message.content || "");
            else addAiMsg(message.content || "");
        });
        if (!messages.length) showWelcome();
        setActiveTitle("Conversation");
        await loadChats();
        toggleSidebar(false);
        scrollBottom();
    } catch (err) {
        console.error(err);
        alert("Chat open nahi hui");
    }
}

async function sendMessage() {
    if (!currentUser) {
        alert("Sign in with Google first");
        return;
    }
    if (isSending) return;

    const input = document.getElementById("user-input");
    const message = input.value.trim();
    if (!message) return;

    input.value = "";
    setSending(true);
    addUserMsg(message);
    addThinking();
    scrollBottom();

    try {
        const res = await fetch("/chat/send", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message, type: "text", chat_id: currentChatId })
        });
        const data = await res.json();
        if (data.chat_id) currentChatId = data.chat_id;

        removeThinking();
        addAiMsg(data.reply || "No reply");
        scrollBottom();

        if (data.audio) {
            const audio = new Audio(data.audio);
            audio.play().catch((err) => console.log("Audio blocked:", err));
        }
    } catch (err) {
        console.error(err);
        removeThinking();
        addAiMsg("AI error occurred. Please try again.");
    } finally {
        setSending(false);
        input.focus();
    }
}

async function sendVoiceMessage(text) {
    if (!currentUser) {
        alert("Sign in with Google first");
        return;
    }
    if (isSending) return;

    setSending(true);
    addUserMsg(text);
    addThinking();
    scrollBottom();

    try {
        const res = await fetch("/chat/send", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: text, type: "voice", chat_id: currentChatId })
        });
        const data = await res.json();
        if (data.chat_id) currentChatId = data.chat_id;

        removeThinking();
        addAiMsg(data.reply || "");
        speakText(data.reply || "");
        scrollBottom();

        if (data.audio) {
            new Audio(data.audio).play();
        }
    } catch (err) {
        console.error(err);
        removeThinking();
        addAiMsg("Voice message failed. Please try again.");
    } finally {
        setSending(false);
    }
}

function handleEnter(e) {
    if (e.key === "Enter" && !e.shiftKey) sendMessage();
}

function addUserMsg(text) {
    hideWelcome();
    chatBox.insertAdjacentHTML("beforeend", `
    <div class="flex justify-end mb-3 message-enter">
        <div class="bg-slate-100 text-black px-4 py-3 rounded-2xl rounded-br-md max-w-[85%] sm:max-w-lg break-words">
            ${escapeHTML(text)}
        </div>
    </div>`);
}

function addAiMsg(text) {
    hideWelcome();
    chatBox.insertAdjacentHTML("beforeend", `
    <div class="flex justify-start mb-3 message-enter">
        <div class="bg-black border border-neutral-900 px-4 py-3 rounded-2xl rounded-bl-md max-w-[92%] sm:max-w-2xl break-words leading-relaxed text-slate-100">
            ${escapeHTML(text)}
        </div>
    </div>`);
}

function addThinking() {
    hideWelcome();
    chatBox.insertAdjacentHTML("beforeend", `
    <div id="thinking" class="flex justify-start mb-3 message-enter">
        <div class="bg-black border border-neutral-900 px-4 py-3 rounded-2xl rounded-bl-md text-neutral-400 text-sm flex items-center gap-2">
            <span class="inline-flex h-2 w-2 rounded-full bg-slate-100 animate-pulse"></span>
            thinking...
        </div>
    </div>`);
}

function removeThinking() {
    document.getElementById("thinking")?.remove();
}

function scrollBottom() {
    chatBox.scrollTop = chatBox.scrollHeight;
}

function hideWelcome() {
    welcomePanel?.classList.add("hidden");
}

function showWelcome() {
    welcomePanel?.classList.remove("hidden");
}

function clearChat(showPanel = true) {
    Array.from(chatBox.children).forEach((child) => {
        if (child.id !== "welcomePanel") child.remove();
    });
    if (showPanel) showWelcome();
}

function setActiveTitle(title) {
    const activeTitle = document.getElementById("activeTitle");
    if (activeTitle) activeTitle.textContent = title;
}

function toggleSidebar(force) {
    const sidebar = document.getElementById("sidebar");
    const backdrop = document.getElementById("sidebarBackdrop");
    if (!sidebar || !backdrop) return;
    if (!sidebar.classList.contains("-translate-x-full")) return;

    const shouldOpen = typeof force === "boolean" ? force : sidebar.classList.contains("-translate-x-full");
    sidebar.classList.toggle("-translate-x-full", !shouldOpen);
    backdrop.classList.toggle("hidden", !shouldOpen);
}

function setSending(value) {
    isSending = value;
    const btn = document.getElementById("sendBtn");
    const input = document.getElementById("user-input");
    if (btn) btn.disabled = value;
    if (input) input.setAttribute("aria-busy", value ? "true" : "false");
}

function startMic() {
    const overlay = document.getElementById("micOverlay");
    const micBtn = document.getElementById("micBtn");
    const stopListeningUI = () => {
        overlay.classList.add("hidden");
        overlay.classList.remove("flex");
        micBtn?.classList.remove("is-listening", "text-white", "bg-neutral-900");
    };

    overlay.classList.remove("hidden");
    overlay.classList.add("flex");
    micBtn?.classList.add("is-listening", "text-white", "bg-neutral-900");

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
        alert("Mic not supported");
        stopListeningUI();
        return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "en-IN";
    recognition.start();

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        stopListeningUI();
        sendVoiceMessage(transcript);
    };

    recognition.onerror = () => {
        stopListeningUI();
    };

    recognition.onend = () => {
        stopListeningUI();
    };

    setTimeout(() => {
        try { recognition.stop(); } catch {}
        stopListeningUI();
    }, 10000);
}

function speakText(text) {
    if (!text || !("speechSynthesis" in window)) return;

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "en-IN";
    utterance.rate = 1;
    utterance.pitch = 1;

    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
}

document.getElementById("logoutBtn")?.addEventListener("click", logout);
document.querySelectorAll(".quickPrompt").forEach((button) => {
    button.addEventListener("click", () => {
        const input = document.getElementById("user-input");
        if (!input || input.disabled) {
            alert("Sign in with Google to start");
            return;
        }
        input.value = button.dataset.prompt || "";
        input.focus();
    });
});

loadCurrentUser();
loadGeminiKeyStatus();
initGoogleLogin();

window.sendMessage = sendMessage;
window.handleEnter = handleEnter;
window.startMic = startMic;
window.sendVoiceMessage = sendVoiceMessage;
window.toggleSidebar = toggleSidebar;
window.createNewChat = createNewChat;
window.loadChat = loadChat;
window.loadChats = loadChats;
window.saveGeminiKey = saveGeminiKey;
window.clearGeminiKey = clearGeminiKey;
