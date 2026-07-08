// ICMR NITVAR Booking Portal JS
const $ = (id) => document.getElementById(id);

const state = {
  halls: [],
  selectedHall: null,
  date: null, // "YYYY-MM-DD"
  cfg: { day_start: "09:30", day_end: "17:30", slot_minutes: 15 }, // hardcoded for 15-min precision
  bookings: [], // list of existing bookings for selected date/hall
  selectedStartSlot: null, // "HH:MM"
  selectedEndSlot: null, // "HH:MM"
  isCustomTimeMode: false,
  presets: {}
};

// Date utilities
function todayISO() {
  return new Date().toLocaleDateString('en-CA'); // Gets local YYYY-MM-DD format correctly
}

function toMin(t) {
  const [h, m] = t.split(":").map(Number);
  return h * 60 + m;
}

function fmt(m) {
  return String(Math.floor(m / 60)).padStart(2, "0") + ":" + String(m % 60).padStart(2, "0");
}

function fmtDisplayTime(t) {
  const [h, m] = t.split(":").map(Number);
  const ampm = h >= 12 ? 'PM' : 'AM';
  const displayHour = h % 12 === 0 ? 12 : h % 12;
  return `${displayHour}:${String(m).padStart(2, '0')} ${ampm}`;
}

function getDurationText(start, end) {
  const diff = toMin(end) - toMin(start);
  const hrs = Math.floor(diff / 60);
  const mins = diff % 60;
  let out = [];
  if (hrs > 0) out.push(`${hrs} hr${hrs > 1 ? 's' : ''}`);
  if (mins > 0) out.push(`${mins} min${mins > 1 ? 's' : ''}`);
  return out.join(" ") || "0 mins";
}

function show(id) { $(id).classList.remove("hidden"); }
function hide(id) { $(id).classList.add("hidden"); }

// Wizard progress visual manager
function setWizardStep(activeStep) {
  for (let i = 1; i <= 4; i++) {
    const el = $(`wstep-${i}`);
    if (!el) continue;
    if (i < activeStep) {
      el.className = "wizard-step completed";
    } else if (i === activeStep) {
      el.className = "wizard-step active";
    } else {
      el.className = "wizard-step";
    }
  }
}

async function api(path, opts) {
  const res = await fetch(path, Object.assign({ headers: { "Content-Type": "application/json" } }, opts));
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw body.detail || body;
  return body;
}

// Initialise Application
async function init() {
  state.date = todayISO();
  await loadHalls();
  renderHalls();
  setWizardStep(1);
}

// Fetch halls from backend
async function loadHalls() {
  try {
    state.halls = await api("/api/halls");
  } catch (e) {
    console.error("Error loading halls", e);
  }
}

// Render BookMyShow-style Hall Cards
async function renderHalls() {
  const container = $("hall-grid-container");
  container.innerHTML = "";
  
  if (!state.halls.length) {
    container.innerHTML = `<p class="instructions" style="text-align: center; width: 100%; padding: 24px;">No halls are currently available.</p>`;
    return;
  }

  const today = todayISO();

  for (const hall of state.halls) {
    const card = document.createElement("div");
    card.className = "hall-card";
    
    // Fetch availability to calculate free time
    let availableText = "Checking availability...";
    try {
      const data = await api(`/api/halls/${hall.id}/availability?on=${today}`);
      const bookedMinutes = data.bookings.reduce((sum, b) => {
        return sum + (toMin(b.end) - toMin(b.start));
      }, 0);
      const totalDayMinutes = toMin(state.cfg.day_end) - toMin(state.cfg.day_start); // 17:30 - 09:30 = 480 mins
      const freeMinutes = Math.max(0, totalDayMinutes - bookedMinutes);
      
      const hrsPart = Math.floor(freeMinutes / 60);
      const minsPart = freeMinutes % 60;
      
      let timeParts = [];
      if (hrsPart > 0) timeParts.push(`${hrsPart} hr${hrsPart > 1 ? 's' : ''}`);
      if (minsPart > 0) timeParts.push(`${minsPart} min${minsPart > 1 ? 's' : ''}`);
      availableText = timeParts.join(" ") || "No slots";
      availableText += " free today";
    } catch (e) {
      console.error(e);
      availableText = "Available for booking";
    }
    
    card.innerHTML = `
      <div class="hall-image-container">
        <img src="/static/images/hall_placeholder.png" alt="${hall.name}" class="hall-card-img" />
      </div>
      <div class="hall-card-header" style="margin-top: 12px; margin-bottom: 8px;">
        <h2 class="hall-card-title">${hall.name}</h2>
        <span class="capacity-badge">${hall.capacity} Seats</span>
      </div>
      <div class="hall-card-body" style="margin-bottom: 16px;">
        <div class="hall-availability-status">
          <span class="status-indicator-dot"></span>
          <span class="availability-text">${availableText}</span>
        </div>
        ${hall.features && hall.features.length ? `
          <div class="hall-features-preview" style="margin-top: 8px;">
            ${hall.features.map(f => `<span class="pill" style="font-size: 10px; padding: 1px 6px; margin-right: 4px;">${f}</span>`).join("")}
          </div>` : ""}
      </div>
      <button class="select-hall-btn" type="button">Select & Book &rarr;</button>
    `;
    
    card.querySelector(".select-hall-btn").onclick = () => selectHall(hall);
    container.appendChild(card);
  }
}

// Step 1 -> Step 2
function selectHall(hall) {
  state.selectedHall = hall;
  state.selectedStartSlot = null;
  state.selectedEndSlot = null;
  
  $("selected-hall-name").textContent = `Configure booking: ${hall.name}`;
  
  // Render date picker
  renderDatePicker();
  
  hide("step-halls");
  show("step-datetime");
  setWizardStep(2);
  
  // Fetch bookings and render grid
  fetchAvailability();
}

// Render Horizontal Day Picker
function renderDatePicker() {
  const track = $("day-picker-track");
  track.innerHTML = "";
  
  const daysOfWeek = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"];
  const months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];
  
  const today = new Date();
  
  for (let i = 0; i < 7; i++) {
    const d = new Date(today);
    d.setDate(today.getDate() + i);
    
    const dayStr = daysOfWeek[d.getDay()];
    const dateNum = String(d.getDate()).padStart(2, "0");
    const monthStr = months[d.getMonth()];
    const isoString = d.toLocaleDateString('en-CA');
    
    const button = document.createElement("div");
    button.className = "day-picker-btn" + (isoString === state.date ? " active" : "");
    button.innerHTML = `
      <span class="day-lbl">${dayStr}</span>
      <span class="date-lbl">${dateNum}</span>
      <span class="month-lbl">${monthStr}</span>
    `;
    
    button.onclick = () => {
      document.querySelectorAll(".day-picker-btn").forEach(btn => btn.classList.remove("active"));
      button.classList.add("active");
      state.date = isoString;
      state.selectedStartSlot = null;
      state.selectedEndSlot = null;
      fetchAvailability();
    };
    
    track.appendChild(button);
  }
}

// Fetch availability from server
async function fetchAvailability() {
  try {
    const data = await api(`/api/halls/${state.selectedHall.id}/availability?on=${state.date}`);
    state.bookings = data.bookings;
    renderGrid();
    updateDateTimeSummary();
  } catch (e) {
    console.error(e);
  }
}

// Check if a 15-minute slot overlaps with any confirmed booking
function isSlotBusy(timeStr) {
  const slotStart = toMin(timeStr);
  const slotEnd = slotStart + 15;
  return state.bookings.find(b => toMin(b.start) < slotEnd && toMin(b.end) > slotStart);
}

// Render Time Grid
function renderGrid() {
  const grid = $("tl-grid");
  grid.innerHTML = "";
  
  const startM = toMin(state.cfg.day_start); // 09:30
  const endM = toMin(state.cfg.day_end);     // 17:30
  
  for (let m = startM; m < endM; m += 15) {
    const t = fmt(m);
    const busy = isSlotBusy(t);
    
    const cell = document.createElement(busy ? "div" : "button");
    cell.className = "slot-cell " + (busy ? "busy" : "free");
    
    // Highlight if selected
    if (!busy && isSlotInRange(t)) {
      cell.classList.add("selected");
    }
    
    cell.innerHTML = `
      <span class="slot-time">${t}</span>
      <span class="slot-status">${busy ? (busy.dept || busy.booked_by) : "Free"}</span>
    `;
    
    if (!busy) {
      cell.type = "button";
      cell.onclick = () => handleGridSlotClick(t);
    }
    
    grid.appendChild(cell);
  }
}

// Check if time slot is within currently selected range
function isSlotInRange(timeStr) {
  if (!state.selectedStartSlot) return false;
  const t = toMin(timeStr);
  const start = toMin(state.selectedStartSlot);
  if (!state.selectedEndSlot) return t === start;
  
  const end = toMin(state.selectedEndSlot);
  return t >= start && t <= end;
}

// Handle Grid Clicks to ensure contiguous range selection
function handleGridSlotClick(t) {
  const slotMin = toMin(t);
  
  if (!state.selectedStartSlot || (state.selectedStartSlot && state.selectedEndSlot)) {
    // Start a new selection
    state.selectedStartSlot = t;
    state.selectedEndSlot = null;
  } else {
    // Complete the selection
    const startMin = toMin(state.selectedStartSlot);
    if (slotMin < startMin) {
      // Clicked slot is before start, set as new start
      state.selectedStartSlot = t;
      state.selectedEndSlot = null;
    } else if (slotMin === startMin) {
      // Clicked same slot again, keep as start
      state.selectedEndSlot = null;
    } else {
      // Check if there is any busy slot in between [start, clicked_slot)
      let hasBusyInBetween = false;
      for (let m = startMin; m < slotMin; m += 15) {
        if (isSlotBusy(fmt(m))) {
          hasBusyInBetween = true;
          break;
        }
      }
      
      if (hasBusyInBetween) {
        // Reset selection starting at current click
        state.selectedStartSlot = t;
        state.selectedEndSlot = null;
      } else {
        // Set end time to the clicked slot time
        state.selectedEndSlot = t;
      }
    }
  }
  
  renderGrid();
  updateDateTimeSummary();
}

// Toggle Custom Time Range Mode
$("btn-toggle-custom-time").onclick = () => {
  state.isCustomTimeMode = !state.isCustomTimeMode;
  
  if (state.isCustomTimeMode) {
    $("grid-selector-container").classList.add("hidden");
    $("custom-time-container").classList.remove("hidden");
    $("btn-toggle-custom-time").textContent = "Use Chart Selection";
    
    // Set default custom times
    $("c-start-time").value = state.selectedStartSlot || "09:30";
    if (state.selectedEndSlot) {
      $("c-end-time").value = state.selectedEndSlot;
    } else if (state.selectedStartSlot) {
      $("c-end-time").value = fmt(toMin(state.selectedStartSlot) + 30);
    } else {
      $("c-end-time").value = "10:00";
    }
  } else {
    $("grid-selector-container").classList.remove("hidden");
    $("custom-time-container").classList.add("hidden");
    $("btn-toggle-custom-time").textContent = "Use Custom Time Input";
  }
  
  updateDateTimeSummary();
};

// Add input event listeners to custom inputs
$("c-start-time").onchange = validateAndSetCustomTimes;
$("c-end-time").onchange = validateAndSetCustomTimes;

function validateAndSetCustomTimes() {
  const start = $("c-start-time").value;
  const end = $("c-end-time").value;
  
  if (!start || !end) return;
  
  if (toMin(end) <= toMin(start)) {
    $("tl-summary").textContent = "Error: End time must be after start time";
    $("btn-continue-to-features").disabled = true;
    return;
  }
  
  if (toMin(start) < toMin("09:30") || toMin(end) > toMin("17:30")) {
    $("tl-summary").textContent = "Error: Booking must be within 09:30 to 17:30";
    $("btn-continue-to-features").disabled = true;
    return;
  }
  
  // Verify no overlap
  let isOverlap = false;
  let overlappingBooking = null;
  const sMin = toMin(start);
  const eMin = toMin(end);
  
  for (let b of state.bookings) {
    if (toMin(b.start) < eMin && toMin(b.end) > sMin) {
      isOverlap = true;
      overlappingBooking = b;
      break;
    }
  }
  
  if (isOverlap) {
    $("tl-summary").textContent = `Error: Overlaps with booking by ${overlappingBooking.booked_by}`;
    $("btn-continue-to-features").disabled = true;
    return;
  }
  
  state.selectedStartSlot = start;
  state.selectedEndSlot = end;
  updateDateTimeSummary();
}

function updateDateTimeSummary() {
  const btn = $("btn-continue-to-features");
  
  if (state.isCustomTimeMode) {
    validateAndSetCustomTimes();
    if (btn.disabled) return;
  }
  
  if (!state.selectedStartSlot) {
    $("tl-summary").textContent = "No time selected";
    btn.disabled = true;
    return;
  }
  
  const start = state.selectedStartSlot;
  
  if (!state.selectedEndSlot) {
    $("tl-summary").textContent = `Selected start: ${fmtDisplayTime(start)}. Please choose the end time slot on the chart.`;
    btn.disabled = true;
    return;
  }
  
  const end = state.selectedEndSlot;
  
  $("tl-summary").textContent = `Selected: ${fmtDisplayTime(start)} – ${fmtDisplayTime(end)} (${getDurationText(start, end)})`;
  btn.disabled = false;
}

// Step 2 -> Step 3
$("btn-continue-to-features").onclick = () => {
  if (!state.selectedEndSlot) return;
  
  // Render features
  renderFeaturesSection();
  
  hide("step-datetime");
  show("step-features");
  setWizardStep(3);
};

$("btn-back-to-halls").onclick = () => {
  hide("step-datetime");
  show("step-halls");
  setWizardStep(1);
};

// Render Step 3: Features
function renderFeaturesSection() {
  const btnSelectAll = $("btn-select-all-feats");
  if (btnSelectAll) {
    btnSelectAll.textContent = "Select All";
  }
  const container = $("hall-features-list");
  container.innerHTML = "";
  
  const features = state.selectedHall.features || [];
  if (!features.length) {
    container.innerHTML = `<p class="instructions">No custom amenities available for this room. Proceed to the next step.</p>`;
    return;
  }
  
  features.forEach((feat, index) => {
    const item = document.createElement("div");
    item.className = "feature-checkbox-row";
    item.innerHTML = `
      <label class="checkbox-label">
        <input type="checkbox" class="feature-opt-cb" data-feat="${feat}" id="feat-cb-${index}" />
        <div class="checkbox-custom"></div>
        <span>${feat}</span>
      </label>
    `;
    container.appendChild(item);
  });
  
  updateFeaturesSummary();
  
  // Setup checkbox change listeners
  document.querySelectorAll(".feature-opt-cb").forEach(cb => {
    cb.onchange = updateFeaturesSummary;
  });
}

function getSelectedFeatures() {
  const list = [];
  document.querySelectorAll(".feature-opt-cb:checked").forEach(cb => {
    list.push(cb.getAttribute("data-feat"));
  });
  return list;
}

function updateFeaturesSummary() {
  const feats = getSelectedFeatures();
  $("features-summary-text").textContent = feats.length ? `Selected amenities: ${feats.join(", ")}` : "No special hardware features selected";
}

// Select/Deselect All Features Logic
$("btn-select-all-feats").onclick = () => {
  const checkboxes = document.querySelectorAll(".feature-opt-cb");
  const allChecked = Array.from(checkboxes).every(cb => cb.checked);
  checkboxes.forEach(cb => {
    cb.checked = !allChecked;
  });
  $("btn-select-all-feats").textContent = allChecked ? "Select All" : "Deselect All";
  updateFeaturesSummary();
};

// Step 3 -> Step 4
$("btn-continue-to-info").onclick = () => {
  const start = state.selectedStartSlot;
  const end = state.selectedEndSlot;
  const support = $("c-support-staff").checked ? "Yes" : "No";
  const feats = getSelectedFeatures().join(", ") || "None";
  
  $("confirm-summary").innerHTML = `
    <p><strong>Hall Name:</strong> ${state.selectedHall.name}</p>
    <p><strong>Booking Date:</strong> ${state.date}</p>
    <p><strong>Scheduled Time:</strong> ${fmtDisplayTime(start)} – ${fmtDisplayTime(end)} (${getDurationText(start, end)})</p>
    <p><strong>Technical Staff requested:</strong> ${support}</p>
    <p><strong>Linked Amenities:</strong> ${feats}</p>
  `;
  
  $("confirm-error").innerHTML = "";
  
  hide("step-features");
  show("step-confirm");
  setWizardStep(4);
};

$("btn-back-to-datetime").onclick = () => {
  hide("step-features");
  show("step-datetime");
  setWizardStep(2);
};

$("btn-back-to-features").onclick = () => {
  hide("step-confirm");
  show("step-features");
  setWizardStep(3);
};

// Step 4: Register Booking Submit
$("btn-book").onclick = async () => {
  const name = $("c-name").value.trim();
  const purpose = $("c-purpose").value.trim();
  
  if (!name) { $("c-name").focus(); return; }
  if (!purpose) { $("c-purpose").focus(); return; }
  
  const payload = {
    hall_id: state.selectedHall.id,
    booking_date: state.date,
    start_time: state.selectedStartSlot,
    end_time: state.selectedEndSlot,
    booked_by: name,
    dept: $("c-dept").value,
    purpose: purpose,
    support_staff_requested: $("c-support-staff").checked,
    scientist_designation: $("c-designation").value,
    project_id: $("c-project-id").value.trim() || null,
    attendees_count: parseInt($("c-attendees").value) || 1,
    features_requested: getSelectedFeatures().join(", ") || null
  };
  
  try {
    const res = await api("/api/bookings", { method: "POST", body: JSON.stringify(payload) });
    
    // Render Done Details Box
    $("done-details").innerHTML = `
      <p><strong>Hall:</strong> ${state.selectedHall.name}</p>
      <p><strong>Date:</strong> ${state.date}</p>
      <p><strong>Time:</strong> ${fmtDisplayTime(payload.start_time)} – ${fmtDisplayTime(payload.end_time)}</p>
      <p><strong>Staff Scientist:</strong> ${payload.scientist_designation} ${payload.booked_by}</p>
      <p><strong>Division:</strong> ${payload.dept}</p>
      <p><strong>Project ID:</strong> ${payload.project_id || "N/A"}</p>
      <p><strong>IT Stand-by Support:</strong> ${payload.support_staff_requested ? "Requested" : "None"}</p>
    `;
    
    $("done-code").textContent = res.cancel_code;
    
    hide("step-confirm");
    show("step-done");
    
    // Hide progress bar and hero header on success screen
    hide("step-wizard");
    hide("hero-banner");
    
    $("step-done").scrollIntoView({ behavior: "smooth" });
  } catch (e) {
    const msg = (e && e.message) ? e.message : "Could not register booking.";
    $("confirm-error").innerHTML = `<div class="error-msg">${msg} Someone may have booked this slot. Please click back and select another slot.</div>`;
  }
};

$("btn-new").onclick = () => location.reload();

// Initialise
init();
