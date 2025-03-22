let isGeneratingResponse = false;

/**
 * Initializes Notyf for displaying dismissible notifications
 */
const notyf = new Notyf({
    duration: 2500,
    position: {
        x: 'right',
        y: 'top',
    },
    dismissible: true
});

const themeIcon = document.getElementById('theme-icon-dark');


/**
 * Toggles the theme between dark and light mode.
 */
function toggleTheme() {
    document.body.classList.toggle('dark-theme');
    const isDarkTheme = document.body.classList.contains('dark-theme');
    themeIcon.src = isDarkTheme ? '/static/img/moon.svg' : '/static/img/sun.svg';
}


/**
 * Sends the content of the textarea to the server to set the system prompt.
 */
async function setSystemPrompt() {
    const textarea = document.getElementById('system-prompt-input');
    const systemPromptText = textarea.value.trim();

    // Allow the system prompt field to be empty if the user wishes to clear it

    try {
        const response = await fetch('/set-system-prompt/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ system_prompt: systemPromptText })
        });

        if (!response.ok) throw new Error('Error sending system prompt.');

        const result = await response.json();

        notyf.success('System prompt set successfully.');
        textarea.value = '';
    } catch (error) {
        console.error('Error sending system prompt:', error);
        notyf.error('Error sending system prompt. Please try again.');
    }
}


/**
 * Handles file uploads and sends the files to the server.
 */
async function uploadDocuments() {
    const fileInput = document.getElementById('file-input');
    const files = fileInput.files;

    if (files.length === 0) {
        notyf.error("Please select a file to upload.");
        return;
    }

    const allowedExtensions = ['docx', 'pptx', 'pdf', 'txt', 'xlsx', 'csv', 'html', 'md', 'rtf', 'odt'];

    for (let file of files) {
        const fileExtension = file.name.split('.').pop().toLowerCase();
        if (!allowedExtensions.includes(fileExtension)) {
            notyf.error(`The file "${file.name}" is not allowed. Only DOCX, PPTX, PDF, TXT, XLSX, CSV, HTML, Markdown, RTF, and ODT formats are accepted.`);
            return;
        }
    }

    const formData = new FormData();
    for (let file of files) {
        formData.append('files', file);
    }

    try {
        const response = await fetch('/upload-documents/', {
            method: 'POST',
            body: formData
        });
        if (!response.ok) throw new Error('Failed to upload documents.');
        notyf.success('Documents uploaded successfully.');
    } catch (error) {
        console.error('Error uploading documents:', error);
        notyf.error('Error uploading documents. Please try again.');
    }
}


/**
 * Updates the file count display based on the number of selected files.
 */
document.getElementById('file-input').addEventListener('change', function() {
    const fileCount = this.files.length;
    const fileCountText = fileCount > 1 ? `${fileCount} files selected` : fileCount === 1 ? '1 file selected' : 'No files selected';
    document.getElementById('file-count').textContent = fileCountText;
});


/**
 * Handles the database cleanup request.
 */
async function cleanDatabase() {
    try {
        const response = await fetch('/cleanup-database/', {
            method: 'POST'
        });
        if (!response.ok) throw new Error('Failed to clean the database.');
        notyf.success('Database cleaned successfully.');
    } catch (error) {
        console.error('Error cleaning the database:', error);
        notyf.error('Error cleaning the database. Please try again.');
    }
}


/**
 * Toggles the Retrieval-Augmented Generation (RAG) mode on or off.
 */
async function toggleRAG() {
    const isRAGEnabled = document.getElementById('rag-toggle').checked;

    try {
        const response = await fetch('/toggle-rag/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ enableRAG: isRAGEnabled })
        });
        if (!response.ok) throw new Error('Failed to toggle RAG mode.');
        notyf.success(`RAG mode ${isRAGEnabled ? 'enabled' : 'disabled'}.`);
    } catch (error) {
        console.error('Error toggling RAG mode:', error);
        notyf.error('Error toggling RAG mode. Please try again.');
    }
}


/**
 * Updates the visibility of the RAG configuration field based on the state of the RAG checkbox.
 */
function updateRAGConfigVisibility() {
    const ragConfig = document.getElementById('rag-config');
    const isRAGEnabled = document.getElementById('rag-toggle').checked;

    if (isRAGEnabled) ragConfig.style.display = 'flex';
    else ragConfig.style.display = 'none';
}


/**
 * Add an event listener to the checkbox that calls updateRAGConfigVisibility whenever its state changes.
 */
document.getElementById('rag-toggle').addEventListener('change', function() {
    updateRAGConfigVisibility();
    toggleRAG();
});


/**
 * Toggles the visibility of the vertical menu with an animated slide effect.
 */
document.getElementById("toggle-menu-container").addEventListener("click", () => {
    const mainContainer = document.getElementById('main-container');
    mainContainer.classList.toggle("hide-menu");

    const verticalMenu = document.getElementById('vertical-menu');

    if (verticalMenu.classList.contains("hide-menu")) {
            setTimeout(() => {
            verticalMenu.classList.remove("hide-menu");
        }, 500);
    } else {
        verticalMenu.classList.add("hide-menu");
    }
})


/**
 * Validates user input parameters to ensure they are within acceptable ranges.
 */
function validateGenerationParams(numCtx, temperature, repeatLastN, repeatPenalty, numDocs) {

    result = true
    if (isNaN(numCtx) || numCtx < 1 || numCtx > 4096) {
        notyf.error("Context Size must be between 1 and 4096.");
        result = false;
    }

    if (isNaN(temperature) || temperature < 0 || temperature > 2) {
        notyf.error("Temperature must be between 0 and 2.");
        result = false;
    }

    if (isNaN(repeatLastN) || repeatLastN < 1 || repeatLastN > 1024) {
        notyf.error("Repeat Last N must be between 1 and 1024.");
        result = false;
    }

    if (isNaN(repeatPenalty) || repeatPenalty < 1 || repeatPenalty > 2) {
        notyf.error("Repeat Penalty must be between 1 and 2.");
        result = false;
    }

    if (document.getElementById('rag-toggle').checked && (isNaN(numDocs) || numDocs < 1 || numDocs > 10)) {
        notyf.error("The number of document chunks to retrieve must be between 1 and 10.");
        result = false;
    }

    return result;
}


/**
 * Prepares the request body with the user input parameters.
 */
function prepareGenerationRequestBody(prompt, numCtx, temperature, repeatLastN, repeatPenalty, numDocs) {
    return { 
        prompt: prompt,
        top_n: document.getElementById('rag-toggle').checked ? numDocs : undefined,
        num_ctx: numCtx,
        temperature: temperature,
        repeat_last_n: repeatLastN,
        repeat_penalty: repeatPenalty
    };
}


/**
 * Sends a request to the backend with the provided body.
 */
async function sendGenerationRequest(body) {
    const response = await fetch("/generate-response/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(body)
    });
    if (!response.ok) throw new Error("API error");
    return response;
}


/**
 * Handles the response from the backend and updates the chat box.
 */
async function handleGenerationResponse(response) {
    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    let result = '';
    let messageDiv = document.createElement('div');
    messageDiv.className = "bot-message";

    const botMessageIconContainer = document.createElement('div');
    botMessageIconContainer.className = "bot-message-icon-container";

    const botMessageIcon = document.createElement('img');
    botMessageIcon.src = "/static/img/favicon.ico";
    botMessageIcon.className = "bot-message-icon";
    botMessageIconContainer.appendChild(botMessageIcon);

    /*
    const responseSpinner = document.createElement("img");
    responseSpinner.src = "/static/img/dual-balls.svg";
    responseSpinner.className = "response-spinner";
    messageDiv.appendChild(responseSpinner);
    */

    messageDiv.appendChild(botMessageIconContainer);
    document.getElementById('chat-box').appendChild(messageDiv);

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        result += decoder.decode(value, { stream: true });

        messageDiv.innerHTML = formatText(result);
        messageDiv.appendChild(botMessageIconContainer);
        document.getElementById('chat-box-container').scrollTop = document.getElementById('chat-box-container').scrollHeight;
    }
    isGeneratingResponse = false;
}


/**
 * Generates a response based on user input by validating parameters and sending the request.
 */
async function generateResponse() {
    if (isGeneratingResponse) return;

    isGeneratingResponse = true;
    const numCtx = parseInt(document.getElementById('num_ctx').value, 10);
    const temperature = parseFloat(document.getElementById('temperature').value);
    const repeatLastN = parseInt(document.getElementById('repeat_last_n').value, 10);
    const repeatPenalty = parseFloat(document.getElementById('repeat_penalty').value);
    const numDocs = parseInt(document.getElementById('doc-count').value, 10);
    if (!validateGenerationParams(numCtx, temperature, repeatLastN, repeatPenalty, numDocs)) {
        notyf.error("An error occurred regarding the settings.");
        return;
    }

    const prompt = document.getElementById('prompt').textContent;
    if (!prompt) {
        notyf.error("Please enter a prompt.");
        return;
    }

    const inputIcon = document.getElementById("input-icon")
    inputIcon.src = "/static/img/stop.svg";
    inputIcon.addEventListener("click", () => {
        stopGeneration();
    });

    const requestBody = prepareGenerationRequestBody(prompt, numCtx, temperature, repeatLastN, repeatPenalty, numDocs);
    addMessage(requestBody.prompt, "user");
    document.getElementById('prompt').textContent = '';
    document.getElementById('placeholder').style.display = 'block';

    try {
        const response = await sendGenerationRequest(requestBody);
        await handleGenerationResponse(response);
    } catch (error) {
        if (error.status === 409) return;
        console.error("Error during the request:", error);
        notyf.error("Error during the request. Make sure the server is running.");
        isGeneratingResponse = false;
    }
    inputIcon.src = "/static/img/up_arrow.svg";
}


async function stopGeneration() {
    const response = await fetch("/stop-generation", {
        method: "POST",
    });
    if (!response.ok) throw new Error("API error");
    document.getElementById('input-icon-container').classList.remove('active');
}


/**
 * Handles Enter and Shift+Enter key presses in the prompt input field.
 */
document.getElementById('prompt').addEventListener('input', function() {
    const promptElement = document.getElementById('prompt');
    const inputIconContainer = document.getElementById("input-icon-container");
    const placeholderElement = document.getElementById('placeholder');

    if (promptElement.textContent.length > 0) {
        placeholderElement.style.display = 'none';
        inputIconContainer.classList.add('active');
    } else {
        inputIconContainer.classList.remove('active');
        placeholderElement.style.display = 'block';
    }
});


document.getElementById('prompt').addEventListener('keydown', function(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        generateResponse();
    }
});


document.getElementById('input-icon-container').addEventListener('click', () => {
    generateResponse();
})


/**
 * Escapes special characters to prevent HTML interpretation.
 */
function escapeHtml(text) {
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


/**
 * Formats text for HTML display.
 */
function formatText(text) {
    // First escape any HTML characters to prevent code injection
    text = escapeHtml(text);

    // Then apply markdown-like formatting
    text = text.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
    text = text.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>');
    text = text.replace(/___(.+?)___/g, '<strong><em>$1</em></strong>');
    text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    text = text.replace(/__(.+?)__/g, '<strong>$1</strong>');
    text = text.replace(/\*(.+?)\*/g, '<em>$1</em>');
    text = text.replace(/_(.+?)_/g, '<em>$1</em>');
    text = text.replace(/\n/g, '<br>');

    return text;
}


/**
 * Adds a message to the chat box.
 */
function addMessage(text, sender) {
    const chatBox = document.getElementById('chat-box');
    const messageDiv = document.createElement('div');
    
    messageDiv.className = sender === "user" ? "user-message" : "bot-message";
    if (sender === "bot") messageDiv.innerHTML = formatText(text);
    else messageDiv.innerHTML = escapeHtml(text);
    
    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}


function toggleParametersContainer() {
    const parametersSection = document.getElementsByClassName("parameters-section")[0];
    const indicator = document.getElementById("parameters-label-img");

    if (parametersSection.style.display === "flex") {
        parametersSection.style.display = "none";
        indicator.classList.remove("active");
    } else {
        parametersSection.style.display = "flex";
        indicator.classList.add("active");
    }
}


document.getElementById("parameters-label-container").addEventListener('click', toggleParametersContainer);
