// UX Enhancements for WMS Dashboards
// 1. Role-based redirect
function roleRedirect() {
    const token = localStorage.getItem('access_token');
    if (!token) return window.location.href = 'login.html';
    const payload = JSON.parse(atob(token.split('.')[1]));
    if (window.location.pathname.endsWith('index.html') || window.location.pathname === '/' || window.location.pathname === '') {
        if (payload.role === 'Distributor') window.location.href = 'distributor.html';
        else if (payload.role === 'Retailer') window.location.href = 'retailer.html';
    }
}
roleRedirect();

// 2. Active nav highlight
function highlightNav() {
    const navLinks = document.querySelectorAll('.wms-nav a');
    navLinks.forEach(link => {
        if (window.location.pathname.endsWith(link.getAttribute('href'))) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
}
document.addEventListener('DOMContentLoaded', highlightNav);

// 3. User profile dropdown
function addProfileDropdown() {
    const token = localStorage.getItem('access_token');
    if (!token) return;
    const payload = JSON.parse(atob(token.split('.')[1]));
    let profile = document.getElementById('profileDropdown');
    if (!profile) {
        profile = document.createElement('div');
        profile.id = 'profileDropdown';
        profile.className = 'dropdown position-absolute top-0 end-0 m-3';
        profile.innerHTML = `
        <button class="btn btn-light dropdown-toggle" type="button" data-bs-toggle="dropdown" aria-expanded="false">
            <i class="fa fa-user"></i> ${payload.username || payload.sub}
        </button>
        <ul class="dropdown-menu dropdown-menu-end">
            <li><span class="dropdown-item-text"><b>Role:</b> ${payload.role}</span></li>
            <li><hr class="dropdown-divider"></li>
            <li><a class="dropdown-item" href="#" id="logoutLink">Logout</a></li>
        </ul>`;
        document.body.appendChild(profile);
        document.getElementById('logoutLink').onclick = function() {
            localStorage.removeItem('access_token');
            window.location.href = 'login.html';
        };
    }
}
document.addEventListener('DOMContentLoaded', addProfileDropdown);

// 4. Responsive tables
function makeTablesResponsive() {
    document.querySelectorAll('table').forEach(table => {
        if (!table.parentElement.classList.contains('table-responsive')) {
            const wrapper = document.createElement('div');
            wrapper.className = 'table-responsive';
            table.parentNode.insertBefore(wrapper, table);
            wrapper.appendChild(table);
        }
    });
}
document.addEventListener('DOMContentLoaded', makeTablesResponsive);

// 5. Toasts and loaders (global)
function showWmsToast(msg, type='info') {
    let toast = document.getElementById('wms-toast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'wms-toast';
        toast.className = 'toast position-fixed top-0 end-0 m-3';
        toast.style.zIndex = 3000;
        toast.innerHTML = `<div class="toast-body"></div>`;
        document.body.appendChild(toast);
    }
    toast.querySelector('.toast-body').textContent = msg;
    toast.className = `toast position-fixed top-0 end-0 m-3 text-bg-${type}`;
    toast.style.display = 'block';
    setTimeout(() => { toast.style.display = 'none'; }, 3500);
}
function showWmsLoader(show=true) {
    let loader = document.getElementById('wms-loader');
    if (!loader && show) {
        loader = document.createElement('div');
        loader.id = 'wms-loader';
        loader.innerHTML = `<div class="position-fixed top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center bg-white bg-opacity-75" style="z-index: 2000;">
            <div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div>
        </div>`;
        document.body.appendChild(loader);
    }
    if (loader) loader.style.display = show ? 'block' : 'none';
}

// 6. Error handling (global fetch wrapper)
window.fetchWms = function(url, options={}) {
    showWmsLoader(true);
    const token = localStorage.getItem('access_token');
    options.headers = options.headers || {};
    if (token) options.headers['Authorization'] = 'Bearer ' + token;
    return fetch(url, options)
        .then(res => {
            showWmsLoader(false);
            if (!res.ok) {
                if (res.status === 401) window.location.href = 'login.html';
                return res.json().then(e => { throw new Error(e.detail || 'API error'); });
            }
            return res.json();
        })
        .catch(e => {
            showWmsLoader(false);
            showWmsToast(e.message || 'Network error', 'danger');
            throw e;
        });
};

// 7. Dashboard summaries (example for distributor/retailer)
window.renderSummaryCards = function(cards, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    let html = '<div class="row g-3">';
    cards.forEach(card => {
        html += `<div class="col-md-4"><div class="card dashboard-card text-white bg-${card.color} mb-3"><div class="card-body text-center"><div class="summary-icon"><i class="${card.icon}"></i></div><h5 class="card-title">${card.title}</h5><p class="card-text fs-4 fw-bold">${card.value}</p></div></div></div>`;
    });
    html += '</div>';
    container.innerHTML = html;
};

// 8. Search/filter for tables
window.addTableFilter = function(tableId, inputId) {
    const input = document.getElementById(inputId);
    const table = document.getElementById(tableId);
    if (!input || !table) return;
    input.addEventListener('input', function() {
        const val = input.value.toLowerCase();
        table.querySelectorAll('tbody tr').forEach(row => {
            row.style.display = row.textContent.toLowerCase().includes(val) ? '' : 'none';
        });
    });
};

// 9. Pagination for tables
window.paginateTable = function(tableId, pageSize=10) {
    const table = document.getElementById(tableId);
    if (!table) return;
    const rows = Array.from(table.querySelectorAll('tbody tr'));
    let page = 0;
    function renderPage() {
        rows.forEach((row, i) => {
            row.style.display = (i >= page*pageSize && i < (page+1)*pageSize) ? '' : 'none';
        });
    }
    renderPage();
    // Add pagination controls
    let controls = document.getElementById(tableId+'-pagination');
    if (!controls) {
        controls = document.createElement('div');
        controls.id = tableId+'-pagination';
        controls.className = 'my-2';
        table.parentNode.appendChild(controls);
    }
    controls.innerHTML = `<button class='btn btn-sm btn-outline-primary me-2' ${page===0?'disabled':''}>Prev</button><button class='btn btn-sm btn-outline-primary' ${((page+1)*pageSize>=rows.length)?'disabled':''}>Next</button>`;
    controls.querySelectorAll('button')[0].onclick = function() { if (page>0) { page--; renderPage(); } };
    controls.querySelectorAll('button')[1].onclick = function() { if ((page+1)*pageSize<rows.length) { page++; renderPage(); } };
};

// 10. Dark mode toggle
function addDarkModeToggle() {
    let toggle = document.getElementById('darkModeToggle');
    if (!toggle) {
        toggle = document.createElement('button');
        toggle.id = 'darkModeToggle';
        toggle.className = 'btn btn-outline-dark position-fixed bottom-0 end-0 m-3';
        toggle.innerHTML = '<i class="fa fa-moon"></i> Dark Mode';
        document.body.appendChild(toggle);
        toggle.onclick = function() {
            document.body.classList.toggle('dark-mode');
            if (document.body.classList.contains('dark-mode')) {
                toggle.innerHTML = '<i class="fa fa-sun"></i> Light Mode';
            } else {
                toggle.innerHTML = '<i class="fa fa-moon"></i> Dark Mode';
            }
        };
    }
}
document.addEventListener('DOMContentLoaded', addDarkModeToggle);

// Debug: Integration check for all UX features
window.addEventListener('DOMContentLoaded', function() {
    // 1. Role redirect check
    if (!localStorage.getItem('access_token')) {
        console.warn('UX.js: No access_token found, redirect expected.');
    } else {
        const payload = JSON.parse(atob(localStorage.getItem('access_token').split('.')[1]));
        console.info('UX.js: User role is', payload.role);
    }
    // 2. Nav highlight check
    if (document.querySelector('.wms-nav')) {
        console.info('UX.js: .wms-nav found, nav highlight enabled.');
    } else {
        console.warn('UX.js: .wms-nav not found, nav highlight skipped.');
    }
    // 3. Profile dropdown check
    if (document.getElementById('profileDropdown')) {
        console.info('UX.js: Profile dropdown present.');
    } else {
        console.warn('UX.js: Profile dropdown missing.');
    }
    // 4. Responsive tables check
    if (document.querySelector('table')) {
        console.info('UX.js: Table(s) found, responsive wrapper applied.');
    } else {
        console.warn('UX.js: No tables found on this page.');
    }
    // 5. Toast/Loader test
    showWmsToast('UX.js: Toast test (info)', 'info');
    showWmsLoader(true); setTimeout(() => showWmsLoader(false), 1000);
    // 6. fetchWms test (API call)
    if (typeof fetchWms === 'function') {
        fetchWms('/static/favicon.ico').then(() => {
            console.info('UX.js: fetchWms test (favicon) succeeded.');
        }).catch(() => {
            console.warn('UX.js: fetchWms test (favicon) failed.');
        });
    }
    // 7. Summary cards test (if container exists)
    if (document.getElementById('testSummaryCards')) {
        renderSummaryCards([
            {title:'Test Card', value:42, color:'info', icon:'fa fa-check'}
        ], 'testSummaryCards');
        console.info('UX.js: renderSummaryCards test rendered.');
    }
    // 8. Table filter test (if table/input exists)
    if (document.getElementById('testTable') && document.getElementById('testFilter')) {
        addTableFilter('testTable', 'testFilter');
        console.info('UX.js: addTableFilter test attached.');
    }
    // 9. Pagination test (if table exists)
    if (document.getElementById('testTable')) {
        paginateTable('testTable', 5);
        console.info('UX.js: paginateTable test attached.');
    }
    // 10. Dark mode toggle check
    if (document.getElementById('darkModeToggle')) {
        console.info('UX.js: Dark mode toggle present.');
    } else {
        console.warn('UX.js: Dark mode toggle missing.');
    }
});
