document.addEventListener('DOMContentLoaded', () => {
    const textInput = document.getElementById('text-input');
    const fileInput = document.getElementById('file-input');
    const sendButton = document.getElementById('send-button');

    const uploadedFilePreview = document.getElementById('uploaded-file-preview');
    const uploadedFileNameSpan = uploadedFilePreview.querySelector('.file-name');
    const removeFileBtn = uploadedFilePreview.querySelector('.remove-file-btn');

    const chatHistoryContainer = document.getElementById('chat-history-container');
    let currentFile = null;

    async function typeBotMessage(fullText, speed = 50) {
        const messageElement = addMessageToHistory('', 'bot');
        const pre = document.createElement('pre');
        messageElement.appendChild(pre);

        for (let i = 0; i < fullText.length; i++) {
            pre.textContent += fullText[i];
            chatHistoryContainer.scrollTop = chatHistoryContainer.scrollHeight;
            await new Promise(r => setTimeout(r, speed));
        }
    }

    textInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            sendButton.click();
        }
    });

    textInput.addEventListener('input', () => {
        textInput.style.height = 'auto';
        textInput.style.height = (textInput.scrollHeight) + 'px';
    });

    fileInput.addEventListener('change', (event) => {
        const file = event.target.files[0];
        if (file) {
            currentFile = file;
            uploadedFileNameSpan.textContent = file.name;
            uploadedFilePreview.style.display = 'flex';
        }
    });

    removeFileBtn.addEventListener('click', () => {
        currentFile = null;
        fileInput.value = '';
        uploadedFilePreview.style.display = 'none';
        uploadedFileNameSpan.textContent = '';
    });

    function escapeHtml(unsafe) {
        if (typeof unsafe !== 'string') return '';
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function addMessageToHistory(content, type, options = {}) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('chat-message', type === 'user' ? 'user-message' : 'bot-message');

        let messageHTML = '';

        if (type === 'user') {
            if (content) {
                const textNode = document.createElement('div');
                textNode.classList.add('message-text');
                textNode.textContent = content; 
                messageHTML += textNode.outerHTML;
            }
            if (options.fileName) {
                const fileInfoNode = document.createElement('div');
                fileInfoNode.classList.add('file-info');
                fileInfoNode.textContent = `Прикреплен файл: ${options.fileName}`; 
                messageHTML += fileInfoNode.outerHTML;
            }
        } else {
            if (options.isLoading) {
                messageHTML = `<div class="loading-indicator">Обработка...</div>`;
            } else if (options.error) {
                messageHTML = `<div class="error-message">Ошибка: ${escapeHtml(options.error)}</div>`;
            } else {
                if (content) {
                    messageHTML = `<h3>Результат:</h3>${content}`;
                } else {
                    messageHTML = '';
                }
                if (options.downloadUrl && options.downloadFileName) {
                    messageHTML += `<a href="${escapeHtml(options.downloadUrl)}" class="download-button" download="${escapeHtml(options.downloadFileName)}">Скачать ${escapeHtml(options.downloadFileName)}</a>`;
                }
            }
        }

        messageElement.innerHTML = messageHTML;
        chatHistoryContainer.appendChild(messageElement);
        chatHistoryContainer.scrollTop = chatHistoryContainer.scrollHeight;
        return messageElement;
    }


    typeBotMessage("Здравствуйте! Введите текст или прикрепите файл для анонимизации.", 30);

    async function callAnonymizationAPI(payload) {
        await new Promise(resolve => setTimeout(resolve, 1500));

        try {
            const formData = new FormData();
            if (payload.file) formData.append('file', payload.file);
            if (payload.text) formData.append('text', payload.text);
            if (payload.comment) formData.append('comment', payload.comment);

            const response = await fetch('/send_message', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: `HTTP ошибка: ${response.status} ${response.statusText}` }));
                return { success: false, error: errorData.error || `HTTP ошибка: ${response.status} ${response.statusText}` };
            }

            const result = await response.json();
            console.log(result);
            return result;

        } catch (err) {
            return { success: false, error: 'Ошибка при подключении к серверу или обработке ответа.' };
        }
    }

    sendButton.addEventListener('click', async () => {
        const text = textInput.value.trim();

        if (!text && !currentFile) {
            textInput.placeholder = "Пожалуйста, введите текст или прикрепите файл!";
            setTimeout(() => {
                textInput.placeholder = "Напишите Hackanomics или прикрепите файл...";
            }, 2000);
            return;
        }

        addMessageToHistory(text, 'user', { fileName: currentFile ? currentFile.name : null });

        const payload = {};
        if (currentFile) {
            payload.file = currentFile;
            if (text) payload.comment = text;
        } else {
            payload.text = text;
        }

        textInput.value = '';
        textInput.dispatchEvent(new Event('input'));
        if (currentFile) {
            removeFileBtn.click();
        }

        const botMessageElement = addMessageToHistory(null, 'bot', { isLoading: true });

        const result = await callAnonymizationAPI(payload);

        let botContent = '';
        const botOptions = { isLoading: false };

        if (result.success) {
            if (result.blurredImageUrl) {
                botContent += `<img src="${escapeHtml(result.blurredImageUrl)}" 
                                alt="Зашумленное изображение" 
                                style="max-width:100%;margin-bottom:10px;" />`;
            }

            botContent += result.anonymizedHtml || '';
            botContent += result.replyHtml || '';
        } else {
            botOptions.error = result.error || 'Не удалось обработать запрос.';
        }

        botMessageElement.remove();
        addMessageToHistory(botContent, 'bot', botOptions);
    });

    textInput.dispatchEvent(new Event('input'));
});
