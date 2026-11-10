const platformSelect = document.getElementById('platform-select');
const contactSelect  = document.getElementById('contact-select');
const commandInput   = document.getElementById('command-input');
const sendForm       = document.getElementById('send-form');
const sendBtn        = document.getElementById('send-btn');
const transcript     = document.getElementById('transcript');
const hero           = document.getElementById('hero');
const notifBar       = document.getElementById('notif-bar');
const contactListEl  = document.getElementById('contact-list');
const contactForm    = document.getElementById('contact-form');
const toggleBtn      = document.getElementById('toggle-btn');

let allContacts = [];
let notifTimer = null;

// --------------------------------------------------------------------
// Notification bar
// --------------------------------------------------------------------
function showNotif(text, state) {
  clearTimeout(notifTimer);
  notifBar.textContent = text;
  notifBar.className = `notif-bar visible ${state}`;
}

function hideNotifSoon(delayMs) {
  clearTimeout(notifTimer);
  notifTimer = setTimeout(() => notifBar.classList.remove('visible'), delayMs);
}

// --------------------------------------------------------------------
// Contacts
// --------------------------------------------------------------------
async function loadContacts() {
  const res = await fetch('/api/contacts');
  const rawData = await res.json();
  
  // Convert the Python dictionary into a JavaScript array
  allContacts = Object.entries(rawData).map(([key, val]) => ({
    key: key,
    name: val.display_name || key,
    phone: val.phone || '',
    email: val.email || ''
  }));

  renderContactList();
  renderContactDropdown();
}

function renderContactList() {
  contactListEl.innerHTML = '';
  if (allContacts.length === 0) {
    contactListEl.innerHTML = '<p class="muted small">No contacts yet — add one below.</p>';
    return;
  }
  allContacts.forEach((c) => {
    const row = document.createElement('div');
    row.className = 'contact-row';
    row.innerHTML = `
      <div>
        <strong>${escapeHtml(c.name)}</strong>
        <div class="muted small">${escapeHtml(c.phone || '—')} &nbsp;·&nbsp; ${escapeHtml(c.email || '—')}</div>
      </div>
      <button class="delete-btn" type="button" data-key="${escapeHtml(c.key)}">Delete</button>
    `;
    contactListEl.appendChild(row);
  });
  contactListEl.querySelectorAll('.delete-btn').forEach((btn) => {
    btn.addEventListener('click', async () => {
      await fetch(`/api/contacts/${encodeURIComponent(btn.dataset.key)}`, { method: 'DELETE' });
      loadContacts();
    });
  });
}

function renderContactDropdown() {
  const platform = platformSelect.value; // "whatsapp" | "email"
  const field = platform === 'whatsapp' ? 'phone' : 'email';
  const filtered = allContacts.filter((c) => (c[field] || '').trim());

  contactSelect.innerHTML = '';

  if (filtered.length === 0) {
    const label = field === 'phone' ? 'a phone number' : 'an email';
    contactSelect.innerHTML = `<option value="">No contact has ${label} yet</option>`;
    contactSelect.disabled = true;
    commandInput.disabled = true;
    commandInput.placeholder = 'Add a contact first';
    sendBtn.disabled = true;
    return;
  }

  filtered.forEach((c) => {
    const opt = document.createElement('option');
    opt.value = c.name;
    opt.textContent = c.name;
    contactSelect.appendChild(opt);
  });
  contactSelect.disabled = false;
  commandInput.disabled = false;
  commandInput.placeholder = `Message for ${filtered[0].name}...`;
  sendBtn.disabled = false;
}

platformSelect.addEventListener('change', renderContactDropdown);
contactSelect.addEventListener('change', () => {
  if (contactSelect.value) {
    commandInput.placeholder = `Message for ${contactSelect.value}...`;
  }
});

contactForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const name = document.getElementById('c-name').value.trim();
  const phone = document.getElementById('c-phone').value.trim();
  const email = document.getElementById('c-email').value.trim();
  if (!name) return;

  await fetch('/api/contacts', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, phone, email }),
  });
  contactForm.reset();
  loadContacts();
});

// --------------------------------------------------------------------
// Transcript
// --------------------------------------------------------------------
function appendMessage(role, text, platform = null) {
  hero.classList.add('hidden');
  const bubble = document.createElement('div');
  bubble.className = `bubble ${role}`;
  if (platform) bubble.classList.add(platform); 
  bubble.textContent = text;
  transcript.appendChild(bubble);
  bubble.scrollIntoView({ behavior: 'smooth', block: 'end' });
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

// --------------------------------------------------------------------
// Send -- opens an SSE stream so the notification bar reflects live
// backend progress while the (visible, on-screen) automation runs.
// --------------------------------------------------------------------
sendForm.addEventListener('submit', (e) => {
  e.preventDefault();
  const command = commandInput.value.trim();
  const contact = contactSelect.value;
  const platform = platformSelect.value;
  if (!command || !contact) return;

  appendMessage('user', command, platform);
  commandInput.value = '';
  sendBtn.disabled = true;
  commandInput.disabled = true;

  const params = new URLSearchParams({ command, platform, contact });
  const es = new EventSource(`/api/send?${params.toString()}`);

  es.addEventListener('status', (evt) => {
    const data = JSON.parse(evt.data);
    showNotif(data.text, 'info');
  });

  es.addEventListener('done', (evt) => {
    const data = JSON.parse(evt.data);
    showNotif(data.text, 'success');
    appendMessage('assistant', `${data.text}`);
    es.close();
    finishSend();
    hideNotifSoon(4000);
  });

  es.addEventListener('failed', (evt) => {
    const data = JSON.parse(evt.data);
    showNotif(data.text, 'failed');
    appendMessage('assistant', `${data.text}`);
    es.close();
    finishSend();
    hideNotifSoon(6000);
  });

  // Genuine connection-level failure (server dropped, network issue) --
  // distinct from the 'failed' business-logic event above.
  es.onerror = () => {
    if (es.readyState === EventSource.CLOSED) return;
    showNotif('Connection to the server was lost.', 'failed');
    es.close();
    finishSend();
    hideNotifSoon(6000);
  };
});

function finishSend() {
  sendBtn.disabled = false;
  commandInput.disabled = false;
  commandInput.focus();
}

// --------------------------------------------------------------------
// Sidebar toggle
// --------------------------------------------------------------------
toggleBtn.addEventListener('click', () => {
  document.querySelector('.layout').classList.toggle('sidebar-collapsed');
});

loadContacts();