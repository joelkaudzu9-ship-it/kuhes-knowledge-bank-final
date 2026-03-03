// Floating Toast Notifications - No Layout Shift!
class FloatingToast {
    constructor() {
        this.toasts = [];
        this.container = null;
        this.init();
    }

    init() {
        console.log('Initializing FloatingToast...');

        // Check if container already exists
        let container = document.getElementById('toast-container');
        if (!container) {
            // Create container for toasts
            container = document.createElement('div');
            container.id = 'toast-container';
            container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
                display: flex;
                flex-direction: column;
                gap: 10px;
                pointer-events: none;
                max-width: 400px;
                width: calc(100% - 40px);
            `;
            document.body.appendChild(container);
        }

        this.container = container;
        console.log('Toast container initialized');
    }

    show(message, type = 'success', duration = 3000) {
        console.log(`Showing toast: ${message} (${type})`);

        const id = 'toast-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);

        // Create toast element
        const toast = document.createElement('div');
        toast.id = id;

        // Base styles
        let styles = `
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.1), 0 5px 10px rgba(0,51,160,0.2);
            padding: 16px 20px;
            min-width: 280px;
            max-width: 100%;
            display: flex;
            align-items: center;
            gap: 12px;
            transform: translateX(120%);
            transition: transform 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55);
            pointer-events: auto;
            backdrop-filter: blur(10px);
            background: rgba(255, 255, 255, 0.98);
            border: 1px solid rgba(0,51,160,0.1);
            margin: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        `;

        // Set border color and icon based on type
        let icon, borderColor, bgColor;
        switch(type) {
            case 'success':
                borderColor = '#2E7D32';
                icon = '✓';
                bgColor = 'linear-gradient(135deg, #E8F5E9, #C8E6C9)';
                break;
            case 'error':
                borderColor = '#D32F2F';
                icon = '✕';
                bgColor = 'linear-gradient(135deg, #FFEBEE, #FFCDD2)';
                break;
            case 'warning':
                borderColor = '#ED6C02';
                icon = '⚠';
                bgColor = 'linear-gradient(135deg, #FFF3E0, #FFE0B2)';
                break;
            case 'info':
                borderColor = '#0288D1';
                icon = 'ℹ';
                bgColor = 'linear-gradient(135deg, #E1F5FE, #B3E5FC)';
                break;
            default:
                borderColor = '#0033A0';
                icon = '✓';
                bgColor = 'linear-gradient(135deg, #E3F2FD, #BBDEFB)';
        }

        styles += `border-left: 6px solid ${borderColor}; background: ${bgColor};`;
        toast.style.cssText = styles;

        // Add icon
        const iconSpan = document.createElement('span');
        iconSpan.style.cssText = `
            width: 30px;
            height: 30px;
            background: ${borderColor};
            color: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 18px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            flex-shrink: 0;
        `;
        iconSpan.textContent = icon;

        // Add message
        const messageSpan = document.createElement('span');
        messageSpan.style.cssText = `
            flex: 1;
            color: #1e293b;
            font-weight: 500;
            font-size: 14px;
            line-height: 1.5;
            word-break: break-word;
        `;
        messageSpan.textContent = message;

        // Add close button
        const closeBtn = document.createElement('span');
        closeBtn.style.cssText = `
            cursor: pointer;
            color: #64748b;
            font-weight: bold;
            font-size: 20px;
            padding: 0 5px;
            transition: color 0.2s;
            opacity: 0.5;
            flex-shrink: 0;
        `;
        closeBtn.innerHTML = '&times;';
        closeBtn.onmouseover = () => closeBtn.style.opacity = '1';
        closeBtn.onmouseout = () => closeBtn.style.opacity = '0.5';
        closeBtn.onclick = (e) => {
            e.stopPropagation();
            this.hide(id);
        };

        toast.appendChild(iconSpan);
        toast.appendChild(messageSpan);
        toast.appendChild(closeBtn);

        // Add to container
        this.container.appendChild(toast);

        // Store toast
        this.toasts.push({ id, timeout: null });

        // Trigger animation
        setTimeout(() => {
            toast.style.transform = 'translateX(0)';
        }, 10);

        // Auto hide after duration
        const timeout = setTimeout(() => {
            this.hide(id);
        }, duration);

        // Update timeout in store
        const toastIndex = this.toasts.findIndex(t => t.id === id);
        if (toastIndex !== -1) {
            this.toasts[toastIndex].timeout = timeout;
        }

        return id;
    }

    hide(id) {
        const toast = document.getElementById(id);
        if (!toast) return;

        // Animate out
        toast.style.transform = 'translateX(120%)';

        // Remove after animation
        setTimeout(() => {
            if (toast && toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);

        // Clear timeout
        const toastIndex = this.toasts.findIndex(t => t.id === id);
        if (toastIndex !== -1) {
            if (this.toasts[toastIndex].timeout) {
                clearTimeout(this.toasts[toastIndex].timeout);
            }
            this.toasts.splice(toastIndex, 1);
        }
    }

    success(message, duration = 4000) {
        return this.show(message, 'success', duration);
    }

    error(message, duration = 5000) {
        return this.show(message, 'error', duration);
    }

    warning(message, duration = 4500) {
        return this.show(message, 'warning', duration);
    }

    info(message, duration = 4000) {
        return this.show(message, 'info', duration);
    }
}

// Initialize global toast instance
console.log('Creating global toast instance...');
window.toast = new FloatingToast();

// Add convenience methods
window.showSuccess = (msg) => window.toast?.success(msg);
window.showError = (msg) => window.toast?.error(msg);
window.showWarning = (msg) => window.toast?.warning(msg);
window.showInfo = (msg) => window.toast?.info(msg);

console.log('Toast system ready');