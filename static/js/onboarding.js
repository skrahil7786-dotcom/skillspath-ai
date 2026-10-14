// ==========================================================================
// MentorAI — Multi-step Onboarding Controller (5-step simple flow)
// ==========================================================================

document.addEventListener('DOMContentLoaded', () => {
  let currentStep = 1;
  let userId = document.getElementById('userIdField').value || null;

  // Pre-fill name if coming from signup/query param
  const urlParams = new URLSearchParams(window.location.search);
  const nameParam = urlParams.get('name') || localStorage.getItem('mentorai_user_name');
  if (nameParam) {
    document.getElementById('fullName').value = nameParam;
  }

  // Pre-fill default exam date (90 days from now)
  const defaultDate = new Date();
  defaultDate.setDate(defaultDate.getDate() + 90);
  document.getElementById('examDate').value = defaultDate.toISOString().split('T')[0];

  const defaultSubjects = [
    "Data Structures & Algorithms", "DBMS", "Operating Systems", "Computer Networks",
    "Java", "Python", "C/C++", "SQL", "Software Engineering", "Discrete Mathematics",
    "Engineering Mathematics", "Aptitude"
  ];

  const selectedSubjects = {};

  // Setup Subject Chips in Step 2
  const pillsContainer = document.getElementById('subjectPillsContainer');
  defaultSubjects.forEach(subj => {
    const chip = document.createElement('button');
    chip.type = 'button';
    chip.className = 'btn btn-secondary btn-sm';
    chip.style.borderRadius = 'var(--radius-pill)';
    chip.style.fontSize = '0.85rem';
    chip.textContent = subj;
    chip.dataset.subject = subj;
    chip.addEventListener('click', () => toggleSubjectSelection(subj, chip));
    pillsContainer.appendChild(chip);
  });

  // Goal conditional fields
  const primaryGoalSelect = document.getElementById('primaryGoal');
  primaryGoalSelect.addEventListener('change', updateConditionalGoalFields);
  updateConditionalGoalFields();

  function updateConditionalGoalFields() {
    const val = primaryGoalSelect.value;
    document.getElementById('gateFields').style.display = (val === 'GATE CSE' || val === 'GATE Data Science & AI') ? 'block' : 'none';
    document.getElementById('placementFields').style.display = (val === 'Campus Placement' || val === 'Off-Campus Placement') ? 'block' : 'none';
    document.getElementById('semesterFields').style.display = (val === 'Semester Exams') ? 'block' : 'none';
    document.getElementById('govtFields').style.display = (val === 'Government Exam') ? 'block' : 'none';
  }

  // Custom subject input
  document.getElementById('addCustomSubjectBtn').addEventListener('click', () => {
    const customInput = document.getElementById('customSubjectInput');
    const customName = customInput.value.trim();
    if (customName && !selectedSubjects[customName]) {
      selectedSubjects[customName] = { confidence_level: 'Average', priority: 'Medium' };
      renderConfiguredSubjects();
      customInput.value = '';
    }
  });

  function toggleSubjectSelection(subjName, chip) {
    if (selectedSubjects[subjName]) {
      delete selectedSubjects[subjName];
      chip.classList.remove('btn-primary');
      chip.classList.add('btn-secondary');
    } else {
      selectedSubjects[subjName] = {
        confidence_level: 'Average',
        priority: 'Medium'
      };
      chip.classList.remove('btn-secondary');
      chip.classList.add('btn-primary');
    }
    renderConfiguredSubjects();
  }

  function renderConfiguredSubjects() {
    const container = document.getElementById('configuredSubjectsList');
    container.innerHTML = '';
    const names = Object.keys(selectedSubjects);
    const errEl = document.getElementById('subjectError');

    if (names.length === 0) {
      errEl.style.display = 'block';
      return;
    } else {
      errEl.style.display = 'none';
    }

    names.forEach(name => {
      const s = selectedSubjects[name];
      const card = document.createElement('div');
      card.className = 'card';
      card.style.padding = '14px 18px';
      card.style.background = '#ffffff';

      card.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
          <strong style="color: var(--text-main); font-size: 0.95rem;">${name}</strong>
          <button type="button" class="btn btn-sm btn-secondary" style="min-height: 28px; padding: 2px 8px; font-size: 0.75rem; color: var(--danger);" data-remove="${name}">✕ Remove</button>
        </div>

        <div class="grid grid-2" style="gap: 12px;">
          <!-- Confidence -->
          <div>
            <label class="form-label" style="font-size: 0.78rem; margin-bottom: 4px;">Confidence Level</label>
            <div class="segmented-control" data-type="confidence" data-subject="${name}">
              <button type="button" class="segmented-btn ${s.confidence_level === 'Weak' ? 'active' : ''}" data-val="Weak">Weak</button>
              <button type="button" class="segmented-btn ${s.confidence_level === 'Average' ? 'active' : ''}" data-val="Average">Average</button>
              <button type="button" class="segmented-btn ${s.confidence_level === 'Good' ? 'active' : ''}" data-val="Good">Good</button>
              <button type="button" class="segmented-btn ${s.confidence_level === 'Strong' ? 'active' : ''}" data-val="Strong">Strong</button>
            </div>
          </div>

          <!-- Priority -->
          <div>
            <label class="form-label" style="font-size: 0.78rem; margin-bottom: 4px;">Exam Priority</label>
            <div class="segmented-control" data-type="priority" data-subject="${name}">
              <button type="button" class="segmented-btn ${s.priority === 'High' ? 'active' : ''}" data-val="High">High</button>
              <button type="button" class="segmented-btn ${s.priority === 'Medium' ? 'active' : ''}" data-val="Medium">Medium</button>
              <button type="button" class="segmented-btn ${s.priority === 'Low' ? 'active' : ''}" data-val="Low">Low</button>
            </div>
          </div>
        </div>
      `;

      // Segmented control click handlers
      card.querySelectorAll('.segmented-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          const control = btn.parentElement;
          const type = control.dataset.type;
          const subj = control.dataset.subject;
          const val = btn.dataset.val;

          control.querySelectorAll('.segmented-btn').forEach(b => b.classList.remove('active'));
          btn.classList.add('active');

          if (type === 'confidence') {
            selectedSubjects[subj].confidence_level = val;
          } else if (type === 'priority') {
            selectedSubjects[subj].priority = val;
          }
        });
      });

      // Remove handler
      card.querySelector('[data-remove]').addEventListener('click', () => {
        delete selectedSubjects[name];
        const chip = pillsContainer.querySelector(`[data-subject="${name}"]`);
        if (chip) {
          chip.classList.remove('btn-primary');
          chip.classList.add('btn-secondary');
        }
        renderConfiguredSubjects();
      });

      container.appendChild(card);
    });
  }

  // Step Navigator (Step 1 to 5)
  function showStep(step) {
    currentStep = step;
    document.querySelectorAll('.wizard-step').forEach(el => el.style.display = 'none');

    const stepEl = document.getElementById(`step${step}`);
    if (stepEl) stepEl.style.display = 'block';

    const titles = {
      1: "Exam Goal & Timeline",
      2: "Subjects, Confidence, Priority",
      3: "Study Availability",
      4: "Weak Topics & Challenges",
      5: "Review & Generate Plan"
    };

    document.getElementById('stepIndicator').textContent = `Step ${step} of 5`;
    document.getElementById('stepTitle').textContent = titles[step] || '';
    document.getElementById('wizardProgressBar').style.width = `${(step / 5) * 100}%`;

    const backBtn = document.getElementById('wizardBackBtn');
    const continueBtn = document.getElementById('wizardContinueBtn');
    const generateBtn = document.getElementById('generatePlanBtn');

    if (step === 1) {
      backBtn.style.visibility = 'hidden';
      continueBtn.style.display = 'inline-flex';
      generateBtn.style.display = 'none';
    } else if (step === 5) {
      backBtn.style.visibility = 'visible';
      backBtn.textContent = '← Edit Details';
      continueBtn.style.display = 'none';
      generateBtn.style.display = 'inline-flex';
    } else {
      backBtn.style.visibility = 'visible';
      backBtn.textContent = '← Back';
      continueBtn.style.display = 'inline-flex';
      generateBtn.style.display = 'none';
    }

    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  // Consistent Back button handler
  document.getElementById('wizardBackBtn').addEventListener('click', () => {
    if (currentStep > 1) {
      showStep(currentStep - 1);
    }
  });

  // Consistent Continue button handler (dispatches by currentStep)
  document.getElementById('wizardContinueBtn').addEventListener('click', async () => {
    if (currentStep === 1) {
      await handleStep1Submit();
    } else if (currentStep === 2) {
      await handleStep2Submit();
    } else if (currentStep === 3) {
      await handleStep3Submit();
    } else if (currentStep === 4) {
      await handleStep4Submit();
    }
  });

  // Step 1: Goal & Name Submission
  async function handleStep1Submit() {
    const fullName = document.getElementById('fullName').value.trim();
    const nameError = document.getElementById('nameError');
    if (!fullName) {
      nameError.style.display = 'block';
      return;
    }
    nameError.style.display = 'none';

    const examDate = document.getElementById('examDate').value;
    const dateError = document.getElementById('examDateError');
    if (!examDate) {
      dateError.style.display = 'block';
      return;
    }
    dateError.style.display = 'none';

    showLoading("Saving exam target...");
    
    // Save Step 1 (User profile)
    const res1 = await apiFetch('/api/onboarding/step1', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: userId,
        name: fullName,
        education_level: document.getElementById('educationLevel').value,
        branch: 'CSE',
        year: '3'
      })
    });

    if (res1.ok && res1.data && res1.data.success) {
      userId = res1.data.user_id;
      setActiveUserId(userId);
      document.getElementById('userIdField').value = userId;

      // Save Step 2 (Goal & Date)
      const res2 = await apiFetch('/api/onboarding/step2', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          primary_goal: document.getElementById('primaryGoal').value,
          exam_name: document.getElementById('primaryGoal').value,
          exam_date: examDate,
          preparation_stage: document.getElementById('prepStage').value,
          gate_attempt_year: document.getElementById('gateYear').value,
          target_role: document.getElementById('targetRole').value,
          semester: document.getElementById('semesterSelect').value,
          government_exam_category: document.getElementById('govtCategory').value
        })
      });

      hideLoading();
      if (res2.ok && res2.data && res2.data.success) {
        showStep(2);
      } else {
        alert("Error saving exam goal. Please try again.");
      }
    } else {
      hideLoading();
      alert("Error saving profile: " + (res1.data ? res1.data.error : "Please check your input."));
    }
  }

  // Step 2: Subjects Submission
  async function handleStep2Submit() {
    const subjKeys = Object.keys(selectedSubjects);
    const errEl = document.getElementById('subjectError');
    if (subjKeys.length === 0) {
      errEl.style.display = 'block';
      return;
    }
    errEl.style.display = 'none';

    showLoading("Saving subjects & syllabus...");
    const subjectsArray = subjKeys.map(k => ({
      subject_name: k,
      ...selectedSubjects[k]
    }));

    const fileInput = document.getElementById('notesFile');
    const syllabusText = document.getElementById('syllabusText').value;

    let res;
    if (fileInput.files && fileInput.files.length > 0) {
      const formData = new FormData();
      formData.append('user_id', userId);
      formData.append('subjects', JSON.stringify(subjectsArray));
      formData.append('syllabus_text', syllabusText);
      formData.append('notes_file', fileInput.files[0]);

      res = await apiFetch('/api/onboarding/step3', { method: 'POST', body: formData });
    } else {
      res = await apiFetch('/api/onboarding/step3', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          subjects: subjectsArray,
          syllabus_text: syllabusText
        })
      });
    }

    hideLoading();
    if (res.ok && res.data && res.data.success) {
      showStep(3);
    } else {
      alert("Error saving subjects. Please try again.");
    }
  }

  // Step 3: Availability Submission
  async function handleStep3Submit() {
    const studyDays = parseInt(document.getElementById('studyDays').value || 6, 10);
    const studyHours = parseFloat(document.getElementById('studyHours').value || 3.0);
    const learningStyles = Array.from(document.querySelectorAll('input[name="learning_style"]:checked')).map(cb => cb.value);

    showLoading("Saving availability...");
    const res = await apiFetch('/api/onboarding/step4', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: userId,
        study_days_per_week: studyDays,
        study_hours_per_day: studyHours,
        preferred_time: document.getElementById('preferredTime').value,
        language_preference: document.getElementById('languagePref').value,
        learning_styles: learningStyles,
        resource_preferences: ["Free YouTube playlists", "Free practice platforms"]
      })
    });

    hideLoading();
    if (res.ok && res.data && res.data.success) {
      showStep(4);
    } else {
      alert("Error saving availability. Please try again.");
    }
  }

  // Step 4: Challenges & Review Prep
  async function handleStep4Submit() {
    const challenges = Array.from(document.querySelectorAll('input[name="challenge"]:checked')).map(cb => cb.value);
    const weakTopicsRaw = document.getElementById('weakTopicsInput').value;
    const weakTopics = weakTopicsRaw.split(',').map(s => s.trim()).filter(Boolean);
    const dailyRev = document.querySelector('input[name="daily_revision"]:checked')?.value || 'yes';
    const weeklyMock = document.querySelector('input[name="weekly_mock_test"]:checked')?.value || 'yes';

    showLoading("Preparing review...");
    const res = await apiFetch('/api/onboarding/step5', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: userId,
        challenges: challenges,
        weak_topics: weakTopics,
        avoid_topics: [],
        upcoming_events: '',
        daily_revision: dailyRev,
        weekly_mock_test: weeklyMock
      })
    });

    hideLoading();
    if (res.ok && res.data && res.data.success) {
      await loadReviewScreen();
      showStep(5);
    } else {
      alert("Error saving challenges. Please try again.");
    }
  }

  // Step 5 Review Screen Rendering
  async function loadReviewScreen() {
    showLoading("Loading review summary...");
    const res = await apiFetch(`/api/onboarding/review/${userId}`);
    hideLoading();

    if (res.ok && res.data && res.data.success) {
      const { user, subjects, preferences, challenges } = res.data.data;
      const reviewArea = document.getElementById('reviewContentArea');

      const subjectsHtml = subjects.map(s => `
        <div style="background: #ffffff; padding: 10px 14px; border-radius: 8px; border: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center;">
          <strong style="color: var(--text-main); font-size: 0.92rem;">${s.subject_name}</strong>
          <div style="display: flex; gap: 6px;">
            <span class="badge ${s.confidence_level === 'Weak' ? 'badge-danger' : (s.confidence_level === 'Strong' ? 'badge-success' : 'badge-warning')}">${s.confidence_level}</span>
            <span class="badge badge-primary">${s.priority} Priority</span>
          </div>
        </div>
      `).join('');

      const weakHtml = (challenges.weak_topics && challenges.weak_topics.length > 0)
        ? challenges.weak_topics.map(t => `<span class="badge badge-danger">${t}</span>`).join(' ')
        : '<span style="color: var(--text-muted);">None specified</span>';

      reviewArea.innerHTML = `
        <div class="card" style="padding: 16px; background: var(--bg-primary);">
          <h4 style="color: var(--text-main); margin-bottom: 10px; font-size: 0.95rem;">Goal & Target Timeline</h4>
          <div class="grid grid-2" style="font-size: 0.9rem;">
            <div><strong>Student:</strong> ${user.name}</div>
            <div><strong>Exam Goal:</strong> <span class="badge badge-primary">${user.primary_goal}</span></div>
            <div><strong>Exam Date:</strong> ${user.exam_date}</div>
            <div><strong>Preparation Stage:</strong> ${user.preparation_stage}</div>
          </div>
        </div>

        <div class="card" style="padding: 16px; background: var(--bg-primary);">
          <h4 style="color: var(--text-main); margin-bottom: 10px; font-size: 0.95rem;">Selected Subjects (${subjects.length})</h4>
          <div style="display: flex; flex-direction: column; gap: 6px;">
            ${subjectsHtml}
          </div>
        </div>

        <div class="card" style="padding: 16px; background: var(--bg-primary);">
          <h4 style="color: var(--text-main); margin-bottom: 10px; font-size: 0.95rem;">Schedule & Weak Areas</h4>
          <div class="grid grid-2" style="font-size: 0.9rem; margin-bottom: 8px;">
            <div><strong>Commitment:</strong> ${preferences.study_days_per_week || 6} days/wk, ${preferences.study_hours_per_day || 3} hrs/day</div>
            <div><strong>Preferred Slot:</strong> ${preferences.preferred_time || 'Evening'}</div>
          </div>
          <div><strong>Weak Topics:</strong> ${weakHtml}</div>
        </div>
      `;
    }
  }

  // Step 5 Generate Plan Submission
  document.getElementById('generatePlanBtn').addEventListener('click', async () => {
    showLoading("Generating your personalized 7-day study plan...");
    const res = await apiFetch(`/api/onboarding/generate-plan/${userId}`, { method: 'POST' });
    hideLoading();

    if (res.ok && res.data && res.data.success) {
      setActiveUserId(userId);
      window.location.href = `/dashboard/${userId}`;
    } else {
      alert("Error generating plan: " + (res.data ? res.data.error : "Please try again."));
    }
  });

  // Start at step 1
  showStep(1);
});
