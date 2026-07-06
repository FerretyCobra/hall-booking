// Booking portal: filter -> hall -> timeline -> confirm -> done.
const $ = (id) => document.getElementById(id);
const state = { date: null, hall: null, cfg: null, selected: new Set(), bookings: [] };

function todayISO() { return new Date().toISOString().slice(0, 10); }
function toMin(t) { const [h, m] = t.split(":").map(Number); return h * 60 + m; }
function fmt(m) { return String(Math.floor(m / 60)).padStart(2, "0") + ":" + String(m % 60).padStart(2, "0"); }
function dur(m) { const h = Math.floor(m / 60), mm = m % 60, o = []; if (h) o.push(h + " hr"); if (mm) o.push(mm + " min"); return o.join(" "); }
function show(id) { $(id).classList.remove("hidden"); }
function hide(id) { $(id).classList.add("hidden"); }

async function api(path, opts) {
  const res = await fetch(path, Object.assign({ headers: { "Content-Type": "application/json" } }, opts));
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw body.detail || body;
  return body;
}

async function init() {
  $("f-date").value = todayISO();
  $("f-date").min = todayISO();
  state.cfg = await api("/api/config");
  try {
    const feats = await api("/api/halls"); // warm up; features come from a dedicated call below
  } catch (e) {}
  // Populate the "must have" filter from distinct hall features.
  try {
    const halls = await api("/api/halls");
    const seen = new Set();
    halls.forEach((h) => (h.features || []).forEach((f) => {
      const name = f.split(":")[0].trim();
      seen.add(name);
    }));
    // We filter by feature name client-side via the halls we already fetched,
    // but for a precise server filter we'd map name->feature_id. Keep it simple:
    [...seen].sort().forEach((name) => {
      const o = document.createElement("option");
      o.value = name; o.textContent = name; $("f-feature").appendChild(o);
    });
  } catch (e) {}
}

$("btn-find").onclick = async () => {
  state.date = $("f-date").value || todayISO();
  const minCap = $("f-capacity").value || 0;
  let halls = await api(`/api/halls?min_capacity=${minCap}`);
  const featName = $("f-feature").value;
  if (featName) halls = halls.filter((h) => (h.features || []).some((f) => f.startsWith(featName)));
  renderHalls(halls);
  show("step-halls");
  $("step-halls").scrollIntoView({ behavior: "smooth", block: "nearest" });
};

function renderHalls(halls) {
  const box = $("hall-list");
  box.innerHTML = "";
  if (!halls.length) { box.innerHTML = '<p class="muted">No halls match. Try loosening the filters.</p>'; return; }
  halls.forEach((h) => {
    const el = document.createElement("div");
    el.className = "hall-item";
    el.innerHTML = `<div><strong>${h.name}</strong>
      <div class="feats"><span class="pill">${h.capacity} seats</span>
      ${(h.features || []).map((f) => `<span class="pill">${f}</span>`).join("")}</div></div>
      <span class="muted">Select &rarr;</span>`;
    el.onclick = () => selectHall(h, el);
    box.appendChild(el);
  });
}

async function selectHall(hall, el) {
  document.querySelectorAll(".hall-item").forEach((n) => n.classList.remove("active"));
  el.classList.add("active");
  state.hall = hall;
  state.selected.clear();
  const data = await api(`/api/halls/${hall.id}/availability?on=${state.date}`);
  state.bookings = data.bookings;
  $("tl-hall").textContent = `${hall.name} \u00b7 ${state.date}`;
  renderGrid();
  show("step-timeline");
  updateSummary();
  $("step-timeline").scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function slotBusy(start) {
  const s = toMin(start), e = s + state.cfg.slot_minutes;
  return state.bookings.find((b) => toMin(b.start) < e && toMin(b.end) > s);
}

function renderGrid() {
  const grid = $("tl-grid");
  grid.innerHTML = "";
  const startM = toMin(state.cfg.day_start), endM = toMin(state.cfg.day_end);
  for (let m = startM; m < endM; m += state.cfg.slot_minutes) {
    const t = fmt(m);
    const busy = slotBusy(t);
    const cell = document.createElement(busy ? "div" : "button");
    cell.className = "slot " + (busy ? "busy" : "free");
    cell.innerHTML = `<span>${t}</span><span class="c">${busy ? (busy.dept || busy.booked_by) : "Free"}</span>`;
    if (!busy) {
      cell.type = "button";
      cell.onclick = () => {
        if (state.selected.has(t)) { state.selected.delete(t); cell.classList.remove("sel"); }
        else { state.selected.add(t); cell.classList.add("sel"); }
        updateSummary();
      };
    }
    grid.appendChild(cell);
  }
}

function selectionRange() {
  const mins = [...state.selected].map(toMin).sort((a, b) => a - b);
  if (!mins.length) return null;
  const start = mins[0], end = mins[mins.length - 1] + state.cfg.slot_minutes;
  const total = state.selected.size * state.cfg.slot_minutes;
  return { start: fmt(start), end: fmt(end), total, contiguous: end - start === total };
}

function updateSummary() {
  const r = selectionRange();
  const btn = $("btn-continue");
  if (!r) { $("tl-summary").textContent = "No time selected"; btn.disabled = true; return; }
  $("tl-summary").textContent =
    `Selected: ${r.start}\u2013${r.end} \u00b7 ${dur(r.total)}` + (r.contiguous ? "" : " (non-contiguous)");
  btn.disabled = false;
}

$("btn-continue").onclick = () => {
  const r = selectionRange();
  if (!r) return;
  if (!r.contiguous) { alert("Please pick a single continuous block of time."); return; }
  state.range = r;
  $("confirm-summary").textContent = `${state.hall.name} \u00b7 ${state.date} \u00b7 ${r.start}\u2013${r.end} \u00b7 ${dur(r.total)}`;
  $("confirm-error").innerHTML = "";
  show("step-confirm");
  $("step-confirm").scrollIntoView({ behavior: "smooth", block: "nearest" });
};

$("btn-back").onclick = () => hide("step-confirm");

$("btn-book").onclick = async () => {
  const name = $("c-name").value.trim();
  if (!name) { $("c-name").focus(); return; }
  const payload = {
    hall_id: state.hall.id, booking_date: state.date,
    start_time: state.range.start, end_time: state.range.end,
    booked_by: name, dept: $("c-dept").value, purpose: $("c-purpose").value.trim(),
  };
  try {
    const res = await api("/api/bookings", { method: "POST", body: JSON.stringify(payload) });
    $("done-line").textContent = `${state.hall.name} \u00b7 ${state.date} \u00b7 ${res.start}\u2013${res.end}`;
    $("done-code").textContent = res.cancel_code;
    hide("step-confirm"); hide("step-timeline"); hide("step-halls"); hide("step-filter");
    show("step-done");
    $("step-done").scrollIntoView({ behavior: "smooth", block: "nearest" });
  } catch (e) {
    const msg = (e && e.message) ? e.message : "Could not book that slot.";
    $("confirm-error").innerHTML = `<div class="error">${msg} Someone may have just taken it \u2014 go back and pick another slot.</div>`;
  }
};

$("btn-new").onclick = () => location.reload();

init();
