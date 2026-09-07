const messageInput =
    document.getElementById("messageInput");

const chatBox =
    document.getElementById("chatBox");

const sendButton =
    document.getElementById("sendButton");


// --------------------------------------------------
// Add message to chat
// --------------------------------------------------

function addMessage(text, type) {

    const message = document.createElement("div");

    message.className = `message ${type}`;

    const avatar = document.createElement("div");

    avatar.className = "avatar";

    avatar.textContent =
        type === "user" ? "👤" : "🤖";


    const bubble = document.createElement("div");

    bubble.className = "bubble";

    const name = document.createElement("strong");

    name.textContent =
        type === "user"
            ? "You"
            : "AI Helpdesk";


    const content = document.createElement("p");

    content.textContent = text;


    bubble.appendChild(name);

    bubble.appendChild(content);


    message.appendChild(avatar);

    message.appendChild(bubble);


    chatBox.appendChild(message);


    chatBox.scrollTop =
        chatBox.scrollHeight;
}


// --------------------------------------------------
// Send message
// --------------------------------------------------

async function sendMessage() {

    const message =
        messageInput.value.trim();


    if (!message) {
        return;
    }


    addMessage(message, "user");


    messageInput.value = "";

    sendButton.disabled = true;

    sendButton.textContent = "Thinking...";


    try {

        const response = await fetch(
            "/chat",
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({
                    message: message
                })
            }
        );


        const data =
            await response.json();


        addMessage(
            data.answer,
            "bot"
        );


    } catch (error) {

        console.error(error);

        addMessage(
            "Unable to connect to the Helpdesk server. Please make sure the Python server is running.",
            "bot"
        );

    } finally {

        sendButton.disabled = false;

        sendButton.textContent = "Send";

        messageInput.focus();
    }
}


// --------------------------------------------------
// Enter key
// --------------------------------------------------

messageInput.addEventListener(
    "keydown",
    function(event) {

        if (
            event.key === "Enter" &&
            !event.shiftKey
        ) {

            event.preventDefault();

            sendMessage();
        }

    }
);