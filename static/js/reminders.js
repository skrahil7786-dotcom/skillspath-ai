// ==========================================================================
// MentorAI — Smart Revision Reminders Controller
// ==========================================================================

document.addEventListener('DOMContentLoaded', async () => {
  const userId = window.REMINDERS_USER_ID || getActiveUserId();
  const container = document.getElementById('remindersListContainer');
  let currentTab = 'due'; // 'due', 'upcoming', 'completed'

  let queueItems = [];
  const completedLocalItems = [];

  // Quick quiz button
  if (userId) {
    document.getElementById('takeQuizQuickBtn').href = `/quiz/${userId}`;
  }

  // Tab switching
  const tabs = document.querySelectorAll('.rem-tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => {
        t.classList.remove('btn-primary', 'active');
        t.classList.add('btn-secondary');
      });
      tab.classList.remove('btn-secondary');
      tab.classList.add('btn-primary', 'active');

      currentTab = tab.dataset.tab;
      renderReminders();
    });
  });

  async function loadReminders() {
    if (!userId) {
      renderEmptyState();
      return;
    }

    showLoading("Loading revision reminders...");
    const res = await apiFetch(`/api/dashboard/${userId}`);
    hideLoading();

    if (res.ok && res.data && res.data.success) {
      queueItems = res.data.data.revision_queue || [];
      updateCounts();
      renderReminders();
    } else {
      renderEmptyState();
    }
  }

  function updateCounts() {
    const todayStr = new Date().toISOString().split('T')[0];

    const dueCount = queueItems.filter(i => (i.due_date || '') <= todayStr).length;
    const upcomingCount = queueItems.filter(i => (i.due_date || '') > todayStr).length;
    const completedCount = completedLocalItems.length;

    document.getElementById('dueTodayCount').textContent = dueCount;
    document.getElementById('upcomingCount').textContent = upcomingCount;
    document.getElementById('completedCount').textContent = completedCount;
  }

  function renderReminders() {
    container.innerHTML = '';
    const todayStr = new Date().toISOString().split('T')[0];

    let itemsToDisplay = [];
    if (currentTab === 'due') {
      itemsToDisplay = queueItems.filter(i => (i.due_date || '') <= todayStr);
    } else if (currentTab === 'upcoming') {
      itemsToDisplay = queueItems.filter(i => (i.due_date || '') > todayStr);
    } else if (currentTab === 'completed') {
      itemsToDisplay = completedLocalItems;
    }

    if (itemsToDisplay.length === 0) {
      renderEmptyState();
      return;
    }

    itemsToDisplay.forEach(item => {
      const card = document.createElement('div');
      card.className = 'glass-card card-hover-lift';
      card.style.display = 'flex';
      card.style.justifyContent = 'space-between';
      card.style.alignItems = 'center';
      card.style.flexWrap = 'wrap';
      card.style.gap = '1rem';

      const intervalText = item.interval_days === 1 ? 'Stage 1 (1-Day)' : (item.interval_days === 3 ? 'Stage 2 (3-Day)' : 'Stage 3 (7-Day)');

      card.innerHTML = `
        <div style="flex: 1; min-width: 260px;">
          <div style="display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.35rem;">
            <span class="badge ${currentTab === 'completed' ? 'badge-success' : 'badge-warning'}">
              ${currentTab === 'completed' ? '✓ Mastered' : intervalText}
            </span>
            <span style="font-size: 0.8rem; color: var(--text-dim);">Due: ${item.due_date || 'Today'}</span>
          </div>

          <h3 style="font-size: 1.15rem; color: #fff; margin-bottom: 0.35rem; font-family: var(--font-heading);">
            ${item.concept}
          </h3>

          <p style="color: var(--text-muted); font-size: 0.88rem; line-height: 1.45; margin: 0;">
            ${currentTab === 'completed' ? 'Spaced repetition verified. Concept consolidated in long-term memory.' : 'Spaced repetition review: 15-minute concept recall to solidify long-term retention.'}
          </p>
        </div>

        ${currentTab !== 'completed' ? `
          <div style="display: flex; gap: 0.5rem; align-items: center;">
            <button type="button" class="btn btn-secondary btn-sm snooze-btn" data-id="${item.id}">
              Snooze
            </button>
            <button type="button" class="btn btn-primary btn-sm complete-btn" data-id="${item.id}">
              ✓ Mark Complete
            </button>
          </div>
        ` : `
          <div>
            <span class="badge badge-success" style="font-size: 0.85rem; padding: 0.35rem 0.75rem;">Done ✓</span>
          </div>
        `}
      `;

      // Event listeners
      if (currentTab !== 'completed') {
        const completeBtn = card.querySelector('.complete-btn');
        const snoozeBtn = card.querySelector('.snooze-btn');

        completeBtn.addEventListener('click', async () => {
          showLoading("Updating spaced repetition interval...");
          const res = await apiFetch(`/api/revision/${item.id}/complete`, { method: 'POST' });
          hideLoading();

          if (res.ok && res.data && res.data.success) {
            // Remove from active queue
            queueItems = queueItems.filter(q => q.id !== item.id);
            completedLocalItems.push({
              ...item,
              completed: 1
            });
            updateCounts();
            renderReminders();
          } else {
            alert("Error completing revision item.");
          }
        });

        snoozeBtn.addEventListener('click', () => {
          snoozeBtn.textContent = 'Snoozed';
          snoozeBtn.disabled = true;
          card.style.opacity = '0.4';
        });
      }

      container.appendChild(card);
    });
  }

  function renderEmptyState() {
    container.innerHTML = `
      <div class="glass-card empty-state" style="padding: 3.5rem 1.5rem;">
        <div class="empty-state-icon">✨</div>
        <h3 class="empty-state-title">No reminders right now.</h3>
        <p class="empty-state-desc">
          You are completely caught up! Concepts you struggle with during adaptive quizzes will automatically be scheduled here.
        </p>
        <a href="/quiz/${userId || ''}" class="btn btn-primary btn-sm" style="margin-top: 0.5rem;">
          Take an Adaptive Quiz →
        </a>
      </div>
    `;
  }

  loadReminders();
});
