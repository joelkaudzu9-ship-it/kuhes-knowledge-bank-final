// core/static/core/js/toasts.js
// Modern Toast Notification System with Glass Morphism

class ModernToast {
    constructor() {
        this.toasts = [];
        this.container = null;
        this.init();
    }

    init() {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.style.cssText = `
                position: fixed;
                top: 80px;
                right: 20px;
                z-index: 9999;
                display: flex;
                flex-direction: column;
                gap: 12px;
                pointer-events: none;
                max-width: 380px;
                width: calc(100% - 40px);
            `;
            document.body.appendChild(container);
        }
        this.container = container;
    }

    show(message, type = 'info', duration = 4000) {
        const id = 'toast-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);

        const toast = document.createElement('div');
        toast.id = id;

        // Toast configurations
        const configs = {
            success: {
                icon: 'fa-check-circle',
                gradient: 'linear-gradient(135deg, #10b981, #059669)',
                bgGradient: 'linear-gradient(135deg, rgba(16, 185, 129, 0.12), rgba(16, 185, 129, 0.05))'
            },
            error: {
                icon: 'fa-exclamation-circle',
                gradient: 'linear-gradient(135deg, #ef4444, #dc2626)',
                bgGradient: 'linear-gradient(135deg, rgba(239, 68, 68, 0.12), rgba(239, 68, 68, 0.05))'
            },
            warning: {
                icon: 'fa-exclamation-triangle',
                gradient: 'linear-gradient(135deg, #f59e0b, #d97706)',
                bgGradient: 'linear-gradient(135deg, rgba(245, 158, 11, 0.12), rgba(245, 158, 11, 0.05))'
            },
            info: {
                icon: 'fa-info-circle',
                gradient: 'linear-gradient(135deg, #3b82f6, #2563eb)',
                bgGradient: 'linear-gradient(135deg, rgba(59, 130, 246, 0.12), rgba(59, 130, 246, 0.05))'
            }
        };

        const config = configs[type] || configs.info;

        toast.style.cssText = `
            background: ${config.bgGradient};
            backdrop-filter: blur(12px);
            border-radius: 20px;
            padding: 16px 20px;
            display: flex;
            align-items: center;
            gap: 14px;
            transform: translateX(120%);
            transition: transform 0.4s cubic-bezier(0.34, 1.2, 0.64, 1);
            pointer-events: auto;
            border: 1px solid rgba(255, 255, 255, 0.3);
            box-shadow: 0 12px 32px rgba(0, 0, 0, 0.12);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        `;

        toast.innerHTML = `
            <div style="width: 36px; height: 36px; background: ${config.gradient}; border-radius: 12px; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                <i class="fas ${config.icon}" style="color: white; font-size: 1rem;"></i>
            </div>
            <div style="flex: 1; color: #1e293b; font-weight: 500; font-size: 0.875rem; line-height: 1.5;">
                ${message}
            </div>
            <button style="
                background: none;
                border: none;
                color: #94a3b8;
                cursor: pointer;
                font-size: 1.25rem;
                padding: 0;
                width: 24px;
                height: 24px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 8px;
                transition: all 0.2s ease;
                flex-shrink: 0;
            " class="toast-close-btn">
                <i class="fas fa-times"></i>
            </button>
        `;

        this.container.appendChild(toast);

        // Add close button handler
        const closeBtn = toast.querySelector('.toast-close-btn');
        closeBtn.addEventListener('click', () => this.hide(id));

        // Animate in
        setTimeout(() => {
            toast.style.transform = 'translateX(0)';
        }, 10);

        // Store toast info
        const timeout = setTimeout(() => this.hide(id), duration);
        this.toasts.push({ id, timeout });

        return id;
    }

    hide(id) {
        const toast = document.getElementById(id);
        if (!toast) return;

        toast.style.transform = 'translateX(120%)';

        setTimeout(() => {
            if (toast.parentNode) toast.remove();
        }, 300);

        const index = this.toasts.findIndex(t => t.id === id);
        if (index !== -1) {
            clearTimeout(this.toasts[index].timeout);
            this.toasts.splice(index, 1);
        }
    }

    success(msg, duration = 4000) { return this.show(msg, 'success', duration); }
    error(msg, duration = 5000) { return this.show(msg, 'error', duration); }
    warning(msg, duration = 4500) { return this.show(msg, 'warning', duration); }
    info(msg, duration = 4000) { return this.show(msg, 'info', duration); }
}

// Initialize global toast
window.toast = new ModernToast();

// Convenience methods
window.showSuccess = (msg) => window.toast?.success(msg);
window.showError = (msg) => window.toast?.error(msg);
window.showWarning = (msg) => window.toast?.warning(msg);
window.showInfo = (msg) => window.toast?.info(msg);

console.log('✨ Modern Toast System Ready');