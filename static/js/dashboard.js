// IT dashboard: login gate, polled live feed, hall + feature management, audit.
const $ = (id) => document.getElementById(id);
let pollTimer = null;
let activeHallId = null;
let globalFeaturesCatalog = [];

async function api(path, opts) {
  const res = await fetch(path, Object.assign({ headers: { "Content-Type": "application/json" } }, opts));
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw (typeof body.detail === "string" ? new Error(body.detail) : body);
  return body;
}

// ---------- metrics ----------
async function updateMetrics() {
  try {
    const bookings = await api("/api/admin/bookings");
    const activeBookings = bookings.filter(b => b.status === "confirmed").length;
    $("metric-bookings").textContent = activeBookings;
  } catch (e) {
    $("metric-bookings").textContent = "--";
  }

  try {
    const halls = await api("/api/admin/halls");
    const activeHalls = halls.filter(h => h.active).length;
    $("metric-halls").textContent = activeHalls;
  } catch (e) {
    $("metric-halls").textContent = "--";
  }

  try {
    const features = await api("/api/admin/features");
    $("metric-features").textContent = features.length;
  } catch (e) {
    $("metric-features").textContent = "--";
  }
}

// ---------- auth ----------
async function checkAuth() {
  try { 
    await api("/api/auth/me"); 
    enterApp(); 
  } catch { 
    showLogin(); 
  }
}

function showLogin() { 
  $("login-card").classList.remove("hidden"); 
  $("app").classList.add("hidden"); 
  $("link-logout").classList.add("hidden"); 
}

function enterApp() {
  $("login-card").classList.add("hidden"); 
  $("app").classList.remove("hidden"); 
  $("link-logout").classList.remove("hidden");
  $("live-date").value = "";
  loadLive(); 
  startPoll();
  updateMetrics();
}

$("btn-login").onclick = async () => {
  $("login-error").innerHTML = "";
  try {
    await api("/api/auth/login", { 
      method: "POST", 
      body: JSON.stringify({ username: $("l-user").value, password: $("l-pass").value }) 
    });
    enterApp();
  } catch (e) {
    $("login-error").innerHTML = `<div class="error-msg">${e.message || "Sign-in failed."}</div>`;
  }
};

$("link-logout").onclick = async (e) => { 
  e.preventDefault(); 
  await api("/api/auth/logout", { method: "POST" }); 
  stopPoll(); 
  showLogin(); 
};

// ---------- tabs ----------
document.querySelectorAll(".tab").forEach((t) => {
  t.onclick = () => {
    document.querySelectorAll(".tab").forEach((n) => n.classList.remove("active"));
    document.querySelectorAll(".tab-body").forEach((n) => n.classList.add("hidden"));
    t.classList.add("active");
    const name = t.dataset.tab;
    
    // Manage halls has specific subviews; make sure we reset back to list view
    if (name === "halls") {
      $("tab-halls").classList.remove("hidden");
      showHallsListView();
      loadHalls();
      updateMetrics();
    } else {
      const el = $("tab-" + name);
      if (el) el.classList.remove("hidden");
      if (name === "live") { loadLive(); updateMetrics(); }
      if (name === "features") { loadFeatures(); updateMetrics(); }
      if (name === "dropdowns") { loadDropdowns(); }
      if (name === "audit") { loadAudit(); }
      if (name === "settings") { loadSettings(); }
      if (name === "cancel") {
        $("dash-c-cancel-code").value = "";
        $("dash-cancel-error").innerHTML = "";
      }
      if (name === "security") {
        $("dash-security-error").innerHTML = "";
        $("dash-security-success").innerHTML = "";
        $("sec-password").value = "";
        api("/api/auth/me").then(user => {
          $("sec-username").value = user.username;
        }).catch(err => {
          $("dash-security-error").innerHTML = `<div class="error-msg">Failed to load user info.</div>`;
        });
      }
    }
  };
});

// ---------- live bookings (polled) ----------
function startPoll() { 
  stopPoll(); 
  pollTimer = setInterval(() => { 
    if (!$("tab-live").classList.contains("hidden")) {
      loadLive(true); 
      updateMetrics();
    }
  }, 5000); 
}

function stopPoll() { 
  if (pollTimer) clearInterval(pollTimer); 
  pollTimer = null; 
}

async function loadLive(quiet) {
  const q = [];
  if ($("live-date").value) q.push("on=" + $("live-date").value);
  if ($("live-status").value) q.push("status=" + $("live-status").value);
  let rows;
  try { 
    rows = await api("/api/admin/bookings" + (q.length ? "?" + q.join("&") : "")); 
  } catch { 
    showLogin(); 
    return; 
  }
  $("live-meta").textContent = `(${rows.length} bookings shown)`;
  if (!rows.length) { 
    $("live-table").innerHTML = '<p class="instructions" style="padding: 24px; text-align: center;">No active bookings found.</p>'; 
    return; 
  }
  
  $("live-table").innerHTML = `<table>
    <thead>
      <tr>
        <th>Date</th>
        <th>Hall</th>
        <th>Time</th>
        <th>Booker</th>
        <th>Designation</th>
        <th>Dept/Division</th>
        <th>Coordinator</th>
        <th>Purpose</th>
        <th>Project ID</th>
        <th>Attendees</th>
        <th>Stationery</th>
        <th>Catering</th>
        <th>Features</th>
        <th>IT Support</th>
        <th>Housekeeping</th>
        <th>Status</th>
        <th>Cancel Code</th>
        <th>Actions</th>
      </tr>
    </thead>
    <tbody>
      ${rows.map((b) => `<tr class="${b.status}">
        <td><strong>${b.date}</strong></td>
        <td><span style="font-weight: 700; color: var(--primary);">${b.hall}</span></td>
        <td>${b.start}\u2013${b.end}</td>
        <td><strong>${b.booked_by}</strong></td>
        <td>${b.scientist_designation || ""}</td>
        <td>${b.dept || ""}</td>
        <td>${b.coordinator_name || ""} ${b.coordinator_phone ? `(${b.coordinator_phone})` : ""}</td>
        <td>${b.purpose || ""}</td>
        <td><code>${b.project_id || ""}</code></td>
        <td><span class="pill">${b.attendees_count || "0"}</span></td>
        <td><span class="pill" title="${b.stationery_requested || 'None'}">${b.stationery_requested || "None"}</span></td>
        <td><span class="pill">${b.food_requested || "None"}</span></td>
        <td><span class="pill">${b.features_requested || "None"}</span></td>
        <td>${b.support_staff_requested ? '<span class="status-tag confirmed">Requested</span>' : '<span>No</span>'}</td>
        <td>${b.housekeeping_requested ? '<span class="status-tag confirmed">Requested</span>' : '<span>No</span>'}</td>
        <td><span class="status-tag ${b.status}">${b.status}</span></td>
        <td><code>${b.cancel_code || ""}</code></td>
        <td>
          ${b.status === "pending_approval" ? `
            <button class="approve-btn" data-id="${b.id}" style="background: #22c55e; color: white; border: none; padding: 4px 8px; border-radius: 4px; cursor: pointer; font-size: 11px; margin-right: 4px;">Approve</button>
            <button class="reject-btn" data-id="${b.id}" style="background: #ef4444; color: white; border: none; padding: 4px 8px; border-radius: 4px; cursor: pointer; font-size: 11px;">Reject</button>
          ` : (b.meeting_link ? `<a href="${b.meeting_link}" target="_blank" style="font-size: 11px; text-decoration: underline; font-weight: bold; color: var(--primary);">Join Meet</a>` : '-')}
        </td>
      </tr>`).join("")}
    </tbody>
  </table>`;

  // Attach handlers
  document.querySelectorAll(".approve-btn").forEach((btn) => {
    btn.onclick = async () => {
      if (confirm("Approve this booking?")) {
        try {
          await api(`/api/admin/bookings/${btn.dataset.id}/approve`, { method: "POST" });
          loadLive();
          updateMetrics();
        } catch (e) {
          alert("Error: " + (e.message || e));
        }
      }
    };
  });
  document.querySelectorAll(".reject-btn").forEach((btn) => {
    btn.onclick = async () => {
      if (confirm("Reject this booking?")) {
        try {
          await api(`/api/admin/bookings/${btn.dataset.id}/reject`, { method: "POST" });
          loadLive();
          updateMetrics();
        } catch (e) {
          alert("Error: " + (e.message || e));
        }
      }
    };
  });
}

$("live-date").onchange = () => loadLive();
$("live-status").onchange = () => loadLive();
$("live-clear").onclick = () => { 
  $("live-date").value = ""; 
  $("live-status").value = ""; 
  loadLive(); 
};

// ---------- halls list view ----------
async function loadHalls() {
  const halls = await api("/api/admin/halls");
  $("halls-table").innerHTML = `<table>
    <thead>
      <tr>
        <th>Hall Name</th>
        <th>Seat Capacity</th>
        <th>Operational Status</th>
        <th style="text-align: right;">Action</th>
      </tr>
    </thead>
    <tbody>
      ${halls.map((h) => `<tr>
        <td>
          <a href="#" class="hall-name-link" data-id="${h.id}" style="font-weight: 700; border-bottom: 1px dashed var(--primary);">
            ${h.name}
          </a>
        </td>
        <td><strong>${h.capacity}</strong> seats ${h.requires_approval ? '<span style="color: #ea580c; font-size: 11px; font-weight: 600;">(Needs Approval)</span>' : ''}</td>
        <td><span class="status-tag ${h.active ? "confirmed" : "cancelled"}">${h.active ? "active" : "archived"}</span></td>
        <td style="text-align: right;">
          <button class="ghost toggle" data-id="${h.id}" data-active="${h.active}" style="padding: 4px 10px; font-size: 12px;">
            ${h.active ? "Archive" : "Restore"}
          </button>
        </td>
      </tr>`).join("")}
    </tbody>
  </table>`;
  
  document.querySelectorAll(".hall-name-link").forEach((link) => {
    link.onclick = (e) => {
      e.preventDefault();
      openHallDetail(parseInt(link.dataset.id, 10));
    };
  });
  
  document.querySelectorAll(".toggle").forEach((b) => {
    b.onclick = async () => {
      await patchHall(b.dataset.id, { active: b.dataset.active !== "true" });
      await loadHalls();
      updateMetrics();
    };
  });
}

async function patchHall(id, body) { 
  await api(`/api/admin/halls/${id}`, { method: "PATCH", body: JSON.stringify(body) }); 
}

$("h-add").onclick = async () => {
  const name = $("h-name").value.trim(); 
  if (!name) return;
  const imageVal = $("h-image").value.trim() || null;
  const requires_approval = $("h-approval").checked;
  await api("/api/admin/halls", { 
    method: "POST", 
    body: JSON.stringify({ 
      name, 
      capacity: parseInt($("h-cap").value || "0", 10),
      image: imageVal,
      requires_approval: requires_approval
    }) 
  });
  $("h-name").value = ""; 
  $("h-cap").value = "0"; 
  $("h-image").value = "";
  $("h-approval").checked = false;
  await loadHalls();
  updateMetrics();
};

// ---------- hall detail view ----------
function showHallsListView() {
  $("halls-list-view").classList.remove("hidden");
  $("hall-detail-view").classList.add("hidden");
  activeHallId = null;
}

async function openHallDetail(hallId) {
  activeHallId = hallId;
  $("halls-list-view").classList.add("hidden");
  $("hall-detail-view").classList.remove("hidden");
  $("detail-hall-error").innerHTML = "";
  
  // Fetch details
  const halls = await api("/api/admin/halls");
  const hall = halls.find(h => h.id === hallId);
  if (!hall) {
    showHallsListView();
    return;
  }
  
  $("detail-hall-title").textContent = `Configure Room: ${hall.name}`;
  $("detail-hall-name").value = hall.name;
  $("detail-hall-cap").value = hall.capacity;
  $("detail-hall-approval").checked = !!hall.requires_approval;
  
  // Set current image preview or default placeholder
  if (hall.image) {
    $("detail-hall-img-preview").src = `/static/images/${hall.image}?t=${Date.now()}`;
  } else {
    $("detail-hall-img-preview").src = "/static/images/hall_placeholder.png";
  }
  $("detail-hall-file").value = "";
  $("detail-hall-file-name").textContent = "";
  $("btn-detail-upload-img").disabled = true;
  
  // Load global feature catalog
  globalFeaturesCatalog = await api("/api/admin/features");
  
  // Populate the assign features select dropdown
  const assignSelect = $("detail-assign-feat");
  assignSelect.innerHTML = '<option value="">-- Choose Feature --</option>' + 
    globalFeaturesCatalog.map(f => f.active ? `<option value="${f.id}">${f.name} (${f.value_type})</option>` : '').join("");
  
  resetAssignFields();
  await loadAssignedFeatures();
}

$("btn-detail-back").onclick = () => {
  showHallsListView();
  loadHalls();
};

$("btn-detail-save").onclick = async () => {
  $("detail-hall-error").innerHTML = "";
  const name = $("detail-hall-name").value.trim();
  const capacity = parseInt($("detail-hall-cap").value || "0", 10);
  const requires_approval = $("detail-hall-approval").checked;
  if (!name) {
    $("detail-hall-error").innerHTML = '<div class="error-msg">Name is required.</div>';
    return;
  }
  try {
    await patchHall(activeHallId, { name, capacity, requires_approval });
    $("detail-hall-title").textContent = `Configure Room: ${name}`;
    updateMetrics();
  } catch (e) {
    $("detail-hall-error").innerHTML = `<div class="error-msg">${e.message || "Failed to update."}</div>`;
  }
};

$("detail-hall-file").onchange = (e) => {
  const file = e.target.files[0];
  if (!file) {
    $("detail-hall-file-name").textContent = "";
    $("btn-detail-upload-img").disabled = true;
    return;
  }
  $("detail-hall-file-name").textContent = file.name;
  $("btn-detail-upload-img").disabled = false;
  
  const reader = new FileReader();
  reader.onload = (evt) => {
    $("detail-hall-img-preview").src = evt.target.result;
  };
  reader.readAsDataURL(file);
};

$("btn-detail-upload-img").onclick = async () => {
  const fileInput = $("detail-hall-file");
  const file = fileInput.files[0];
  if (!file) return;
  
  $("detail-hall-error").innerHTML = "";
  $("btn-detail-upload-img").disabled = true;
  $("btn-detail-upload-img").textContent = "Uploading...";
  
  const formData = new FormData();
  formData.append("file", file);
  
  try {
    const res = await fetch(`/api/admin/halls/${activeHallId}/picture`, {
      method: "POST",
      body: formData
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Upload failed.");
    
    if (data.image) {
      $("detail-hall-img-preview").src = `/static/images/${data.image}?t=${Date.now()}`;
    }
    $("detail-hall-file").value = "";
    $("detail-hall-file-name").textContent = "";
    alert("Picture updated successfully!");
  } catch (e) {
    $("detail-hall-error").innerHTML = `<div class="error-msg">${e.message || "Failed to upload picture."}</div>`;
    $("btn-detail-upload-img").disabled = false;
  } finally {
    $("btn-detail-upload-img").textContent = "Upload New Picture";
  }
};

async function loadAssignedFeatures() {
  const assignments = await api(`/api/admin/features/hall/${activeHallId}`);
  const listDiv = $("assigned-features-list");
  
  if (!assignments.length) {
    listDiv.innerHTML = '<p class="instructions">No custom features assigned to this hall yet.</p>';
    return;
  }
  
  listDiv.innerHTML = assignments.map(a => {
    const feat = globalFeaturesCatalog.find(f => f.id === a.feature_id);
    const featName = feat ? feat.name : `Feature #${a.feature_id}`;
    const featType = feat ? feat.value_type : 'unknown';
    
    let displayVal = "";
    if (featType === 'bool') {
      displayVal = a.value === 'true' ? 'Yes' : 'No';
    } else if (['single_select', 'multi_select'].includes(featType)) {
      if (feat && a.option_id) {
        const opt = feat.options.find(o => o.id === a.option_id);
        displayVal = opt ? opt.label : `Option #${a.option_id}`;
      }
    } else {
      displayVal = a.value || "";
    }
    
    const qtyStr = (a.quantity !== null && a.quantity !== undefined) ? ` &middot; Qty: ${a.quantity}` : '';
    
    return `<div class="feature-assignment-row">
      <div class="info">
        <span class="title">${featName}</span>
        <span class="details">Value: <strong>${displayVal}</strong>${qtyStr}</span>
      </div>
      <button class="ghost remove-assign" data-aid="${a.id}" style="padding: 4px 10px; font-size: 11px; border-color: var(--primary); color: var(--primary);">
        Remove
      </button>
    </div>`;
  }).join("");
  
  document.querySelectorAll(".remove-assign").forEach(b => {
    b.onclick = async () => {
      await api(`/api/admin/features/remove/assignment/${b.dataset.aid}`, { method: "DELETE" }).catch(async () => {
        // Fallback endpoint just in case
        await api(`/api/admin/features/hall/assignment/${b.dataset.aid}`, { method: "DELETE" });
      });
      await loadAssignedFeatures();
    };
  });
}

function resetAssignFields() {
  $("div-assign-val").classList.add("hidden");
  $("div-assign-opt").classList.add("hidden");
  $("div-assign-qty").classList.add("hidden");
  $("container-assign-val").innerHTML = "";
  $("detail-assign-opt").innerHTML = "";
  $("detail-assign-qty").value = "1";
}

$("detail-assign-feat").onchange = () => {
  resetAssignFields();
  const fid = parseInt($("detail-assign-feat").value, 10);
  if (!fid) return;
  
  const feat = globalFeaturesCatalog.find(f => f.id === fid);
  if (!feat) return;
  
  if (feat.value_type === "bool") {
    $("div-assign-val").classList.remove("hidden");
    $("lbl-assign-val").textContent = "Yes/No Option";
    $("container-assign-val").innerHTML = `<select id="detail-assign-val">
      <option value="true">Yes (Enabled)</option>
      <option value="false">No (Disabled)</option>
    </select>`;
  } else if (feat.value_type === "number") {
    $("div-assign-val").classList.remove("hidden");
    $("lbl-assign-val").textContent = "Numeric Value";
    $("container-assign-val").innerHTML = `<input type="number" id="detail-assign-val" value="0" />`;
  } else if (feat.value_type === "text") {
    $("div-assign-val").classList.remove("hidden");
    $("lbl-assign-val").textContent = "Text Value";
    $("container-assign-val").innerHTML = `<input type="text" id="detail-assign-val" placeholder="Enter configuration value" />`;
  } else if (["single_select", "multi_select"].includes(feat.value_type)) {
    $("div-assign-opt").classList.remove("hidden");
    $("detail-assign-opt").innerHTML = feat.options.map(o => o.active ? `<option value="${o.id}">${o.label}</option>` : '').join("");
    $("div-assign-qty").classList.remove("hidden");
  }
};

$("btn-detail-assign").onclick = async () => {
  const fid = parseInt($("detail-assign-feat").value, 10);
  if (!fid) return;
  
  const feat = globalFeaturesCatalog.find(f => f.id === fid);
  if (!feat) return;
  
  let val = null;
  let optId = null;
  let qty = null;
  
  if (feat.value_type === "bool") {
    val = $("detail-assign-val").value;
  } else if (feat.value_type === "number" || feat.value_type === "text") {
    val = $("detail-assign-val").value.trim();
  } else if (["single_select", "multi_select"].includes(feat.value_type)) {
    optId = parseInt($("detail-assign-opt").value, 10);
    qty = parseInt($("detail-assign-qty").value || "1", 10);
  }
  
  try {
    await api(`/api/admin/features/hall/${activeHallId}`, {
      method: "POST",
      body: JSON.stringify({
        feature_id: fid,
        option_id: optId,
        value: val,
        quantity: qty
      })
    });
    
    $("detail-assign-feat").value = "";
    resetAssignFields();
    await loadAssignedFeatures();
  } catch (e) {
    alert(e.message || "Failed to assign feature.");
  }
};

// ---------- features catalog ----------
async function loadFeatures() {
  const feats = await api("/api/admin/features");
  $("features-list").innerHTML = feats.map((f) => `
    <div class="card" style="margin-bottom: 16px;">
      <div style="display:flex; justify-content:space-between; align-items:center; border-bottom: 1px solid var(--border); padding-bottom: 10px; margin-bottom: 12px;">
        <div>
          <strong style="font-size: 15px; color: var(--primary);">${f.name}</strong> 
          <span class="pill" style="margin-left: 8px;">Type: ${f.value_type}</span>
        </div>
        <div>
          ${f.active ? '<span class="status-tag confirmed">active</span>' : '<span class="status-tag cancelled">inactive</span>'}
        </div>
      </div>
      ${["single_select", "multi_select"].includes(f.value_type) ? `
        <div style="margin-top: 8px;">
          <label style="font-size: 11px; text-transform: uppercase; color: var(--text-muted);">Options</label>
          ${f.options.map((o) => `<div class="opt-row">
            <span class="lbl ${o.active ? "" : "muted"}" contenteditable="true" data-oid="${o.id}">${o.label}</span>
            <button class="ghost opt-toggle" data-oid="${o.id}" data-active="${o.active}" style="padding: 3px 8px; font-size: 11px;">
              ${o.active ? "Retire" : "Restore"}
            </button>
          </div>`).join("")}
          <div class="opt-row" style="background: var(--bg); border-style: dashed;">
            <input class="new-opt" data-fid="${f.id}" placeholder="Add option..." style="border: 0; padding: 4px;" />
            <button class="add-opt" data-fid="${f.id}" style="padding: 4px 10px; font-size: 12px;">Add</button>
          </div>
        </div>` : ""}
    </div>`).join("");
  
  document.querySelectorAll(".add-opt").forEach((b) => {
    b.onclick = async () => {
      const inp = document.querySelector(`.new-opt[data-fid="${b.dataset.fid}"]`);
      if (!inp.value.trim()) return;
      await api(`/api/admin/features/${b.dataset.fid}/options`, { 
        method: "POST", 
        body: JSON.stringify({ label: inp.value.trim() }) 
      });
      loadFeatures();
    };
  });
  
  document.querySelectorAll(".opt-toggle").forEach((b) => {
    b.onclick = async () => {
      await api(`/api/admin/features/options/${b.dataset.oid}`, { 
        method: "PATCH", 
        body: JSON.stringify({ active: b.dataset.active !== "true" }) 
      });
      loadFeatures();
    };
  });
  
  document.querySelectorAll(".lbl[data-oid]").forEach((el) => {
    el.onblur = async () => {
      await api(`/api/admin/features/options/${el.dataset.oid}`, { 
        method: "PATCH", 
        body: JSON.stringify({ label: el.textContent.trim() }) 
      });
    };
  });
}

$("ft-add").onclick = async () => {
  const name = $("ft-name").value.trim(); 
  if (!name) return;
  await api("/api/admin/features", { 
    method: "POST", 
    body: JSON.stringify({ name, value_type: $("ft-type").value }) 
  });
  $("ft-name").value = ""; 
  await loadFeatures();
  updateMetrics();
};

// ---------- audit ----------
async function loadAudit() {
  const rows = await api("/api/admin/audit");
  $("audit-table").innerHTML = rows.length ? `<table>
    <thead>
      <tr>
        <th>Timestamp</th>
        <th>Action</th>
        <th>Actor</th>
        <th>IP Address</th>
        <th>Details</th>
      </tr>
    </thead>
    <tbody>
      ${rows.map((r) => `<tr>
        <td class="muted"><code>${(r.ts || "").replace("T", " ").slice(0, 19)}</code></td>
        <td><strong>${r.action}</strong></td>
        <td><strong>${r.actor || "System"}</strong></td>
        <td class="muted"><code>${r.actor_ip || ""}</code></td>
        <td class="muted">${r.detail || ""}</td>
      </tr>`).join("")}
    </tbody>
  </table>`
  : '<p class="muted" style="padding: 24px; text-align: center;">No administrative audit activities logged yet.</p>';
}

// ---------- Cancel Booking Tab Logic ----------
$("btn-dash-submit-cancel").onclick = async () => {
  const code = $("dash-c-cancel-code").value.trim().toUpperCase();
  $("dash-cancel-error").innerHTML = "";
  
  if (!code) {
    $("dash-cancel-error").innerHTML = '<div class="error-msg">Please enter a cancel code.</div>';
    return;
  }
  
  try {
    await api("/api/bookings/by-code/cancel", {
      method: "POST",
      body: JSON.stringify({ cancel_code: code })
    });
    alert("Booking cancelled successfully! The slots have been freed up.");
    $("dash-c-cancel-code").value = "";
    updateMetrics();
  } catch (e) {
    const msg = e.message || "Failed to cancel booking. Please check the Cancel Code.";
    $("dash-cancel-error").innerHTML = `<div class="error-msg">${msg}</div>`;
  }
};

// ---------- Security Tab Logic ----------
$("btn-dash-update-credentials").onclick = async () => {
  $("dash-security-error").innerHTML = "";
  $("dash-security-success").innerHTML = "";
  
  const newUsername = $("sec-username").value.trim();
  const newPassword = $("sec-password").value;
  
  if (!newUsername) {
    $("dash-security-error").innerHTML = '<div class="error-msg">Username cannot be empty.</div>';
    return;
  }
  if (!newPassword) {
    $("dash-security-error").innerHTML = '<div class="error-msg">Password cannot be empty.</div>';
    return;
  }
  
  try {
    const res = await api("/api/auth/credentials", {
      method: "POST",
      body: JSON.stringify({ new_username: newUsername, new_password: newPassword })
    });
    
    $("dash-security-success").innerHTML = `<div class="success-msg" style="color: #16a34a; font-weight: 600; margin-bottom: 16px;">Credentials updated successfully!</div>`;
    $("sec-password").value = "";
  } catch (e) {
    const msg = e.message || "Failed to update credentials.";
    $("dash-security-error").innerHTML = `<div class="error-msg">${msg}</div>`;
  }
};

// ---------- Dropdown Config Tab Logic ----------
async function loadDropdowns() {
  $("dropdowns-error").innerHTML = "";
  try {
    const data = await api("/api/admin/dropdowns");
    $("dropdowns-table-body").innerHTML = data.map(item => `
      <tr style="border-bottom: 1px solid var(--border);">
        <td style="padding: 10px;"><strong>${item.category}</strong></td>
        <td style="padding: 10px;">${item.value}</td>
        <td style="padding: 10px; text-align: right;">
          <button class="ghost delete-dd" data-id="${item.id}" style="color: #ef4444; border-color: #fca5a5; padding: 4px 10px; font-size: 11px;">Delete</button>
        </td>
      </tr>
    `).join("");
    
    document.querySelectorAll(".delete-dd").forEach(btn => {
      btn.onclick = async () => {
        if (confirm("Delete this dropdown option?")) {
          try {
            await api(`/api/admin/dropdowns/${btn.dataset.id}`, { method: "DELETE" });
            loadDropdowns();
          } catch (e) {
            $("dropdowns-error").innerHTML = `<div class="error-msg">${e.message || "Failed to delete dropdown option."}</div>`;
          }
        }
      };
    });
  } catch (e) {
    $("dropdowns-error").innerHTML = `<div class="error-msg">Failed to load dropdown options.</div>`;
  }
}

$("btn-add-dropdown").onclick = async () => {
  $("dropdowns-error").innerHTML = "";
  const category = $("dd-category").value;
  const value = $("dd-value").value.trim();
  if (!value) {
    $("dropdowns-error").innerHTML = '<div class="error-msg">Option value cannot be empty.</div>';
    return;
  }
  try {
    await api("/api/admin/dropdowns", {
      method: "POST",
      body: JSON.stringify({ category, value })
    });
    $("dd-value").value = "";
    loadDropdowns();
  } catch (e) {
    $("dropdowns-error").innerHTML = `<div class="error-msg">${e.message || "Failed to add option."}</div>`;
  }
};

// ---------- Settings Admin tab ----------
async function loadSettings() {
  $("settings-error").innerHTML = "";
  $("settings-success").innerHTML = "";
  try {
    const s = await api("/api/admin/settings");
    $("set-smtp-host").value = s.smtp_host || "";
    $("set-smtp-port").value = s.smtp_port || "";
    $("set-smtp-username").value = s.smtp_username || "";
    $("set-smtp-password").value = s.smtp_password || "";
    $("set-smtp-from").value = s.smtp_from || "";
    $("set-smtp-use-tls").checked = s.smtp_use_tls === "True";
    $("set-director-email").value = s.director_email || "";
    $("set-email-housekeeping").value = s.email_housekeeping || "";
    $("set-email-it").value = s.email_it || "";
    $("set-email-stationery").value = s.email_stationery || "";
    $("set-email-canteen").value = s.email_canteen || "";
    $("set-template-housekeeping").value = s.template_housekeeping || "";
    $("set-template-it").value = s.template_it || "";
    $("set-template-stationery").value = s.template_stationery || "";
    $("set-template-canteen").value = s.template_canteen || "";
  } catch (e) {
    $("settings-error").innerHTML = `<div class="error-msg">${e.message || "Failed to load system settings."}</div>`;
  }
}

$("btn-save-settings").onclick = async () => {
  $("settings-error").innerHTML = "";
  $("settings-success").innerHTML = "";
  
  const payload = {
    smtp_host: $("set-smtp-host").value.trim(),
    smtp_port: $("set-smtp-port").value.trim(),
    smtp_username: $("set-smtp-username").value.trim(),
    smtp_password: $("set-smtp-password").value.trim(),
    smtp_from: $("set-smtp-from").value.trim(),
    smtp_use_tls: $("set-smtp-use-tls").checked ? "True" : "False",
    director_email: $("set-director-email").value.trim(),
    email_housekeeping: $("set-email-housekeeping").value.trim(),
    email_it: $("set-email-it").value.trim(),
    email_stationery: $("set-email-stationery").value.trim(),
    email_canteen: $("set-email-canteen").value.trim(),
    template_housekeeping: $("set-template-housekeeping").value,
    template_it: $("set-template-it").value,
    template_stationery: $("set-template-stationery").value,
    template_canteen: $("set-template-canteen").value
  };

  try {
    await api("/api/admin/settings", {
      method: "POST",
      body: JSON.stringify(payload)
    });
    $("settings-success").innerHTML = `<div style="background: #dcfce7; border: 1px solid #bbf7d0; color: #15803d; padding: 12px; border-radius: 6px; margin-bottom: 16px;">✓ System settings and HTML templates saved successfully!</div>`;
    $("settings-success").scrollIntoView({ behavior: "smooth" });
  } catch (e) {
    $("settings-error").innerHTML = `<div class="error-msg">${e.message || "Failed to save settings."}</div>`;
    $("settings-error").scrollIntoView({ behavior: "smooth" });
  }
};

checkAuth();
