// ==========================================================================
// MentorAI — Adaptive Quiz Controller (One question per screen)
// ==========================================================================

document.addEventListener('DOMContentLoaded', () => {
  let userId = window.QUIZ_USER_ID || getActiveUserId();
  let currentSubject = window.QUIZ_DEFAULT_SUBJECT || "Data Structures & Algorithms";
  let currentDifficulty = "medium";
  let currentQuestions = [];
  let currentIndex = 0;
  let userAnswers = {}; // { question_id: selected_index }

  const subjectSelect = document.getElementById('quizSubjectSelect');
  if (subjectSelect) {
    subjectSelect.value = currentSubject;
    subjectSelect.addEventListener('change', () => {
      currentSubject = subjectSelect.value;
      loadQuestions();
    });
  }

  document.getElementById('prevQuestionBtn')?.addEventListener('click', () => {
    if (currentIndex > 0) {
      currentIndex--;
      renderCurrentQuestion();
    }
  });

  document.getElementById('nextQuestionBtn')?.addEventListener('click', () => {
    if (currentIndex < currentQuestions.length - 1) {
      currentIndex++;
      renderCurrentQuestion();
    }
  });

  async function loadQuestions() {
    showLoading(`Loading 5 diagnostic questions for ${currentSubject}...`);
    userAnswers = {};
    currentIndex = 0;

    const res = await apiFetch(`/api/quiz/${userId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        subject_name: currentSubject,
        difficulty: currentDifficulty
      })
    });
    hideLoading();

    if (res.ok && res.data && res.data.success) {
      currentQuestions = res.data.questions || [];
      renderCurrentQuestion();
    } else {
      alert("Failed to load questions. Please check connection.");
    }
  }

  function renderCurrentQuestion() {
    const cardContainer = document.getElementById('singleQuestionCard');
    const total = currentQuestions.length;

    if (!total) {
      cardContainer.innerHTML = `<div style="text-align: center; color: var(--text-muted);">No questions available.</div>`;
      return;
    }

    const q = currentQuestions[currentIndex];

    // Progress updates: "Question 2 of 5"
    document.getElementById('progressQuestionText').textContent = `Question ${currentIndex + 1} of ${total}`;
    document.getElementById('quizProgressBar').style.width = `${((currentIndex + 1) / total) * 100}%`;

    const answeredCount = Object.keys(userAnswers).length;
    document.getElementById('answeredCounter').textContent = `${answeredCount} of ${total} Answered`;

    // Navigation buttons
    const prevBtn = document.getElementById('prevQuestionBtn');
    const nextBtn = document.getElementById('nextQuestionBtn');
    const submitBtn = document.getElementById('submitQuizBtn');

    prevBtn.disabled = (currentIndex === 0);

    if (currentIndex === total - 1) {
      nextBtn.style.display = 'none';
      submitBtn.style.display = 'inline-flex';
    } else {
      nextBtn.style.display = 'inline-flex';
      submitBtn.style.display = (answeredCount === total) ? 'inline-flex' : 'none';
    }

    // Build question card with large readable options
    const optionLetters = ['A', 'B', 'C', 'D'];
    const optionsHtml = (q.options || []).map((opt, optIdx) => {
      const selected = userAnswers[q.id] === optIdx;
      return `
        <div class="option-card" data-optidx="${optIdx}" style="cursor: pointer; padding: 14px 18px; border: 1px solid ${selected ? 'var(--primary)' : 'var(--border)'}; background: ${selected ? 'var(--primary-light)' : '#ffffff'}; border-radius: 12px; margin-bottom: 10px; display: flex; align-items: center; gap: 12px; transition: all 0.15s ease;">
          <div style="width: 28px; height: 28px; border-radius: 50%; background: ${selected ? 'var(--primary)' : '#f3f4f6'}; color: ${selected ? '#ffffff' : 'var(--text-main)'}; font-weight: 600; font-size: 0.85rem; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
            ${optionLetters[optIdx]}
          </div>
          <div style="font-size: 0.98rem; color: var(--text-main); flex: 1;">
            ${opt}
          </div>
        </div>
      `;
    }).join('');

    cardContainer.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
        <div style="display: flex; align-items: center; gap: 8px;">
          <span class="badge badge-primary">Question ${currentIndex + 1}</span>
          <span class="badge badge-neutral">${q.topic || currentSubject}</span>
        </div>
        <span style="font-size: 0.82rem; color: var(--text-muted);">${q.concept || ''}</span>
      </div>

      <h3 style="font-size: 1.18rem; font-weight: 600; color: var(--text-main); margin-bottom: 20px; line-height: 1.45;">
        ${q.question}
      </h3>

      <div class="options-wrapper">
        ${optionsHtml}
      </div>
    `;

    // Click handler for option cards
    cardContainer.querySelectorAll('.option-card').forEach(card => {
      card.addEventListener('click', () => {
        const selectedIdx = parseInt(card.dataset.optidx, 10);
        userAnswers[q.id] = selectedIdx;
        renderCurrentQuestion();
      });
    });
  }

  // Quiz Submit
  document.getElementById('submitQuizBtn')?.addEventListener('click', async () => {
    const total = currentQuestions.length;
    const answeredCount = Object.keys(userAnswers).length;

    if (answeredCount < total) {
      if (!confirm(`You answered ${answeredCount} of ${total} questions. Submit anyway?`)) {
        return;
      }
    }

    const payloadAnswers = currentQuestions.map(q => ({
      question_id: q.id,
      selected_index: userAnswers[q.id] !== undefined ? userAnswers[q.id] : null
    }));

    showLoading("Evaluating quiz and recording mastery...");
    const res = await apiFetch(`/api/quiz/${userId}/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ answers: payloadAnswers })
    });
    hideLoading();

    if (res.ok && res.data && res.data.success) {
      currentDifficulty = res.data.next_difficulty || currentDifficulty;
      displayResults(res.data);
    } else {
      alert("Error submitting quiz. Please try again.");
    }
  });

  function displayResults(data) {
    document.getElementById('quizContainer').style.display = 'none';
    const resultsContainer = document.getElementById('resultsContainer');
    resultsContainer.style.display = 'block';

    document.getElementById('scoreDisplay').textContent = `${data.score} / ${data.total}`;
    document.getElementById('accuracyDisplay').textContent = `${data.accuracy}%`;
    document.getElementById('nextActionText').textContent = data.next_action || 'Continue targeted practice on your priority topics.';
    document.getElementById('resultsDashboardLink').href = `/dashboard/${userId}`;

    // Render detailed review (Score, Review, Explanation, Misconception)
    const reviewList = document.getElementById('detailedReviewList');
    reviewList.innerHTML = '';

    const optionLetters = ['A', 'B', 'C', 'D'];

    (data.results || []).forEach((r, idx) => {
      const card = document.createElement('div');
      card.className = 'card';
      card.style.borderLeft = r.is_correct ? '4px solid var(--success)' : '4px solid var(--danger)';

      const userText = (r.selected_index !== null && r.options && r.options[r.selected_index])
        ? `${optionLetters[r.selected_index]}. ${r.options[r.selected_index]}`
        : 'Unanswered';

      const correctText = (r.options && r.options[r.correct_index])
        ? `${optionLetters[r.correct_index]}. ${r.options[r.correct_index]}`
        : '';

      card.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
          <div style="display: flex; align-items: center; gap: 8px;">
            <span class="badge ${r.is_correct ? 'badge-success' : 'badge-danger'}">
              ${r.is_correct ? '✓ Correct' : '✗ Incorrect'}
            </span>
            <span class="badge badge-neutral">${r.topic}</span>
          </div>
          <span style="font-size: 0.8rem; color: var(--text-muted);">${r.concept}</span>
        </div>

        <div style="font-size: 1rem; font-weight: 600; color: var(--text-main); margin-bottom: 12px;">
          ${idx + 1}. ${r.question}
        </div>

        <div style="background: var(--bg-primary); border: 1px solid var(--border); padding: 12px 14px; border-radius: 8px; margin-bottom: 12px; font-size: 0.9rem;">
          <div style="margin-bottom: 4px;">
            <strong>Your Answer:</strong>
            <span style="color: ${r.is_correct ? 'var(--success)' : 'var(--danger)'}; font-weight: 600;"> ${userText}</span>
          </div>
          ${!r.is_correct ? `
            <div>
              <strong>Correct Answer:</strong>
              <span style="color: var(--success); font-weight: 600;"> ${correctText}</span>
            </div>
          ` : ''}
        </div>

        <!-- Explanation -->
        <div style="background: var(--success-light); border-left: 2px solid var(--success); padding: 10px 12px; border-radius: 6px; font-size: 0.88rem; color: #166534; margin-bottom: 6px;">
          <strong>Explanation:</strong> ${r.explanation}
        </div>

        <!-- Misconception -->
        ${r.misconception ? `
          <div style="background: var(--danger-light); border-left: 2px solid var(--danger); padding: 10px 12px; border-radius: 6px; font-size: 0.88rem; color: #991b1b;">
            <strong>Misconception:</strong> ${r.misconception}
          </div>
        ` : ''}
      `;

      reviewList.appendChild(card);
    });

    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  // Start initial questions
  loadQuestions();
});
