// Enhanced script.js with improved functionality

// DOM Ready handler with enhanced functionality
document.addEventListener('DOMContentLoaded', function() {
    // Theme management
    initializeTheme();
    
    // Setup notification polling
    if (isUserLoggedIn()) {
        initializeNotifications();
    }
    
    // Setup auto-dismissing alerts
    setupAlertDismissal();
    
    // Initialize charts if on dashboard
    if (document.getElementById('progressChart')) {
        initializeCharts();
    }
    
    // Initialize course filters if on courses page
    if (document.getElementById('courseFilters')) {
        initializeCourseFilters();
    }
    
    // Initialize rating system if on course details page
    if (document.getElementById('ratingSystem')) {
        initializeRatingSystem();
    }
    
    // Initialize profile image preview if on profile page
    if (document.getElementById('profileImageUpload')) {
        initializeProfileImagePreview();
    }
});

// Theme management functions
function initializeTheme() {
    const theme = getCookie('theme') || 'light';
    document.body.setAttribute('data-bs-theme', theme);
    
    // Update theme switch state
    const themeSwitch = document.getElementById('themeSwitch');
    if (themeSwitch) {
        themeSwitch.checked = (theme === 'dark');
    }
}

function toggleTheme() {
    const currentTheme = document.body.getAttribute('data-bs-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    document.body.setAttribute('data-bs-theme', newTheme);
    setCookie('theme', newTheme, 30);
    
    // Update theme label text
    const themeLabel = document.querySelector('.theme-switch-label');
    if (themeLabel) {
        themeLabel.textContent = newTheme === 'dark' ? 'الوضع النهاري' : 'الوضع الليلي';
    }
    
    // Trigger event for chart rerendering if needed
    if (window.charts) {
        window.dispatchEvent(new Event('themeChanged'));
    }
}

// Notification system
function initializeNotifications() {
    // Initial fetch
    fetchNotifications();
    
    // Setup polling every 30 seconds
    setInterval(fetchNotifications, 30000);
}

function fetchNotifications() {
    fetch('/api/notifications/unread')
        .then(response => response.json())
        .then(data => {
            updateNotificationBadge(data.length);
            updateNotificationDropdown(data);
        })
        .catch(error => console.error('Error fetching notifications:', error));
}

function updateNotificationBadge(count) {
    const badge = document.querySelector('.notification-count');
    if (badge) {
        if (count > 0) {
            badge.textContent = count;
            badge.style.display = 'flex';
        } else {
            badge.style.display = 'none';
        }
    }
}

function updateNotificationDropdown(notifications) {
    const dropdown = document.getElementById('notificationDropdown');
    if (!dropdown) return;
    
    const container = dropdown.querySelector('.notification-list');
    if (!container) return;
    
    // Clear existing notifications
    container.innerHTML = '';
    
    if (notifications.length === 0) {
        container.innerHTML = '<div class="p-3 text-center text-muted">لا توجد إشعارات جديدة</div>';
        return;
    }
    
    // Add new notifications
    notifications.forEach(notification => {
        const item = document.createElement('a');
        item.href = '/notifications';
        item.className = 'dropdown-item notification-item notification-unread';
        
        const title = document.createElement('div');
        title.className = 'notification-title';
        title.textContent = notification.title;
        
        const message = document.createElement('div');
        message.className = 'notification-message';
        message.textContent = notification.message;
        
        const time = document.createElement('div');
        time.className = 'notification-time';
        time.textContent = formatDate(notification.timestamp);
        
        item.appendChild(title);
        item.appendChild(message);
        item.appendChild(time);
        container.appendChild(item);
    });
}

// Course filtering system
function initializeCourseFilters() {
    // Setup search input
    const searchInput = document.getElementById('courseSearch');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(filterCourses, 300));
    }
    
    // Setup category filter
    const categoryFilter = document.getElementById('categoryFilter');
    if (categoryFilter) {
        categoryFilter.addEventListener('change', filterCourses);
    }
    
    // Setup level filter
    const levelFilter = document.getElementById('levelFilter');
    if (levelFilter) {
        levelFilter.addEventListener('change', filterCourses);
    }
    
    // Initial load of courses
    loadCourses();
}

function loadCourses(filters = {}) {
    const coursesList = document.getElementById('coursesList');
    if (!coursesList) return;
    
    // Show loading spinner
    coursesList.innerHTML = `
        <div class="loading-spinner">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">جاري التحميل...</span>
            </div>
        </div>
    `;
    
    // Build query string from filters
    const queryParams = new URLSearchParams();
    if (filters.search) queryParams.append('search', filters.search);
    if (filters.category) queryParams.append('category', filters.category);
    if (filters.level) queryParams.append('level', filters.level);
    
    // Fetch courses with filters
    fetch(`/api/courses?${queryParams.toString()}`)
        .then(response => response.json())
        .then(courses => {
            displayCourses(courses);
        })
        .catch(error => {
            console.error('Error loading courses:', error);
            coursesList.innerHTML = `
                <div class="alert alert-danger">
                    حدث خطأ أثناء تحميل الدورات. يرجى المحاولة مرة أخرى.
                </div>
            `;
        });
}

function filterCourses() {
    const searchInput = document.getElementById('courseSearch');
    const categoryFilter = document.getElementById('categoryFilter');
    const levelFilter = document.getElementById('levelFilter');
    
    const filters = {
        search: searchInput ? searchInput.value : '',
        category: categoryFilter ? categoryFilter.value : '',
        level: levelFilter ? levelFilter.value : ''
    };
    
    loadCourses(filters);
}

function displayCourses(courses) {
    const coursesList = document.getElementById('coursesList');
    if (!coursesList) return;
    
    if (courses.length === 0) {
        coursesList.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📚</div>
                <div class="empty-state-text">لم يتم العثور على دورات مطابقة للبحث</div>
                <button class="btn btn-primary" onclick="resetFilters()">إعادة ضبط الفلاتر</button>
            </div>
        `;
        return;
    }
    
    coursesList.innerHTML = '';
    
    courses.forEach(course => {
        const courseCard = document.createElement('div');
        courseCard.className = 'col-md-6 col-lg-4 mb-4 fade-in';
        
        // Format the rating stars
        const ratingStars = generateRatingStars(course.average_rating);
        
        courseCard.innerHTML = `
            <div class="card course-card h-100">
                <img src="/static/uploads/${course.image}" class="course-image" alt="${course.title}">
                <div class="card-body">
                    <h5 class="course-title">${course.title}</h5>
                    <div class="course-meta">
                        <span><i class="bi bi-person"></i> ${course.instructor || 'غير محدد'}</span>
                        <span><i class="bi bi-clock"></i> ${course.duration || 'غير محدد'}</span>
                    </div>
                    <div class="course-rating">
                        <div class="rating-stars">${ratingStars}</div>
                        <span>(${course.ratings_count} تقييم)</span>
                    </div>
                    <p class="course-description">${course.description}</p>
                    <div class="d-flex justify-content-between align-items-center mt-auto">
                        <span class="badge bg-${getLevelBadgeColor(course.level)}">${course.level || 'غير محدد'}</span>
                        <a href="/course/${course.id}" class="btn btn-outline-primary">عرض التفاصيل</a>
                    </div>
                </div>
            </div>
        `;
        
        coursesList.appendChild(courseCard);
    });
}

function resetFilters() {
    const searchInput = document.getElementById('courseSearch');
    const categoryFilter = document.getElementById('categoryFilter');
    const levelFilter = document.getElementById('levelFilter');
    
    if (searchInput) searchInput.value = '';
    if (categoryFilter) categoryFilter.value = '';
    if (levelFilter) levelFilter.value = '';
    
    filterCourses();
}

// Rating system
function initializeRatingSystem() {
    const ratingForm = document.getElementById('ratingForm');
    if (ratingForm) {
        ratingForm.addEventListener('submit', submitRating);
    }
}

function submitRating(event) {
    event.preventDefault();
    
    const form = event.target;
    const courseId = form.getAttribute('data-course-id');
    const ratingValue = form.querySelector('input[name="rating"]:checked').value;
    const reviewText = form.querySelector('textarea[name="review"]').value;
    
    const data = {
        course_id: parseInt(courseId),
        rating: parseInt(ratingValue),
        review: reviewText
    };
    
    fetch('/ajax/rate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            showToast('نجاح', result.message, 'success');
            // Reload the page to show updated ratings
            setTimeout(() => window.location.reload(), 1500);
        } else {
            showToast('خطأ', result.message, 'danger');
        }
    })
    .catch(error => {
        console.error('Error submitting rating:', error);
        showToast('خطأ', 'حدث خطأ أثناء إرسال التقييم', 'danger');
    });
}

// Course enrollment
function enrollInCourse(courseId, courseTitle) {
    // Show confirmation modal
    const modal = new bootstrap.Modal(document.getElementById('enrollmentModal'));
    document.getElementById('courseName').textContent = courseTitle;
    document.getElementById('confirmEnroll').setAttribute('data-course-id', courseId);
    modal.show();
    
    // Setup confirmation button
    document.getElementById('confirmEnroll').onclick = function() {
        const courseId = this.getAttribute('data-course-id');
        
        fetch('/ajax/enroll', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({ course_id: parseInt(courseId) })
        })
        .then(response => response.json())
        .then(result => {
            modal.hide();
            
            if (result.success) {
                showToast('نجاح', result.message, 'success');
                // Disable enroll button and change its text
                const enrollButton = document.querySelector(`.enroll-button[data-course-id="${courseId}"]`);
                if (enrollButton) {
                    enrollButton.classList.remove('btn-primary');
                    enrollButton.classList.add('btn-success');
                    enrollButton.textContent = 'تم التسجيل';
                    enrollButton.disabled = true;
                }
            } else {
                showToast('خطأ', result.message, 'danger');
            }
        })
        .catch(error => {
            console.error('Error enrolling in course:', error);
            modal.hide();
            showToast('خطأ', 'حدث خطأ أثناء التسجيل في الدورة', 'danger');
        });
    };
}

// Progress update
function updateProgress(courseId, progress) {
    fetch('/ajax/update_progress', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({ 
            course_id: parseInt(courseId),
            progress: parseInt(progress)
        })
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            showToast('نجاح', result.message, 'success');
            
            // Update progress bar
            const progressBar = document.querySelector(`.progress-bar[data-course-id="${courseId}"]`);
            if (progressBar) {
                progressBar.style.width = `${progress}%`;
                progressBar.setAttribute('aria-valuenow', progress);
                progressBar.textContent = `${progress}%`;
            }
            
            // Update completed status if needed
            if (result.completed) {
                const statusBadge = document.querySelector(`.course-status[data-course-id="${courseId}"]`);
                if (statusBadge) {
                    statusBadge.textContent = 'مكتمل';
                    statusBadge.classList.remove('bg-warning');
                    statusBadge.classList.add('bg-success');
                }
            }
        } else {
            showToast('خطأ', result.message, 'danger');
        }
    })
    .catch(error => {
        console.error('Error updating progress:', error);
        showToast('خطأ', 'حدث خطأ أثناء تحديث التقدم', 'danger');
    });
}

// Profile image preview
function initializeProfileImagePreview() {
    const imageInput = document.getElementById('profileImageUpload');
    const imagePreview = document.getElementById('profileImagePreview');
    
    if (imageInput && imagePreview) {
        imageInput.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                const reader = new FileReader();
                
                reader.onload = function(e) {
                    imagePreview.src = e.target.result;
                };
                
                reader.readAsDataURL(this.files[0]);
            }
        });
    }
}

// Charts initialization
function initializeCharts() {
    // Only initialize if Chart.js is loaded
    if (typeof Chart === 'undefined') return;
    
    // Store charts in window object for theme change updates
    window.charts = {};
    
    // Progress chart
    const progressCtx = document.getElementById('progressChart');
    if (progressCtx) {
        const progressData = JSON.parse(progressCtx.getAttribute('data-progress'));
        
        window.charts.progress = new Chart(progressCtx, {
            type: 'doughnut',
            data: {
                labels: ['مكتمل', 'قيد التقدم', 'لم يبدأ بعد'],
                datasets: [{
                    data: [
                        progressData.completed,
                        progressData.in_progress,
                        progressData.not_started
                    ],
                    backgroundColor: [
                        '#198754',
                        '#ffc107',
                        '#6c757d'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: getTextColor()
                        }
                    }
                }
            }
        });
    }
    
    // Activity chart
    const activityCtx = document.getElementById('activityChart');
    if (activityCtx) {
        const activityData = JSON.parse(activityCtx.getAttribute('data-activity'));
        
        window.charts.activity = new Chart(activityCtx, {
            type: 'line',
            data: {
                labels: activityData.labels,
                datasets: [{
                    label: 'نشاط التعلم',
                    data: activityData.values,
                    borderColor: '#0d6efd',
                    backgroundColor: 'rgba(13, 110, 253, 0.1)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            color: getTextColor()
                        },
                        grid: {
                            color: getGridColor()
                        }
                    },
                    x: {
                        ticks: {
                            color: getTextColor()
                        },
                        grid: {
                            color: getGridColor()
                        }
                    }
                },
                plugins: {
                    legend: {
                        labels: {
                            color: getTextColor()
                        }
                    }
                }
            }
        });
    }
    
    // Update charts on theme change
    window.addEventListener('themeChanged', updateChartsTheme);
}

function updateChartsTheme() {
    if (!window.charts) return;
    
    // Update text and grid colors for all charts
    Object.values(window.charts).forEach(chart => {
        // Update legend text color
        if (chart.options.plugins && chart.options.plugins.legend) {
            chart.options.plugins.legend.labels.color = getTextColor();
        }
        
        // Update axis colors for cartesian charts
        if (chart.options.scales) {
            if (chart.options.scales.y) {
                chart.options.scales.y.ticks.color = getTextColor();
                chart.options.scales.y.grid.color = getGridColor();
            }
            if (chart.options.scales.x) {
                chart.options.scales.x.ticks.color = getTextColor();
                chart.options.scales.x.grid.color = getGridColor();
            }
        }
        
        chart.update();
    });
}

// Utility functions
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}

function setCookie(name, value, days) {
    const date = new Date();
    date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
    document.cookie = `${name}=${value};expires=${date.toUTCString()};path=/;SameSite=Lax`;
}

function getCsrfToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}

function isUserLoggedIn() {
    // Check if user is logged in by looking for user-specific elements
    return !!document.getElementById('userDropdown') || 
           !!document.querySelector('[data-logged-in="true"]');
}

function setupAlertDismissal() {
    // Auto-dismiss alerts after 5 seconds
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert:not(.alert-info)');
        alerts.forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
}

function showToast(title, message, type = 'success') {
    // Create toast container if it doesn't exist
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container';
        document.body.appendChild(toastContainer);
    }
    
    // Create toast element
    const toastId = 'toast-' + Date.now();
    const toast = document.createElement('div');
    toast.className = `custom-toast toast-${type} fade-in`;
    toast.id = toastId;
    
    toast.innerHTML = `
        <div class="toast-header">
            <strong class="me-auto">${title}</strong>
            <button type="button" class="btn-close" onclick="dismissToast('${toastId}')"></button>
        </div>
        <div class="toast-body">
            ${message}
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => dismissToast(toastId), 5000);
}

function dismissToast(toastId) {
    const toast = document.getElementById(toastId);
    if (toast) {
        toast.classList.remove('fade-in');
        toast.classList.add('fade-out');
        setTimeout(() => toast.remove(), 300);
    }
}

function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHour = Math.floor(diffMin / 60);
    const diffDay = Math.floor(diffHour / 24);
    
    if (diffSec < 60) {
        return 'الآن';
    } else if (diffMin < 60) {
        return `منذ ${diffMin} دقيقة`;
    } else if (diffHour < 24) {
        return `منذ ${diffHour} ساعة`;
    } else if (diffDay < 7) {
        return `منذ ${diffDay} يوم`;
    } else {
        return date.toLocaleDateString('ar-SA');
    }
}

function generateRatingStars(rating) {
    const fullStar = '<i class="bi bi-star-fill"></i>';
    const halfStar = '<i class="bi bi-star-half"></i>';
    const emptyStar = '<i class="bi bi-star"></i>';
    
    let stars = '';
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating % 1 >= 0.5;
    
    // Add full stars
    for (let i = 0; i < fullStars; i++) {
        stars += fullStar;
    }
    
    // Add half star if needed
    if (hasHalfStar) {
        stars += halfStar;
    }
    
    // Add empty stars
    const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0);
    for (let i = 0; i < emptyStars; i++) {
        stars += emptyStar;
    }
    
    return stars;
}

function getLevelBadgeColor(level) {
    if (!level) return 'secondary';
    
    switch (level.toLowerCase()) {
        case 'مبتدئ':
            return 'success';
        case 'متوسط':
            return 'warning';
        case 'متقدم':
            return 'danger';
        default:
            return 'secondary';
    }
}

function getTextColor() {
    return document.body.getAttribute('data-bs-theme') === 'dark' ? '#e0e0e0' : '#212529';
}

function getGridColor() {
    return document.body.getAttribute('data-bs-theme') === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)';
}

// Debounce function for search input
function debounce(func, wait) {
    let timeout;
    return function() {
        const context = this;
        const args = arguments;
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(context, args), wait);
    };
}

// Form validation functions
function validateRegistrationForm() {
    const nameInput = document.getElementById('name');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirmPassword');
    
    let isValid = true;
    
    // Validate name
    if (!nameInput.value.trim()) {
        showInputError(nameInput, 'الرجاء إدخال الاسم الكامل');
        isValid = false;
    } else {
        clearInputError(nameInput);
    }
    
    // Validate email
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(emailInput.value.trim())) {
        showInputError(emailInput, 'الرجاء إدخال بريد إلكتروني صحيح');
        isValid = false;
    } else {
        clearInputError(emailInput);
    }
    
    // Validate password
    if (passwordInput.value.length < 8) {
        showInputError(passwordInput, 'يجب أن تتكون كلمة المرور من 8 أحرف على الأقل');
        isValid = false;
    } else {
        clearInputError(passwordInput);
    }
    
    // Validate password confirmation
    if (confirmPasswordInput && passwordInput.value !== confirmPasswordInput.value) {
        showInputError(confirmPasswordInput, 'كلمات المرور غير متطابقة');
        isValid = false;
    } else if (confirmPasswordInput) {
        clearInputError(confirmPasswordInput);
    }
    
    return isValid;
}

function validateLoginForm() {
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    
    let isValid = true;
    
    // Validate email
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(emailInput.value.trim())) {
        showInputError(emailInput, 'الرجاء إدخال بريد إلكتروني صحيح');
        isValid = false;
    } else {
        clearInputError(emailInput);
    }
    
    // Validate password
    if (!passwordInput.value) {
        showInputError(passwordInput, 'الرجاء إدخال كلمة المرور');
        isValid = false;
    } else {
        clearInputError(passwordInput);
    }
    
    return isValid;
}

function showInputError(input, message) {
    // Clear any existing error
    clearInputError(input);
    
    // Add error class to input
    input.classList.add('is-invalid');
    
    // Create and append error message
    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback';
    errorDiv.textContent = message;
    input.parentNode.appendChild(errorDiv);
}

function clearInputError(input) {
    input.classList.remove('is-invalid');
    
    // Remove any existing error message
    const errorDiv = input.parentNode.querySelector('.invalid-feedback');
    if (errorDiv) {
        errorDiv.remove();
    }
}
