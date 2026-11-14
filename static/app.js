/**
 * Claimed — Readiness Checker
 * Scans a business URL and returns eligibility + verification path.
 */

const svg = (inner) => `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${inner}</svg>`;

const ICONS = {
  shopify: svg('<path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><path d="M3 6h18"/><path d="M16 10a4 4 0 0 1-8 0"/>'),
  domain: svg('<circle cx="12" cy="12" r="10"/><path d="M2 12h20"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>'),
  lock: svg('<rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>'),
  info: svg('<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>'),
  location: svg('<path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/>')
};

const form = document.getElementById('scanForm');
const input = document.getElementById('urlInput');
const resultEl = document.getElementById('result');
const loadingEl = document.getElementById('loading');
const errorEl = document.getElementById('error');
const scanBtn = document.getElementById('scanBtn');
const originalBtnHTML = scanBtn.innerHTML;

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const url = input.value.trim();
  if (!url) return;

  // Reset UI
  resultEl.style.display = 'none';
  errorEl.style.display = 'none';
  loadingEl.style.display = 'block';
  scanBtn.disabled = true;
  scanBtn.textContent = 'Scanning…';

  try {
    const res = await fetch('/api/scan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || 'Something went wrong');
    }

    const data = await res.json();
    renderResult(data);
  } catch (err) {
    errorEl.textContent = err.message;
    errorEl.style.display = 'block';
  } finally {
    loadingEl.style.display = 'none';
    scanBtn.disabled = false;
    scanBtn.innerHTML = originalBtnHTML;
  }
});

function renderResult(data) {
  // Verdict
  const verdictEl = document.getElementById('resultVerdict');
  const verdictClass = `result-verdict-${data.eligibility}`;
  const verdictIcon = data.eligibility === 'ready'
    ? svg('<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>')
    : data.eligibility === 'possible'
      ? svg('<path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><path d="M12 9v4"/><path d="M12 17h.01"/>')
      : svg('<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>');
  verdictEl.className = verdictClass;
  verdictEl.innerHTML = `${verdictIcon} ${data.verdict}`;
  verdictEl.insertAdjacentHTML('afterend', `<p class="result-detail">${data.verdict_detail}</p>`);

  // Signals
  const signalsEl = document.getElementById('resultSignals');
  signalsEl.innerHTML = data.signals.map(s => `
    <div class="signal signal-${s.type}">
      <span class="signal-icon">${ICONS[s.icon] || '•'}</span>
      <span>${s.text}</span>
    </div>
  `).join('');

  // Next step
  const nextEl = document.getElementById('resultNext');
  nextEl.innerHTML = `
    <div class="result-next-label">Recommended verification path</div>
    <div class="result-next-method">${data.verification_label}</div>
  `;

  // Add wizard CTA
  const wizardLink = document.createElement('a');
  wizardLink.href = `/wizard?method=${data.verification_method}&domain=${data.domain}`;
  wizardLink.className = 'button button-primary';
  wizardLink.style.cssText = 'margin-top: 16px;';
  wizardLink.textContent = 'Start guided wizard →';
  nextEl.appendChild(wizardLink);

  resultEl.style.display = 'block';
  resultEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}