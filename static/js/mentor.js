// ==========================================================================
// MentorAI — Chat Interface Handler
// ==========================================================================

document.addEventListener('DOMContentLoaded', () => {
  const userId = window.MENTOR_USER_ID || getActiveUserId();
  const chatMessages = document.getElementById('chatMessages');
  const chatForm = document.getElementById('chatForm');
  const chatInput = document.getElementById('chatInput');
  const typingIndicator = document.getElementById('typingIndicator');

  // Handle prompt chips
  document.querySelectorAll('.prompt-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      const text = chip.textContent.replace(/^[\p{Emoji}\s]+/u, '').trim();
      chatInput.value = text;
      sendMessage(text);
    });
  });

  // Handle form submission
  chatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const text = chatInput.value.trim();
    if (!text) return;
    sendMessage(text);
  });

  async function sendMessage(text) {
    chatInput.value = '';

    // Append User Message (Right-aligned)
    appendUserMessage(text);
    scrollToBottom();

    // Show Typing Indicator
    if (typingIndicator) typingIndicator.style.display = 'flex';

    try {
      const res = await apiFetch('/api/mentor/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          message: text
        })
      });

      if (typingIndicator) typingIndicator.style.display = 'none';

      if (res.ok && res.data && res.data.success) {
        appendMentorMessage(res.data.reply);
      } else {
        appendMentorMessage("I'm analyzing your request. Based on your syllabus, make sure to review core theorems and take a quick 5-question adaptive quiz!");
      }
    } catch (err) {
      if (typingIndicator) typingIndicator.style.display = 'none';
      appendMentorMessage("Could not connect to mentor service right now. Please verify your connection or try another topic.");
    }

    scrollToBottom();
  }

  function appendUserMessage(text) {
    const wrapper = document.createElement('div');
    wrapper.style.display = 'flex';
    wrapper.style.justifyContent = 'flex-end';
    wrapper.innerHTML = `
      <div class="chat-bubble student" style="margin: 0; max-width: 80%; border-radius: 16px; border-top-right-radius: 4px;">
        ${escapeHtml(text)}
      </div>
    `;
    chatMessages.appendChild(wrapper);
  }

  function appendMentorMessage(text) {
    const wrapper = document.createElement('div');
    wrapper.style.display = 'flex';
    wrapper.style.gap = '0.75rem';
    wrapper.style.alignItems = 'flex-start';
    wrapper.style.maxWidth = '85%';

    // Basic markdown bolding/newlines formatting
    const formattedText = escapeHtml(text)
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n/g, '<br>');

    wrapper.innerHTML = `
      <div class="brand-spark" style="width: 28px; height: 28px; font-size: 0.85rem; flex-shrink: 0; margin-top: 2px;">✦</div>
      <div class="chat-bubble mentor" style="margin: 0; border-radius: 16px; border-top-left-radius: 4px;">
        ${formattedText}
      </div>
    `;
    chatMessages.appendChild(wrapper);
  }

  function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }
});
