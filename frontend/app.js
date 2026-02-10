const API = window.location.origin;
let token = localStorage.getItem("token");
let currentUser = null;
let userPermissions = [];
let editingPdfId = null;

/* ---------- AUTH GUARD ---------- */
if (!token && location.pathname.includes("dashboard.html")) {
  location.href = "/static/index.html";
}

function authHeaders() {
  return { Authorization: "Bearer " + token };
}

/* ---------- LOGIN ---------- */
async function login() {
  const username = document.getElementById("loginUsername").value;
  const password = document.getElementById("loginPassword").value;
  const msg = document.getElementById("msg");
  msg.textContent = "";

  const res = await fetch(`${API}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password })
  });

  if (!res.ok) {
    msg.textContent = "Invalid username or password";
    msg.className = "error";
    return;
  }

  const data = await res.json();
  localStorage.setItem("token", data.access_token);
  location.href = "/static/dashboard.html";
}

/* ---------- SIGNUP ---------- */
async function register() {
  const username = document.getElementById("signup_username").value;
  const email = document.getElementById("signup_email").value;
  const password = document.getElementById("signup_password").value;
  const msg = document.getElementById("msg");
  const btn = document.querySelector("#signupForm .btn");
  
  // Clear previous messages
  msg.textContent = "";
  msg.className = "";

  if (!username || !email || !password) {
    msg.textContent = "❌ Please fill all fields";
    msg.className = "error";
    return;
  }

  // Show loading state
  btn.disabled = true;
  btn.textContent = "Creating account...";
  msg.textContent = "";

  try {
    const res = await fetch(`${API}/users`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, email, password })
    });

    console.log("Signup response status:", res.status, "ok:", res.ok);
    
    // Check if successful BEFORE parsing JSON
    // (Some responses might be 200 but have invalid JSON)
    if (res.ok) {
      console.log("Signup successful (status check)!");
      msg.textContent = "✓ Account created successfully! Redirecting to login...";
      msg.className = "success";
      
      // Clear form fields
      document.getElementById("signup_username").value = "";
      document.getElementById("signup_email").value = "";
      document.getElementById("signup_password").value = "";
      document.getElementById("loginUsername").value = username;
      
      // Auto-switch to login tab after 2 seconds
      setTimeout(() => {
        showLogin();
        msg.textContent = "";
        btn.disabled = false;
        btn.textContent = "Sign Up";
      }, 2000);
      return;
    }

    // Handle error response
    let errorMsg = "Signup failed";
    try {
      const data = await res.json();
      console.log("Signup response data:", data);
      if (data.detail) {
        errorMsg = typeof data.detail === "string" ? data.detail : "Invalid request";
      }
    } catch (e) {
      console.log("Failed to parse error response as JSON:", e);
    }

    console.log("Signup failed - showing error:", errorMsg);
    msg.textContent = "❌ " + errorMsg;
    msg.className = "error";
    btn.disabled = false;
    btn.textContent = "Sign Up";
  } catch (err) {
    console.error("Signup error:", err);
    msg.textContent = "❌ Network error. Please check your connection and try again.";
    msg.className = "error";
    btn.disabled = false;
    btn.textContent = "Sign Up";
  }
}

/* ---------- LOGOUT ---------- */
function logout() {
  localStorage.clear();
  location.href = "/static/index.html";
}

/* ---------- INIT DASHBOARD ---------- */
document.addEventListener("DOMContentLoaded", async () => {
  if (!location.pathname.includes("dashboard.html")) return;
  try {
    await loadUser();
    await loadPermissions();
    await loadPDFs();
    await loadUserManagementIfSuperAdmin();
  } catch (err) {
    console.error("Error loading dashboard:", err);
    logout();
  }
});

/* ---------- LOAD USER ---------- */
async function loadUser() {
  const res = await fetch(`${API}/users/me`, { headers: authHeaders() });
  if (!res.ok) return logout();

  currentUser = await res.json();
  
  document.getElementById("dashboardUsername").textContent = currentUser.username;
  console.log('loadUser -> server roles:', currentUser.roles);

  // If backend returns explicit roles, use them to display the role immediately
  const roles = currentUser.roles || [];
  if (roles.length) {
    let roleLabel = "USER";
    if (roles.includes("super_admin")) roleLabel = "SUPER ADMIN";
    else if (roles.includes("admin")) roleLabel = "ADMIN";
    document.getElementById("dashboardRole").textContent = roleLabel;
  }
}

/* ---------- LOAD PERMISSIONS ---------- */
async function loadPermissions() {
  const res = await fetch(`${API}/users/me/permissions`, {
    headers: authHeaders()
  });

  userPermissions = res.ok ? (await res.json()).map(p => p.name) : [];
  console.log('loadPermissions -> permissions:', userPermissions);
  
  // If backend already provided explicit roles, don't override them with permission inference
  const existingRoles = (currentUser && currentUser.roles) ? currentUser.roles : [];
  if (!existingRoles || existingRoles.length === 0) {
    // Determine role from permissions
    let roleLabel = "USER";
    if (userPermissions.includes("DELETE")) roleLabel = "SUPER ADMIN";
    else if (userPermissions.includes("UPDATE")) roleLabel = "ADMIN";

    document.getElementById("dashboardRole").textContent = roleLabel;
  }
  
  // Show/hide upload section based on CREATE permission
  const uploadSection = document.getElementById("uploadSection");
  if (uploadSection) {
    uploadSection.style.display = userPermissions.includes("CREATE") ? "block" : "none";
  }
}

/* ---------- LOAD PDFs ---------- */
async function loadPDFs() {
  const pdfGrid = document.getElementById("pdfGrid");
  const emptyState = document.getElementById("emptyState");
  
  pdfGrid.innerHTML = "";

  const res = await fetch(`${API}/api/pdf/`, { headers: authHeaders() });

  if (!res.ok) {
    emptyState.textContent = "No permission to view PDFs";
    emptyState.style.display = "block";
    return;
  }

  const pdfs = await res.json();
  if (!pdfs.length) {
    emptyState.textContent = "No PDFs available";
    emptyState.style.display = "block";
    return;
  }

  emptyState.style.display = "none";

  pdfs.forEach(pdf => {
    const card = document.createElement("div");
    card.className = "pdf-card";
    
    // Determine which buttons to show based on permissions
    // If the current user is an 'admin', show the delete button as disabled
    const isAdmin = currentUser && currentUser.roles && currentUser.roles.includes("admin");

    let actionButtons = `
      <div class="pdf-actions">
        <button class="btn-sm btn-read" onclick="readPDF(${pdf.id})">📥 Read</button>
    `;
    
    if (userPermissions.includes("UPDATE")) {
      actionButtons += `<button class="btn-sm btn-edit" onclick="editPDF(${pdf.id}, '${pdf.title.replace(/'/g, "\\'")}')">✏️ Edit</button>`;
    }
    
    // Prevent admin from seeing an active delete button; show disabled (not-allowed cursor)
    if (userPermissions.includes("DELETE") && !isAdmin) {
      actionButtons += `<button class="btn-sm btn-delete" onclick="deletePDF(${pdf.id})">🗑️ Delete</button>`;
    } else {
      actionButtons += `<button class="btn-sm btn-delete" disabled>🗑️ Delete</button>`;
    }
    
    actionButtons += `</div>`;

    card.innerHTML = `
      <h3>${escapeHtml(pdf.title)}</h3>
      <div class="pdf-meta">
        <div class="pdf-uploader">
          This was uploaded by <span class="uploader-badge">${pdf.uploader_role}</span>
        </div>
        <div>👤 ${escapeHtml(pdf.uploader_name)}</div>
      </div>
      ${actionButtons}
    `;
    
    pdfGrid.appendChild(card);
  });
}

/* ---------- UPLOAD PDF ---------- */
async function uploadPDF() {
  const pdfTitle = document.getElementById("pdfTitle");
  const pdfFile = document.getElementById("pdfFile");
  const uploadMsg = document.getElementById("uploadMsg");
  
  uploadMsg.className = "";
  uploadMsg.textContent = "";

  if (!pdfTitle.value || !pdfFile.files[0]) {
    uploadMsg.textContent = "Please enter a title and select a file";
    uploadMsg.className = "upload-msg error";
    return;
  }

  const form = new FormData();
  form.append("title", pdfTitle.value);
  form.append("file", pdfFile.files[0]);

  const res = await fetch(`${API}/api/pdf/upload`, {
    method: "POST",
    headers: authHeaders(),
    body: form
  });

  if (!res.ok) {
    uploadMsg.textContent = "Upload failed (permission denied or file error)";
    uploadMsg.className = "upload-msg error";
    return;
  }

  uploadMsg.textContent = "✓ PDF uploaded successfully!";
  uploadMsg.className = "upload-msg success";
  pdfTitle.value = "";
  pdfFile.value = "";
  
  setTimeout(() => {
    loadPDFs();
  }, 500);
}

/* ---------- READ PDF ---------- */
async function readPDF(id) {
  try {
    const res = await fetch(`${API}/api/pdf/${id}/download`, {
      headers: authHeaders()
    });

    if (!res.ok) {
      alert('Failed to download PDF (permission or server error)');
      return;
    }

    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    window.open(url, '_blank');
    // revoke after some time
    setTimeout(() => URL.revokeObjectURL(url), 10000);
  } catch (err) {
    console.error('Download error:', err);
    alert('Error downloading PDF');
  }
}

/* ---------- EDIT PDF ---------- */
function editPDF(id, currentTitle) {
  const newTitle = prompt("Enter new title:", currentTitle);
  if (!newTitle || newTitle === currentTitle) return;

  updatePDF(id, newTitle);
}

async function updatePDF(id, newTitle) {
  const form = new FormData();
  form.append("title", newTitle);

  const res = await fetch(`${API}/api/pdf/${id}`, {
    method: "PUT",
    headers: authHeaders(),
    body: form
  });

  if (!res.ok) {
    alert("Failed to update PDF");
    return;
  }

  alert("PDF updated successfully!");
  loadPDFs();
}

/* ---------- DELETE PDF ---------- */
async function deletePDF(id) {
  if (!confirm("Are you sure you want to delete this PDF?")) return;

  const res = await fetch(`${API}/api/pdf/${id}`, {
    method: "DELETE",
    headers: authHeaders()
  });

  if (!res.ok) {
    alert("Failed to delete PDF (permission denied)");
    return;
  }

  alert("PDF deleted successfully!");
  loadPDFs();
}

/* ---------- USER MANAGEMENT (super_admin only) ---------- */
let userListRefreshInterval = null;

async function loadUserManagementIfSuperAdmin() {
  if (!currentUser || !currentUser.roles) return;
  
  if (!currentUser.roles.includes("super_admin")) {
    document.getElementById("userManagementSection").style.display = "none";
    return;
  }

  // Super admin - show user management section
  document.getElementById("userManagementSection").style.display = "block";
  await loadUsersList();
  
  // Auto-refresh user list every 2 seconds to show newly signed up users
  if (userListRefreshInterval) clearInterval(userListRefreshInterval);
  userListRefreshInterval = setInterval(loadUsersList, 2000);
}

async function loadUsersList() {
  const res = await fetch(`${API}/admin/users`, { headers: authHeaders() });
  if (!res.ok) {
    console.error("Failed to load users list");
    return;
  }

  const users = await res.json();
  const tbody = document.getElementById("usersTableBody");
  tbody.innerHTML = "";

  users.forEach(user => {
    const userRoles = user.roles || [];
    const currentRole = userRoles.length > 0 ? userRoles[0] : "user";
    
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${escapeHtml(user.username)}</td>
      <td>${escapeHtml(user.email)}</td>
      <td>
        <select id="roleSelect_${user.id}" onchange="handleRoleChange(${user.id}, this.value)">
          <option value="user" ${currentRole === "user" ? "selected" : ""}>User</option>
          <option value="admin" ${currentRole === "admin" ? "selected" : ""}>Admin</option>
          <option value="super_admin" ${currentRole === "super_admin" ? "selected" : ""}>Super Admin</option>
        </select>
      </td>
      <td>
        <div class="user-actions">
          <button class="btn-change-role" onclick="handleRoleChange(${user.id}, document.getElementById('roleSelect_${user.id}').value)">
            ✓ Update Role
          </button>
          <button class="btn-remove-user" onclick="handleDeleteUser(${user.id}, '${escapeHtml(user.username)}')">
            🗑️ Delete User
          </button>
        </div>
      </td>
    `;
    tbody.appendChild(row);
  });
}

async function handleRoleChange(userId, newRole) {
  if (!newRole) return;

  const res = await fetch(`${API}/admin/users/${userId}/set_role?role_name=${newRole}`, {
    method: "POST",
    headers: authHeaders()
  });

  if (!res.ok) {
    alert("Failed to change role");
    return;
  }

  const data = await res.json();
  alert(data.message);
  await loadUsersList();
}

async function handleDeleteUser(userId, username) {
  if (!confirm(`Are you sure you want to delete user "${username}"?`)) return;

  const res = await fetch(`${API}/admin/users/${userId}`, {
    method: "DELETE",
    headers: authHeaders()
  });

  if (!res.ok) {
    alert("Failed to delete user");
    return;
  }

  const data = await res.json();
  alert(data.message);
  await loadUsersList();
}

/* ---------- UTILITY FUNCTIONS ---------- */
function escapeHtml(text) {
  const map = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;"
  };
  return text.replace(/[&<>"']/g, m => map[m]);
}
