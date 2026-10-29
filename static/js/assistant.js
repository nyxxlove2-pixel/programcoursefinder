// AI assistant chat page: sends questions without reloading the page, shows a
// "thinking" indicator while the server asks the AI, then adds the answer to the chat.

const form = document.getElementById('chat-form');
const input = document.getElementById('id_question');
const sendButton = document.getElementById('chat-send');
const chatLog = document.getElementById('chat-log');
const emptyState = document.getElementById('chat-empty');
const historyList = document.getElementById('chat-history');

const THINKING_STEPS = [
  'Searching verified courses…',
  'Reading student reviews…',
  'Comparing tuition and distance…',
  'Writing your answer…',
];
let waiting = false;

// Copy a piece of HTML kept in a <template> on the page
function fromTemplate(id) {
  return document.getElementById(id).content.firstElementChild.cloneNode(true);
}

function scrollToBottom(behavior = 'smooth') {
  window.scrollTo({ top: document.body.scrollHeight, behavior });
}

// Grow the box with the text, and only allow sending when there is a question
function updateInput() {
  input.style.height = 'auto';
  input.style.height = `${input.scrollHeight}px`;
  sendButton.disabled = waiting || !input.value.trim();
}

function showConversation() {
  emptyState.classList.add('hidden');
  chatLog.classList.remove('hidden');
}

// Show the question bubble right away so the chat feels instant
function addQuestion(question) {
  const bubble = fromTemplate('question-template');
  bubble.querySelector('[data-question]').textContent = question;
  chatLog.append(bubble);
}

// Add the thinking indicator and rotate its text; returns a function that removes it
function startThinking() {
  const thinking = fromTemplate('thinking-template');
  const label = thinking.querySelector('[data-thinking-text]');
  let step = 0;
  const timer = setInterval(() => {
    step = (step + 1) % THINKING_STEPS.length;
    label.textContent = THINKING_STEPS[step];
  }, 1800);
  chatLog.append(thinking);
  return () => {
    clearInterval(timer);
    thinking.remove();
  };
}

// Add the answer HTML from the server (ai_assistant/chat_answer.html)
function addAnswer(html) {
  chatLog.insertAdjacentHTML('beforeend', html.trim());
  scrollToBottom();
}

// Put this chat at the top of the sidebar, and give a new chat its own address
// so a refresh (or a shared link) opens it again
function updateHistory(reply) {
  document.getElementById('history-empty')?.remove();
  historyList.querySelector(`[data-conversation="${reply.conversation_id}"]`)?.remove();
  historyList.insertAdjacentHTML('afterbegin', reply.history_html);
  historyList.firstElementChild.classList.add('animate-rise-in');
  if (window.location.pathname !== reply.conversation_url) {
    window.history.pushState({}, '', reply.conversation_url);
  }
}

function addError(message) {
  const error = fromTemplate('error-template');
  error.querySelector('p').textContent = message;
  chatLog.append(error);
  scrollToBottom();
}

async function sendToServer(formData) {
  try {
    const response = await fetch(window.location.href, {
      method: 'POST',
      body: formData,
      headers: { 'X-Requested-With': 'fetch' },
    });
    return await response.json();
  } catch (error) {
    return { error: 'Could not reach the server. Check your connection and try again.' };
  }
}

async function ask(question) {
  const formData = new FormData(form);
  formData.set('question', question);
  input.value = '';
  waiting = true;
  updateInput();

  showConversation();
  addQuestion(question);
  const stopThinking = startThinking();
  scrollToBottom();

  const reply = await sendToServer(formData);
  stopThinking();
  if (reply.html) {
    addAnswer(reply.html);
    updateHistory(reply);
  } else {
    addError(reply.error);
  }
  waiting = false;
  updateInput();
  input.focus();
}

form.addEventListener('submit', (event) => {
  event.preventDefault();
  const question = input.value.trim();
  if (question && !waiting) ask(question);
});

// Enter sends, Shift+Enter adds a new line (like most chat apps)
input.addEventListener('keydown', (event) => {
  if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
    event.preventDefault();
    form.requestSubmit();
  }
});
input.addEventListener('input', updateInput);

document.querySelectorAll('[data-example]').forEach((button) => {
  button.addEventListener('click', () => ask(button.dataset.example));
});

// The page content follows the address, so going back or forward reloads it
window.addEventListener('popstate', () => window.location.reload());

updateInput();
scrollToBottom('instant');
