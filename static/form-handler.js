// ========================================
// EMAIL FORM HANDLER (STEP 1)
// ========================================
const emailForm = document.getElementById('email-form');
const emailStep = document.getElementById('email-step');
const uploadStep = document.getElementById('upload-step');

if (emailForm) {
    emailForm.addEventListener('submit', (e) => {
        e.preventDefault();
        
        const emailInput = document.getElementById('trial-email');
        const email = emailInput.value.trim();
        
        // Basic email validation
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        
        if (!emailRegex.test(email)) {
            showError('Please enter a valid email address');
            return;
        }
        
        // Hide email step, show upload step
        emailStep.classList.add('hidden');
        uploadStep.classList.remove('hidden');
        
        // Smooth scroll to upload section
        uploadStep.scrollIntoView({ behavior: 'smooth', block: 'start' });
        
        // Log email (for showcase purposes only)
        console.log('Email captured:', email);
    });
}

// ========================================
// FILE UPLOAD HANDLER
// ========================================
const fileInput = document.getElementById('file');
const fileUploadDisplay = document.querySelector('.file-upload-display');
const fileUploadName = document.querySelector('.file-upload-name');
const uploadForm = document.getElementById('upload-form');
const analyzeBtn = document.getElementById('analyze-btn');

if (fileInput && fileUploadDisplay) {
    // File input change handler
    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        
        if (file) {
            // Validate file type
            const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif'];
            if (!allowedTypes.includes(file.type)) {
                showError('Please upload a valid image file (PNG, JPG, JPEG, or GIF)');
                fileInput.value = '';
                return;
            }
            
            // Validate file size (16MB limit)
            const maxSize = 16 * 1024 * 1024; // 16MB in bytes
            if (file.size > maxSize) {
                showError('File size must be less than 16MB');
                fileInput.value = '';
                return;
            }
            
            // Display file name
            fileUploadName.textContent = file.name;
            fileUploadDisplay.style.borderColor = 'var(--success)';
            fileUploadDisplay.style.background = 'rgba(72, 187, 120, 0.05)';
        }
    });
    
    // Drag and drop functionality
    fileUploadDisplay.addEventListener('dragover', (e) => {
        e.preventDefault();
        fileUploadDisplay.style.borderColor = 'var(--primary)';
        fileUploadDisplay.style.background = 'rgba(102, 126, 234, 0.05)';
    });
    
    fileUploadDisplay.addEventListener('dragleave', () => {
        fileUploadDisplay.style.borderColor = 'var(--border-color)';
        fileUploadDisplay.style.background = 'var(--bg-light)';
    });
    
    fileUploadDisplay.addEventListener('drop', (e) => {
        e.preventDefault();
        const file = e.dataTransfer.files[0];
        
        if (file) {
            // Create a new FileList-like object
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(file);
            fileInput.files = dataTransfer.files;
            
            // Trigger change event
            const event = new Event('change', { bubbles: true });
            fileInput.dispatchEvent(event);
        }
        
        fileUploadDisplay.style.borderColor = 'var(--border-color)';
        fileUploadDisplay.style.background = 'var(--bg-light)';
    });
}

// ========================================
// FORM SUBMISSION HANDLER
// ========================================
if (uploadForm && analyzeBtn) {
    uploadForm.addEventListener('submit', (e) => {
        // Validate form before submission
        const categorySelect = document.getElementById('category');
        const fileInput = document.getElementById('file');
        
        if (!categorySelect.value) {
            e.preventDefault();
            showError('Please select an industry sector');
            return;
        }
        
        if (!fileInput.files || fileInput.files.length === 0) {
            e.preventDefault();
            showError('Please upload an ad image');
            return;
        }
        
        // Show loading state
        const btnText = analyzeBtn.querySelector('.btn-text');
        const btnLoader = analyzeBtn.querySelector('.btn-loader');
        
        if (btnText && btnLoader) {
            btnText.classList.add('hidden');
            btnLoader.classList.remove('hidden');
            btnLoader.classList.add('active');
        }
        
        analyzeBtn.disabled = true;
        analyzeBtn.style.opacity = '0.7';
        analyzeBtn.style.cursor = 'not-allowed';
        
        // Form will submit normally to Flask backend
        // Loading state will persist until page reloads with results
    });
}

// ========================================
// ERROR MESSAGE DISPLAY
// ========================================
function showError(message) {
    // Remove any existing error messages
    const existingError = document.querySelector('.error-message');
    if (existingError) {
        existingError.remove();
    }
    
    // Create new error message
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.style.cssText = `
        background: rgba(245, 101, 101, 0.1);
        border: 2px solid var(--error);
        color: var(--error);
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        animation: shake 0.5s ease;
    `;
    errorDiv.textContent = message;
    
    // Insert error message
    if (uploadForm) {
        uploadForm.insertBefore(errorDiv, uploadForm.firstChild);
    }
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        errorDiv.style.opacity = '0';
        errorDiv.style.transition = 'opacity 0.3s ease';
        setTimeout(() => errorDiv.remove(), 300);
    }, 5000);
}

// Shake animation for errors
const shakeStyle = document.createElement('style');
shakeStyle.textContent = `
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-10px); }
        75% { transform: translateX(10px); }
    }
`;
document.head.appendChild(shakeStyle);

// ========================================
// CATEGORY SELECT STYLING
// ========================================
const categorySelect = document.getElementById('category');
if (categorySelect) {
    categorySelect.addEventListener('change', (e) => {
        if (e.target.value) {
            e.target.style.borderColor = 'var(--success)';
            e.target.style.color = 'var(--text-dark)';
        }
    });
}

// ========================================
// PRINT FUNCTIONALITY FOR RESULTS
// ========================================
const setupPrintStyles = () => {
    const printStyle = document.createElement('style');
    printStyle.media = 'print';
    printStyle.textContent = `
        @media print {
            body {
                background: white !important;
            }
            .header,
            .btn,
            .results-cta,
            .scroll-top-btn,
            .mobile-menu-toggle {
                display: none !important;
            }
            .results-section {
                padding: 1rem;
            }
            .overall-score-card,
            .analysis-card,
            .platform-card {
                break-inside: avoid;
                page-break-inside: avoid;
            }
            * {
                box-shadow: none !important;
            }
        }
    `;
    document.head.appendChild(printStyle);
};

setupPrintStyles();

// ========================================
// BACK NAVIGATION CONFIRMATION
// ========================================
if (uploadForm) {
    let formModified = false;
    
    fileInput?.addEventListener('change', () => {
        formModified = true;
    });
    
    categorySelect?.addEventListener('change', () => {
        formModified = true;
    });
    
    window.addEventListener('beforeunload', (e) => {
        if (formModified && !uploadForm.submitted) {
            e.preventDefault();
            e.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
            return e.returnValue;
        }
    });
    
    uploadForm.addEventListener('submit', () => {
        uploadForm.submitted = true;
    });
}

// ========================================
// IMAGE PREVIEW (OPTIONAL ENHANCEMENT)
// ========================================
const addImagePreview = () => {
    if (!fileInput) return;
    
    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (!file) return;
        
        // Remove existing preview
        const existingPreview = document.querySelector('.image-preview');
        if (existingPreview) {
            existingPreview.remove();
        }
        
        // Create preview
        const reader = new FileReader();
        reader.onload = (event) => {
            const preview = document.createElement('div');
            preview.className = 'image-preview';
            preview.style.cssText = `
                margin-top: 1rem;
                text-align: center;
                animation: fadeIn 0.3s ease;
            `;
            
            const img = document.createElement('img');
            img.src = event.target.result;
            img.style.cssText = `
                max-width: 100%;
                max-height: 300px;
                border-radius: 8px;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            `;
            
            const caption = document.createElement('p');
            caption.textContent = 'Preview of your uploaded image';
            caption.style.cssText = `
                margin-top: 0.5rem;
                color: var(--text-light);
                font-size: 0.9rem;
            `;
            
            preview.appendChild(img);
            preview.appendChild(caption);
            
            fileInput.parentElement.parentElement.appendChild(preview);
        };
        
        reader.readAsDataURL(file);
    });
};

addImagePreview();

// ========================================
// RESULTS PAGE ENHANCEMENTS
// ========================================
const enhanceResultsPage = () => {
    // Animate score circle on load
    const scoreCircle = document.querySelector('.overall-score-card circle:last-of-type');
    if (scoreCircle) {
        const originalDashoffset = scoreCircle.style.strokeDashoffset;
        scoreCircle.style.strokeDashoffset = '565.48';
        
        setTimeout(() => {
            scoreCircle.style.transition = 'stroke-dashoffset 1.5s ease';
            scoreCircle.style.strokeDashoffset = originalDashoffset;
        }, 300);
    }
    
    // Animate progress bars
    document.querySelectorAll('.score-fill, .platform-fill').forEach((bar, index) => {
        const targetWidth = bar.style.width;
        bar.style.width = '0%';
        
        setTimeout(() => {
            bar.style.width = targetWidth;
        }, 500 + (index * 100));
    });
};

// Run on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', enhanceResultsPage);
} else {
    enhanceResultsPage();
}

// ========================================
// ACCESSIBILITY IMPROVEMENTS
// ========================================
const improveAccessibility = () => {
    // Add ARIA labels
    if (fileInput) {
        fileInput.setAttribute('aria-label', 'Upload ad image file');
    }
    
    if (categorySelect) {
        categorySelect.setAttribute('aria-label', 'Select industry sector');
    }
    
    // Keyboard navigation for file upload
    if (fileUploadDisplay) {
        fileUploadDisplay.setAttribute('tabindex', '0');
        fileUploadDisplay.setAttribute('role', 'button');
        fileUploadDisplay.setAttribute('aria-label', 'Click to upload file or drag and drop');
        
        fileUploadDisplay.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                fileInput.click();
            }
        });
    }
};

improveAccessibility();

console.log('%c Form Handler Ready 🚀', 'color: #764ba2; font-weight: bold; font-size: 14px;');