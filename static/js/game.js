// Initialize Socket.IO connection
const socket = io();

// DOM elements
const chatMessages = document.getElementById("chat-messages");
const messageInput = document.getElementById("message-input");
const sendButton = document.getElementById("send-button");
const connectionStatus = document.getElementById("connection-status");
const sessionId = document.getElementById("session-id");
const diceButtons = document.querySelectorAll(".dice-btn");
const customDiceInput = document.getElementById("custom-dice");
const rollCustomButton = document.getElementById("roll-custom");
const diceResults = document.getElementById("dice-results");
const sessionSelect = document.getElementById("session-select");
const refreshSessionsButton = document.getElementById("refresh-sessions");

// Session management
let currentSessionId = null;

// Socket.IO event handlers
socket.on("connect", () => {
  console.log("Connected to server");
  connectionStatus.textContent = "Connected";
  connectionStatus.classList.add("connected");
  connectionStatus.classList.remove("disconnected");
});

socket.on("disconnect", () => {
  console.log("Disconnected from server");
  connectionStatus.textContent = "Disconnected";
  connectionStatus.classList.add("disconnected");
  connectionStatus.classList.remove("connected");
});

socket.on("connected", (data) => {
  console.log("Server acknowledgement:", data);
});

socket.on("gm_response", (data) => {
  // Add GM response to chat
  addMessage(data.response, "gm");

  // Display dice rolls if any
  if (data.dice_rolls && data.dice_rolls.length > 0) {
    data.dice_rolls.forEach((roll) => {
      addDiceResult(`${roll.notation} = ${roll.result}`);
    });
  }
});

socket.on("dice_result", (data) => {
  // Display dice roll result
  const rollText = `${data.notation}: [${data.rolls.join(", ")}]${data.modifier !== 0 ? (data.modifier > 0 ? "+" : "") + data.modifier : ""} = ${data.total}`;
  addDiceResult(rollText);

  // Also add to chat
  addMessage(`Rolled ${rollText}`, "player");
});

socket.on("error", (data) => {
  console.error("Server error:", data.message);
  addMessage(`Error: ${data.message}`, "error");
});

socket.on("session_switched", (data) => {
  console.log("Session switched:", data);
  currentSessionId = data.session_id;
  sessionId.textContent = data.session_id || "New";
  const sessionName = data.session_id ? `${data.session_id.substring(0, 8)}...` : "New Session";
  addMessage(`Switched to: ${sessionName}`, "system");
});

// Send message function
function sendMessage() {
  const message = messageInput.value.trim();
  if (!message) return;

  // Add player message to chat
  addMessage(message, "player");

  // Send to server
  socket.emit("send_message", {
    message: message,
    session_id: currentSessionId,  // null for new sessions
  });

  // Clear input
  messageInput.value = "";
}

// Add message to chat
function addMessage(text, type) {
  const messageDiv = document.createElement("div");
  messageDiv.className = `message ${type}-message`;

  const strong = document.createElement("strong");
  strong.textContent =
    type === "gm" ? "GM:" : type === "player" ? "You:" : type === "system" ? "System:" : "Error:";
  messageDiv.appendChild(strong);

  // Parse for dice roll notation in GM messages
  if (type === "gm") {
    const parsedText = text.replace(
      /\[(\d+d\d+(?:[+-]\d+)?)\]\s*=\s*(\d+)/g,
      '<span class="dice-roll">[$1 = $2]</span>',
    );
    const textSpan = document.createElement("span");
    textSpan.innerHTML = parsedText;
    messageDiv.appendChild(textSpan);
  } else {
    const textNode = document.createTextNode(text);
    messageDiv.appendChild(textNode);
  }

  chatMessages.appendChild(messageDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Roll dice function
function rollDice(notation) {
  socket.emit("roll_dice", {
    notation: notation,
  });
}

// Add dice result to sidebar
function addDiceResult(text) {
  const resultDiv = document.createElement("div");
  resultDiv.className = "dice-result";
  resultDiv.textContent = text;

  diceResults.insertBefore(resultDiv, diceResults.firstChild);

  // Keep only last 5 results
  while (diceResults.children.length > 5) {
    diceResults.removeChild(diceResults.lastChild);
  }
}

// Event listeners
sendButton.addEventListener("click", sendMessage);
messageInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter") {
    sendMessage();
  }
});

// Dice button listeners
diceButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const dice = button.getAttribute("data-dice");
    rollDice(dice);
  });
});

// Custom dice roll
rollCustomButton.addEventListener("click", () => {
  const notation = customDiceInput.value.trim();
  if (notation) {
    rollDice(notation);
    customDiceInput.value = "";
  }
});

customDiceInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter") {
    const notation = customDiceInput.value.trim();
    if (notation) {
      rollDice(notation);
      customDiceInput.value = "";
    }
  }
});

// Session management functions
async function loadSessions() {
  try {
    const response = await fetch("/api/sessions");
    const data = await response.json();
    
    if (data.sessions) {
      // Clear existing options
      sessionSelect.innerHTML = '<option value="">New Session</option>';
      
      // Add Claude sessions
      data.sessions.forEach(session => {
        const option = document.createElement("option");
        option.value = session.session_id;
        // Truncate summary for display
        const summary = session.summary.length > 30 
          ? session.summary.substring(0, 30) + "..." 
          : session.summary;
        option.textContent = `${summary} (${session.message_count} msgs)`;
        option.title = `${session.summary}\n${session.first_message}`;
        sessionSelect.appendChild(option);
      });
      
      // Set current selection
      sessionSelect.value = currentSessionId || "";
    }
  } catch (error) {
    console.error("Failed to load sessions:", error);
  }
}

// Session selector change handler
sessionSelect.addEventListener("change", (e) => {
  const newSessionId = e.target.value || null;
  if (newSessionId !== currentSessionId) {
    socket.emit("switch_session", { session_id: newSessionId });
  }
});

// Refresh sessions button
refreshSessionsButton.addEventListener("click", () => {
  loadSessions();
  refreshSessionsButton.textContent = "✓";
  setTimeout(() => {
    refreshSessionsButton.textContent = "↻";
  }, 1000);
});

// Focus on input when page loads
window.addEventListener("load", () => {
  messageInput.focus();
  loadSessions();
});
