/**
 * static/js/chatbot.js
 * AAA — AimondAIAssistant Frontend Logic
 */

const Chatbot = (() => {
  let isOpen   = false;
  let isTyping = false;
  let history  = [];  // Luu lich su hoi thoai

  let elTrigger, elWindow, elMessages, elInput, elSend, elClose, elNotif, elSuggestions;

  function init() {
    elTrigger     = document.getElementById('aaa-trigger');
    elWindow      = document.getElementById('aaa-window');
    elMessages    = document.getElementById('aaa-messages');
    elInput       = document.getElementById('aaa-input');
    elSend        = document.getElementById('aaa-send');
    elClose       = document.getElementById('aaa-close');
    elNotif       = document.getElementById('aaa-notif');
    elSuggestions = document.getElementById('aaa-suggestions');

    if (!elTrigger) return;

    elTrigger.addEventListener('click', toggle);
    elClose.addEventListener('click',   close);
    elSend.addEventListener('click',    sendMessage);

    elInput.addEventListener('keydown', e => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });

    // Suggestion buttons
    elSuggestions?.querySelectorAll('.aaa-suggestion-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const msg = btn.dataset.msg;
        if (msg) {
          elInput.value = msg;
          sendMessage();
          elSuggestions.style.display = 'none';
        }
      });
    });

    // Close on outside click
    document.addEventListener('click', e => {
      if (isOpen && !elWindow.contains(e.target) && !elTrigger.contains(e.target)) {
        close();
      }
    });
  }

  function toggle() {
    isOpen ? close() : open();
  }

  function open() {
    isOpen = true;
    elWindow.classList.add('open');
    elTrigger.setAttribute('aria-expanded', 'true');
    // Hide notification
    if (elNotif) elNotif.classList.add('hidden');
    // Focus input
    setTimeout(() => elInput?.focus(), 250);
  }

  function close() {
    isOpen = false;
    elWindow.classList.remove('open');
    elTrigger.setAttribute('aria-expanded', 'false');
  }

  async function sendMessage() {
    const text = (elInput.value || '').trim();
    if (!text || isTyping) return;

    // Append user message
    _appendMessage(text, 'user');
    elInput.value = '';
    elSuggestions && (elSuggestions.style.display = 'none');

    // Them vao history
    history.push({ role: 'user', content: text });
    // Giu toi da 10 luot hoi dap (20 entries)
    if (history.length > 20) history = history.slice(-20);

    // Show typing
    const typingEl = _showTyping();
    isTyping = true;
    elSend.disabled = true;

    try {
      const res = await API.chatbot.message(text, history.slice(0, -1));
      _removeTyping(typingEl);
      console.log('[Chatbot] response:', res);

      if (res.ok && res.data && res.data.reply) {
        _appendMessage(res.data.reply, 'bot');
        history.push({ role: 'assistant', content: res.data.reply });
      } else {
        const errMsg = res.error || (res.data && res.data.error) || 'Lỗi không xác định';
        console.error('[Chatbot] error:', errMsg, res);
        _appendMessage('Xin lỗi, có lỗi xảy ra: ' + errMsg, 'bot');
      }
    } catch(err) {
      _removeTyping(typingEl);
      console.error('[Chatbot] exception:', err);
      _appendMessage('Không thể kết nối đến server: ' + err.message, 'bot');
    } finally {
      isTyping = false;
      elSend.disabled = false;
      elInput.focus();
    }
  }

  function _appendMessage(text, role) {
    const div = document.createElement('div');
    div.className = `aaa-msg aaa-msg-${role}`;

    // Convert newlines to <br> and allow simple bold **text**
    const formatted = UI.escapeHtml(text)
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n/g, '<br>');

    div.innerHTML = `<div class="aaa-msg-bubble">${formatted}</div>`;
    elMessages.appendChild(div);
    _scrollToBottom();
  }

  function _showTyping() {
    const div = document.createElement('div');
    div.className = 'aaa-msg aaa-msg-bot';
    div.innerHTML = `
      <div class="aaa-msg-bubble aaa-typing">
        <span></span><span></span><span></span>
      </div>`;
    elMessages.appendChild(div);
    _scrollToBottom();
    return div;
  }

  function _removeTyping(el) {
    el?.remove();
  }

  function _scrollToBottom() {
    if (elMessages) {
      elMessages.scrollTop = elMessages.scrollHeight;
    }
  }

  return { init, open, close, toggle };
})();

document.addEventListener('DOMContentLoaded', () => Chatbot.init());
window.Chatbot = Chatbot;