/**
 * CipherVault Pro — Main JavaScript
 * Handles: sidebar toggle, copy buttons, dropzone, flash auto-dismiss,
 *          algorithm info tooltips, and general UI utilities.
 */

'use strict';

// ── Sidebar toggle (mobile) ────────────────────────────────────────────────
const sidebar = document.getElementById('cv-sidebar');
const mToggle = document.getElementById('mobile-toggle');
const overlay = document.getElementById('sidebar-overlay');

if (mToggle && sidebar) {
    mToggle.addEventListener('click', () => {
        sidebar.classList.toggle('open');
        if (overlay) overlay.classList.toggle('active');
    });
}
if (overlay) {
    overlay.addEventListener('click', () => {
        sidebar.classList.remove('open');
        overlay.classList.remove('active');
    });
}

// ── Active nav item ────────────────────────────────────────────────────────
document.querySelectorAll('.cv-nav-item').forEach(link => {
    if (link.href && link.href !== window.location.origin + '/') {
        if (window.location.pathname.startsWith(new URL(link.href).pathname)) {
            link.classList.add('active');
        }
    }
});

// ── Copy to clipboard ─────────────────────────────────────────────────────
document.querySelectorAll('[data-copy]').forEach(btn => {
    btn.addEventListener('click', async () => {
        const target = document.getElementById(btn.dataset.copy);
        if (!target) return;
        const text = target.value || target.textContent;
        try {
            await navigator.clipboard.writeText(text.trim());
            const original = btn.innerHTML;
            btn.innerHTML = '✓ Copied';
            btn.style.color = 'var(--success)';
            setTimeout(() => {
                btn.innerHTML = original;
                btn.style.color = '';
            }, 1800);
        } catch {
            showToast('Copy failed — please select and copy manually.', 'danger');
        }
    });
});

// ── Toast notifications ────────────────────────────────────────────────────
function showToast(message, type = 'info', duration = 3500) {
    let container = document.querySelector('.cv-toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'cv-toast-container';
        document.body.appendChild(container);
    }

    const typeMap = {
        success: { bg: 'rgba(34,197,94,.12)', border: 'var(--success)', icon: '✓' },
        danger: { bg: 'rgba(244,63,94,.12)', border: 'var(--danger)', icon: '✕' },
        warning: { bg: 'rgba(245,158,11,.12)', border: 'var(--warning)', icon: '⚠' },
        info: { bg: 'rgba(34,211,238,.12)', border: 'var(--cyan)', icon: 'ℹ' },
    };
    const style = typeMap[type] || typeMap.info;

    const toast = document.createElement('div');
    toast.style.cssText = `
    background:${style.bg};border:1px solid ${style.border};border-radius:8px;
    padding:.65rem 1rem;font-size:.85rem;color:var(--text-primary);
    display:flex;gap:.5rem;align-items:center;
    animation:fadeIn .25s ease forwards;max-width:320px;
    box-shadow:var(--shadow-md);
  `;
    toast.innerHTML = `<span>${style.icon}</span><span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => { toast.style.opacity = '0'; setTimeout(() => toast.remove(), 300); }, duration);
}

window.showToast = showToast; // expose globally

// Auto-dismiss flash messages
document.querySelectorAll('.cv-alert[data-auto-dismiss]').forEach(alert => {
    setTimeout(() => {
        alert.style.transition = 'opacity .4s';
        alert.style.opacity = '0';
        setTimeout(() => alert.remove(), 400);
    }, 4000);
});

// ── File dropzone ──────────────────────────────────────────────────────────
document.querySelectorAll('.cv-dropzone').forEach(zone => {
    const input = zone.querySelector('input[type="file"]');
    if (!input) return;

    zone.addEventListener('click', () => input.click());

    zone.addEventListener('dragover', e => {
        e.preventDefault();
        zone.classList.add('drag-over');
    });
    zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));
    zone.addEventListener('drop', e => {
        e.preventDefault();
        zone.classList.remove('drag-over');
        if (e.dataTransfer.files.length) {
            const dt = new DataTransfer();
            dt.items.add(e.dataTransfer.files[0]);
            input.files = dt.files;
            updateDropzoneLabel(zone, e.dataTransfer.files[0].name);
        }
    });

    input.addEventListener('change', () => {
        if (input.files.length) updateDropzoneLabel(zone, input.files[0].name);
    });

    function updateDropzoneLabel(zone, name) {
        const lbl = zone.querySelector('.cv-dropzone-text');
        if (lbl) lbl.textContent = `✓ ${name}`;
    }
});

// ── Algorithm info ─────────────────────────────────────────────────────────
const algoInfo = {
    'AES-256': 'AES-256 in EAX mode — authenticated encryption. Fastest and most widely trusted. Recommended.',
    'Blowfish': 'Blowfish-448 in EAX mode — legacy Feistel cipher. Good for educational comparison.',
    '3DES': 'Triple DES with HMAC-SHA256 — applies DES three times. Legacy; included for compatibility study.',
};

document.querySelectorAll('select[id*="algorithm"], select[name="algorithm"]').forEach(sel => {
    const hint = sel.parentElement.querySelector('.algo-hint');
    if (!hint) return;

    const update = () => { hint.textContent = algoInfo[sel.value] || ''; };
    sel.addEventListener('change', update);
    update();
});

// ── Confirm delete dialogs ─────────────────────────────────────────────────
document.querySelectorAll('[data-confirm]').forEach(el => {
    el.addEventListener('click', e => {
        if (!confirm(el.dataset.confirm || 'Are you sure?')) e.preventDefault();
    });
});

// ── Password visibility toggle ─────────────────────────────────────────────
document.querySelectorAll('[data-toggle-pw]').forEach(btn => {
    const input = document.getElementById(btn.dataset.togglePw);
    if (!input) return;
    btn.addEventListener('click', () => {
        input.type = input.type === 'password' ? 'text' : 'password';
        btn.textContent = input.type === 'password' ? '👁' : '🙈';
    });
});

// ── Passive CSRF token helper for fetch ───────────────────────────────────
function getCsrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.content : '';
}
window.getCsrfToken = getCsrfToken;

// ── Smooth page transitions ───────────────────────────────────────────────
document.querySelectorAll('.cv-nav-item, .btn-cv').forEach(el => {
    el.addEventListener('click', () => {
        // tiny ripple effect
        const ripple = document.createElement('span');
        ripple.style.cssText = `position:absolute;width:4px;height:4px;background:rgba(255,255,255,.3);
      border-radius:50%;pointer-events:none;animation:rippleOut .4s ease forwards;`;
        el.style.position = 'relative';
        el.style.overflow = 'hidden';
        el.appendChild(ripple);
        setTimeout(() => ripple.remove(), 400);
    });
});