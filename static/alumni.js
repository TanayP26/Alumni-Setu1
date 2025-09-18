document.addEventListener('DOMContentLoaded', () => {
    const alumniGrid = document.getElementById('alumni-grid');
    const loadingAlumni = document.getElementById('loading-alumni');
    const noAlumni = document.getElementById('no-alumni');
    const searchAlumniBtn = document.getElementById('search-alumni-btn');
    const alumniSearch = document.getElementById('alumni-search');
    const graduationYearFilter = document.getElementById('graduation-year-filter');
    const departmentFilter = document.getElementById('department-filter');

    let allAlumni = [];
    let filteredAlumni = [];

    // Load alumni on page load
    loadAlumni();
    loadFilterOptions();

    // Event listeners
    searchAlumniBtn.addEventListener('click', filterAlumni);
    alumniSearch.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') filterAlumni();
    });
    graduationYearFilter.addEventListener('change', filterAlumni);
    departmentFilter.addEventListener('change', filterAlumni);

    async function loadAlumni() {
        showLoading(true);
        try {
            const response = await apiCall('/api/alumni/list');
            if (response.ok) {
                const data = await response.json();
                allAlumni = data.alumni || [];
                filteredAlumni = [...allAlumni];
                displayAlumni(filteredAlumni);
            } else {
                showToast('Failed to load alumni directory', 'error');
            }
        } catch (error) {
            console.error('Error loading alumni:', error);
            showToast('Error loading alumni directory', 'error');
        } finally {
            showLoading(false);
        }
    }

    async function loadFilterOptions() {
        try {
            // Load graduation years
            const years = [...new Set(allAlumni.map(alumni => alumni.graduation_year).filter(year => year))]
                .sort((a, b) => b - a);
            
            graduationYearFilter.innerHTML = '<option value="">All Years</option>' +
                years.map(year => `<option value="${year}">${year}</option>`).join('');

            // Load departments
            const departments = [...new Set(allAlumni.map(alumni => alumni.department).filter(dept => dept))]
                .sort();
            
            departmentFilter.innerHTML = '<option value="">All Departments</option>' +
                departments.map(dept => `<option value="${dept}">${dept}</option>`).join('');

        } catch (error) {
            console.error('Error loading filter options:', error);
        }
    }

    function filterAlumni() {
        const searchTerm = alumniSearch.value.toLowerCase().trim();
        const graduationYear = graduationYearFilter.value;
        const department = departmentFilter.value;

        filteredAlumni = allAlumni.filter(alumni => {
            const fullName = `${alumni.first_name} ${alumni.last_name}`.toLowerCase();
            const matchesSearch = !searchTerm || 
                fullName.includes(searchTerm) ||
                (alumni.current_company && alumni.current_company.toLowerCase().includes(searchTerm)) ||
                (alumni.current_position && alumni.current_position.toLowerCase().includes(searchTerm));
            
            const matchesYear = !graduationYear || alumni.graduation_year == graduationYear;
            const matchesDepartment = !department || alumni.department === department;

            return matchesSearch && matchesYear && matchesDepartment;
        });

        displayAlumni(filteredAlumni);
    }

    function displayAlumni(alumni) {
        if (alumni.length === 0) {
            alumniGrid.classList.add('hidden');
            noAlumni.classList.remove('hidden');
            return;
        }

        noAlumni.classList.add('hidden');
        alumniGrid.classList.remove('hidden');

        alumniGrid.innerHTML = alumni.map(person => `
            <div class="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
                <div class="text-center mb-4">
                    <img src="${person.profile_picture || '/static/profile_placeholder.png'}" 
                         alt="${person.first_name} ${person.last_name}" 
                         class="w-20 h-20 rounded-full mx-auto mb-3 object-cover">
                    <h3 class="text-lg font-semibold text-slate-900">
                        ${person.first_name} ${person.last_name}
                    </h3>
                    ${person.current_position && person.current_company ? `
                    <p class="text-indigo-600 font-medium text-sm">
                        ${person.current_position} at ${person.current_company}
                    </p>
                    ` : ''}
                </div>

                <div class="space-y-2 mb-4">
                    ${person.graduation_year ? `
                    <div class="flex items-center text-sm text-slate-600">
                        <i data-lucide="graduation-cap" class="w-4 h-4 mr-2"></i>
                        Class of ${person.graduation_year}
                    </div>
                    ` : ''}
                    
                    ${person.department ? `
                    <div class="flex items-center text-sm text-slate-600">
                        <i data-lucide="book" class="w-4 h-4 mr-2"></i>
                        ${person.department}
                    </div>
                    ` : ''}
                    
                    ${person.city && person.country ? `
                    <div class="flex items-center text-sm text-slate-600">
                        <i data-lucide="map-pin" class="w-4 h-4 mr-2"></i>
                        ${person.city}, ${person.country}
                    </div>
                    ` : ''}
                </div>

                ${person.bio ? `
                <p class="text-sm text-slate-600 mb-4 line-clamp-3">${person.bio}</p>
                ` : ''}

                ${person.skills ? `
                <div class="mb-4">
                    <div class="flex flex-wrap gap-1">
                        ${JSON.parse(person.skills || '[]').slice(0, 3).map(skill => 
                            `<span class="px-2 py-1 bg-slate-100 text-slate-600 text-xs rounded">${skill}</span>`
                        ).join('')}
                        ${JSON.parse(person.skills || '[]').length > 3 ? 
                            `<span class="px-2 py-1 bg-slate-100 text-slate-600 text-xs rounded">+${JSON.parse(person.skills).length - 3}</span>` : ''
                        }
                    </div>
                </div>
                ` : ''}

                <div class="flex space-x-2">
                    <button onclick="viewProfile(${person.id})" 
                            class="flex-1 bg-slate-100 text-slate-700 px-3 py-2 rounded-lg hover:bg-slate-200 transition text-sm font-medium">
                        View Profile
                    </button>
                    <button onclick="sendMessage(${person.id})" 
                            class="flex-1 bg-indigo-600 text-white px-3 py-2 rounded-lg hover:bg-indigo-700 transition text-sm font-medium">
                        Message
                    </button>
                </div>
            </div>
        `).join('');

        // Re-initialize Lucide icons for the new content
        lucide.createIcons();
    }

    function showLoading(show) {
        if (show) {
            loadingAlumni.classList.remove('hidden');
            alumniGrid.classList.add('hidden');
            noAlumni.classList.add('hidden');
        } else {
            loadingAlumni.classList.add('hidden');
        }
    }

    // Global functions for alumni interactions
    window.viewProfile = (alumniId) => {
        window.location.href = `/alumni/${alumniId}`;
    };

    window.sendMessage = (alumniId) => {
        const token = localStorage.getItem('token');
        if (!token) {
            showToast('Please log in to send messages', 'error');
            return;
        }
        
        window.location.href = `/messaging?to=${alumniId}`;
    };
});
