// Nineveh International Film Festival 2nd Edition - Step-by-Step Booking Wizard Logic



let seatsData = [];
generateLocalSeatsFallback();

let selectedSeats = [];

let categoryCounts = {

  cat_guest: 0

};



let attendeesList = []; // Array of { name, category }

let currentStep = 1;

let html5QrcodeScanner = null;

let generatedTicketsData = [];



const LIVE_SERVER_URL = window.location.origin;

const API_BASE = '/api'; // نفس السيرفر الذي يقدّم الموقع (يعمل محلياً وأونلاين)



// On Page Load

document.addEventListener('DOMContentLoaded', () => {
  openGateManual();
  try { fetchSeats(); } catch(e){ generateLocalSeatsFallback(); }
  try { checkURLTicketParam(); } catch(e){}

  // Start at Step 1
  goToStep(1);
});



function openGateManual() {

  const gate = document.getElementById('gateOverlay');

  if (gate) {

    gate.classList.add('opened');

    setTimeout(() => {

      try { gate.style.display = 'none'; } catch(e){}

      try { gate.remove(); } catch(e){}

    }, 1200);

  }

}



// Check if ticket query parameter exists in URL (e.g. ?ticket=NIFF2-XXXX)

async function checkURLTicketParam() {

  const urlParams = new URLSearchParams(window.location.search);

  const ticketId = urlParams.get('ticket');

  const paramName = urlParams.get('name');

  const paramSeat = urlParams.get('seat');

  const paramCat = urlParams.get('cat') || 'ضيوف المهرجان';



  if (ticketId) {

    openGateManual();



    const baseId = ticketId.includes('-') ? ticketId.split('-').slice(0, 2).join('-') : ticketId;



    // Instant Zero-Delay Ticket Rendering from URL parameters

    if (paramName && paramSeat) {

      const instantAttendee = [{ name: paramName, category: paramCat, seatCode: paramSeat }];

      showMultiTicketModal(instantAttendee, baseId, `${LIVE_SERVER_URL}/pdfs/${baseId}.pdf`, true);



      // Background async sync

      try {

        fetch(`${API_BASE}/verify/${ticketId}`).then(r => r.json()).then(data => {

          if (data && data.booking) {

            const isApproved = (data.approved === true || data.booking.status === 'approved');

            const attendees = data.booking.attendees || instantAttendee;

            showMultiTicketModal(attendees, baseId, `${LIVE_SERVER_URL}/pdfs/${baseId}.pdf`, isApproved);

          }

        }).catch(e => {});

      } catch(e) {}

      return;

    }

    

    let isRendered = false;

    try {

      const res = await fetch(`${API_BASE}/verify/${ticketId}`);

      const data = await res.json();

      if (data.booking) {

        const b = data.booking;

        const attendees = b.attendees || [{ name: b.name, category: b.category, seatCode: (b.seatCodes || ['R1-S01'])[0] }];

        const isApproved = (data.approved === true || b.status === 'approved');

        showMultiTicketModal(attendees, baseId, `${LIVE_SERVER_URL}/pdfs/${baseId}.pdf`, isApproved);

        isRendered = true;

      }

    } catch(e) {}



    if (!isRendered) {

      const localBookings = JSON.parse(localStorage.getItem('niff2_bookings') || '[]');

      const found = localBookings.find(b => b.id.toUpperCase() === ticketId.toUpperCase());

      if (found) {

        const attendees = found.attendees || [{ name: found.name, category: found.category, seatCode: found.seatCodes[0] }];

        showMultiTicketModal(attendees, baseId, `${LIVE_SERVER_URL}/pdfs/${baseId}.pdf`, found.status === 'approved');

      } else {

        const fallbackAttendee = [{ name: 'ضيف المهرجان', category: 'ضيوف المهرجان', seatCode: 'مخصص' }];

        showMultiTicketModal(fallbackAttendee, baseId, `${LIVE_SERVER_URL}/pdfs/${baseId}.pdf`, true);

      }

    }

  }

}



// Fetch 800 Seats Data

async function fetchSeats() {
  try {
    const res = await fetch(`${API_BASE}/seats`);
    const data = await res.json();
    if (data.seats && data.seats.length > 0) {
      seatsData = data.seats;
    } else {
      generateLocalSeatsFallback();
    }
  } catch (err) {
    generateLocalSeatsFallback();
  }
  renderUnified800SeatsGrid();
}



// Fallback Seats Generator (Theater Blocks B, C, D, E, F + 4000 Outdoor Seats)
function generateLocalSeatsFallback() {
  seatsData = [];
  let idCounter = 1;

  // حسب الخريطة: B 110 | C 110 | D 117 | E 179 | F 117 (القطاع A محجوز)
  const theaterBlocks = [{"id": "B", "rows": [{"row": 1, "count": 10}, {"row": 2, "count": 11}, {"row": 3, "count": 11}, {"row": 4, "count": 12}, {"row": 5, "count": 12}, {"row": 6, "count": 13}, {"row": 7, "count": 13}, {"row": 8, "count": 14}, {"row": 9, "count": 14}]}, {"id": "C", "rows": [{"row": 1, "count": 10}, {"row": 2, "count": 10}, {"row": 3, "count": 11}, {"row": 4, "count": 12}, {"row": 5, "count": 12}, {"row": 6, "count": 13}, {"row": 7, "count": 13}, {"row": 8, "count": 14}, {"row": 9, "count": 15}]}, {"id": "D", "rows": [{"row": 1, "count": 13}, {"row": 2, "count": 13}, {"row": 3, "count": 13}, {"row": 4, "count": 13}, {"row": 5, "count": 13}, {"row": 6, "count": 13}, {"row": 7, "count": 13}, {"row": 8, "count": 13}, {"row": 9, "count": 13}]}, {"id": "E", "rows": [{"row": 1, "count": 20}, {"row": 2, "count": 19}, {"row": 3, "count": 19}, {"row": 4, "count": 19}, {"row": 5, "count": 18}, {"row": 6, "count": 18}, {"row": 7, "count": 17}, {"row": 8, "count": 17}, {"row": 9, "count": 16}, {"row": 10, "count": 16}]}, {"id": "F", "rows": [{"row": 1, "count": 13}, {"row": 2, "count": 13}, {"row": 3, "count": 13}, {"row": 4, "count": 13}, {"row": 5, "count": 13}, {"row": 6, "count": 13}, {"row": 7, "count": 13}, {"row": 8, "count": 13}, {"row": 9, "count": 13}]}];

  theaterBlocks.forEach(b => {
    b.rows.forEach(r => {
      for (let s = 1; s <= r.count; s++) {
        seatsData.push({
          id: idCounter++,
          code: b.id + '-' + r.row + '-' + s,
          block: b.id,
          row: r.row,
          number: s,
          type: 'theater',
          status: 'available'
        });
      }
    });
  });

  // المقاعد الصيفية: 4000 مقعد (50 صف x 80)
  for (let i = 1; i <= 4000; i++) {
    seatsData.push({
      id: idCounter++,
      code: '\u0635\u064a\u0641\u064a-' + i,
      block: '\u0635\u064a\u0641\u064a',
      row: Math.ceil(i / 80),
      number: i,
      type: 'outdoor',
      status: 'available'
    });
  }
}



// Wizard Navigation Manager

function goToStep(stepNum) {

  currentStep = stepNum;



  [1, 2, 3].forEach(s => {

    const stepEl = document.getElementById(`wizard-step-${s}`);

    const indEl = document.getElementById(`step-ind-${s}`);

    if (stepEl) {

      if (s === stepNum) {

        stepEl.classList.remove('hidden');

      } else {

        stepEl.classList.add('hidden');

      }

    }



    if (indEl) {

      if (s <= stepNum) {

        indEl.classList.remove('text-gray-500');

        indEl.classList.add('text-yellow-400');

        const span = indEl.querySelector('span');

        if (span) span.classList.add('bg-yellow-500', 'text-black');

      } else {

        indEl.classList.add('text-gray-500');

        indEl.classList.remove('text-yellow-400');

        const span = indEl.querySelector('span');

        if (span) span.classList.remove('bg-yellow-500', 'text-black');

      }

    }

  });

}



// STEP 1: Adjust Quantity Counters

function adjustCount(catKey, delta) {

  if (typeof categoryCounts[catKey] !== 'number') {

    categoryCounts[catKey] = 0;

  }

  categoryCounts[catKey] = Math.max(0, categoryCounts[catKey] + delta);



  const el = document.getElementById(`count_${catKey}`);

  if (el) {

    el.textContent = categoryCounts[catKey];

  }

  updateTotalTicketsCount();

}



function getTotalTicketsCount() {

  return Object.values(categoryCounts).reduce((a, b) => a + b, 0);

}



function updateTotalTicketsCount() {

  const total = getTotalTicketsCount();

  const totalEl = document.getElementById('totalTicketsCount');

  if (totalEl) totalEl.textContent = total;

}



// STEP 1 -> STEP 2 Transition

function proceedToStep2() {

  let total = getTotalTicketsCount();

  if (total === 0) {

    if (typeof categoryCounts.cat_guest !== 'number') categoryCounts.cat_guest = 0;

    categoryCounts.cat_guest = 1;

    const el = document.getElementById('count_cat_guest');

    if (el) el.textContent = '1';

    updateTotalTicketsCount();

    total = 1;

  }



  // Render Name Input Fields for each attendee (one under another)

  const container = document.getElementById('attendeesNameFields');

  if (!container) return;

  container.innerHTML = '';



  let personIndex = 1;

  const categoryLabels = {

    cat_guest: 'ضيوف المهرجان'

  };



  Object.keys(categoryCounts).forEach(catKey => {

    const count = categoryCounts[catKey];

    for (let i = 0; i < count; i++) {

      const fieldDiv = document.createElement('div');

      fieldDiv.className = 'glass-panel p-3.5 rounded-xl space-y-1.5 border border-yellow-500/20';

      fieldDiv.innerHTML = `

        <div class="flex justify-between items-center text-xs text-yellow-300 font-bold mb-1">

          <span>الحاضر رقم ${personIndex}</span>

          <span class="px-2 py-0.5 rounded bg-yellow-500/20 text-yellow-200 text-[11px]">${categoryLabels[catKey]}</span>

        </div>

        <input type="text" required data-cat="${catKey}" data-cat-label="${categoryLabels[catKey]}" placeholder="أدخل الاسم الكامل للحاضر رقم ${personIndex}" class="attendee-name-input w-full bg-black/60 border border-yellow-500/40 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-yellow-400">

      `;

      container.appendChild(fieldDiv);

      personIndex++;

    }

  });



  const orgWrapper = document.getElementById('step2OrgWrapper');

  const orgInput = document.getElementById('step2OrgInput');

  if (orgWrapper && orgInput) {

    orgWrapper.classList.add('hidden');

    orgInput.required = false;

  }



  goToStep(2);

}



// STEP 2 -> STEP 3 Transition

function proceedToStep3(e) {

  if (e && e.preventDefault) e.preventDefault();



  const nameInputs = document.querySelectorAll('.attendee-name-input');

  attendeesList = [];



  for (let input of nameInputs) {

    const val = input.value.trim();

    if (!val) {

      alert('يرجى ملء الاسم الكامل لجميع الحاضرين');

      return;

    }

    attendeesList.push({

      name: val,

      categoryKey: input.dataset.cat,

      categoryLabel: input.dataset.catLabel

    });

  }



  const totalRequired = attendeesList.length;

  const reqText = document.getElementById('requiredSeatsCountText');

  if (reqText) reqText.textContent = totalRequired;



  const statusText = document.getElementById('seatSelectionStatusText');

  if (statusText) statusText.textContent = `${selectedSeats.length} / ${totalRequired}`;



  selectedSeats = []; // Reset seat selections for new flow

  renderUnified800SeatsGrid();

  updateWizardSeatsListText();



  goToStep(3);

}




let currentWizardSeatTab = 'theater';
let outdoorPage = 1;
const OUTDOOR_PAGE_SIZE = 200;

function populateOutdoorDropdown() {
  const select = document.getElementById('outdoorSeatDropdown');
  if (!select || select.children.length > 5) return;
  
  let html = '<option value="">-- اختر رقم المقعد الصيفي (1 - 4000) --</option>';
  for (let i = 1; i <= 4000; i++) {
    const code = `صيفي-${i}`;
    const isBooked = seatsData.some(s => s.code === code && s.status === 'reserved');
    const isSelected = selectedSeats.includes(code);
    let label = `مقعد صيفي رقم ${i}`;
    if (isBooked) label += ' (محجوز)';
    else if (isSelected) label += ' (محدد)';
    html += `<option value="${code}" ${isBooked ? 'disabled' : ''}>${label}</option>`;
  }
  select.innerHTML = html;
}

function selectOutdoorSeatFromDropdown(seatCode) {
  if (!seatCode) return;
  toggleWizardSeatSelection(seatCode);
}

function switchWizardSeatTab(tab) {
  currentWizardSeatTab = tab;
  const btnTheater = document.getElementById('tab-theater-btn');
  const btnOutdoor = document.getElementById('tab-outdoor-btn');
  const searchBox = document.getElementById('outdoorSearchBox');
  const banner = document.getElementById('cinemaScreenBanner');

  if (tab === 'theater') {
    if (btnTheater) {
      btnTheater.className = "px-4 py-2 rounded-xl text-xs md:text-sm font-bold bg-gold-matte text-black border border-yellow-400 shadow-lg transition-all";
    }
    if (btnOutdoor) {
      btnOutdoor.className = "px-4 py-2 rounded-xl text-xs md:text-sm font-bold bg-black/60 text-yellow-200 border border-yellow-700/40 hover:bg-white/10 transition-all";
    }
    if (searchBox) searchBox.classList.add('hidden');
    if (banner) banner.classList.remove('hidden');
  } else {
    if (btnOutdoor) {
      btnOutdoor.className = "px-4 py-2 rounded-xl text-xs md:text-sm font-bold bg-gold-matte text-black border border-yellow-400 shadow-lg transition-all";
    }
    if (btnTheater) {
      btnTheater.className = "px-4 py-2 rounded-xl text-xs md:text-sm font-bold bg-black/60 text-yellow-200 border border-yellow-700/40 hover:bg-white/10 transition-all";
    }
    if (searchBox) searchBox.classList.remove('hidden');
    if (banner) banner.classList.add('hidden');
    populateOutdoorDropdown();
  }
  renderUnified800SeatsGrid();
}

function jumpToOutdoorSeatWizard() {
  const input = document.getElementById('outdoorSearchInput');
  if (!input || !input.value) return;
  const num = parseInt(input.value);
  if (isNaN(num) || num < 1 || num > 4000) {
    alert('يرجى كتابة رقم مقعد صحيح بين 1 و 4000');
    return;
  }
  const code = `صيفي-${num}`;
  toggleWizardSeatSelection(code);
}

function renderUnified800SeatsGrid() {
  const container = document.getElementById('unifiedSeatsGrid');
  if (!container) return;
  container.innerHTML = '';

  if (currentWizardSeatTab === 'theater') {
    const theaterSeats = seatsData.filter(s => s.type === 'theater' || s.block !== 'صيفي');

    const blocks = {};
    theaterSeats.forEach(s => {
      const bKey = s.block || (s.code ? s.code.split('-')[0] : 'B');
      if (!blocks[bKey]) blocks[bKey] = {};
      if (!blocks[bKey][s.row]) blocks[bKey][s.row] = [];
      blocks[bKey][s.row].push(s);
    });

    // ===== خريطة القاعة (مطابقة للخريطة الرسمية) =====
    // صف علوي: D (يسار) - E (وسط) - F (يمين) | صف سفلي: B (يسار) - [A محجوز] - C (يمين)
    // الصفوف تُعرض من الأعلى رقماً إلى الأقل (الصف 1 الأقرب للأسفل) كما في الخريطة
    function createBlockCard(bKey, tilt) {
      if (!blocks[bKey]) return null;
      const total = Object.values(blocks[bKey]).reduce((n, arr) => n + arr.length, 0);
      const wrap = document.createElement('div');
      wrap.className = 'hall-block';
      wrap.style.setProperty('--tilt', tilt + 'deg');

      const head = document.createElement('div');
      head.className = 'hall-block-title';
      head.innerHTML = `<span class="hall-block-letter">${bKey}</span><span class="hall-block-count">${total} مقعد</span>`;
      wrap.appendChild(head);

      Object.keys(blocks[bKey]).map(Number).sort((x, y) => y - x).forEach(rowNum => {
        const rowLine = document.createElement('div');
        rowLine.className = 'hall-row';

        const rowLabel = document.createElement('span');
        rowLabel.className = 'hall-row-label';
        rowLabel.textContent = rowNum;
        rowLine.appendChild(rowLabel);

        const seatsFlex = document.createElement('div');
        seatsFlex.className = 'hall-row-seats';

        blocks[bKey][rowNum].sort((x, y) => x.number - y.number).forEach(seat => {
          const seatEl = document.createElement('div');
          const isSelected = selectedSeats.includes(seat.code);
          const st = seat.status === 'pending' ? 'pending' : seat.status;
          seatEl.className = `seat ${st} ${isSelected ? 'selected' : ''}`;
          seatEl.title = `${seat.code} (بلوك ${seat.block} - صف ${seat.row} - مقعد ${seat.number})`;
          seatEl.textContent = seat.number;
          if (seat.status === 'available') {
            seatEl.onclick = () => toggleWizardSeatSelection(seat.code);
          }
          seatsFlex.appendChild(seatEl);
        });

        rowLine.appendChild(seatsFlex);
        wrap.appendChild(rowLine);
      });
      return wrap;
    }

    const hallWrapper = document.createElement('div');
    hallWrapper.className = 'hall-map';

    const topRow = document.createElement('div');
    topRow.className = 'hall-top';
    [['D', 0], ['E', 0], ['F', 0]].forEach(([k, t]) => { const c = createBlockCard(k, t); if (c) topRow.appendChild(c); });
    hallWrapper.appendChild(topRow);

    const bottomRow = document.createElement('div');
    bottomRow.className = 'hall-bottom';
    const cB = createBlockCard('B', 0);
    const cC = createBlockCard('C', 0);
    if (cB) bottomRow.appendChild(cB);
    const gapA = document.createElement('div');
    gapA.className = 'hall-sector-a';
    gapA.textContent = 'القطاع A — محجوز بالكامل';
    bottomRow.appendChild(gapA);
    if (cC) bottomRow.appendChild(cC);
    hallWrapper.appendChild(bottomRow);

    container.appendChild(hallWrapper);

  } else {
    // Outdoor Mode: 4000 seats grid
    populateOutdoorDropdown();
    const outdoorSeats = seatsData.filter(s => s.type === 'outdoor' || s.block === 'صيفي');
    
    const startIdx = (outdoorPage - 1) * OUTDOOR_PAGE_SIZE;
    const endIdx = Math.min(startIdx + OUTDOOR_PAGE_SIZE, outdoorSeats.length);
    const pageSeats = outdoorSeats.slice(startIdx, endIdx);

    const pagWrapper = document.createElement('div');
    pagWrapper.className = 'flex items-center justify-between text-xs text-yellow-200 font-bold mb-2 px-1';
    pagWrapper.innerHTML = `
      <span>عرض المقاعد الصيفية من ${startIdx + 1} إلى ${endIdx} (من إجمالي 4،000)</span>
      <div class="flex gap-1.5">
        <button type="button" onclick="changeOutdoorPageWizard(-1)" class="px-2.5 py-1 bg-white/10 rounded hover:bg-white/20">السابقة</button>
        <button type="button" onclick="changeOutdoorPageWizard(1)" class="px-2.5 py-1 bg-white/10 rounded hover:bg-white/20">التالية</button>
      </div>
    `;
    container.appendChild(pagWrapper);

    const gridDiv = document.createElement('div');
    gridDiv.className = 'grid grid-cols-5 sm:grid-cols-8 md:grid-cols-10 gap-2 max-h-96 overflow-y-auto p-2 bg-black/40 rounded-xl border border-yellow-700/20';

    pageSeats.forEach(seat => {
      const seatEl = document.createElement('div');
      const isSelected = selectedSeats.includes(seat.code);
      
      seatEl.id = `seat-btn-outdoor-${seat.number}`;
      seatEl.className = `seat ${seat.status} ${isSelected ? 'selected' : ''} !w-full !h-9 text-xs font-bold rounded-lg flex items-center justify-center cursor-pointer select-none`;
      seatEl.title = `المقعد الصيفي رقم ${seat.number}`;
      seatEl.textContent = seat.number;

      if (seat.status === 'available') {
        seatEl.onclick = () => toggleWizardSeatSelection(seat.code);
      }

      gridDiv.appendChild(seatEl);
    });

    container.appendChild(gridDiv);
  }
}

function jumpToOutdoorSeatWizard() {
  const input = document.getElementById('outdoorSearchInput');
  if (!input || !input.value) return;
  const num = parseInt(input.value);
  if (isNaN(num) || num < 1 || num > 4000) {
    alert('يرجى كتابة رقم مقعد صحيح بين 1 و 4000');
    return;
  }
  outdoorPage = Math.ceil(num / OUTDOOR_PAGE_SIZE);
  renderUnified800SeatsGrid();

  setTimeout(() => {
    const el = document.getElementById(`seat-btn-outdoor-${num}`);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      el.classList.add('ring-4', 'ring-yellow-400');
      setTimeout(() => el.classList.remove('ring-4', 'ring-yellow-400'), 3000);
    }
  }, 150);
}

function changeOutdoorPageWizard(dir) {
  const maxPages = Math.ceil(4000 / OUTDOOR_PAGE_SIZE);
  outdoorPage += dir;
  if (outdoorPage < 1) outdoorPage = 1;
  if (outdoorPage > maxPages) outdoorPage = maxPages;
  renderUnified800SeatsGrid();
}



// Toggle Seat Selection in Unified Wizard

function getMaxRequiredSeats() {
  const countSelect = document.getElementById('unifiedAttendeeCount');
  if (countSelect) {
    const val = parseInt(countSelect.value);
    if (!isNaN(val) && val > 0) return val;
  }
  if (typeof activePersonCount !== 'undefined' && activePersonCount > 0) {
    return activePersonCount;
  }
  if (typeof attendeesList !== 'undefined' && attendeesList && attendeesList.length > 0) {
    return attendeesList.length;
  }
  return 1;
}

function toggleWizardSeatSelection(code) {
  const maxRequired = getMaxRequiredSeats();
  const index = selectedSeats.indexOf(code);

  if (index > -1) {
    selectedSeats.splice(index, 1);
  } else {
    if (selectedSeats.length >= maxRequired) {
      alert(`لقد حددت بالفعل ${maxRequired} مقاعد وهو العدد المطلوب للتذاكر.`);
      return;
    }
    selectedSeats.push(code);
  }

  const statusText = document.getElementById('seatSelectionStatusText');
  if (statusText) statusText.textContent = `${selectedSeats.length} / ${getMaxRequiredSeats()}`;

  updateWizardSeatsListText();
  renderUnified800SeatsGrid();
}



function updateWizardSeatsListText() {

  const textEl = document.getElementById('wizardSeatsListText');

  if (textEl) {

    if (selectedSeats.length > 0) {

      textEl.textContent = selectedSeats.join(', ');

    } else {

      textEl.textContent = 'لم يتم تحديد المقاعد بعد';

    }

  }

}



// STEP 3: Final Registration Submission

async function submitFinalRegistration() {

  // Ensure attendeesList is populated

  if (!attendeesList || attendeesList.length === 0) {

    const nameInputs = document.querySelectorAll('.attendee-name-input');

    attendeesList = [];

    if (nameInputs.length > 0) {

      nameInputs.forEach(input => {

        const val = input.value.trim() || 'ضيف المهرجان';

        attendeesList.push({ name: val, categoryKey: 'cat_guest', categoryLabel: 'ضيوف المهرجان' });

      });

    } else {

      attendeesList = [{ name: 'ضيف المهرجان', categoryKey: 'cat_guest', categoryLabel: 'ضيوف المهرجان' }];

    }

  }



  const requiredCount = attendeesList.length;

  if (selectedSeats.length < requiredCount) {

    alert(`يرجى تحديد ${requiredCount} مقاعد من الخارطة لإكمال الحجز (${selectedSeats.length} محدد حالياً).`);

    return;

  }



  const phoneEl = document.getElementById('mainPhoneInput');

  const orgEl = document.getElementById('step2OrgInput');

  const phone = phoneEl ? phoneEl.value.trim() : '';

  const org = orgEl ? orgEl.value.trim() : '';



  if (!phone) {

    alert('يرجى كتابة رقم الهاتف للتواصل');

    return;

  }



  // Show loading indicator

  showLoadingOverlay('جاري تسجيل طلب الحجز وتوجيه التقرير للمنظم...');



  const registeredAttendees = attendeesList.map((att, idx) => ({

    name: att.name || 'ضيف المهرجان',

    category: att.categoryLabel || 'ضيوف المهرجان',

    seatCode: selectedSeats[idx] || (selectedSeats[0] || 'R1-S01'),

    phone: phone || '',

    organization: org || ''

  }));



  const mainName = registeredAttendees[0] ? registeredAttendees[0].name : 'ضيف المهرجان';



  const payload = {

    seatCodes: selectedSeats,

    name: mainName,

    phone,

    category: registeredAttendees[0].category,

    organization: org,

    personsCount: requiredCount,

    attendees: registeredAttendees

  };



  try {

    const res = await fetch(`${API_BASE}/register`, {

      method: 'POST',

      headers: { 'Content-Type': 'application/json' },

      body: JSON.stringify(payload)

    });



    const result = await res.json();

    if (!res.ok) {

      hideLoadingOverlay();

      alert(result.error || 'حدث خطأ أثناء إجراء الحجز');

      return;

    }



    // Save local backup

    const localBookings = JSON.parse(localStorage.getItem('niff2_bookings') || '[]');

    localBookings.push(result.ticket);

    localStorage.setItem('niff2_bookings', JSON.stringify(localBookings));



    setTimeout(() => {

      hideLoadingOverlay();

      showPendingSubmissionConfirmation(result.ticket || payload);

      fetchSeats();

    }, 1000);



  } catch (err) {

    const mockTicketId = `NIFF2-${Date.now().toString(16).toUpperCase()}`;

    const fallbackBooking = {

      id: mockTicketId,

      name: mainName,

      phone,

      category: registeredAttendees[0].category,

      organization: org,

      personsCount: requiredCount,

      seatCodes: selectedSeats,

      attendees: registeredAttendees,

      status: 'pending_approval',

      createdAt: new Date().toISOString()

    };

    

    // Save to LocalStorage Backup

    const localBookings = JSON.parse(localStorage.getItem('niff2_bookings') || '[]');

    localBookings.push(fallbackBooking);

    localStorage.setItem('niff2_bookings', JSON.stringify(localBookings));



    setTimeout(() => {

      hideLoadingOverlay();

      showPendingSubmissionConfirmation(fallbackBooking);

    }, 1000);

  }

}



// Show Pending Submission Confirmation Box (No Barcode shown at registration stage)

function showPendingSubmissionConfirmation(booking) {

  const modalContainer = document.getElementById('ticketModal');

  if (!modalContainer) return;



  const bookingId = (booking && booking.id) ? booking.id : `NIFF2-${Date.now().toString(16).toUpperCase()}`;

  const bookingName = (booking && booking.name) ? booking.name : 'ضيف المهرجان';

  const seatsStr = (booking && booking.seatCodes && booking.seatCodes.length > 0) ? booking.seatCodes.join(', ') : 'محدد';



  modalContainer.innerHTML = `

    <div class="glass-panel p-6 md:p-8 rounded-3xl border-2 border-yellow-500 max-w-md w-full my-auto text-center space-y-4 shadow-2xl relative">

      <div class="w-16 h-16 bg-amber-500/20 text-yellow-300 rounded-full flex items-center justify-center text-3xl font-black mx-auto border border-amber-500/40 animate-bounce">⏳</div>

      

      <h3 class="text-xl md:text-2xl font-extrabold text-gold-matte">تم استلام طلب حجزكم بنجاح!</h3>

      

      <div class="bg-black/60 p-4 rounded-2xl border border-yellow-500/30 text-right space-y-2 text-xs">

        <p class="flex justify-between border-b border-white/10 pb-1.5">

          <span class="text-gray-400">رقم الحجز:</span>

          <span class="font-mono font-bold text-yellow-300">${bookingId}</span>

        </p>

        <p class="flex justify-between border-b border-white/10 pb-1.5">

          <span class="text-gray-400">اسم المسجل:</span>

          <span class="font-bold text-white">${bookingName}</span>

        </p>

        <p class="flex justify-between">

          <span class="text-gray-400">المقاعد المطلوبة:</span>

          <span class="font-bold text-gold-matte text-sm">${seatsStr}</span>

        </p>

      </div>



      <div class="bg-amber-500/10 p-3.5 rounded-xl border border-amber-500/30 text-xs text-amber-200 leading-relaxed text-right">

        <i class="fa-solid fa-clock ml-1 text-yellow-400"></i>

        طلبكم الآن بانتظار إقرار وموافقة منظم المهرجان.<br>

        <span class="font-bold text-white">ستصلكم التذكرة الرسمية مع باركود الدخول المعتمد مباشرة على الواتساب فور إقرار الحجز.</span>

      </div>



      <button onclick="window.location.reload()" class="w-full py-3 bg-yellow-600/30 text-yellow-200 border border-yellow-500/40 font-extrabold text-xs rounded-xl hover:bg-yellow-600 hover:text-black transition-all">

        العودة للصفحة الرئيسية

      </button>

    </div>

  `;



  modalContainer.classList.remove('hidden');

}



// Show/Hide Loading Overlay

function showLoadingOverlay(msgText) {

  let overlay = document.getElementById('statusLoadingOverlay');

  if (!overlay) {

    overlay = document.createElement('div');

    overlay.id = 'statusLoadingOverlay';

    overlay.className = 'fixed inset-0 bg-black/90 backdrop-blur-md z-50 flex items-center justify-center p-4 text-center';

    document.body.appendChild(overlay);

  }

  overlay.innerHTML = `

    <div class="glass-panel p-8 rounded-3xl border-2 border-yellow-500 max-w-sm w-full space-y-4 shadow-2xl animate-pulse">

      <div class="w-12 h-12 border-4 border-yellow-500 border-t-transparent rounded-full animate-spin mx-auto"></div>

      <h3 class="text-lg font-bold text-gold-matte">${msgText || 'جاري توليد ملف الـ PDF...'}</h3>

      <p class="text-xs text-gray-300">مهرجان نينوى السينمائي الدولي - الدورة الثانية</p>

    </div>

  `;

  overlay.classList.remove('hidden');

}



function hideLoadingOverlay() {

  const overlay = document.getElementById('statusLoadingOverlay');

  if (overlay) overlay.classList.add('hidden');

}



let currentTicketIsApproved = false;



// Render Multi-Attendee Ticket Modal with PDF Link

function showMultiTicketModal(attendees, baseTicketId, pdfUrl, isApproved = false) {

  currentTicketIsApproved = isApproved;

  generatedTicketsData = attendees.map((att, idx) => ({

    id: `${baseTicketId}-${idx+1}`,

    name: att.name,

    category: att.category,

    organization: att.organization,

    seatCode: att.seatCode,

    phone: att.phone

  }));



  const modalContainer = document.getElementById('ticketModal');

  if (!modalContainer) return;



  const modalBody = modalContainer.querySelector('.glass-panel');

  if (modalBody && !document.getElementById('qrcode')) {

    modalBody.innerHTML = `

      <div class="flex justify-between items-center border-b border-yellow-700/30 pb-3 mb-2">

        <h3 class="text-sm md:text-base font-bold text-gold-matte">التذكرة والباركود المعتمد للدخول</h3>

        <button onclick="closeTicketModal()" class="text-gray-400 hover:text-white font-bold text-lg px-2"></button>

      </div>



      <div id="ticketTabsHeader" class="flex gap-2 overflow-x-auto pb-2 mb-2 scrollbar-none"></div>



      <div id="ticketPrintArea" class="glass-panel p-4 rounded-2xl border border-yellow-600/40 space-y-3 bg-[#120304]/90 shadow-2xl relative overflow-hidden">

        <div class="flex items-center justify-between border-b border-yellow-600/30 pb-3">

          <img src="assets/emblem.png?v=5" class="h-12 w-auto" alt="Logo">

          <div class="text-left">

            <span id="ticketBadgeText" class="inline-block bg-green-500/20 text-green-300 px-2.5 py-0.5 rounded-full text-[9px] font-bold border border-green-500/40 mb-1">تذكرة رسمية معتمدة صالحة للدخول </span>

            <h4 class="text-xs font-bold text-gold-matte">مهرجان نينوى السينمائي الدولي</h4>

            <p class="text-[9px] text-gray-300">الدورة الثانية - 2nd Edition</p>

          </div>

        </div>



        <div class="space-y-1.5 text-xs">

          <div class="flex justify-between border-b border-white/10 pb-1">

            <span class="text-gray-400">رقم التذكرة:</span>

            <span id="ticketIdDisplay" class="font-mono font-bold text-yellow-300">--</span>

          </div>

          <div class="flex justify-between border-b border-white/10 pb-1">

            <span class="text-gray-400">اسم المسجل:</span>

            <span id="ticketNameDisplay" class="font-bold text-white">--</span>

          </div>

          <div class="flex justify-between border-b border-white/10 pb-1">

            <span class="text-gray-400">الصفة / الجهة:</span>

            <span id="ticketCategoryDisplay" class="font-bold text-yellow-200">--</span>

          </div>

          <div class="flex justify-between border-b border-white/10 pb-1">

            <span class="text-gray-400">المقعد المخصص:</span>

            <span id="ticketSeatsDisplay" class="font-bold text-gold-matte text-sm">--</span>

          </div>

        </div>



        <div class="bg-[#1c0508] border-2 border-yellow-600/40 rounded-2xl p-4 text-center space-y-3 shadow-2xl relative overflow-hidden">

          <div class="border-b border-yellow-600/30 pb-2">

            <h5 class="text-xs md:text-sm font-extrabold text-gold-matte tracking-wide">

              <i class="fa-solid fa-qrcode text-yellow-400 ml-1"></i>

              باركود دخول - مهرجان نينوى السينمائي الدولي

            </h5>

            <p class="text-[10px] text-yellow-100/70 font-serif">الدورة الثانية - 2nd Edition</p>

          </div>

          <div class="bg-white p-3 rounded-xl inline-block shadow-lg mx-auto">

            <div id="qrcode" class="flex justify-center"></div>

          </div>

          <div class="bg-white p-2.5 rounded-xl shadow-lg mx-auto max-w-xs">

            <svg id="barcodeSvg" class="w-full h-14 mx-auto"></svg>

          </div>

          <div class="pt-1 border-t border-yellow-600/20 text-[10px] text-yellow-200/80 font-bold">

            يرجى إبراز هذا الباركود عند بوابة المسرح الرئيسي للدخول

          </div>

        </div>

      </div>



      <div class="mt-3 space-y-2">

        <a id="ticketPdfBtn" target="_blank" class="w-full py-3 px-3 bg-red-600/30 text-red-200 border border-red-500/50 font-bold text-xs rounded-xl text-center flex items-center justify-center gap-2 shadow-lg hover:bg-red-600 hover:text-white transition-all">

          <i class="fa-solid fa-file-pdf text-base"></i>

          <span>عرض وتنزيل تقرير الـ PDF المرفق للحجز</span>

        </a>

        <button onclick="window.print()" class="w-full py-2 px-3 bg-yellow-700/20 border border-yellow-700/40 text-yellow-200 hover:bg-yellow-600 hover:text-black rounded-xl font-bold text-xs flex items-center justify-center gap-1.5">

          <i class="fa-solid fa-print"></i>

          <span>طباعة / حفظ التذكرة والباركود</span>

        </button>

      </div>

    `;

  }



  const tabsContainer = document.getElementById('ticketTabsHeader');

  if (tabsContainer) {

    tabsContainer.innerHTML = '';

    if (generatedTicketsData.length > 1) {

      generatedTicketsData.forEach((t, i) => {

        const tabBtn = document.createElement('button');

        tabBtn.className = `px-3 py-1.5 rounded-lg text-xs font-bold transition-colors ${i === 0 ? 'bg-yellow-500 text-black' : 'bg-white/10 text-yellow-200 hover:bg-white/20'}`;

        tabBtn.textContent = `تذكرة ${i+1}: ${t.name} (${t.seatCode})`;

        tabBtn.onclick = () => renderTicketCardIndex(i);

        tabsContainer.appendChild(tabBtn);

      });

    }

  }



  const pdfBtn = document.getElementById('ticketPdfBtn');

  if (pdfBtn && pdfUrl) {

    pdfBtn.href = pdfUrl;

  }



  renderTicketCardIndex(0);

  const ticketModal = document.getElementById('ticketModal');

  if (ticketModal) ticketModal.classList.remove('hidden');

}



// Deep-link helper for opening WhatsApp application directly on Mobile & Desktop

function openWhatsAppDirectly(e, targetUrl) {

  if (e && e.preventDefault) e.preventDefault();

  const urlToUse = targetUrl || (document.getElementById('ticketWhatsappBtn') ? document.getElementById('ticketWhatsappBtn').href : '');

  const phone = '9647765681958';

  

  let textParam = '';

  try {

    const urlObj = new URL(urlToUse);

    textParam = urlObj.searchParams.get('text') || '';

  } catch(err) {

    textParam = 'طلب موافقة حجز جديد - مهرجان نينوى السينمائي الدولي (الدورة الثانية)';

  }



  const deepLink = `whatsapp://send?phone=${phone}&text=${encodeURIComponent(textParam)}`;

  const webLink = `https://api.whatsapp.com/send?phone=${phone}&text=${encodeURIComponent(textParam)}`;



  const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);

  if (isMobile) {

    window.location.href = deepLink;

    setTimeout(() => {

      window.open(webLink, '_blank');

    }, 1000);

  } else {

    window.open(webLink, '_blank');

  }

}



window.openWhatsAppDirectly = openWhatsAppDirectly;



function renderTicketCardIndex(index) {

  const t = generatedTicketsData[index];

  if (!t) return;



  const tabBtns = document.querySelectorAll('#ticketTabsHeader button');

  tabBtns.forEach((btn, i) => {

    if (i === index) {

      btn.className = 'px-3 py-1.5 rounded-lg text-xs font-bold bg-yellow-500 text-black';

    } else {

      btn.className = 'px-3 py-1.5 rounded-lg text-xs font-bold bg-white/10 text-yellow-200 hover:bg-white/20';

    }

  });



  const idDisp = document.getElementById('ticketIdDisplay');

  if (idDisp) idDisp.textContent = t.id;



  const nameDisp = document.getElementById('ticketNameDisplay');

  if (nameDisp) nameDisp.textContent = t.name;



  let catText = t.category;

  if (t.organization) catText += ` (${t.organization})`;

  const catDisp = document.getElementById('ticketCategoryDisplay');

  if (catDisp) catDisp.textContent = catText;



  const seatsDisp = document.getElementById('ticketSeatsDisplay');

  if (seatsDisp) seatsDisp.textContent = t.seatCode;



  const statusBadge = document.getElementById('ticketBadgeText');

  if (statusBadge) {

    if (currentTicketIsApproved) {

      statusBadge.textContent = 'تذكرة رسمية معتمدة صالحة للدخول ';

      statusBadge.className = 'inline-block bg-green-500/20 text-green-300 px-2.5 py-0.5 rounded-full text-[9px] font-bold border border-green-500/40 mb-1';

    } else {

      statusBadge.textContent = 'طلب حجز - بانتظار موافقة منظم المهرجان';

      statusBadge.className = 'inline-block bg-amber-500/20 text-amber-300 px-2.5 py-0.5 rounded-full text-[9px] font-bold border border-amber-500/40 mb-1';

    }

  }



  const qrContainer = document.getElementById('qrcode');

  if (qrContainer) {

    qrContainer.innerHTML = '';

    const qrPayload = JSON.stringify({

      event: 'NIFF 2nd Edition',

      id: t.id,

      name: t.name,

      seat: t.seatCode,

      category: t.category

    });



    try {

      if (typeof QRCode !== 'undefined') {

        new QRCode(qrContainer, {

          text: qrPayload,

          width: 140,

          height: 140,

          colorDark: "#1a0507",

          colorLight: "#ffffff",

          correctLevel: QRCode.CorrectLevel.H

        });

      } else {

        qrContainer.innerHTML = `<img src="https://api.qrserver.com/v1/create-qr-code/?size=140x140&data=${encodeURIComponent(qrPayload)}" class="mx-auto w-35 h-35 rounded shadow" alt="QR Code">`;

      }

    } catch(e) {

      qrContainer.innerHTML = `<img src="https://api.qrserver.com/v1/create-qr-code/?size=140x140&data=${encodeURIComponent(qrPayload)}" class="mx-auto w-35 h-35 rounded shadow" alt="QR Code">`;

    }

  }



  try {

    if (typeof JsBarcode !== 'undefined') {

      JsBarcode("#barcodeSvg", t.id, {

        format: "CODE128",

        lineColor: "#1a0507",

        width: 2,

        height: 50,

        displayValue: true,

        fontSize: 12,

        font: "Tajawal"

      });

    } else {

      drawFallbackSVGBarcode(document.getElementById('barcodeSvg'), t.id);

    }

  } catch(e) {

    drawFallbackSVGBarcode(document.getElementById('barcodeSvg'), t.id);

  }

}



// Fallback SVG Barcode Renderer

function drawFallbackSVGBarcode(svgEl, text) {

  if (!svgEl) return;

  svgEl.innerHTML = '';

  svgEl.setAttribute('viewBox', '0 0 300 70');

  

  let x = 10;

  for (let i = 0; i < text.length; i++) {

    const charCode = text.charCodeAt(i);

    const w1 = (charCode % 3) + 1;

    const w2 = (charCode % 2) + 1;

    

    const rect1 = document.createElementNS('http://www.w3.org/2000/svg', 'rect');

    rect1.setAttribute('x', x);

    rect1.setAttribute('y', '5');

    rect1.setAttribute('width', w1);

    rect1.setAttribute('height', '45');

    rect1.setAttribute('fill', '#1a0507');

    svgEl.appendChild(rect1);

    

    x += w1 + w2;

  }

  

  const textEl = document.createElementNS('http://www.w3.org/2000/svg', 'text');

  textEl.setAttribute('x', '150');

  textEl.setAttribute('y', '63');

  textEl.setAttribute('text-anchor', 'middle');

  textEl.setAttribute('fill', '#1a0507');

  textEl.setAttribute('font-size', '11');

  textEl.setAttribute('font-weight', 'bold');

  textEl.textContent = text;

  svgEl.appendChild(textEl);

}



function closeTicketModal() {

  const modal = document.getElementById('ticketModal');

  if (modal) modal.classList.add('hidden');

  goToStep(1);

}



// Bind functions to global window object explicitly for inline HTML onclick handlers

window.openGateManual = openGateManual;

window.goToStep = goToStep;

window.adjustCount = adjustCount;

window.proceedToStep2 = proceedToStep2;

window.proceedToStep3 = proceedToStep3;

window.submitFinalRegistration = submitFinalRegistration;

window.closeTicketModal = closeTicketModal;



let currentBookingCategory = 'theater'; // 'theater' or 'outdoor'
let activePersonCount = 1;

function selectBookingCategory(cat) {
  currentBookingCategory = cat;
  currentWizardSeatTab = cat;

  const btnIndoor = document.getElementById('btn-cat-indoor');
  const btnOutdoor = document.getElementById('btn-cat-outdoor');
  const titleText = document.getElementById('seatCategoryTitleText');
  const searchBox = document.getElementById('outdoorSearchBox');
  const banner = document.getElementById('cinemaScreenBanner');

  if (cat === 'theater') {
    if (btnIndoor) {
      btnIndoor.className = "p-4 rounded-xl border font-bold text-sm transition-all flex flex-col items-center justify-center gap-1 bg-gold-matte text-black border-yellow-400 shadow-lg scale-[1.02]";
    }
    if (btnOutdoor) {
      btnOutdoor.className = "p-4 rounded-xl border font-bold text-sm transition-all flex flex-col items-center justify-center gap-1 bg-black/60 text-yellow-200 border-yellow-700/40 hover:bg-white/10";
    }
    if (titleText) titleText.textContent = "المقاعد والاختيار (المقاعد الداخلية - مسرح الجامعة)";
    if (searchBox) searchBox.classList.add('hidden');
    if (banner) banner.classList.remove('hidden');
  } else {
    if (btnOutdoor) {
      btnOutdoor.className = "p-4 rounded-xl border font-bold text-sm transition-all flex flex-col items-center justify-center gap-1 bg-gold-matte text-black border-yellow-400 shadow-lg scale-[1.02]";
    }
    if (btnIndoor) {
      btnIndoor.className = "p-4 rounded-xl border font-bold text-sm transition-all flex flex-col items-center justify-center gap-1 bg-black/60 text-yellow-200 border border-yellow-700/40 hover:bg-white/10";
    }
    if (titleText) titleText.textContent = "المقاعد والاختيار (المقاعد الخارجية - 4،000 مقعد)";
    if (searchBox) searchBox.classList.remove('hidden');
    if (banner) banner.classList.add('hidden');
    populateOutdoorDropdown();
  }

  selectedSeats = [];
  updateWizardSeatsListText();
  renderUnified800SeatsGrid();
}

function onUnifiedPersonCountChange(countVal) {
  activePersonCount = parseInt(countVal) || 1;
  
  const statusText = document.getElementById('seatSelectionStatusText');
  if (statusText) statusText.textContent = `${selectedSeats.length} / ${activePersonCount}`;

  // If selected seats exceeds new limit, trim selection
  if (selectedSeats.length > activePersonCount) {
    selectedSeats = selectedSeats.slice(0, activePersonCount);
    updateWizardSeatsListText();
    renderUnified800SeatsGrid();
  }

  // Generate additional attendee name fields if count > 1
  const addContainer = document.getElementById('additionalNamesContainer');
  const addFields = document.getElementById('additionalNamesFields');
  
  if (addContainer && addFields) {
    if (activePersonCount > 1) {
      addContainer.classList.remove('hidden');
      let fieldsHtml = '';
      for (let i = 2; i <= activePersonCount; i++) {
        fieldsHtml += `
          <div>
            <label class="block font-bold text-yellow-200/80 text-[11px] mb-1">اسم الحاضر رقم ${i} <span class="text-red-400">*</span></label>
            <input type="text" required data-additional-name="true" placeholder="أدخل اسم الحاضر رقم ${i}" class="w-full bg-black/70 border border-yellow-700/40 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-yellow-400">
          </div>
        `;
      }
      addFields.innerHTML = fieldsHtml;
    } else {
      addContainer.classList.add('hidden');
      addFields.innerHTML = '';
    }
  }
}

async function handleUnifiedFormSubmit(e) {
  if (e && e.preventDefault) e.preventDefault();

  const mainName = document.getElementById('unifiedAttendeeName').value.trim();
  const mainPhone = document.getElementById('unifiedAttendeePhone').value.trim();
  const catName = (currentBookingCategory === 'theater') ? 'المقاعد الداخلية' : 'المقاعد الخارجية';

  if (!mainName || !mainPhone) {
    alert('يرجى كتابة الاسم الثلاثي ورقم الهاتف أولاً');
    return;
  }

  if (selectedSeats.length !== activePersonCount) {
    alert(`عفواً، لقد اخترت ${activePersonCount} تذاكر/أشخاص، يرجى تحديد بالضبط ${activePersonCount} مقاعد من الخارطة.`);
    return;
  }

  // Build attendees list
  attendeesList = [{ name: mainName, categoryKey: 'cat_guest', categoryLabel: catName, seatCode: selectedSeats[0] }];
  
  const additionalInputs = document.querySelectorAll('[data-additional-name="true"]');
  additionalInputs.forEach((input, idx) => {
    const aName = input.value.trim() || `حاضر ${idx + 2}`;
    const sCode = selectedSeats[idx + 1] || selectedSeats[0];
    attendeesList.push({ name: aName, categoryKey: 'cat_guest', categoryLabel: catName, seatCode: sCode });
  });

  const isOutdoor = (currentBookingCategory === 'outdoor') || selectedSeats.every(s => s.startsWith('صيفي'));
  const initialStatus = isOutdoor ? 'approved' : 'pending_approval';

  const payload = {
    name: mainName,
    phone: mainPhone,
    category: catName,
    organization: '-',
    seatCodes: selectedSeats,
    attendees: attendeesList
  };

  try {
    const res = await fetch(`${API_BASE}/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();

    if (data.success && data.booking) {
      const b = data.booking;
      const localBookings = JSON.parse(localStorage.getItem('niff2_bookings') || '[]');
      localBookings.unshift(b);
      localStorage.setItem('niff2_bookings', JSON.stringify(localBookings));

      // Reset form
      document.getElementById('unifiedBookingForm').reset();
      selectedSeats = [];
      onUnifiedPersonCountChange(1);
      fetchSeats();

      if (b.status === 'approved' || isOutdoor) {
        showMultiTicketModal(b.attendees, b.id, `${LIVE_SERVER_URL}/pdfs/${b.id}.pdf`, true);
      } else {
        showPendingSubmissionConfirmation(b);
      }
    } else {
      alert(data.message || data.error || 'حدث خطأ أثناء حفظ الحجز');
    }
  } catch(err) {
    // Offline fallback submission
    const offlineId = 'NIFF2-' + Math.floor(100000 + Math.random() * 900000);
    const offlineBooking = {
      id: offlineId,
      name: mainName,
      phone: mainPhone,
      category: catName,
      seatCodes: selectedSeats,
      attendees: attendeesList,
      status: initialStatus
    };
    const localBookings = JSON.parse(localStorage.getItem('niff2_bookings') || '[]');
    localBookings.unshift(offlineBooking);
    localStorage.setItem('niff2_bookings', JSON.stringify(localBookings));

    // Reset form
    document.getElementById('unifiedBookingForm').reset();
    selectedSeats = [];
    onUnifiedPersonCountChange(1);
    fetchSeats();

    if (isOutdoor) {
      showMultiTicketModal(attendeesList, offlineId, `#`, true);
    } else {
      showPendingSubmissionConfirmation(offlineBooking);
    }
  }
}
