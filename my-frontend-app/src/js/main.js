// This file is intentionally left blank.
function getToken() {
    return localStorage.getItem('access_token');
}

function fetchWithAuth(url, options = {}) {
    const token = getToken();
    options.headers = options.headers || {};
    if (token) {
        options.headers['Authorization'] = 'Bearer ' + token;
    }
    return fetch(url, options);
}

function parseJwt (token) {
    try {
        return JSON.parse(atob(token.split('.')[1]));
    } catch (e) {
        return null;
    }
}

function getUserRole() {
    const token = getToken();
    if (!token) return null;
    const payload = parseJwt(token);
    return payload && payload.role;
}

// Example: Fetch current user info (protected route)
document.addEventListener('DOMContentLoaded', function() {
    const role = getUserRole();
    if (role) {
        if (role === 'Distributor') {
            document.body.classList.add('role-distributor');
        } else if (role === 'Retailer') {
            document.body.classList.add('role-retailer');
        }
    }
    // Example: Fetch inventory valuation analytics
    if (window.location.pathname.endsWith('index.html')) {
        fetchWithAuth('http://localhost:8000/api/analytics/inventory-valuation')
            .then(res => res.json())
            .then(data => {
                if (data.total_value !== undefined) {
                    document.body.insertAdjacentHTML('beforeend', `<div class='alert alert-info'>Total Inventory Value: ₹${data.total_value}</div>`);
                }
            });
    }
    if (window.location.pathname.endsWith('index.html')) {
        fetchWithAuth('http://localhost:8000/api/me')
            .then(res => res.json())
            .then(user => {
                if (user.username) {
                    document.body.insertAdjacentHTML('afterbegin', `<div class='alert alert-success'>Welcome, ${user.username}!</div>`);
                } else {
                    window.location.href = 'login.html';
                }
            })
            .catch(() => {
                window.location.href = 'login.html';
            });
    }
});

// Dashboard: Show near-expiry batches
function showNearExpiryBatches() {
    fetchWithAuth('http://localhost:8000/api/analytics/near-expiry-batches?days=15')
        .then(res => res.json())
        .then(batches => {
            if (Array.isArray(batches) && batches.length > 0) {
                let html = `<h5>Near-Expiry Batches (next 15 days)</h5><table class='table table-sm'><thead><tr><th>Batch ID</th><th>Product ID</th><th>Expiry</th><th>Qty</th><th>QC</th></tr></thead><tbody>`;
                batches.forEach(b => {
                    html += `<tr><td>${b.batch_id}</td><td>${b.product_id}</td><td>${b.expiry_date}</td><td>${b.current_quantity}</td><td>${b.qc_status}</td></tr>`;
                });
                html += '</tbody></table>';
                document.body.insertAdjacentHTML('beforeend', html);
            }
        });
}

// Dashboard: Show stock by category
function showStockByCategory() {
    fetchWithAuth('http://localhost:8000/api/analytics/stock-by-category')
        .then(res => res.json())
        .then(data => {
            if (Array.isArray(data) && data.length > 0) {
                let html = `<h5>Stock by Category</h5><table class='table table-sm'><thead><tr><th>Category</th><th>Total Qty</th></tr></thead><tbody>`;
                data.forEach(row => {
                    html += `<tr><td>${row.category}</td><td>${row.total_quantity}</td></tr>`;
                });
                html += '</tbody></table>';
                document.body.insertAdjacentHTML('beforeend', html);
            }
        });
}

// Dashboard: FEFO batch picking example
function pickBatchFEFO(productId, quantity) {
    fetchWithAuth(`http://localhost:8000/api/pick-batch/fefo?product_id=${productId}&quantity=${quantity}`)
        .then(res => res.json())
        .then(data => {
            if (data.picked) {
                let html = `<h5>FEFO Batch Picking</h5><ul class='list-group'>`;
                data.picked.forEach(pick => {
                    html += `<li class='list-group-item'>Batch: ${pick.batch_id}, Expiry: ${pick.expiry_date}, Qty: ${pick.pick_quantity}</li>`;
                });
                html += '</ul>';
                document.body.insertAdjacentHTML('beforeend', html);
            } else if (data.error) {
                document.body.insertAdjacentHTML('beforeend', `<div class='alert alert-warning'>${data.error}</div>`);
            }
        });
}

document.addEventListener('DOMContentLoaded', function() {
    // ...existing code...
    if (window.location.pathname.endsWith('index.html')) {
        showNearExpiryBatches();
        showStockByCategory();
        // Example: FEFO picking for product_id=1, quantity=10
        pickBatchFEFO(1, 10);
    }
});