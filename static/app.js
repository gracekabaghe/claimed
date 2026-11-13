/**
 * Claimed — Readiness Checker
 * Scans a business URL and returns eligibility + verification path.
 */

const ICONS = {
  shopify: '🛒',
  domain: '🌐',
  lock: '🔒',
  info: 'ℹ️',
  location: '📍'
};

const form = document.getElementById('scanForm');
const input = document.getElementById('urlInput');
const resultEl = document.getElementById('result');
const loadingEl = document.getElementById('loading');
const errorEl = document.getElementById('error');
const scanBtn = document.getElementById('scanBtn');

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
    scanBtn.innerHTML = 'Scan my business <svg width="16" height="16" viewBox="0 0 16 16" fill="none" class="button-arrow"><path d="M3 8H13M10 5L13 8L10 11" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';
  }
});

function renderResult(data) {
  // Verdict
  const verdictEl = document.getElementById('resultVerdict');
  const verdictClass = `result-verdict-${data.eligibility}`;
  const verdictEmoji = data.eligibility === 'ready' ? '✅' : data.eligibility === 'possible' ? '🔶' : 'ℹ️';
  verdictEl.className = verdictClass;
  verdictEl.innerHTML = `${verdictEmoji} ${data.verdict}`;
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