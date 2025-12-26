/* 
   Modern Theme Interactions
*/

// Fix URLs for multi-bot routing
function fixUrl(url) {
    if (!url || typeof url !== 'string' || url.startsWith('http') || url.startsWith('/static/')) return url;
    const pathParts = window.location.pathname.split('/').filter(p => p);
    // Only treat the first part as a bot prefix if it is numeric (Bot ID)
    if (pathParts.length > 0) {
        const potentialBotId = pathParts[0];
        if (/^\d+$/.test(potentialBotId)) {
            if (!url.startsWith(`/${potentialBotId}`)) {
                return `/${potentialBotId}${url.startsWith('/') ? url : '/' + url}`;
            }
        }
    }
    return url;
}

// Toast Notification System
function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');

    // Styles for the toast
    toast.style.background = 'rgba(30, 41, 59, 0.9)';
    toast.style.backdropFilter = 'blur(10px)';
    toast.style.border = '1px solid rgba(255, 255, 255, 0.1)';
    toast.style.color = '#fff';
    toast.style.padding = '12px 20px';
    toast.style.borderRadius = '12px';
    toast.style.display = 'flex';
    toast.style.alignItems = 'center';
    toast.style.gap = '10px';
    toast.style.boxShadow = '0 10px 30px rgba(0,0,0,0.5)';
    toast.style.transform = 'translateY(-20px)';
    toast.style.opacity = '0';
    toast.style.transition = 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
    toast.style.fontFamily = 'Vazirmatn, sans-serif';
    toast.style.fontSize = '0.9rem';

    // Icon based on type
    let icon = '';
    if (type === 'success') {
        icon = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>';
        toast.style.borderLeft = '4px solid #10b981';
    } else {
        icon = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>';
        toast.style.borderLeft = '4px solid #ef4444';
    }

    toast.innerHTML = `${icon}<span>${message}</span>`;
    container.appendChild(toast);

    // Animate in
    requestAnimationFrame(() => {
        toast.style.transform = 'translateY(0)';
        toast.style.opacity = '1';
    });

    // Remove after 3 seconds
    setTimeout(() => {
        toast.style.transform = 'translateY(-20px)';
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Copy Link Function
async function copyLink(text) {
    if (!text) return;

    try {
        await navigator.clipboard.writeText(text);
        showToast('لینک با موفقیت کپی شد', 'success');
    } catch (err) {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        try {
            document.execCommand('copy');
            showToast('لینک با موفقیت کپی شد', 'success');
        } catch (err) {
            showToast('خطا در کپی لینک', 'error');
        }
        document.body.removeChild(textArea);
    }
}

// Add ripple effect to buttons
document.addEventListener('click', function (e) {
    if (e.target.closest('.btn') || e.target.closest('.nav-item') || e.target.closest('.bottom-nav-item') || e.target.closest('.fab')) {
        const button = e.target.closest('.btn') || e.target.closest('.nav-item') || e.target.closest('.bottom-nav-item') || e.target.closest('.fab');

        // Create ripple element
        const ripple = document.createElement('span');
        const rect = button.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = e.clientX - rect.left - size / 2;
        const y = e.clientY - rect.top - size / 2;

        ripple.style.width = ripple.style.height = `${size}px`;
        ripple.style.left = `${x}px`;
        ripple.style.top = `${y}px`;
        ripple.style.position = 'absolute';
        ripple.style.borderRadius = '50%';
        ripple.style.transform = 'scale(0)';
        ripple.style.animation = 'ripple 0.6s linear';
        ripple.style.background = 'rgba(255, 255, 255, 0.1)';
        ripple.style.pointerEvents = 'none';

        // Ensure button has relative positioning
        const computedStyle = window.getComputedStyle(button);
        if (computedStyle.position === 'static') {
            button.style.position = 'relative';
            button.style.overflow = 'hidden';
        }

        button.appendChild(ripple);

        setTimeout(() => {
            ripple.remove();
        }, 600);
    }
});

// Add keyframes for ripple
const style = document.createElement('style');
style.innerHTML = `
    @keyframes ripple {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
