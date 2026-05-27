// ========================================
// INTERSECTION OBSERVER FOR SCROLL ANIMATIONS
// ========================================

const observerOptions = {
    threshold: 0.15,
    rootMargin: '0px 0px -50px 0px'
};

const scrollObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('revealed');
            
            // Add stagger delay for grid items
            if (entry.target.classList.contains('stagger')) {
                const siblings = Array.from(entry.target.parentElement.children);
                const index = siblings.indexOf(entry.target);
                entry.target.style.transitionDelay = `${index * 0.1}s`;
            }
        }
    });
}, observerOptions);

// Initialize scroll reveal on page load
const initScrollAnimations = () => {
    // Gallery items
    document.querySelectorAll('.gallery-item').forEach((item, index) => {
        item.classList.add('scroll-reveal');
        scrollObserver.observe(item);
    });
    
    // Launch cards with stagger
    document.querySelectorAll('.launch-card').forEach((card, index) => {
        card.classList.add('scroll-reveal-left', 'stagger');
        scrollObserver.observe(card);
    });
    
    // Sector images
    document.querySelectorAll('.sector-images img').forEach(img => {
        img.classList.add('scroll-reveal');
        scrollObserver.observe(img);
    });
    
    // Agentic features with stagger
    document.querySelectorAll('.agentic-feature').forEach((feature, index) => {
        feature.classList.add('scroll-reveal-left', 'stagger');
        scrollObserver.observe(feature);
    });
    
    // Platform items with stagger
    document.querySelectorAll('.platform-item').forEach((item, index) => {
        item.classList.add('scroll-reveal', 'stagger');
        scrollObserver.observe(item);
    });
    
    // Tool cards with stagger
    document.querySelectorAll('.tool-card').forEach((card, index) => {
        card.classList.add('scroll-reveal', 'stagger');
        scrollObserver.observe(card);
    });
    
    // Testimonial cards
    document.querySelectorAll('.testimonial-card').forEach((card, index) => {
        card.classList.add('scroll-reveal', 'stagger');
        scrollObserver.observe(card);
    });
    
    // Section titles
    document.querySelectorAll('.section-title').forEach(title => {
        title.classList.add('scroll-reveal');
        scrollObserver.observe(title);
    });
    
    // Analysis cards (for results page)
    document.querySelectorAll('.analysis-card, .criterion-card, .platform-card').forEach((card, index) => {
        card.classList.add('scroll-reveal', 'stagger');
        scrollObserver.observe(card);
    });
};

// ========================================
// PARALLAX EFFECT
// ========================================

const parallaxElements = [];

const initParallax = () => {
    // Hero image parallax
    const heroImage = document.querySelector('.hero-image img');
    if (heroImage) {
        parallaxElements.push({ element: heroImage, speed: 0.3 });
    }
    
    // Agentic visual parallax
    const agenticVisual = document.querySelector('.agentic-visual img');
    if (agenticVisual) {
        parallaxElements.push({ element: agenticVisual, speed: 0.2 });
    }
    
    // Automation visual parallax
    const automationVisual = document.querySelector('.automation-visual img');
    if (automationVisual) {
        parallaxElements.push({ element: automationVisual, speed: 0.25 });
    }
};

const updateParallax = () => {
    const scrolled = window.pageYOffset;
    
    parallaxElements.forEach(({ element, speed }) => {
        const elementTop = element.getBoundingClientRect().top + scrolled;
        const elementHeight = element.offsetHeight;
        const windowHeight = window.innerHeight;
        
        if (scrolled + windowHeight > elementTop && scrolled < elementTop + elementHeight) {
            const yPos = (scrolled - elementTop) * speed;
            element.style.transform = `translateY(${yPos}px)`;
        }
    });
};

// Throttle parallax updates for better performance
let ticking = false;
window.addEventListener('scroll', () => {
    if (!ticking) {
        window.requestAnimationFrame(() => {
            updateParallax();
            ticking = false;
        });
        ticking = true;
    }
});

// ========================================
// CARD TILT EFFECT (3D HOVER)
// ========================================

const initCardTilt = () => {
    const cards = document.querySelectorAll('.launch-card, .tool-card, .testimonial-card');
    
    cards.forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            
            const rotateX = (y - centerY) / 20;
            const rotateY = (centerX - x) / 20;
            
            card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale(1.02)`;
        });
        
        card.addEventListener('mouseleave', () => {
            card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) scale(1)';
        });
    });
};

// ========================================
// NUMBER COUNTER ANIMATION
// ========================================

const animateNumber = (element, start, end, duration) => {
    const range = end - start;
    const increment = range / (duration / 16);
    let current = start;
    
    const timer = setInterval(() => {
        current += increment;
        if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
            current = end;
            clearInterval(timer);
        }
        element.textContent = Math.round(current);
    }, 16);
};

const initNumberCounters = () => {
    // Overall score animation
    const scoreNumber = document.querySelector('.score-number');
    if (scoreNumber) {
        const targetScore = parseInt(scoreNumber.textContent);
        scoreNumber.textContent = '0';
        
        const scoreObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    animateNumber(scoreNumber, 0, targetScore, 1500);
                    scoreObserver.unobserve(entry.target);
                }
            });
        }, { threshold: 0.5 });
        
        scoreObserver.observe(scoreNumber);
    }
    
    // Platform scores
    document.querySelectorAll('.platform-score-number').forEach(scoreEl => {
        const targetScore = parseFloat(scoreEl.textContent);
        scoreEl.textContent = '0';
        
        const platformObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    animateNumber(scoreEl, 0, targetScore, 1000);
                    platformObserver.unobserve(entry.target);
                }
            });
        }, { threshold: 0.5 });
        
        platformObserver.observe(scoreEl);
    });
};

// ========================================
// SCROLL PROGRESS BAR
// ========================================

const createScrollProgressBar = () => {
    const progressBar = document.createElement('div');
    progressBar.className = 'scroll-progress-bar';
    progressBar.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        height: 3px;
        background: linear-gradient(90deg, var(--primary), var(--secondary));
        width: 0%;
        z-index: 9999;
        transition: width 0.1s ease;
    `;
    document.body.appendChild(progressBar);
    
    window.addEventListener('scroll', () => {
        const scrollTop = window.pageYOffset;
        const docHeight = document.documentElement.scrollHeight - window.innerHeight;
        const scrollPercent = (scrollTop / docHeight) * 100;
        progressBar.style.width = scrollPercent + '%';
    });
};

// ========================================
// BUTTON GLOW EFFECT
// ========================================

const initButtonGlow = () => {
    const buttons = document.querySelectorAll('.btn-primary, .btn-hero');
    
    buttons.forEach(button => {
        button.addEventListener('mouseenter', function(e) {
            const x = e.offsetX;
            const y = e.offsetY;
            
            const ripple = document.createElement('span');
            ripple.style.cssText = `
                position: absolute;
                width: 20px;
                height: 20px;
                background: rgba(255, 255, 255, 0.5);
                border-radius: 50%;
                pointer-events: none;
                transform: translate(-50%, -50%);
                left: ${x}px;
                top: ${y}px;
                animation: ripple 0.6s ease-out;
            `;
            
            this.appendChild(ripple);
            
            setTimeout(() => ripple.remove(), 600);
        });
    });
    
    // Add ripple animation
    if (!document.getElementById('ripple-animation')) {
        const style = document.createElement('style');
        style.id = 'ripple-animation';
        style.textContent = `
            @keyframes ripple {
                to {
                    width: 200px;
                    height: 200px;
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
    }
};

// ========================================
// MAGNETIC HOVER EFFECT (SUBTLE)
// ========================================

const initMagneticButtons = () => {
    const magneticElements = document.querySelectorAll('.btn-primary, .logo h1');
    
    magneticElements.forEach(element => {
        element.addEventListener('mousemove', function(e) {
            const rect = this.getBoundingClientRect();
            const x = e.clientX - rect.left - rect.width / 2;
            const y = e.clientY - rect.top - rect.height / 2;
            
            this.style.transform = `translate(${x * 0.1}px, ${y * 0.1}px)`;
        });
        
        element.addEventListener('mouseleave', function() {
            this.style.transform = 'translate(0, 0)';
        });
    });
};

// ========================================
// SMOOTH IMAGE FADE-IN
// ========================================

const initImageFadeIn = () => {
    const images = document.querySelectorAll('img');
    
    images.forEach(img => {
        if (img.complete) {
            img.style.opacity = '1';
        } else {
            img.style.opacity = '0';
            img.addEventListener('load', function() {
                this.style.transition = 'opacity 0.5s ease';
                this.style.opacity = '1';
            });
        }
    });
};

// ========================================
// SECTOR TAB ANIMATION ENHANCEMENT
// ========================================

const enhanceSectorTabs = () => {
    const tabs = document.querySelectorAll('.sector-tab');
    const contents = document.querySelectorAll('.sector-images');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            // Remove active from all
            tabs.forEach(t => t.classList.remove('active'));
            contents.forEach(c => c.classList.remove('active'));
            
            // Add active to clicked
            this.classList.add('active');
            
            // Show content with animation
            const sector = this.getAttribute('data-sector');
            const content = document.querySelector(`[data-sector-content="${sector}"]`);
            if (content) {
                // Fade out current
                const currentActive = document.querySelector('.sector-images.active');
                if (currentActive) {
                    currentActive.style.opacity = '0';
                    setTimeout(() => {
                        currentActive.classList.remove('active');
                    }, 300);
                }
                
                // Fade in new
                setTimeout(() => {
                    content.classList.add('active');
                    content.style.opacity = '0';
                    setTimeout(() => {
                        content.style.opacity = '1';
                    }, 50);
                }, 300);
            }
        });
    });
};

// ========================================
// CURSOR TRAIL EFFECT (OPTIONAL)
// ========================================

const initCursorTrail = () => {
    const hero = document.querySelector('.hero');
    if (!hero) return;
    
    const trail = [];
    const trailLength = 10;
    
    for (let i = 0; i < trailLength; i++) {
        const dot = document.createElement('div');
        dot.style.cssText = `
            position: fixed;
            width: ${8 - i * 0.5}px;
            height: ${8 - i * 0.5}px;
            background: rgba(102, 126, 234, ${0.8 - i * 0.08});
            border-radius: 50%;
            pointer-events: none;
            z-index: 9998;
            transition: transform 0.1s ease;
        `;
        document.body.appendChild(dot);
        trail.push({ element: dot, x: 0, y: 0 });
    }
    
    let mouseX = 0;
    let mouseY = 0;
    
    hero.addEventListener('mousemove', (e) => {
        mouseX = e.clientX;
        mouseY = e.clientY;
    });
    
    const animateTrail = () => {
        let x = mouseX;
        let y = mouseY;
        
        trail.forEach((dot, index) => {
            dot.element.style.left = x + 'px';
            dot.element.style.top = y + 'px';
            
            const nextDot = trail[index + 1] || trail[0];
            x += (nextDot.x - x) * 0.3;
            y += (nextDot.y - y) * 0.3;
            
            dot.x = x;
            dot.y = y;
        });
        
        requestAnimationFrame(animateTrail);
    };
    
    animateTrail();
};

// ========================================
// GALLERY SMOOTH SCROLL SNAP
// ========================================

const enhanceGalleryScroll = () => {
    const galleryWrapper = document.querySelector('.gallery-wrapper');
    if (!galleryWrapper) return;
    
    let isScrolling = false;
    let scrollTimeout;
    
    galleryWrapper.addEventListener('scroll', () => {
        isScrolling = true;
        clearTimeout(scrollTimeout);
        
        scrollTimeout = setTimeout(() => {
            isScrolling = false;
            
            // Snap to nearest item
            const items = document.querySelectorAll('.gallery-item');
            const scrollLeft = galleryWrapper.scrollLeft;
            let closestItem = items[0];
            let minDistance = Math.abs(scrollLeft);
            
            items.forEach(item => {
                const distance = Math.abs(item.offsetLeft - scrollLeft);
                if (distance < minDistance) {
                    minDistance = distance;
                    closestItem = item;
                }
            });
            
            galleryWrapper.scrollTo({
                left: closestItem.offsetLeft,
                behavior: 'smooth'
            });
        }, 150);
    });
};

// ========================================
// TYPEWRITER EFFECT (FOR SPECIFIC TEXT)
// ========================================

const typeWriter = (element, text, speed = 50) => {
    let i = 0;
    element.textContent = '';
    
    const type = () => {
        if (i < text.length) {
            element.textContent += text.charAt(i);
            i++;
            setTimeout(type, speed);
        }
    };
    
    type();
};

// ========================================
// RESULTS PAGE ENHANCEMENTS
// ========================================

const enhanceResultsPage = () => {
    // Animate progress bars
    const progressBars = document.querySelectorAll('.score-fill, .platform-fill');
    progressBars.forEach((bar, index) => {
        const targetWidth = bar.style.width;
        bar.style.width = '0%';
        
        const barObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    setTimeout(() => {
                        bar.style.transition = 'width 1s ease';
                        bar.style.width = targetWidth;
                    }, index * 100);
                    barObserver.unobserve(entry.target);
                }
            });
        }, { threshold: 0.5 });
        
        barObserver.observe(bar);
    });
    
    // Animate score circle
    const scoreCircle = document.querySelector('.overall-score-card circle:last-of-type');
    if (scoreCircle) {
        const originalDashoffset = scoreCircle.style.strokeDashoffset;
        scoreCircle.style.strokeDashoffset = '565.48';
        
        const circleObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    setTimeout(() => {
                        scoreCircle.style.transition = 'stroke-dashoffset 1.5s ease';
                        scoreCircle.style.strokeDashoffset = originalDashoffset;
                    }, 300);
                    circleObserver.unobserve(entry.target);
                }
            });
        }, { threshold: 0.5 });
        
        if (document.querySelector('.overall-score-card')) {
            circleObserver.observe(document.querySelector('.overall-score-card'));
        }
    }
};

// ========================================
// INITIALIZE ALL ANIMATIONS
// ========================================

const initializeAllAnimations = () => {
    // Core animations
    initScrollAnimations();
    initParallax();
    initCardTilt();
    initNumberCounters();
    createScrollProgressBar();
    initButtonGlow();
    initMagneticButtons();
    initImageFadeIn();
    enhanceSectorTabs();
    enhanceGalleryScroll();
    enhanceResultsPage();
    
    // Optional cursor trail (only on hero section)
    // Uncomment if you want this effect:
    // initCursorTrail();
    
    console.log('%c Animations Loaded ✨', 'color: #667eea; font-weight: bold; font-size: 14px;');
};

// Run on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeAllAnimations);
} else {
    initializeAllAnimations();
}

// Re-initialize on dynamic content load
window.addEventListener('load', () => {
    initScrollAnimations();
    initImageFadeIn();
});