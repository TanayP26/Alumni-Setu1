document.addEventListener('DOMContentLoaded', () => {
    const jobListings = document.getElementById('job-listings');
    const loading = document.getElementById('loading');
    const noJobs = document.getElementById('no-jobs');
    const searchBtn = document.getElementById('search-btn');
    const jobSearch = document.getElementById('job-search');
    const jobTypeFilter = document.getElementById('job-type-filter');
    const experienceFilter = document.getElementById('experience-filter');
    const postJobBtn = document.getElementById('post-job-btn');

    let allJobs = [];
    let filteredJobs = [];

    // Load jobs on page load
    loadJobs();

    // Event listeners
    searchBtn.addEventListener('click', filterJobs);
    jobSearch.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') filterJobs();
    });
    jobTypeFilter.addEventListener('change', filterJobs);
    experienceFilter.addEventListener('change', filterJobs);
    postJobBtn.addEventListener('click', showPostJobModal);

    async function loadJobs() {
        showLoading(true);
        try {
            const response = await apiCall('/api/jobs/list');
            if (response.ok) {
                const data = await response.json();
                allJobs = data.jobs || [];
                filteredJobs = [...allJobs];
                displayJobs(filteredJobs);
            } else {
                showToast('Failed to load jobs', 'error');
            }
        } catch (error) {
            console.error('Error loading jobs:', error);
            showToast('Error loading jobs', 'error');
        } finally {
            showLoading(false);
        }
    }

    function filterJobs() {
        const searchTerm = jobSearch.value.toLowerCase().trim();
        const jobType = jobTypeFilter.value;
        const experience = experienceFilter.value;

        filteredJobs = allJobs.filter(job => {
            const matchesSearch = !searchTerm || 
                job.title.toLowerCase().includes(searchTerm) ||
                job.company.toLowerCase().includes(searchTerm) ||
                job.description.toLowerCase().includes(searchTerm);
            
            const matchesJobType = !jobType || job.job_type === jobType;
            const matchesExperience = !experience || job.experience_level === experience;

            return matchesSearch && matchesJobType && matchesExperience;
        });

        displayJobs(filteredJobs);
    }

    function displayJobs(jobs) {
        if (jobs.length === 0) {
            jobListings.classList.add('hidden');
            noJobs.classList.remove('hidden');
            return;
        }

        noJobs.classList.add('hidden');
        jobListings.classList.remove('hidden');

        jobListings.innerHTML = jobs.map(job => `
            <div class="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
                <div class="flex justify-between items-start mb-4">
                    <div class="flex-1">
                        <h3 class="text-xl font-semibold text-slate-900 mb-2">${job.title}</h3>
                        <p class="text-indigo-600 font-medium mb-1">${job.company}</p>
                        <div class="flex items-center space-x-4 text-sm text-slate-500">
                            <span><i data-lucide="map-pin" class="inline w-4 h-4 mr-1"></i>${job.location || 'Remote'}</span>
                            <span><i data-lucide="briefcase" class="inline w-4 h-4 mr-1"></i>${job.job_type || 'Full-time'}</span>
                            <span><i data-lucide="trending-up" class="inline w-4 h-4 mr-1"></i>${job.experience_level || 'Mid Level'}</span>
                        </div>
                    </div>
                    <div class="text-right">
                        <span class="inline-block px-3 py-1 bg-green-100 text-green-800 text-sm font-medium rounded-full">
                            ${job.status === 'active' ? 'Open' : job.status}
                        </span>
                        <p class="text-sm text-slate-500 mt-2">
                            Posted ${formatDate(job.created_at)}
                        </p>
                    </div>
                </div>
                
                <p class="text-slate-600 mb-4 line-clamp-3">${job.description}</p>
                
                ${job.skills_required ? `
                <div class="mb-4">
                    <p class="text-sm font-medium text-slate-700 mb-2">Required Skills:</p>
                    <div class="flex flex-wrap gap-2">
                        ${job.skills_required.split(',').slice(0, 5).map(skill => 
                            `<span class="px-2 py-1 bg-slate-100 text-slate-700 text-xs rounded">${skill.trim()}</span>`
                        ).join('')}
                    </div>
                </div>
                ` : ''}
                
                ${job.salary_range ? `
                <p class="text-sm text-slate-600 mb-4">
                    <i data-lucide="dollar-sign" class="inline w-4 h-4 mr-1"></i>
                    ${job.salary_range}
                </p>
                ` : ''}
                
                <div class="flex justify-between items-center">
                    <button onclick="viewJob(${job.id})" class="text-indigo-600 hover:text-indigo-800 font-medium">
                        View Details →
                    </button>
                    ${job.application_url ? `
                    <a href="${job.application_url}" target="_blank" class="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition">
                        Apply Now
                    </a>
                    ` : `
                    <button onclick="applyToJob(${job.id})" class="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition">
                        Apply Now
                    </button>
                    `}
                </div>
            </div>
        `).join('');

        // Re-initialize Lucide icons for the new content
        lucide.createIcons();
    }

    function showLoading(show) {
        if (show) {
            loading.classList.remove('hidden');
            jobListings.classList.add('hidden');
            noJobs.classList.add('hidden');
        } else {
            loading.classList.add('hidden');
        }
    }

    function formatDate(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffTime = Math.abs(now - date);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        
        if (diffDays === 1) return '1 day ago';
        if (diffDays < 7) return `${diffDays} days ago`;
        if (diffDays < 30) return `${Math.ceil(diffDays / 7)} weeks ago`;
        return date.toLocaleDateString();
    }

    function showPostJobModal() {
        // Check if user is logged in
        const token = localStorage.getItem('token');
        if (!token) {
            showToast('Please log in to post a job', 'error');
            return;
        }
        
        // TODO: Implement job posting modal
        showToast('Job posting feature coming soon!');
    }

    // Global functions for job interactions
    window.viewJob = (jobId) => {
        // TODO: Implement job detail modal or page
        showToast('Job details feature coming soon!');
    };

    window.applyToJob = (jobId) => {
        const token = localStorage.getItem('token');
        if (!token) {
            showToast('Please log in to apply for jobs', 'error');
            return;
        }
        
        // TODO: Implement job application
        showToast('Job application feature coming soon!');
    };
});
