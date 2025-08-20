/**
 * نائبك دوت كوم - ملف JavaScript الرئيسي
 * Main JavaScript file for Naebak.com
 */

// ===== GLOBAL VARIABLES =====
let isRTL = document.documentElement.dir === 'rtl';

// ===== DOM READY =====
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// ===== INITIALIZE APPLICATION =====
function initializeApp() {
    initializeAnimations();
    initializeNavigation();
    initializeForms();
    initializeTooltips();
    initializeModals();
    initializeScrollEffects();
    initializeSearchFunctionality();
}

// ===== ANIMATIONS =====
function initializeAnimations() {
    // Intersection Observer for scroll animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-fade-in-up');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // Observe elements for animation
    document.querySelectorAll('.card, .governorate-card, .candidate-card, .news-card').forEach(el => {
        observer.observe(el);
    });
}

// ===== NAVIGATION =====
function initializeNavigation() {
    const navbar = document.querySelector('.navbar');
    const navLinks = document.querySelectorAll('.nav-link');
    
    // Active link highlighting
    const currentPath = window.location.pathname;
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
    
    // Navbar scroll effect
    window.addEventListener('scroll', () => {
        if (window.scrollY > 100) {
            navbar.classList.add('navbar-scrolled');
        } else {
            navbar.classList.remove('navbar-scrolled');
        }
    });
    
    // Mobile menu auto-close
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            const navbarCollapse = document.querySelector('.navbar-collapse');
            if (navbarCollapse.classList.contains('show')) {
                const bsCollapse = new bootstrap.Collapse(navbarCollapse);
                bsCollapse.hide();
            }
        });
    });
}

// ===== FORMS =====
function initializeForms() {
    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
    
    // Real-time validation
    const inputs = document.querySelectorAll('input, textarea, select');
    inputs.forEach(input => {
        input.addEventListener('blur', function() {
            validateField(this);
        });
        
        input.addEventListener('input', function() {
            if (this.classList.contains('is-invalid')) {
                validateField(this);
            }
        });
    });
}

function validateField(field) {
    const isValid = field.checkValidity();
    
    if (isValid) {
        field.classList.remove('is-invalid');
        field.classList.add('is-valid');
    } else {
        field.classList.remove('is-valid');
        field.classList.add('is-invalid');
    }
}

// ===== TOOLTIPS =====
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// ===== MODALS =====
function initializeModals() {
    // Auto-focus first input in modals
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('shown.bs.modal', function() {
            const firstInput = modal.querySelector('input, textarea, select');
            if (firstInput) {
                firstInput.focus();
            }
        });
    });
}

// ===== SCROLL EFFECTS =====
function initializeScrollEffects() {
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Back to top button
    const backToTopBtn = createBackToTopButton();
    
    window.addEventListener('scroll', () => {
        if (window.scrollY > 300) {
            backToTopBtn.style.display = 'block';
        } else {
            backToTopBtn.style.display = 'none';
        }
    });
}

function createBackToTopButton() {
    const btn = document.createElement('button');
    btn.innerHTML = '<img src="/static/naebak/images/icons8-up-squared-50.png" alt="العودة للأعلى" style="width: 40px; height: 40px;">';
    btn.className = 'position-fixed';
    btn.style.cssText = `
        bottom: 30px;
        left: 30px;
        z-index: 1000;
        display: none;
        width: 50px;
        height: 50px;
        border: none;
        background: transparent;
        cursor: pointer;
        transition: transform 0.3s ease;
    `;
    
    // Add hover effect
    btn.addEventListener('mouseenter', () => {
        btn.style.transform = 'scale(1.1)';
    });
    
    btn.addEventListener('mouseleave', () => {
        btn.style.transform = 'scale(1)';
    });
    
    btn.addEventListener('click', () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
    
    document.body.appendChild(btn);
    return btn;
}

// ===== SEARCH FUNCTIONALITY =====
function initializeSearchFunctionality() {
    const searchInputs = document.querySelectorAll('.search-input');
    
    searchInputs.forEach(input => {
        let searchTimeout;
        
        input.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            const query = this.value.trim();
            
            if (query.length >= 2) {
                searchTimeout = setTimeout(() => {
                    performSearch(query, this);
                }, 300);
            } else {
                clearSearchResults(this);
            }
        });
    });
}

function performSearch(query, inputElement) {
    const searchType = inputElement.dataset.searchType || 'general';
    const resultsContainer = inputElement.nextElementSibling;
    
    // Show loading state
    if (resultsContainer) {
        resultsContainer.innerHTML = '<div class="text-center p-3"><i class="fas fa-spinner fa-spin"></i> جاري البحث...</div>';
        resultsContainer.style.display = 'block';
    }
    
    // Simulate API call (replace with actual API endpoint)
    setTimeout(() => {
        const mockResults = generateMockSearchResults(query, searchType);
        displaySearchResults(mockResults, resultsContainer);
    }, 500);
}

function generateMockSearchResults(query, type) {
    // Mock search results - replace with actual API call
    const results = [];
    
    if (type === 'candidates') {
        results.push(
            { title: `مرشح يحتوي على "${query}"`, url: '#', type: 'مرشح' },
            { title: `مرشح آخر يحتوي على "${query}"`, url: '#', type: 'مرشح' }
        );
    } else if (type === 'governorates') {
        results.push(
            { title: `محافظة تحتوي على "${query}"`, url: '#', type: 'محافظة' }
        );
    } else {
        results.push(
            { title: `نتيجة عامة تحتوي على "${query}"`, url: '#', type: 'عام' },
            { title: `نتيجة أخرى تحتوي على "${query}"`, url: '#', type: 'عام' }
        );
    }
    
    return results;
}

function displaySearchResults(results, container) {
    if (!container) return;
    
    if (results.length === 0) {
        container.innerHTML = '<div class="text-center p-3 text-muted">لا توجد نتائج</div>';
        return;
    }
    
    const html = results.map(result => `
        <a href="${result.url}" class="list-group-item list-group-item-action">
            <div class="d-flex justify-content-between align-items-center">
                <span>${result.title}</span>
                <small class="text-muted">${result.type}</small>
            </div>
        </a>
    `).join('');
    
    container.innerHTML = `<div class="list-group">${html}</div>`;
}

function clearSearchResults(inputElement) {
    const resultsContainer = inputElement.nextElementSibling;
    if (resultsContainer) {
        resultsContainer.style.display = 'none';
        resultsContainer.innerHTML = '';
    }
}

// ===== UTILITY FUNCTIONS =====

// Format numbers in Arabic
function formatArabicNumber(num) {
    const arabicNumbers = ['٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩'];
    return num.toString().replace(/\d/g, (digit) => arabicNumbers[digit]);
}

// Format dates in Arabic
function formatArabicDate(date) {
    const months = [
        'يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
        'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'
    ];
    
    const d = new Date(date);
    return `${d.getDate()} ${months[d.getMonth()]} ${d.getFullYear()}`;
}

// Show notification
function showNotification(message, type = 'info', duration = 5000) {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = `
        top: 100px;
        ${isRTL ? 'right' : 'left'}: 20px;
        z-index: 1050;
        min-width: 300px;
        max-width: 400px;
    `;
    
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after duration
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, duration);
}

// Loading state management
function showLoading(element) {
    const originalContent = element.innerHTML;
    element.dataset.originalContent = originalContent;
    element.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>جاري التحميل...';
    element.disabled = true;
}

function hideLoading(element) {
    const originalContent = element.dataset.originalContent;
    if (originalContent) {
        element.innerHTML = originalContent;
        delete element.dataset.originalContent;
    }
    element.disabled = false;
}

// ===== AJAX HELPERS =====
function makeRequest(url, options = {}) {
    const defaultOptions = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    };
    
    // Add CSRF token for POST requests
    if (options.method === 'POST' || options.method === 'PUT' || options.method === 'DELETE') {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        if (csrfToken) {
            defaultOptions.headers['X-CSRFToken'] = csrfToken.value;
        }
    }
    
    return fetch(url, { ...defaultOptions, ...options })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        });
}

// ===== EXPORT FOR GLOBAL USE =====
window.NaebakApp = {
    showNotification,
    showLoading,
    hideLoading,
    makeRequest,
    formatArabicNumber,
    formatArabicDate
};


// ===== MODERN FLASH NOTIFICATIONS =====
function initializeFlashNotifications() {
    const notifications = document.querySelectorAll('[data-notification]');
    
    notifications.forEach((notification, index) => {
        // Stagger animation delays
        notification.style.animationDelay = `${index * 0.1}s`;
        
        // Auto-dismiss after 5 seconds
        const autoDismissTimer = setTimeout(() => {
            dismissNotification(notification);
        }, 5000);
        
        // Handle manual dismiss
        const closeBtn = notification.querySelector('[data-dismiss-notification]');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                clearTimeout(autoDismissTimer);
                dismissNotification(notification);
            });
        }
        
        // Pause auto-dismiss on hover
        notification.addEventListener('mouseenter', () => {
            clearTimeout(autoDismissTimer);
            const progressBar = notification.querySelector('.flash-progress');
            if (progressBar) {
                progressBar.style.animationPlayState = 'paused';
            }
        });
        
        // Resume auto-dismiss on mouse leave
        notification.addEventListener('mouseleave', () => {
            const progressBar = notification.querySelector('.flash-progress');
            if (progressBar) {
                progressBar.style.animationPlayState = 'running';
            }
            
            // Set a new timer for remaining time
            setTimeout(() => {
                dismissNotification(notification);
            }, 2000); // Reduced time after hover
        });
    });
}

function dismissNotification(notification) {
    notification.style.animation = 'slideOutNotification 0.4s ease-in forwards';
    
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 400);
}

// Create and show a new notification programmatically
function showFlashNotification(message, type = 'info', duration = 5000) {
    const container = document.querySelector('.flash-notifications-container') || createNotificationContainer();
    
    const notification = document.createElement('div');
    notification.className = `flash-notification flash-${type}`;
    notification.setAttribute('data-notification', '');
    
    const iconMap = {
        success: 'fas fa-check-circle',
        error: 'fas fa-exclamation-circle',
        warning: 'fas fa-exclamation-triangle',
        info: 'fas fa-info-circle'
    };
    
    notification.innerHTML = `
        <div class="flash-icon">
            <i class="${iconMap[type] || 'fas fa-bell'}"></i>
        </div>
        <div class="flash-content">
            <div class="flash-message">${message}</div>
        </div>
        <button type="button" class="flash-close" data-dismiss-notification>
            <i class="fas fa-times"></i>
        </button>
        <div class="flash-progress"></div>
    `;
    
    container.appendChild(notification);
    
    // Initialize the new notification
    setTimeout(() => {
        initializeFlashNotifications();
    }, 100);
    
    return notification;
}

function createNotificationContainer() {
    const container = document.createElement('div');
    container.className = 'flash-notifications-container';
    document.body.appendChild(container);
    return container;
}

// Update the main initialization function
function initializeApp() {
    initializeAnimations();
    initializeNavigation();
    initializeForms();
    initializeTooltips();
    initializeModals();
    initializeScrollEffects();
    initializeSearchFunctionality();
    initializeFlashNotifications(); // Add this line
}

// Update the global NaebakApp object
window.NaebakApp = {
    showNotification: showFlashNotification, // Use the new flash notification function
    showLoading,
    hideLoading,
    makeRequest,
    formatArabicNumber,
    formatArabicDate,
    dismissNotification,
    showFlashNotification
};


// ===== FACEBOOK-STYLE NOTIFICATIONS =====
class NotificationSystem {
    constructor() {
        this.isAuthenticated = document.querySelector('#notificationDropdown') !== null;
        this.notificationDropdown = document.querySelector('#notificationDropdown');
        this.notificationCount = document.querySelector('.notification-count');
        this.notificationList = document.querySelector('.notification-list');
        this.markAllReadBtn = document.querySelector('.mark-all-read');
        this.refreshInterval = null;
        
        if (this.isAuthenticated) {
            this.init();
        }
    }
    
    init() {
        // Load notifications on page load
        this.loadNotifications();
        
        // Set up auto-refresh every 30 seconds
        this.refreshInterval = setInterval(() => {
            this.loadNotifications();
        }, 30000);
        
        // Handle dropdown show event
        if (this.notificationDropdown) {
            this.notificationDropdown.addEventListener('show.bs.dropdown', () => {
                this.loadNotifications();
            });
        }
        
        // Handle mark all as read
        if (this.markAllReadBtn) {
            this.markAllReadBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.markAllAsRead();
            });
        }
        
        // Handle page visibility change
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                this.loadNotifications();
            }
        });
    }
    
    async loadNotifications() {
        try {
            const response = await fetch('/api/notifications/', {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json',
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.updateNotificationUI(data.notifications, data.unread_count);
            } else {
                console.error('Failed to load notifications:', data.error);
            }
        } catch (error) {
            console.error('Error loading notifications:', error);
        }
    }
    
    updateNotificationUI(notifications, unreadCount) {
        // Update notification count badge
        if (this.notificationCount) {
            if (unreadCount > 0) {
                this.notificationCount.textContent = unreadCount > 99 ? '99+' : unreadCount;
                this.notificationCount.style.display = 'flex';
                
                // Add bell shake animation for new notifications
                if (this.notificationDropdown && !this.notificationDropdown.classList.contains('notification-bell-shake')) {
                    this.notificationDropdown.querySelector('.fa-bell').classList.add('notification-bell-shake');
                    setTimeout(() => {
                        this.notificationDropdown.querySelector('.fa-bell').classList.remove('notification-bell-shake');
                    }, 500);
                }
            } else {
                this.notificationCount.style.display = 'none';
            }
        }
        
        // Update mark all read button visibility
        if (this.markAllReadBtn) {
            this.markAllReadBtn.style.display = unreadCount > 0 ? 'block' : 'none';
        }
        
        // Update notification list
        if (this.notificationList) {
            if (notifications.length === 0) {
                this.notificationList.innerHTML = `
                    <div class="notification-empty">
                        <i class="fas fa-bell-slash mb-2"></i>
                        <div>لا توجد إشعارات جديدة</div>
                    </div>
                `;
            } else {
                this.notificationList.innerHTML = notifications.map(notification => 
                    this.createNotificationHTML(notification)
                ).join('');
                
                // Add click handlers for notification items
                this.notificationList.querySelectorAll('.notification-item').forEach(item => {
                    item.addEventListener('click', (e) => {
                        e.preventDefault();
                        const notificationId = item.dataset.notificationId;
                        const notificationType = item.dataset.notificationType;
                        const url = item.dataset.url;
                        
                        this.markAsRead(notificationId, notificationType, url);
                    });
                });
            }
        }
    }
    
    createNotificationHTML(notification) {
        const timeAgo = this.getTimeAgo(new Date(notification.timestamp));
        const isUnread = true; // All notifications from API are unread
        
        return `
            <a href="#" class="notification-item ${isUnread ? 'unread' : ''}" 
               data-notification-id="${notification.id}" 
               data-notification-type="${notification.type}"
               data-url="${notification.url}">
                <div class="notification-avatar">
                    <i class="fas ${this.getNotificationIcon(notification.type)}"></i>
                </div>
                <div class="notification-content">
                    <div class="notification-title">${notification.title}</div>
                    <div class="notification-text">${notification.content}</div>
                    <div class="notification-time">${timeAgo}</div>
                </div>
            </a>
        `;
    }
    
    getNotificationIcon(type) {
        const icons = {
            'message': 'fa-envelope',
            'reply': 'fa-reply',
            'rating': 'fa-star',
            'vote': 'fa-thumbs-up'
        };
        return icons[type] || 'fa-bell';
    }
    
    getTimeAgo(date) {
        const now = new Date();
        const diffInSeconds = Math.floor((now - date) / 1000);
        
        if (diffInSeconds < 60) {
            return 'الآن';
        } else if (diffInSeconds < 3600) {
            const minutes = Math.floor(diffInSeconds / 60);
            return `منذ ${minutes} دقيقة`;
        } else if (diffInSeconds < 86400) {
            const hours = Math.floor(diffInSeconds / 3600);
            return `منذ ${hours} ساعة`;
        } else {
            const days = Math.floor(diffInSeconds / 86400);
            return `منذ ${days} يوم`;
        }
    }
    
    async markAsRead(notificationId, notificationType, url) {
        try {
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
            
            const response = await fetch('/api/notifications/mark-read/', {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    notification_id: notificationId,
                    notification_type: notificationType
                })
            });
            
            if (response.ok) {
                // Navigate to the notification URL
                window.location.href = url;
            } else {
                console.error('Failed to mark notification as read');
                // Still navigate to the URL
                window.location.href = url;
            }
        } catch (error) {
            console.error('Error marking notification as read:', error);
            // Still navigate to the URL
            window.location.href = url;
        }
    }
    
    async markAllAsRead() {
        try {
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
            
            const response = await fetch('/api/notifications/mark-all-read/', {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                }
            });
            
            if (response.ok) {
                // Reload notifications to update UI
                this.loadNotifications();
                
                // Show success message
                this.showToast('تم تحديد جميع الإشعارات كمقروءة', 'success');
            } else {
                console.error('Failed to mark all notifications as read');
                this.showToast('حدث خطأ أثناء تحديث الإشعارات', 'error');
            }
        } catch (error) {
            console.error('Error marking all notifications as read:', error);
            this.showToast('حدث خطأ أثناء تحديث الإشعارات', 'error');
        }
    }
    
    showToast(message, type = 'info') {
        // Create a simple toast notification
        const toast = document.createElement('div');
        toast.className = `alert alert-${type === 'success' ? 'success' : 'danger'} position-fixed`;
        toast.style.cssText = `
            top: 100px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
            animation: slideInRight 0.3s ease-out;
        `;
        toast.innerHTML = `
            ${message}
            <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
        `;
        
        document.body.appendChild(toast);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, 3000);
    }
    
    destroy() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
    }
}

// Initialize notification system
let notificationSystem;

// Update the main initialization function
function initializeApp() {
    initializeAnimations();
    initializeNavigation();
    initializeForms();
    initializeTooltips();
    initializeModals();
    initializeScrollEffects();
    initializeSearchFunctionality();
    initializeFlashNotifications();
    
    // Initialize Facebook-style notifications
    notificationSystem = new NotificationSystem();
}

// Clean up on page unload
window.addEventListener('beforeunload', () => {
    if (notificationSystem) {
        notificationSystem.destroy();
    }
});

// Add CSS animation for toast
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
`;
document.head.appendChild(style);

