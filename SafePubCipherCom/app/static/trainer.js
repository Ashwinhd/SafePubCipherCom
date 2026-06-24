/**
 * CipherVault Pro — Typing Trainer
 * Real-time WPM, accuracy, and character-level feedback.
 */

'use strict';

(function () {
    const display = document.getElementById('typing-display');
    const hiddenInput = document.getElementById('typing-input');
    const wpmEl = document.getElementById('stat-wpm');
    const accEl = document.getElementById('stat-acc');
    const timeEl = document.getElementById('stat-time');
    const progressEl = document.getElementById('typing-progress');
    const startBtn = document.getElementById('btn-start');
    const resultPanel = document.getElementById('result-panel');
    const diffSel = document.getElementById('difficulty-sel');

    if (!display) return;  // page guard

    const originalText = display.dataset.text || '';
    let chars = [];
    let started = false;
    let startTime = null;
    let timerInterval = null;
    let currentIndex = 0;
    let errors = 0;
    let totalTyped = 0;
    let finished = false;

    // Build character spans
    function renderText(text) {
        display.innerHTML = '';
        chars = text.split('').map((ch, i) => {
            const span = document.createElement('span');
            span.textContent = ch;
            span.className = i === 0 ? 'char-current' : 'char-pending';
            display.appendChild(span);
            return span;
        });
    }

    renderText(originalText);

    // Focus hidden input on display click
    display.addEventListener('click', () => {
        hiddenInput.focus();
        display.classList.add('focused');
    });

    hiddenInput.addEventListener('keydown', e => {
        if (finished) return;

        // Start timer on first keypress
        if (!started) {
            started = true;
            startTime = Date.now();
            timerInterval = setInterval(updateTimer, 200);
        }

        if (e.key === 'Backspace') {
            e.preventDefault();
            if (currentIndex > 0) {
                currentIndex--;
                chars[currentIndex].className = 'char-current';
                if (currentIndex + 1 < chars.length) {
                    chars[currentIndex + 1].className = 'char-pending';
                }
            }
            return;
        }

        if (e.key.length !== 1) return;

        e.preventDefault();

        const expected = originalText[currentIndex];
        const typed = e.key;
        totalTyped++;

        if (typed === expected) {
            chars[currentIndex].className = 'char-correct';
        } else {
            chars[currentIndex].className = 'char-wrong';
            errors++;
        }

        currentIndex++;

        if (currentIndex < chars.length) {
            chars[currentIndex].className = 'char-current';
            // Auto-scroll to keep current char visible
            chars[currentIndex].scrollIntoView({ block: 'nearest', behavior: 'smooth' });
        }

        // Update progress bar
        if (progressEl) {
            progressEl.style.width = ((currentIndex / chars.length) * 100).toFixed(1) + '%';
        }

        updateStats();

        if (currentIndex >= chars.length) finish();
    });

    function updateTimer() {
        if (!started || finished) return;
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        if (timeEl) timeEl.textContent = elapsed + 's';
    }

    function updateStats() {
        const elapsed = (Date.now() - startTime) / 60000;  // minutes
        const words = currentIndex / 5;
        const wpm = elapsed > 0 ? Math.round(words / elapsed) : 0;
        const acc = totalTyped > 0 ? Math.round(((totalTyped - errors) / totalTyped) * 100) : 100;

        if (wpmEl) wpmEl.textContent = wpm;
        if (accEl) accEl.textContent = acc + '%';
    }

    function finish() {
        finished = true;
        clearInterval(timerInterval);

        const elapsed = Math.round((Date.now() - startTime) / 1000);
        const words = originalText.trim().split(/\s+/).length;
        const wpm = elapsed > 0 ? Math.round((words / elapsed) * 60) : 0;
        const acc = totalTyped > 0 ? Math.round(((totalTyped - errors) / totalTyped) * 100) : 100;

        // Fill result form
        const fWpm = document.getElementById('f-wpm');
        const fAcc = document.getElementById('f-accuracy');
        const fDur = document.getElementById('f-duration');
        const fText = document.getElementById('f-text');
        const fDiff = document.getElementById('f-difficulty');

        if (fWpm) fWpm.value = wpm;
        if (fAcc) fAcc.value = acc;
        if (fDur) fDur.value = elapsed;
        if (fText) fText.value = originalText.slice(0, 256);
        if (fDiff) fDiff.value = diffSel ? diffSel.value : 'medium';

        // Show result panel
        if (resultPanel) {
            document.getElementById('res-wpm').textContent = wpm;
            document.getElementById('res-acc').textContent = acc + '%';
            document.getElementById('res-time').textContent = elapsed + 's';
            resultPanel.classList.remove('d-none');
            resultPanel.scrollIntoView({ behavior: 'smooth' });
        }

        // Auto-submit score via AJAX
        const form = document.getElementById('score-form');
        if (form) {
            const data = new FormData(form);
            fetch(form.action, {
                method: 'POST',
                headers: { 'X-CSRFToken': getCsrfToken() },
                body: data,
            })
                .then(r => r.json())
                .then(json => {
                    if (json.status === 'ok') showToast('Score saved! ' + json.wpm + ' WPM', 'success');
                })
                .catch(() => { });
        }
    }

    // Restart
    if (startBtn) {
        startBtn.addEventListener('click', () => {
            started = finished = false;
            startTime = null;
            currentIndex = errors = totalTyped = 0;
            clearInterval(timerInterval);
            if (wpmEl) wpmEl.textContent = '0';
            if (accEl) accEl.textContent = '100%';
            if (timeEl) timeEl.textContent = '0s';
            if (progressEl) progressEl.style.width = '0%';
            if (resultPanel) resultPanel.classList.add('d-none');
            renderText(originalText);
            hiddenInput.value = '';
            hiddenInput.focus();
        });
    }
})();