// base.js - UI and Authentication Logic with dynamic profile pics and enhanced registration form
document.addEventListener('DOMContentLoaded', () => {
  const authButtons = document.getElementById('auth-buttons');
  const userProfileSection = document.getElementById('user-profile-section');
  const profilePic = document.getElementById('profile-pic');
  const logoutBtn = document.getElementById('logout-btn');
  const loginBtn = document.getElementById('login-btn');
  const joinBtn = document.getElementById('join-btn');
  const heroJoinBtn = document.getElementById('hero-join-btn'); // Added Start Your Journey button
  const loginForm = document.getElementById('login-form');
  const registerForm = document.getElementById('register-form');
  const loginFormContainer = document.getElementById('login-form-container');
  const registerFormContainer = document.getElementById('register-form-container');
  const showRegisterBtn = document.getElementById('show-register-btn');
  const showLoginBtn = document.getElementById('show-login-btn');
  const authModal = document.getElementById('auth-modal');
  const authCard = document.getElementById('auth-card');
  const closeModalBtn = document.getElementById('close-modal-btn');
  const toast = document.getElementById('toast');
  const toastMessage = document.getElementById('toast-message');
  const splashScreen = document.getElementById('splash-screen');
  const mainContent = document.getElementById('main-content');

  const showToast = (message, type = 'success') => {
    toastMessage.textContent = message;
    toast.className = 'fixed bottom-5 right-5 px-6 py-3 rounded-lg shadow-lg transition-opacity duration-300';
    toast.classList.add(type === 'error' ? 'bg-red-500' : 'bg-green-500', 'show');
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

  const updateUIForLogin = (user) => {
    authButtons.classList.add('hidden');
    userProfileSection.classList.remove('hidden');
    userProfileSection.classList.add('flex');
    if (user.profile_picture) {
      profilePic.src = user.profile_picture.startsWith('http')
        ? user.profile_picture
        : `/static/2.png`;
    }
    localStorage.setItem('user', JSON.stringify(user));
    localStorage.setItem('token', user.token);
    closeModal();
    showToast(`Welcome back, ${user.first_name}!`);
  };

  const updateUIForLogout = () => {
    userProfileSection.classList.remove('flex');
    userProfileSection.classList.add('hidden');
    authButtons.classList.remove('hidden');
    localStorage.removeItem('user');
    localStorage.removeItem('token');
    showToast('Logged out successfully.');
  };

  const storedUser = JSON.parse(localStorage.getItem('user') || 'null');
  if (storedUser && localStorage.getItem('token')) {
    updateUIForLogin(storedUser);
  }

  // Login form submission
  loginForm?.addEventListener('submit', async e => {
    e.preventDefault();
    const email = loginForm.email.value;
    const password = loginForm.password.value;
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      const data = await res.json();
      if (res.ok) {
        updateUIForLogin({ ...data.user, token: data.access_token });
      } else {
        showToast(data.error || 'Login failed', 'error');
      }
    } catch {
      showToast('Network error', 'error');
    }
  });

  // Registration form submission
  registerForm?.addEventListener('submit', async e => {
    e.preventDefault();
    const fullName = registerForm.name.value.trim();
    const nameParts = fullName.split(' ');
    const first_name = nameParts.shift() || '';
    const last_name = nameParts.join(' ') || '';
    const email = registerForm.email.value.trim();
    const password = registerForm.password.value;
    const graduation_year = registerForm.graduation_year.value;
    const course = registerForm.course.value.trim();
    const department = registerForm.department.value.trim();

    if (!first_name) {
      showToast('First name is required', 'error');
      return;
    }
    if (!email) {
      showToast('Email is required', 'error');
      return;
    }
    if (!password) {
      showToast('Password is required', 'error');
      return;
    }
    if (!graduation_year) {
      showToast('Graduation year is required', 'error');
      return;
    }
    if (!course) {
      showToast('Course is required', 'error');
      return;
    }
    if (!department) {
      showToast('Department is required', 'error');
      return;
    }

    try {
      const res = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          first_name,
          last_name,
          email,
          password,
          graduation_year,
          course,
          department
        })
      });
      const data = await res.json();
      if (res.ok) {
        showToast('Registration successful!', 'success');
        registerFormContainer.classList.add('hidden');
        loginFormContainer.classList.remove('hidden');
        registerForm.reset();
      } else {
        showToast(data.error || 'Registration failed', 'error');
      }
    } catch {
      showToast('Network error', 'error');
    }
  });

  // Logout button
  logoutBtn?.addEventListener('click', e => {
    e.preventDefault();
    updateUIForLogout();
  });

  // Login/Join button open modal
  loginBtn?.addEventListener('click', () => {
    registerFormContainer.classList.add('hidden');
    loginFormContainer.classList.remove('hidden');
    openModal();
  });
  joinBtn?.addEventListener('click', () => {
    loginFormContainer.classList.add('hidden');
    registerFormContainer.classList.remove('hidden');
    openModal();
  });
  showRegisterBtn?.addEventListener('click', () => {
    loginFormContainer.classList.add('hidden');
    registerFormContainer.classList.remove('hidden');
  });
  showLoginBtn?.addEventListener('click', () => {
    registerFormContainer.classList.add('hidden');
    loginFormContainer.classList.remove('hidden');
  });
  closeModalBtn?.addEventListener('click', closeModal);
  authModal?.addEventListener('click', e => {
    if (e.target === authModal) closeModal();
  });

  // Hero "Start Your Journey" button functionality
  heroJoinBtn?.addEventListener('click', () => {
    loginFormContainer.classList.add('hidden');
    registerFormContainer.classList.remove('hidden');
    openModal();
  });

  profilePic?.addEventListener('click', () => {
    document.getElementById('profile-dropdown').classList.toggle('hidden');
  });
  document.addEventListener('click', e => {
    if (!document.getElementById('user-profile-section')?.contains(e.target)) {
      document.getElementById('profile-dropdown')?.classList.add('hidden');
    }
  });

  window.addEventListener('load', () => {
    setTimeout(() => {
      splashScreen.style.opacity = '0';
      mainContent.style.opacity = '1';
      setTimeout(() => splashScreen.classList.add('hidden'), 1000);
    }, 1500);
  });

  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('fade-in');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });
  document.querySelectorAll('.feature-card').forEach(card => observer.observe(card));

  if (window.lucide) lucide.createIcons();
});
