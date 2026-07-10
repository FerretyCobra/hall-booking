// ICMR NITVAR Booking Portal JS
const $ = (id) => document.getElementById(id);

const state = {
  halls: [],
  selectedHall: null,
  date: null, // "YYYY-MM-DD"
  cfg: { day_start: "09:00", day_end: "18:00", slot_minutes: 30 }, // default fallback, populated dynamically
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
  for (let i = 1; i <= 5; i++) {
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
  try {
    const config = await api("/api/config");
    state.cfg = {
      day_start: config.day_start || "09:00",
      day_end: config.day_end || "18:00",
      slot_minutes: config.slot_minutes || 30
    };
    
    // Dynamic Dropdown Seeding
    if (config.departments) {
      const deptEl = $("c-dept");
      deptEl.innerHTML = "";
      config.departments.forEach(d => {
        const opt = document.createElement("option");
        opt.value = d;
        opt.textContent = d;
        deptEl.appendChild(opt);
      });
    }
    if (config.designations) {
      const desigEl = $("c-designation");
      desigEl.innerHTML = "";
      config.designations.forEach(d => {
        const opt = document.createElement("option");
        opt.value = d;
        opt.textContent = d;
        desigEl.appendChild(opt);
      });
    }
    if (config.stationery) {
      state.stationeryList = config.stationery;
      renderStationeryOptions();
    }
  } catch (e) {
    console.error("Error loading config", e);
  }
  
  // Set up custom time input limits dynamically based on loaded config
  const cStart = $("c-start-time");
  const cEnd = $("c-end-time");
  if (cStart && cEnd) {
    cStart.min = state.cfg.day_start;
    cStart.max = state.cfg.day_end;
    cStart.step = state.cfg.slot_minutes * 60; // HTML step is in seconds
    cEnd.min = state.cfg.day_start;
    cEnd.max = state.cfg.day_end;
    cEnd.step = state.cfg.slot_minutes * 60;
  }
  
  await loadHalls();
  renderHalls();
  setWizardStep(1);
  setupSearchFilters(); // setup UI filters for halls
  setupBookingCancellationUI(); // setup UI elements for cancellation
  setupBookingModificationUI(); // setup UI elements for modification
  setupStepDetailsUI(); // Setup the new Meeting Details wizard step listeners
}

// Fetch halls from backend
let allHalls = [];
async function loadHalls() {
  try {
    allHalls = await api("/api/halls");
    state.halls = [...allHalls];
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
    
    const imgUrl = hall.image ? `/static/images/${hall.image}` : '/static/images/hall_placeholder.png';
    card.innerHTML = `
      <div class="hall-image-container">
        <img src="${imgUrl}" alt="${hall.name}" class="hall-card-img" />
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

// Check if a slot overlaps with any confirmed booking
function isSlotBusy(timeStr) {
  const slotStart = toMin(timeStr);
  const slotEnd = slotStart + state.cfg.slot_minutes;
  return state.bookings.find(b => toMin(b.start) < slotEnd && toMin(b.end) > slotStart);
}

// Render Time Grid
function renderGrid() {
  const grid = $("tl-grid");
  grid.innerHTML = "";
  
  const startM = toMin(state.cfg.day_start); // 09:30
  const endM = toMin(state.cfg.day_end);     // 17:30
  
  for (let m = startM; m < endM; m += state.cfg.slot_minutes) {
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
      for (let m = startMin; m < slotMin; m += state.cfg.slot_minutes) {
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
    $("c-start-time").value = state.selectedStartSlot || state.cfg.day_start;
    if (state.selectedEndSlot) {
      $("c-end-time").value = state.selectedEndSlot;
    } else if (state.selectedStartSlot) {
      $("c-end-time").value = fmt(toMin(state.selectedStartSlot) + state.cfg.slot_minutes);
    } else {
      $("c-end-time").value = fmt(toMin(state.cfg.day_start) + state.cfg.slot_minutes);
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
  
  if (toMin(start) < toMin(state.cfg.day_start) || toMin(end) > toMin(state.cfg.day_end)) {
    $("tl-summary").textContent = `Error: Booking must be within ${state.cfg.day_start} to ${state.cfg.day_end}`;
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
  const btn = $("btn-continue-to-details");
  if (!btn) return;
  
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
$("btn-continue-to-details").onclick = () => {
  if (!state.selectedEndSlot) return;
  
  hide("step-datetime");
  show("step-details");
  setWizardStep(3);
  
  // Refresh attendee count sync & stationery labels
  const attCount = parseInt($("c-details-attendees").value, 10) || 10;
  updateStationeryLabels(attCount);
  autoSelectFoodBasedOnTime();
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

// Step 4 (Features) -> Step 5 (Confirm)
$("btn-continue-to-info").onclick = () => {
  const start = state.selectedStartSlot;
  const end = state.selectedEndSlot;
  const support = $("c-support-staff").checked ? "Yes" : "No";
  const housekeeping = $("c-housekeeping-requested").checked ? "Yes" : "No";
  const feats = getSelectedFeatures().join(", ") || "None";
  const stationeryText = getSelectedStationery() || "None";
  const foodText = getSelectedFood() || "None";
  const attendeesCount = parseInt($("c-details-attendees").value, 10) || 10;
  
  // Sync attendee amount to the confirmation page disabled field
  $("c-attendees").value = attendeesCount;
  
  $("confirm-summary").innerHTML = `
    <p><strong>Hall Name:</strong> ${state.selectedHall.name}</p>
    <p><strong>Booking Date:</strong> ${state.date}</p>
    <p><strong>Scheduled Time:</strong> ${fmtDisplayTime(start)} – ${fmtDisplayTime(end)} (${getDurationText(start, end)})</p>
    <p><strong>Attendees:</strong> ${attendeesCount}</p>
    <p><strong>Virtual Meeting:</strong> ${$("c-virtual-meeting").checked ? "Yes" : "No"}</p>
    <p><strong>Stationery:</strong> ${stationeryText}</p>
    <p><strong>Catering/Refreshments:</strong> ${foodText}</p>
    <p><strong>Technical Staff requested:</strong> ${support}</p>
    <p><strong>Housekeeping Staff requested:</strong> ${housekeeping}</p>
    <p><strong>Linked Amenities:</strong> ${feats}</p>
  `;
  
  $("confirm-error").innerHTML = "";
  
  hide("step-features");
  show("step-confirm");
  setWizardStep(5);
};

$("btn-back-to-datetime").onclick = () => {
  hide("step-details");
  show("step-datetime");
  setWizardStep(2);
};

$("btn-back-to-features").onclick = () => {
  hide("step-confirm");
  show("step-features");
  setWizardStep(4);
};

// Step 4 (Features) Back button
$("btn-back-to-details").onclick = () => {
  hide("step-features");
  show("step-details");
  setWizardStep(3);
};

// Step 3 (Details) Continue button
$("btn-continue-to-features").onclick = () => {
  renderFeaturesSection();
  
  hide("step-details");
  show("step-features");
  setWizardStep(4);
};

// Step 5: Register Booking Submit
$("btn-book").onclick = async () => {
  const name = $("c-name").value.trim();
  const purpose = $("c-purpose").value.trim();
  const coordName = $("c-coord-name").value.trim();
  const coordPhone = $("c-coord-phone").value.trim();
  const coordEmail = $("c-coord-email").value.trim();
  
  if (!name) { $("c-name").focus(); return; }
  if (!coordName) { $("c-coord-name").focus(); return; }
  if (!coordPhone) { $("c-coord-phone").focus(); return; }
  if (!coordEmail) { $("c-coord-email").focus(); return; }
  
  // Quick email format regex validation
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(coordEmail)) {
    alert("Please enter a valid email address for the coordinator.");
    $("c-coord-email").focus();
    return;
  }
  
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
    housekeeping_requested: $("c-housekeeping-requested").checked,
    scientist_designation: $("c-designation").value,
    project_id: $("c-project-id").value.trim() || null,
    attendees_count: parseInt($("c-details-attendees").value, 10) || 10,
    features_requested: getSelectedFeatures().join(", ") || null,
    coordinator_name: coordName,
    coordinator_phone: coordPhone,
    coordinator_email: coordEmail,
    virtual_meeting_requested: $("c-virtual-meeting").checked,
    stationery_requested: getSelectedStationery() || null,
    food_requested: getSelectedFood() || null
  };
  
  try {
    let res;
    if (state.isUpdating) {
      payload.cancel_code = state.updateCancelCode;
      res = await api("/api/bookings/by-code/update", { method: "POST", body: JSON.stringify(payload) });
    } else {
      res = await api("/api/bookings", { method: "POST", body: JSON.stringify(payload) });
    }
    
    // Status display message
    let statusMsg = "";
    if (res.status === "pending_approval") {
      statusMsg = `
        <div style="background: #fff7ed; border: 1px solid #ffedd5; color: #c2410c; padding: 12px; border-radius: 8px; margin-bottom: 16px; font-weight: 500; text-align: center;">
          📋 Awaiting Director's Approval. You will receive an email once decided.
        </div>
      `;
    } else {
      statusMsg = `
        <div style="background: #f0fdf4; border: 1px solid #dcfce7; color: #16a34a; padding: 12px; border-radius: 8px; margin-bottom: 16px; font-weight: 500; text-align: center;">
          ✔ Booking ${state.isUpdating ? 'Updated' : 'Confirmed'}. A confirmation email has been sent.
        </div>
      `;
    }
    
    let meetingLinkHtml = "";
    if (payload.virtual_meeting_requested) {
      if (res.meeting_link) {
        meetingLinkHtml = `<p><strong>Virtual Meeting Link:</strong> <a href="${res.meeting_link}" target="_blank" style="color: var(--primary); font-weight: 600; text-decoration: underline;">Join Meeting</a></p>`;
      } else {
        meetingLinkHtml = `<p><strong>Virtual Meeting Link:</strong> <span style="color: var(--text-muted); font-style: italic;">Will be generated upon Director approval</span></p>`;
      }
    }
    
    let stationeryHtml = "";
    if (res.stationery_requested) {
      stationeryHtml = `<p><strong>Stationery:</strong> ${res.stationery_requested}</p>`;
    }
    let foodHtml = "";
    if (res.food_requested) {
      foodHtml = `<p><strong>Catering/Refreshments:</strong> ${res.food_requested}</p>`;
    }
    
    // Render Done Details Box
    $("done-details").innerHTML = `
      ${statusMsg}
      <p><strong>Hall:</strong> ${state.selectedHall.name}</p>
      <p><strong>Date:</strong> ${state.date}</p>
      <p><strong>Time:</strong> ${fmtDisplayTime(payload.start_time)} – ${fmtDisplayTime(payload.end_time)}</p>
      <p><strong>Staff Scientist:</strong> ${payload.scientist_designation} ${payload.booked_by}</p>
      <p><strong>Coordinator:</strong> ${payload.coordinator_name} (${payload.coordinator_phone}, ${payload.coordinator_email})</p>
      <p><strong>Division:</strong> ${payload.dept}</p>
      <p><strong>Project ID:</strong> ${payload.project_id || "N/A"}</p>
      <p><strong>IT Stand-by Support:</strong> ${payload.support_staff_requested ? "Requested" : "None"}</p>
      <p><strong>Housekeeping Staff Support:</strong> ${payload.housekeeping_requested ? "Requested" : "None"}</p>
      ${stationeryHtml}
      ${foodHtml}
      ${meetingLinkHtml}
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

  $("btn-screenshot").onclick = () => {
    const element = $("step-done");
    // Temporarily hide the buttons in the screenshot
    const btnGroup = element.querySelector(".success .button-group") || element.querySelector("div[style*='display: flex']");
    if (btnGroup) btnGroup.style.visibility = "hidden";
    
    html2canvas(element, {
      backgroundColor: "#ffffff",
      scale: 2 // High-res screenshot
    }).then(canvas => {
      if (btnGroup) btnGroup.style.visibility = "visible";
      const link = document.createElement("a");
      link.download = `Booking_Receipt_${$("done-code").textContent}.png`;
      link.href = canvas.toDataURL("image/png");
      link.click();
    });
  };

  $("btn-new").onclick = () => {
  location.reload();
};

// Search & Filter halls list
function populateFeaturesFilter() {
  const select = $("filter-feature");
  if (!select) return;
  const uniqueFeatures = new Set();
  allHalls.forEach(hall => {
    (hall.features || []).forEach(f => {
      const name = f.split(":")[0].trim();
      uniqueFeatures.add(name);
    });
  });
  select.innerHTML = '<option value="">-- All Amenities --</option>' + 
    Array.from(uniqueFeatures).map(f => `<option value="${f}">${f}</option>`).join("");
}

function applyFilters() {
  const nameQuery = $("filter-name").value.toLowerCase().trim();
  const minCap = parseInt($("filter-capacity").value, 10) || 0;
  const reqFeature = $("filter-feature").value;
  
  state.halls = allHalls.filter(hall => {
    const matchesName = hall.name.toLowerCase().includes(nameQuery);
    const matchesCap = hall.capacity >= minCap;
    
    let matchesFeature = true;
    if (reqFeature) {
      matchesFeature = (hall.features || []).some(f => f.startsWith(reqFeature));
    }
    return matchesName && matchesCap && matchesFeature;
  });
  renderHalls();
}

function setupSearchFilters() {
  populateFeaturesFilter();
  $("filter-name").oninput = applyFilters;
  $("filter-capacity").oninput = applyFilters;
  $("filter-feature").onchange = applyFilters;
  $("btn-clear-filters").onclick = () => {
    $("filter-name").value = "";
    $("filter-capacity").value = "0";
    $("filter-feature").value = "";
    applyFilters();
  };
}

// Cancel Booking UI
function setupBookingCancellationUI() {
  $("link-cancel-booking").onclick = (e) => {
    e.preventDefault();
    hide("step-halls");
    show("step-cancel");
    $("cancel-error").innerHTML = "";
    $("c-cancel-code").value = "";
  };
  
  $("btn-cancel-back").onclick = () => {
    hide("step-cancel");
    show("step-halls");
  };
  
  $("btn-submit-cancel").onclick = async () => {
    const cancelCode = $("c-cancel-code").value.trim().toUpperCase();
    
    if (!cancelCode) {
      $("cancel-error").innerHTML = `<div class="error-msg">Please enter your Cancel Code.</div>`;
      return;
    }
    
    try {
      await api("/api/bookings/by-code/cancel", {
        method: "POST",
        body: JSON.stringify({ cancel_code: cancelCode })
      });
      
      alert("Booking cancelled successfully! The slots have been freed up.");
      hide("step-cancel");
      show("step-halls");
      await loadHalls();
      renderHalls();
    } catch (e) {
      console.error(e);
      const msg = typeof e === "string" ? e : (e.message || "Failed to cancel booking. Please check your Cancel Code.");
      $("cancel-error").innerHTML = `<div class="error-msg">${msg}</div>`;
    }
  };
}

// Modify Booking UI
function setupBookingModificationUI() {
  $("link-modify-booking").onclick = (e) => {
    e.preventDefault();
    hide("step-halls");
    show("step-modify");
    $("modify-error").innerHTML = "";
    $("m-cancel-code").value = "";
  };
  
  $("btn-modify-back").onclick = () => {
    hide("step-modify");
    show("step-halls");
  };
  
  $("btn-submit-modify").onclick = async () => {
    const cancelCode = $("m-cancel-code").value.trim().toUpperCase();
    
    if (!cancelCode) {
      $("modify-error").innerHTML = `<div class="error-msg">Please enter your Cancel Code.</div>`;
      return;
    }
    
    try {
      const booking = await api("/api/bookings/by-code?cancel_code=" + cancelCode);
      
      // Load booking details into state
      state.isUpdating = true;
      state.updateCancelCode = cancelCode;
      
      const hall = allHalls.find(h => h.id === booking.hall_id);
      if (!hall) {
        throw new Error("Associated hall not found or archived.");
      }
      
      state.selectedHall = hall;
      state.date = booking.booking_date;
      state.selectedStartSlot = booking.start_time;
      state.selectedEndSlot = booking.end_time;
      
      // Fill UI fields
      $("c-details-attendees").value = booking.attendees_count || 10;
      $("c-virtual-meeting").checked = !!booking.virtual_meeting_requested;
      
      // Parse food
      $("c-food-requested").checked = !!booking.food_requested;
      const foodContainer = document.getElementById("food-options-container");
      if (booking.food_requested) {
        foodContainer.classList.remove("hidden");
        const list = booking.food_requested.split(", ");
        $("food-morning-tea").checked = list.includes("Morning Tea");
        $("food-lunch").checked = list.includes("Lunch");
        $("food-evening-tea").checked = list.includes("Evening Tea");
      } else {
        foodContainer.classList.add("hidden");
        $("food-morning-tea").checked = false;
        $("food-lunch").checked = false;
        $("food-evening-tea").checked = false;
      }
      
      // Parse stationery
      document.querySelectorAll(".stationery-opt-cb").forEach(cb => cb.checked = false);
      document.querySelectorAll(".qty-container").forEach(div => div.classList.add("hidden"));
      if (booking.stationery_requested) {
        const items = booking.stationery_requested.split(", ");
        items.forEach(item => {
          const lastIdx = item.lastIndexOf(" x");
          if (lastIdx !== -1) {
            const name = item.substring(0, lastIdx);
            const qty = item.substring(lastIdx + 2);
            document.querySelectorAll(".stationery-opt-cb").forEach(cb => {
              if (cb.value === name) {
                cb.checked = true;
                const idx = cb.getAttribute("data-idx");
                const qtyInput = document.getElementById("st-qty-" + idx);
                if (qtyInput) qtyInput.value = qty;
                const wrapper = document.getElementById("qty-wrapper-" + idx);
                if (wrapper) wrapper.classList.remove("hidden");
              }
            });
          }
        });
      }
      
      // Technical + Housekeeping
      $("c-support-staff").checked = !!booking.support_staff_requested;
      $("c-housekeeping-requested").checked = !!booking.housekeeping_requested;
      
      // Info step
      $("c-name").value = booking.booked_by || "";
      $("c-designation").value = booking.scientist_designation || "";
      $("c-dept").value = booking.dept || "";
      $("c-project-id").value = booking.project_id || "";
      $("c-coord-name").value = booking.coordinator_name || "";
      $("c-coord-phone").value = booking.coordinator_phone || "";
      $("c-coord-email").value = booking.coordinator_email || "";
      $("c-purpose").value = booking.purpose || "";
      $("c-attendees").value = booking.attendees_count || 10;
      
      // Update details summary text
      updateDetailsSummary();
      
      // Transition to date & time step
      hide("step-modify");
      show("step-datetime");
      setWizardStep(2);
      
      $("selected-hall-name").textContent = `Modify booking: ${hall.name}`;
      renderDatePicker();
      await fetchAvailability();
      
    } catch (e) {
      console.error(e);
      const msg = typeof e === "string" ? e : (e.message || "Failed to load booking. Please check your Cancel Code.");
      $("modify-error").innerHTML = `<div class="error-msg">${msg}</div>`;
    }
  };
}

// ---------- Step 3 (Meeting Details) Helpers & Setup ----------

function renderStationeryOptions() {
  const container = $("stationery-list-container");
  if (!container) return;
  container.innerHTML = "";
  
  if (!state.stationeryList || !state.stationeryList.length) {
    container.innerHTML = '<p class="muted">No stationery configurations set.</p>';
    return;
  }
  
  const attendeeCount = parseInt($("c-details-attendees").value, 10) || 10;
  
  state.stationeryList.forEach((item, idx) => {
    const itemEsc = item.replace(/"/g, '&quot;');
    container.innerHTML += `
      <div style="display: flex; align-items: center; justify-content: space-between; gap: 8px; border: 1px solid var(--border); padding: 8px 12px; border-radius: 6px; background: var(--bg-subtle);">
        <label class="checkbox-label" style="font-size: 13.5px; margin: 0; flex-grow: 1;">
          <input type="checkbox" class="stationery-opt-cb" value="${itemEsc}" id="st-opt-${idx}" data-idx="${idx}" />
          <div class="checkbox-custom"></div>
          <strong>${item}</strong>
        </label>
        <div class="qty-container hidden" id="qty-wrapper-${idx}" style="display: flex; align-items: center; gap: 6px;">
          <span style="font-size: 12px; color: var(--text-muted);">Qty:</span>
          <input type="number" class="stationery-qty-input" id="st-qty-${idx}" min="1" max="1000" value="${attendeeCount}" style="width: 60px; padding: 4px; border: 1px solid var(--border); border-radius: 4px; text-align: center;" />
        </div>
      </div>
    `;
  });
  
  // Re-attach change listeners to toggle quantity input and update summary
  document.querySelectorAll(".stationery-opt-cb").forEach(cb => {
    cb.onchange = (e) => {
      const idx = e.target.getAttribute("data-idx");
      const qtyWrapper = $(`qty-wrapper-${idx}`);
      if (qtyWrapper) {
        if (e.target.checked) {
          qtyWrapper.classList.remove("hidden");
        } else {
          qtyWrapper.classList.add("hidden");
        }
      }
      updateDetailsSummary();
    };
  });

  document.querySelectorAll(".stationery-qty-input").forEach(input => {
    input.oninput = updateDetailsSummary;
  });
}

function updateStationeryLabels(count) {
  document.querySelectorAll(".stationery-qty-input").forEach(input => {
    input.value = count;
  });
  updateDetailsSummary();
}

function autoSelectFoodBasedOnTime() {
  const start = state.selectedStartSlot;
  const end = state.selectedEndSlot;
  if (!start || !end) return;

  const toMin = (t) => {
    const parts = t.split(":");
    return parseInt(parts[0], 10) * 60 + parseInt(parts[1], 10);
  };

  const sMin = toMin(start);
  const eMin = toMin(end);

  // Overlaps:
  // Morning Tea: 09:00 - 11:30 (540 - 690)
  const overlapsMorning = (sMin < 690 && eMin > 540);
  // Lunch: 12:00 - 14:30 (720 - 870)
  const overlapsLunch = (sMin < 870 && eMin > 720);
  // Evening Tea: 15:00 - 17:30 (900 - 1050)
  const overlapsEvening = (sMin < 1050 && eMin > 900);

  $("food-morning-tea").checked = overlapsMorning;
  $("food-lunch").checked = overlapsLunch;
  $("food-evening-tea").checked = overlapsEvening;
  
  updateDetailsSummary();
}

function getSelectedStationery() {
  const selected = [];
  document.querySelectorAll(".stationery-opt-cb:checked").forEach(cb => {
    const idx = cb.getAttribute("data-idx");
    const qtyInput = $(`st-qty-${idx}`);
    const qty = parseInt(qtyInput.value, 10) || 1;
    selected.push(`${cb.value} x${qty}`);
  });
  return selected.join(", ");
}

function getSelectedFood() {
  if (!$("c-food-requested").checked) return null;
  const selected = [];
  if ($("food-morning-tea").checked) selected.push("Morning Tea");
  if ($("food-lunch").checked) selected.push("Lunch");
  if ($("food-evening-tea").checked) selected.push("Evening Tea");
  return selected.join(", ") || null;
}

function updateDetailsSummary() {
  const count = parseInt($("c-details-attendees").value, 10) || 10;
  const virtual = $("c-virtual-meeting").checked ? "Virtual Link" : "In-Person";
  
  const selectedItems = [];
  document.querySelectorAll(".stationery-opt-cb:checked").forEach(cb => {
    const idx = cb.getAttribute("data-idx");
    const qtyInput = $(`st-qty-${idx}`);
    const qty = qtyInput ? qtyInput.value : count;
    selectedItems.push(`${cb.value} (${qty})`);
  });
  
  const food = getSelectedFood();
  
  let summary = `${count} attendees &middot; ${virtual}`;
  if (selectedItems.length > 0) summary += ` &middot; Stationery: ${selectedItems.join(", ")}`;
  if (food) summary += ` &middot; Refreshments requested (${food})`;
  
  $("details-summary-text").innerHTML = summary;
}

function setupStepDetailsUI() {
  // Sync attendee amount oninput
  $("c-details-attendees").oninput = (e) => {
    const val = parseInt(e.target.value, 10) || 1;
    updateStationeryLabels(val);
  };
  
  // Toggle food options sub-container
  $("c-food-requested").onchange = (e) => {
    if (e.target.checked) {
      $("food-options-container").classList.remove("hidden");
    } else {
      $("food-options-container").classList.add("hidden");
    }
    updateDetailsSummary();
  };
  
  // Re-map the food checkbox handler with selector support since $ custom function is used
  $("c-food-requested").addEventListener("change", (e) => {
    const container = document.getElementById("food-options-container");
    if (e.target.checked) {
      container.classList.remove("hidden");
    } else {
      container.classList.add("hidden");
    }
    updateDetailsSummary();
  });
  
  $("c-virtual-meeting").onchange = updateDetailsSummary;
  $("food-morning-tea").onchange = updateDetailsSummary;
  $("food-lunch").onchange = updateDetailsSummary;
  $("food-evening-tea").onchange = updateDetailsSummary;
}

// Initialise
init();
