// ==========================================================================
// MentorAI — Core JavaScript Utilities & Global Interactions
// ==========================================================================

function showLoading(message) {
  const overlay = document.getElementById('loadingOverlay');
  const msgEl = document.getElementById('loadingMessage');
  if (overlay) {
    if (msgEl && message) msgEl.textContent = message;
    overlay.classList.add('active');
  }
}

function hideLoading() {
  const overlay = document.getElementById('loadingOverlay');
  if (overlay) {
    overlay.classList.remove('active');
  }
}

// User state management (Strictly no default/demo user on fresh load)
function getActiveUserId() {
  const stored = localStorage.getItem('mentorai_user_id');
  return stored ? parseInt(stored, 10) : null;
}

function setActiveUserId(id) {
  if (id) {
    localStorage.setItem('mentorai_user_id', id);
  } else {
    localStorage.removeItem('mentorai_user_id');
  }
}

function clearActiveUser() {
  localStorage.removeItem('mentorai_user_id');
  localStorage.removeItem('mentorai_user_name');
  localStorage.removeItem('mentorai_user_email');
}

// Global fetch helper with robust JSON parsing & error reporting
async function apiFetch(url, options = {}) {
  try {
    const res = await fetch(url, options);
    const contentType = res.headers.get("content-type");
    if (contentType && contentType.includes("application/json")) {
      const data = await res.json();
      return { ok: res.ok, status: res.status, data };
    } else {
      const text = await res.text();
      return { ok: res.ok, status: res.status, text };
    }
  } catch (err) {
    console.error("MentorAI API Fetch Error:", err);
    return { ok: false, error: err.message || "Network request failed" };
  }
}

// Initialize scroll reveal observer & common UI elements on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  // 1. Scroll reveal animation with IntersectionObserver
  const revealElements = document.querySelectorAll('.reveal');
  if (revealElements.length > 0 && 'IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries, obs) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('active');
          obs.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

    revealElements.forEach(el => observer.observe(el));
  } else {
    revealElements.forEach(el => el.classList.add('active'));
  }

  // 2. Mobile landing navigation toggle
  const mobileToggle = document.getElementById('mobileMenuToggle');
  const navLinks = document.getElementById('landingNavLinks');
  if (mobileToggle && navLinks) {
    mobileToggle.addEventListener('click', () => {
      navLinks.classList.toggle('open');
    });
  }

  // 3. FAQ Accordion interaction
  document.querySelectorAll('.accordion-header').forEach(header => {
    header.addEventListener('click', () => {
      const item = header.parentElement;
      const isOpen = item.classList.contains('open');

      // Close sibling items
      document.querySelectorAll('.accordion-item').forEach(i => i.classList.remove('open'));

      if (!isOpen) {
        item.classList.add('open');
      }
    });
  });

  // 4. Update dynamic links for active user if present
  const uid = getActiveUserId();
  if (uid) {
    document.querySelectorAll('[data-user-href]').forEach(el => {
      const base = el.getAttribute('data-user-href');
      el.href = `${base}/${uid}`;
    });
  }
});
