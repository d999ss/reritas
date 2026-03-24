/* Rugiet Static Site - Animations & Interactivity */
(function() {
  'use strict';

  /* ── Scroll-triggered fade-in ── */
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.opacity = '1';
        entry.target.style.transform = 'translateY(0)';
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });

  function initScrollAnimations() {
    // Animate sections on scroll
    document.querySelectorAll('main > div > div, main section, [class*="animate"]').forEach(el => {
      if (el.closest('nav, header, banner, [role="banner"]')) return;
      if (el.getBoundingClientRect().top > window.innerHeight) {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
      }
    });
  }

  /* ── Carousel / Slider ── */
  function initCarousels() {
    // Find carousel containers (they have prev/next buttons)
    document.querySelectorAll('button[disabled]').forEach(btn => {
      const text = btn.textContent || btn.getAttribute('aria-label') || '';
      if (!text.includes('slide')) return;

      const container = btn.closest('div');
      if (!container) return;

      const prevBtn = container.querySelector('button:first-child');
      const nextBtn = container.querySelector('button:last-child');

      // Find the scrollable sibling (previous sibling with overflow)
      let scrollContainer = container.previousElementSibling;
      if (!scrollContainer) return;

      // Look for a horizontally scrollable child
      const scrollTarget = scrollContainer.querySelector('[style*="overflow"], [class*="scroll"], [class*="slider"]')
        || scrollContainer;

      // Enable the buttons
      if (prevBtn) prevBtn.disabled = false;
      if (nextBtn) nextBtn.disabled = false;

      const scrollAmount = 340;

      if (prevBtn) {
        prevBtn.addEventListener('click', () => {
          scrollTarget.scrollBy({ left: -scrollAmount, behavior: 'smooth' });
        });
      }
      if (nextBtn) {
        nextBtn.addEventListener('click', () => {
          scrollTarget.scrollBy({ left: scrollAmount, behavior: 'smooth' });
        });
      }
    });
  }

  /* ── FAQ Accordions ── */
  function initAccordions() {
    document.querySelectorAll('button').forEach(btn => {
      const text = btn.textContent || '';
      // FAQ buttons are questions — look for question marks or common FAQ patterns
      if (!text.includes('?') && !text.includes('How') && !text.includes('What') && !text.includes('Do ') && !text.includes('Are ') && !text.includes('Is ') && !text.includes('If ')) return;
      // Skip nav buttons
      if (btn.closest('nav, [role="banner"], header')) return;

      const panel = btn.nextElementSibling;
      if (!panel) return;

      // Initially hide accordion content
      panel.style.maxHeight = '0';
      panel.style.overflow = 'hidden';
      panel.style.transition = 'max-height 0.3s ease, opacity 0.3s ease';
      panel.style.opacity = '0';

      btn.style.cursor = 'pointer';
      btn.addEventListener('click', () => {
        const isOpen = panel.style.maxHeight !== '0px' && panel.style.maxHeight !== '0';
        if (isOpen) {
          panel.style.maxHeight = '0';
          panel.style.opacity = '0';
        } else {
          panel.style.maxHeight = panel.scrollHeight + 'px';
          panel.style.opacity = '1';
        }
      });
    });
  }

  /* ── Mobile Menu Toggle ── */
  function initMobileMenu() {
    const menuBtn = document.querySelector('button[class*="menu"], button[aria-label*="menu"], button[aria-label*="Menu"]');
    if (!menuBtn) {
      // Try finding by text content
      document.querySelectorAll('button').forEach(btn => {
        if ((btn.textContent || '').includes('Menu')) {
          btn.addEventListener('click', () => {
            const nav = btn.closest('header, [role="banner"], nav')?.querySelector('ul, [role="navigation"]');
            if (nav) {
              nav.style.display = nav.style.display === 'none' ? 'flex' : 'none';
            }
          });
        }
      });
      return;
    }
    menuBtn.addEventListener('click', () => {
      const nav = menuBtn.closest('header, [role="banner"]')?.querySelector('nav, ul');
      if (nav) {
        nav.style.display = nav.style.display === 'none' ? 'flex' : 'none';
      }
    });
  }

  /* ── Sticky Header ── */
  function initStickyHeader() {
    const header = document.querySelector('[role="banner"], header, nav');
    if (!header) return;
    let lastScroll = 0;
    window.addEventListener('scroll', () => {
      const current = window.scrollY;
      if (current > 100) {
        header.style.backdropFilter = 'blur(10px)';
        header.style.webkitBackdropFilter = 'blur(10px)';
      } else {
        header.style.backdropFilter = '';
        header.style.webkitBackdropFilter = '';
      }
      lastScroll = current;
    }, { passive: true });
  }

  /* ── Tab Switching (Sex/Testosterone/Sleep/Weight) ── */
  function initTabs() {
    const tabLabels = ['Sex', 'Testosterone', 'Sleep', 'Weight'];
    const buttons = [];
    document.querySelectorAll('button').forEach(btn => {
      const text = (btn.textContent || '').trim();
      if (tabLabels.includes(text) && !btn.closest('nav, [role="banner"]')) {
        buttons.push(btn);
      }
    });
    if (buttons.length === 0) return;

    buttons.forEach((btn, i) => {
      btn.style.cursor = 'pointer';
      btn.addEventListener('click', () => {
        // Visual active state
        buttons.forEach(b => {
          b.style.opacity = '0.5';
          b.style.borderBottom = '2px solid transparent';
        });
        btn.style.opacity = '1';
        btn.style.borderBottom = '2px solid currentColor';
      });
      // Set first tab active by default
      if (i === 0) {
        btn.style.opacity = '1';
        btn.style.borderBottom = '2px solid currentColor';
      } else {
        btn.style.opacity = '0.5';
      }
    });
  }

  /* ── Smooth scroll for anchor links ── */
  function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(a => {
      a.addEventListener('click', e => {
        const target = document.querySelector(a.getAttribute('href'));
        if (target) {
          e.preventDefault();
          target.scrollIntoView({ behavior: 'smooth' });
        }
      });
    });
  }

  /* ── Init all ── */
  function init() {
    initScrollAnimations();
    initCarousels();
    initAccordions();
    initMobileMenu();
    initStickyHeader();
    initTabs();
    initSmoothScroll();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
