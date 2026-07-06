// IT dashboard: login gate, polled live feed, hall + feature management, audit.
const $ = (id) => document.getElementById(id);
let pollTimer = null;

async function api(path, opts) {
  const res = await fetch(path, Object.assign({ headers: { "Content-Type": "application/json" } }, opts));
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw (typeof body.detail === "string" ? new Error(body.detail) : body);
  return body;
}

// ---------- auth ----------
async function checkAuth() {
  try { await api("/api/auth/me"); enterApp(); }
  catch { showLogin(); }
}
function showLogin() { $("login-card").classList.remove("hidden"); $("app").classList.add("hidden"); $("link-logout").classList.add("hidden"); }
function enterApp() {
  $("login-card").classList.add("hidden"); $("app").classList.remove("hidden"); $("link-logout").classList.remove("hidden");
  $("live-date").value = "";
  loadLive(); startPoll();
}
$("btn-login").onclick = async () => {
  $("login-error").innerHTML = "";
  try {
    await api("/api/auth/login", { method: "POST", body: JSON.stringify({ username: $("l-user").value, password: $("l-pass").value }) });
    enterApp();
  } catch (e) {
    $("login-error").innerHTML = `<div class="error">${e.message || "Sign-in failed."}</div>`;
  }
};
$("link-logout").onclick = async (e) => { e.preventDefault(); await api("/api/auth/logout", { method: "POST" }); stopPoll(); showLogin(); };

// ---------- tabs ----------
document.querySelectorAll(".tab").forEach((t) => {
  t.onclick = () => {
    document.querySelectorAll(".tab").forEach((n) => n.classList.remove("active"));
    document.querySelectorAll(".tab-body").forEach((n) => n.classList.add("hidden"));
    t.classList.add("active");
    const name = t.dataset.tab;
    $("tab-" + name).classList.remove("hidden");
    if (name === "live") loadLive();
    if (name === "halls") loadHalls();
    if (name === "features") loadFeatures();
    if (name === "audit") loadAudit();
  };
});

// ---------- live bookings (polled) ----------
function startPoll() { stopPoll(); pollTimer = setInterval(() => { if (!$("tab-live").classList.contains("hidden")) loadLive(true); }, 5000); }
function stopPoll() { if (pollTimer) clearInterval(pollTimer); pollTimer = null; }

async function loadLive(quiet) {
  const q = [];
  if ($("live-date").value) q.push("on=" + $("live-date").value);
  if ($("live-status").value) q.push("status=" + $("live-status").value);
  let rows;
  try { rows = await api("/api/admin/bookings" + (q.length ? "?" + q.join("&") : "")); }
  catch { showLogin(); return; }
  $("live-meta").textContent = `\u00b7 ${rows.length} shown \u00b7 auto-refreshing`;
  if (!rows.length) { $("live-table").innerHTML = '<p class="muted">No bookings.</p>'; return; }
  $("live-table").innerHTML = `<table><thead><tr>
    <th>Date</th><th>Hall</th><th>Time</th><th>Booked by</th><th>Dept</th><th>Purpose</th><th>Status</th><th>From IP</th></tr></thead>
    <tbody>${rows.map((b) => `<tr class="${b.status}">
      <td>${b.date}</td><td>${b.hall}</td><td>${b.start}\u2013${b.end}</td>
      <td>${b.booked_by}</td><td>${b.dept || ""}</td><td>${b.purpose || ""}</td>
      <td><span class="status-tag ${b.status}">${b.status}</span></td>
      <td class="muted">${b.created_ip || ""}</td></tr>`).join("")}</tbody></table>`;
}
$("live-date").onchange = () => loadLive();
$("live-status").onchange = () => loadLive();
$("live-clear").onclick = () => { $("live-date").value = ""; $("live-status").value = ""; loadLive(); };

// ---------- halls ----------
async function loadHalls() {
  const halls = await api("/api/admin/halls");
  $("halls-table").innerHTML = `<table><thead><tr><th>Name</th><th>Seats</th><th>Status</th><th></th></tr></thead>
    <tbody>${halls.map((h) => `<tr>
      <td><span contenteditable data-id="${h.id}" class="edit-name">${h.name}</span></td>
      <td><span contenteditable data-id="${h.id}" class="edit-cap">${h.capacity}</span></td>
      <td><span class="status-tag ${h.active ? "confirmed" : "cancelled"}">${h.active ? "active" : "archived"}</span></td>
      <td><button class="ghost toggle" data-id="${h.id}" data-active="${h.active}">${h.active ? "Archive" : "Restore"}</button></td>
    </tr>`).join("")}</tbody></table>
    <p class="muted" style="margin-top:8px">Click a name or seat count to edit, then click away to save.</p>`;
  document.querySelectorAll(".edit-name").forEach((el) => el.onblur = () => patchHall(el.dataset.id, { name: el.textContent.trim() }));
  document.querySelectorAll(".edit-cap").forEach((el) => el.onblur = () => patchHall(el.dataset.id, { capacity: parseInt(el.textContent.trim() || "0", 10) }));
  document.querySelectorAll(".toggle").forEach((b) => b.onclick = () => patchHall(b.dataset.id, { active: b.dataset.active !== "true" }).then(loadHalls));
}
async function patchHall(id, body) { await api(`/api/admin/halls/${id}`, { method: "PATCH", body: JSON.stringify(body) }); }
$("h-add").onclick = async () => {
  const name = $("h-name").value.trim(); if (!name) return;
  await api("/api/admin/halls", { method: "POST", body: JSON.stringify({ name, capacity: parseInt($("h-cap").value || "0", 10) }) });
  $("h-name").value = ""; $("h-cap").value = "0"; loadHalls();
};

// ---------- features ----------
async function loadFeatures() {
  const feats = await api("/api/admin/features");
  $("features-list").innerHTML = feats.map((f) => `
    <div class="card" style="box-shadow:none;margin-bottom:12px">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <div><strong>${f.name}</strong> <span class="pill">${f.value_type}</span>
          ${f.active ? "" : '<span class="status-tag cancelled">inactive</span>'}</div>
      </div>
      ${["single_select", "multi_select"].includes(f.value_type) ? `
        <div style="margin-top:10px">
          ${f.options.map((o) => `<div class="opt-row">
            <span class="lbl ${o.active ? "" : "muted"}" contenteditable data-oid="${o.id}">${o.label}</span>
            <button class="ghost opt-toggle" data-oid="${o.id}" data-active="${o.active}">${o.active ? "Retire" : "Restore"}</button>
          </div>`).join("")}
          <div class="opt-row" style="margin-top:8px">
            <input class="new-opt" data-fid="${f.id}" placeholder="Add option, e.g. Boundary mic" />
            <button class="add-opt" data-fid="${f.id}">Add</button>
          </div>
        </div>` : ""}
    </div>`).join("");
  document.querySelectorAll(".add-opt").forEach((b) => b.onclick = async () => {
    const inp = document.querySelector(`.new-opt[data-fid="${b.dataset.fid}"]`);
    if (!inp.value.trim()) return;
    await api(`/api/admin/features/${b.dataset.fid}/options`, { method: "POST", body: JSON.stringify({ label: inp.value.trim() }) });
    loadFeatures();
  });
  document.querySelectorAll(".opt-toggle").forEach((b) => b.onclick = async () => {
    await api(`/api/admin/features/options/${b.dataset.oid}`, { method: "PATCH", body: JSON.stringify({ active: b.dataset.active !== "true" }) });
    loadFeatures();
  });
  document.querySelectorAll(".lbl[data-oid]").forEach((el) => el.onblur = async () => {
    await api(`/api/admin/features/options/${el.dataset.oid}`, { method: "PATCH", body: JSON.stringify({ label: el.textContent.trim() }) });
  });
}
$("ft-add").onclick = async () => {
  const name = $("ft-name").value.trim(); if (!name) return;
  await api("/api/admin/features", { method: "POST", body: JSON.stringify({ name, value_type: $("ft-type").value }) });
  $("ft-name").value = ""; loadFeatures();
};

// ---------- audit ----------
async function loadAudit() {
  const rows = await api("/api/admin/audit");
  $("audit-table").innerHTML = rows.length ? `<table><thead><tr><th>When</th><th>Action</th><th>Actor</th><th>IP</th><th>Detail</th></tr></thead>
    <tbody>${rows.map((r) => `<tr><td class="muted">${(r.ts || "").replace("T", " ").slice(0, 19)}</td>
      <td>${r.action}</td><td>${r.actor || ""}</td><td class="muted">${r.actor_ip || ""}</td>
      <td class="muted">${r.detail || ""}</td></tr>`).join("")}</tbody></table>`
    : '<p class="muted">No activity yet.</p>';
}

checkAuth();
