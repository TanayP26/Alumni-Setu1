// Filename: script.js
// This script handles UI interactions (modals, splash screen, feature animations),
// user authentication state (login, logout), and form submissions via Fetch API.

document.addEventListener('DOMContentLoaded', () => {
  // --- DOM Element Selection ---
  const splashScreen = document.getElementById('splash-screen');
  const mainContent = document.getElementById('main-content');
  const authModal = document.getElementById('auth-modal');
  const authCard = document.getElementById('auth-card');
  const closeModalBtn = document.getElementById('close-modal-btn');

  // Auth Buttons & User Profile
  const authButtons = document.getElementById('auth-buttons');
  const userProfileSection = document.getElementById('user-profile-section');
  const loginBtn = document.getElementById('login-btn');
  const joinBtn = document.getElementById('join-btn');
  const heroJoinBtn = document.getElementById('hero-join-btn');
  const profilePic = document.getElementById('profile-pic');
  const profileDropdown = document.getElementById('profile-dropdown');
  const logoutBtn = document.getElementById('logout-btn');

  // Forms
  const loginFormContainer = document.getElementById('login-form-container');
  const registerFormContainer = document.getElementById('register-form-container');
  const showRegisterBtn = document.getElementById('show-register-btn');
  const showLoginBtn = document.getElementById('show-login-btn');
  const loginForm = document.getElementById('login-form');
  const registerForm = document.getElementById('register-form');

  // Toast Notification
  const toast = document.getElementById('toast');
  const toastMessage = document.getElementById('toast-message');

  // --- State ---
  let isLoggedIn = false;

  // --- UI Functions ---
  const showToast = (message, type = 'success') => {
    toastMessage.textContent = message;
    toast.className = 'fixed bottom-5 right-5 px-6 py-3 rounded-lg shadow-lg transform transition-all duration-300';
    toast.classList.add(type, 'show');
    setTimeout(() => toast.classList.remove('show'), 3000);
  };

  const openModal = () => {
    authModal.classList.remove('hidden');
    authModal.classList.add('flex');
    setTimeout(() => authCard.classList.add('slide-up'), 50);
  };

  const closeModal = () => {
    authCard.classList.remove('slide-up');
    setTimeout(() => {
      authModal.classList.add('hidden');
      authModal.classList.remove('flex');
    }, 300);
  };

  const updateUIForLogin = (userName) => {
    isLoggedIn = true;
    authButtons.classList.add('hidden');
    userProfileSection.classList.remove('hidden');
    userProfileSection.classList.add('flex');
    closeModal();
    showToast(`Welcome back, ${userName}!`, 'success');
  };

  const updateUIForLogout = () => {
    isLoggedIn = false;
    userProfileSection.classList.add('hidden');
    userProfileSection.classList.remove('flex');
    authButtons.classList.remove('hidden');
    profileDropdown.classList.add('hidden');
    showToast('You have been logged out.', 'success');
  };

  // --- Event Handlers ---

  loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = loginForm.email.value;
    const password = loginForm.password.value;

    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      const result = await response.json();
      if (response.ok) {
        // Assuming result.message contains welcome text or user info
        const userName = result.user?.first_name || 'User';
        updateUIForLogin(userName);
      } else {
        showToast(result.error || 'Login failed.', 'error');
      }
    } catch (err) {
      console.error(err);
      showToast('An error occurred. Please try again.', 'error');
    }
  });

  registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = registerForm.name.value;
    const email = registerForm.email.value;
    const password = registerForm.password.value;

    try {
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, password })
      });
      const result = await response.json();
      if (response.ok) {
        showToast(result.message || 'Registration successful!', 'success');
        registerFormContainer.classList.add('hidden');
        loginFormContainer.classList.remove('hidden');
        registerForm.reset();
      } else {
        showToast(result.error || 'Registration failed.', 'error');
      }
    } catch (err) {
      console.error(err);
      showToast('An error occurred. Please try again.', 'error');
    }
  });

  logoutBtn.addEventListener('click', (e) => {
    e.preventDefault();
    updateUIForLogout();
  });

  // UI interaction listeners
  loginBtn.addEventListener('click', () => {
    registerFormContainer.classList.add('hidden');
    loginFormContainer.classList.remove('hidden');
    openModal();
  });

  [joinBtn, heroJoinBtn].forEach(btn => {
    btn.addEventListener('click', () => {
      loginFormContainer.classList.add('hidden');
      registerFormContainer.classList.remove('hidden');
      openModal();
    });
  });

  closeModalBtn.addEventListener('click', closeModal);
  authModal.addEventListener('click', (e) => {
    if (e.target === authModal) closeModal();
  });

  showRegisterBtn.addEventListener('click', () => {
    loginFormContainer.classList.add('hidden');
    registerFormContainer.classList.remove('hidden');
  });
  showLoginBtn.addEventListener('click', () => {
    registerFormContainer.classList.add('hidden');
    loginFormContainer.classList.remove('hidden');
  });

  profilePic.addEventListener('click', () => {
    profileDropdown.classList.toggle('hidden');
  });
  document.addEventListener('click', (e) => {
    if (!userProfileSection.contains(e.target)) {
      profileDropdown.classList.add('hidden');
    }
  });

  // --- App Initialization on Window Load ---

  window.addEventListener('load', () => {
    setTimeout(() => {
      splashScreen.style.opacity = '0';
      mainContent.style.opacity = '1';
      setTimeout(() => splashScreen.classList.add('hidden'), 1000);
    }, 1500);

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('fade-in');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1 });

    document.querySelectorAll('.feature-card').forEach(card => {
      observer.observe(card);
    });

    lucide.createIcons();
  });
});
