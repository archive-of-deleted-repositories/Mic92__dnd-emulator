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

// Session management
let currentSessionId = "default";

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

// Send message function
function sendMessage() {
  const message = messageInput.value.trim();
  if (!message) return;

  // Add player message to chat
  addMessage(message, "player");

  // Send to server
  socket.emit("send_message", {
    message: message,
    session_id: currentSessionId,
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
    type === "gm" ? "GM:" : type === "player" ? "You:" : "System:";
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

// Focus on input when page loads
window.addEventListener("load", () => {
  messageInput.focus();
});
