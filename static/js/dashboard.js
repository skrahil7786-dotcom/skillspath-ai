// ==========================================================================
// MentorAI — Dashboard Logic (Clean Light Theme, 5 Sections Only)
// ==========================================================================

document.addEventListener('DOMContentLoaded', async () => {
  let userId = window.DASHBOARD_USER_ID || getActiveUserId();

  const emptyStateEl = document.getElementById('dashboardEmptyState');
  const activeViewEl = document.getElementById('dashboardActiveView');

  if (!userId) {
    if (emptyStateEl && activeViewEl) {
      emptyStateEl.style.display = 'flex';
      activeViewEl.style.display = 'none';
    }
    return;
  }

  setActiveUserId(userId);
  await loadDashboard(userId);

  async function loadDashboard(uid) {
    showLoading("Loading dashboard...");
    const res = await apiFetch(`/api/dashboard/${uid}`);
    hideLoading();

    if (res.ok && res.data && res.data.success) {
      const data = res.data.data;
      renderDashboard(data);
    } else {
      if (emptyStateEl && activeViewEl) {
        emptyStateEl.style.display = 'flex';
        activeViewEl.style.display = 'none';
      }
    }
  }

  function renderDashboard(data) {
    const { user, topic_mastery, revision_queue, quiz_accuracy, streak, study_plan } = data;

    // If no plan exists, display empty state
    if (!study_plan || study_plan.length === 0) {
      if (emptyStateEl && activeViewEl) {
        emptyStateEl.style.display = 'flex';
        activeViewEl.style.display = 'none';
      }
      return;
    }

    if (emptyStateEl && activeViewEl) {
      emptyStateEl.style.display = 'none';
      activeViewEl.style.display = 'block';
    }

    // 1. Welcome Header (First name only)
    const fullName = user.name || 'Student';
    const firstName = fullName.split(' ')[0] || fullName;
    document.getElementById('studentFirstName').textContent = firstName;
    document.getElementById('studentGoal').textContent = user.primary_goal || 'GATE CSE';
    document.getElementById('studentExamDate').textContent = user.exam_date || 'Upcoming';

    // 2. Today's Focus Card
    const todayPlan = study_plan[0] || {};
    document.getElementById('focusSubject').textContent = todayPlan.focus_subject || 'Data Structures';
    document.getElementById('focusTopic').textContent = todayPlan.focus_topic || 'Foundational Review';
    document.getElementById('focusDuration').textContent = `${todayPlan.study_minutes || 120} mins`;
    document.getElementById('focusReason').textContent = todayPlan.reason || 'Optimal schedule for maximum retention.';
    document.getElementById('startTodayTaskBtn').href = `/quiz/${userId}?subject=${encodeURIComponent(todayPlan.focus_subject || 'Data Structures & Algorithms')}`;

    // 3. Three KPI Cards Only
    document.getElementById('kpiQuizAccuracy').textContent = `${quiz_accuracy}%`;
    document.getElementById('kpiStudyStreak').textContent = `🔥 ${streak} ${streak === 1 ? 'Day' : 'Days'}`;
    document.getElementById('kpiRevisionsDue').textContent = `${(revision_queue || []).length}`;

    // 4. Subject Progress (Selected subjects only)
    renderSubjectProgress(topic_mastery || []);

    // 5. Pending Reminders (Maximum 3)
    renderPendingReminders(revision_queue || []);
  }

  function renderSubjectProgress(topics) {
    const container = document.getElementById('subjectProgressList');
    container.innerHTML = '';

    if (!topics || topics.length === 0) {
      container.innerHTML = `<div style="color: var(--text-muted); font-size: 0.9rem;">No subject progress recorded yet.</div>`;
      return;
    }

    // Aggregate average mastery per subject
    const subjectMap = {};
    topics.forEach(t => {
      const s = t.subject_name || 'General';
      if (!subjectMap[s]) subjectMap[s] = { total: 0, count: 0 };
      subjectMap[s].total += t.mastery;
      subjectMap[s].count += 1;
    });

    const subjects = Object.keys(subjectMap);
    subjects.slice(0, 5).forEach(subj => {
      const avg = Math.round(subjectMap[subj].total / subjectMap[subj].count);

      const el = document.createElement('div');
      el.innerHTML = `
        <div style="display: flex; justify-content: space-between; font-size: 0.88rem; margin-bottom: 5px;">
          <span style="font-weight: 500; color: var(--text-main);">${subj}</span>
          <span style="color: var(--text-main); font-weight: 600;">${avg}%</span>
        </div>
        <div class="progress-track" style="height: 7px;">
          <div class="progress-fill" style="width: ${avg}%;"></div>
        </div>
      `;
      container.appendChild(el);
    });
  }

  function renderPendingReminders(queue) {
    const container = document.getElementById('dashboardRemindersList');
    container.innerHTML = '';

    if (!queue || queue.length === 0) {
      container.innerHTML = `<div style="color: var(--text-muted); font-size: 0.9rem; padding: 4px 0;">No revisions due. Great job staying consistent.</div>`;
      return;
    }

    // Maximum 3 reminders
    const maxThree = queue.slice(0, 3);
    maxThree.forEach(item => {
      const el = document.createElement('div');
      el.style.background = 'var(--bg-primary)';
      el.style.border = '1px solid var(--border)';
      el.style.borderRadius = '10px';
      el.style.padding = '12px 16px';
      el.style.display = 'flex';
      el.style.justifyContent = 'space-between';
      el.style.alignItems = 'center';
      el.style.gap = '12px';

      el.innerHTML = `
        <div style="flex: 1;">
          <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 2px;">
            <span class="badge badge-warning" style="font-size: 0.72rem;">Due ${item.due_date}</span>
          </div>
          <div style="color: var(--text-main); font-size: 0.92rem; font-weight: 500;">
            ${item.concept}
          </div>
        </div>
        <div style="display: flex; gap: 6px;">
          <button type="button" class="btn btn-secondary btn-sm snooze-btn" data-id="${item.id}" style="min-height: 32px; padding: 2px 10px; font-size: 0.8rem;">
            Snooze
          </button>
          <button type="button" class="btn btn-primary btn-sm complete-btn" data-id="${item.id}" style="min-height: 32px; padding: 2px 12px; font-size: 0.8rem;">
            Complete
          </button>
        </div>
      `;

      // Complete button advances interval
      el.querySelector('.complete-btn').addEventListener('click', async () => {
        const res = await apiFetch(`/api/revision/${item.id}/complete`, { method: 'POST' });
        if (res.ok && res.data && res.data.success) {
          el.remove();
          const currentCount = parseInt(document.getElementById('kpiRevisionsDue').textContent || '0', 10);
          document.getElementById('kpiRevisionsDue').textContent = `${Math.max(0, currentCount - 1)}`;
          if (container.children.length === 0) {
            container.innerHTML = `<div style="color: var(--text-muted); font-size: 0.9rem;">No revisions due. Great job staying consistent.</div>`;
          }
        }
      });

      // Snooze button
      el.querySelector('.snooze-btn').addEventListener('click', () => {
        el.style.opacity = '0.4';
        el.querySelector('.snooze-btn').textContent = 'Snoozed';
        el.querySelector('.snooze-btn').disabled = true;
      });

      container.appendChild(el);
    });
  }
});
