const API_BASE = 'http://192.168.0.204:8000';
let currentUserRole = null; 

function hideAllViews() {
  document.getElementById('landing-page').classList.add('hidden');
  document.getElementById('student-view').classList.add('hidden');
  document.getElementById('admin-view').classList.add('hidden');
}

function showLandingPage() {
  currentUserRole = null;
  hideAllViews();
  document.getElementById('landing-page').classList.remove('hidden');
  document.getElementById('active-role-badge').classList.add('hidden');
  document.getElementById('home-btn').classList.add('hidden');
  
  const codeInput = document.getElementById('access-code');
  if (codeInput) {
      codeInput.value = '';
      const slotBoxes = document.querySelectorAll('#code-slots-display .code-slot');
      slotBoxes.forEach(box => {
        const span = box.querySelector('span');
        if (span) span.textContent = '•';
        box.classList.remove('slot-filled');
      });
  }
}

function updateTopBar(roleLabel) {
  const badge = document.getElementById('active-role-badge');
  badge.textContent = roleLabel;
  badge.classList.remove('hidden');
  document.getElementById('home-btn').classList.remove('hidden');
}

function handleCodeSubmit() {
  const codeInput = document.getElementById('access-code').value.trim().toUpperCase();

  if (codeInput === 'ADMIN') {
    currentUserRole = 'ADMIN';
    hideAllViews();
    document.getElementById('admin-view').classList.remove('hidden');
    document.getElementById('admin-login-section').classList.remove('hidden');
    document.getElementById('admin-dashboard-section').classList.add('hidden');
    updateTopBar('ROLE: ADMIN');
  } 
  else if (codeInput === 'STUDENT') {
    currentUserRole = 'STUDENT';
    hideAllViews();
    document.getElementById('student-view').classList.remove('hidden');
    document.getElementById('student-welcome-text').textContent = 'Logged in as Student. Click Register on any event to verify your Roll Number.';
    updateTopBar('ROLE: STUDENT');
    loadStudentEvents('All');
  } 
  else if (codeInput === 'VISITOR') {
    let savedVisitor = localStorage.getItem('visitorName') || '';
    let visitorName = prompt('Please enter your name for your Visitor Pass:', savedVisitor);
    
    if (!visitorName || !visitorName.trim()) {
      alert('Visitor name is required to view events.');
      return;
    }
    
    localStorage.setItem('visitorName', visitorName.trim());
    currentUserRole = 'VISITOR';
    hideAllViews();
    document.getElementById('student-view').classList.remove('hidden');
    document.getElementById('student-welcome-text').textContent = `Welcome Visitor: ${visitorName.trim()}. Click Register on any event to join.`;
    updateTopBar(`VISITOR: ${visitorName.trim()}`);
    loadStudentEvents('All');
  } 
  else {
    alert('Invalid code! Please enter STUDENT, VISITOR, or ADMIN.');
  }
}

async function loadStudentEvents(statusFilter = 'All') {
  ['All', 'Ongoing', 'Published', 'Completed'].forEach(st => {
    const btn = document.getElementById(`filter-${st}`);
    if (btn) btn.classList.toggle('active-filter', st === statusFilter);
  });

  const grid = document.getElementById('student-events-grid');
  if(!grid) return; 
  grid.innerHTML = '<p class="muted">Loading events from server...</p>';

  try {
    const url = statusFilter === 'All' 
      ? `${API_BASE}/api/activities` 
      : `${API_BASE}/api/activities?status=${encodeURIComponent(statusFilter)}`;

    const response = await fetch(url);
    const data = await response.json();

    if (!response.ok) {
      alert(data.detail || 'Error loading activities.');
      return;
    }

    renderStudentEvents(Array.isArray(data) ? data : []);
  } catch (error) {
    console.error('Fetch error:', error);
    grid.innerHTML = `<p class="muted" style="color:#ef4444;">Could not connect to ${API_BASE}. Make sure the backend server is running.</p>`;
  }
}

function renderStudentEvents(events) {
  const grid = document.getElementById('student-events-grid');
  grid.innerHTML = '';

  if (events.length === 0) {
    grid.innerHTML = '<div class="card"><p class="muted">No activities found for this filter.</p></div>';
    return;
  }

  events.forEach(event => {
    const card = document.createElement('div');
    card.className = 'card event-card';

    const isCompleted = event.status === 'Completed';
    const eventId = JSON.stringify(event.id);
    const participationType = JSON.stringify(event.participation_type || "Individual");
    const eventTitle = JSON.stringify(event.title);

    card.innerHTML = `
      <div>
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
          <span class="pill">${event.category || 'General'} • ${event.participation_type || 'Individual'}</span>
          <span class="badge">${event.status || 'Active'}</span>
        </div>
        <h3>${event.title}</h3>
        <div class="event-meta">
          <div><strong>📍 Venue:</strong> ${event.venue || 'TBA'}</div>
          <div><strong>🕒 Start:</strong> ${event.start_time ? event.start_time.replace('T', ' ') : 'TBA'}</div>
          ${event.end_time ? `<div><strong>🏁 End:</strong> ${event.end_time.replace('T', ' ')}</div>` : ''}
          <div><strong>📋 Instructions:</strong> ${event.participant_instructions || 'None'}</div>
        </div>
      </div>
      <button class="btn ${isCompleted ? 'btn-secondary' : 'btn-primary'} full-width" 
              ${isCompleted ? 'disabled' : ''} 
              onclick='handleEventRegistration(${eventId}, ${participationType}, ${eventTitle})'>
        ${isCompleted ? 'Event Completed' : 'Register'}
      </button>
    `;

    grid.appendChild(card);
  });
}

async function handleEventRegistration(activityId, participationType, eventTitle) {
  let studentName = '';
  let studentRollNo = '';

  if (currentUserRole === 'VISITOR') {
    studentName = localStorage.getItem('visitorName') || prompt('Enter your Visitor Name:');
    if (!studentName) return;
    studentRollNo = `VISITOR-${Math.floor(1000 + Math.random() * 9000)}`;
  } else {
    const rollInput = prompt(`Registering for "${eventTitle}"\nPlease enter your Student Roll Number (e.g., 22CS101):`);
    if (!rollInput || !rollInput.trim()) return;
    studentRollNo = rollInput.trim().toUpperCase();

    try {
      const studentRes = await fetch(`${API_BASE}/api/students/${encodeURIComponent(studentRollNo)}`);
      if (!studentRes.ok) throw new Error('Not found');
      
      const studentData = await studentRes.json();
      studentName = studentData.name;
      if (!studentName) throw new Error('Not found');
      
    } catch (error) {
      alert(`Student Roll Number "${studentRollNo}" not found in database.`);
      return;
    }
  }

  const payload = { student_name: studentName, student_roll_no: studentRollNo };

  if (participationType === 'Team') {
    const teamName = prompt(`Verified as ${studentName} (${studentRollNo}).\nEnter your Team Name:`);
    if (!teamName || !teamName.trim()) return alert('Team Name is required.');

    const teamMembers = prompt('Enter Team Members Roll Numbers (comma-separated):');
    if (!teamMembers || !teamMembers.trim()) return alert('Team Members are required.');

    payload.team_name = teamName.trim();
    payload.team_members = teamMembers.trim();
  }

  try {
    const regResponse = await fetch(`${API_BASE}/api/activities/${activityId}/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const regData = await regResponse.json();
    if (!regResponse.ok) return alert(regData.detail || 'Registration failed.');

    alert(`Success! ${studentName} is registered for "${eventTitle}".`);
  } catch (error) {
    console.error('Registration Error:', error);
    alert('Network error while registering.');
  }
}

async function handleAdminLogin(event) {
  event.preventDefault();
  const email = document.getElementById('admin-email').value.trim();
  const password = document.getElementById('admin-password').value.trim();

  try {
    const response = await fetch(`${API_BASE}/api/host/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    const data = await response.json();
    if (!response.ok || !data.success) return alert(data.detail || 'Invalid credentials!');

    document.getElementById('admin-login-section').classList.add('hidden');
    document.getElementById('admin-dashboard-section').classList.remove('hidden');
    loadAdminDashboard();
  } catch (error) {
    alert('Failed to connect to backend login.');
  }
}

async function loadAdminDashboard() {
  const container = document.getElementById('admin-events-container');
  if(!container) return;
  container.innerHTML = '<p class="muted">Loading dashboard...</p>';

  try {
    // FIXED: Fetch Drafts AND Published/Ongoing/Completed so they all show up
    const draftRes = await fetch(`${API_BASE}/api/activities?status=Draft`);
    const drafts = await draftRes.json();
    
    const otherRes = await fetch(`${API_BASE}/api/activities`); 
    const others = await otherRes.json();
    
    const activitiesList = [...drafts, ...others];

    if (!activitiesList.length) {
      container.innerHTML = '<div class="card"><p class="muted">No activities found.</p></div>';
      return;
    }

    const detailedActivities = await Promise.all(
      activitiesList.map(async act => {
        const detailRes = await fetch(`${API_BASE}/api/activities/${act.id}?view=host`);
        return detailRes.ok ? await detailRes.json() : act;
      })
    );

    renderAdminActivities(detailedActivities);
  } catch (error) {
    container.innerHTML = '<p class="muted" style="color:#ef4444;">Error loading dashboard. Check backend.</p>';
  }
}

function renderAdminActivities(activities) {
  const container = document.getElementById('admin-events-container');
  container.innerHTML = '';

  activities.forEach(activity => {
    const card = document.createElement('div');
    card.className = 'card';

    const reqs = activity.requirements || [];
    const regs = activity.registrations || [];

    const reqHtml = reqs.length > 0 
      ? reqs.map(r => `${r.item_name} (Qty: ${r.quantity})`).join(' | ') 
      : 'None';

    const regRows = regs.length === 0 
      ? '<tr><td colspan="4" class="muted">No students registered yet.</td></tr>'
      : regs.map(reg => `
          <tr>
            <td><strong>${reg.student_name}</strong></td>
            <td><code>${reg.student_roll_no}</code></td>
            <td>${reg.team_name ? `${reg.team_name}` : 'Individual'}</td>
            <td>
              ${reg.checked_in 
                ? '<span class="badge" style="color:#10b981;">✓ Checked In</span>' 
                : `<button class="btn btn-success btn-small" onclick="handleCheckIn(${reg.id})">Check-in</button>`}
            </td>
          </tr>
        `).join('');

    card.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:0.5rem;">
        <div>
          <span class="pill">${activity.category || 'Event'}</span>
          <h3 style="margin-top:0.4rem;">${activity.title} (ID: ${activity.id})</h3>
          <p class="muted" style="margin-bottom:0.25rem;">📍 ${activity.venue} | 🕒 ${activity.start_time.replace('T', ' ')}</p>
          <p class="muted" style="margin-bottom:0;"><strong>🧰 Equipment:</strong> ${reqHtml}</p>
        </div>
        <span class="badge">Status: ${activity.status}</span>
      </div>

      <div class="status-bar">
        <span style="font-size:0.8rem; color:#94a3b8; margin-right:0.5rem;">Change Status:</span>
        <button class="btn btn-secondary btn-small" onclick="handleChangeStatus(${activity.id}, 'Draft')">Draft</button>
        <button class="btn btn-primary btn-small" onclick="handleChangeStatus(${activity.id}, 'Published')">Publish</button>
        <button class="btn btn-primary btn-small" onclick="handleChangeStatus(${activity.id}, 'Ongoing')">Ongoing</button>
        <button class="btn btn-secondary btn-small" onclick="handleChangeStatus(${activity.id}, 'Completed')">Completed</button>
      </div>

      <div>
        <h4 style="font-size:0.9rem; color:#cbd5e1; margin-top:1rem;">Registrations (${regs.length})</h4>
        <table class="reg-table">
          <thead><tr><th>Name</th><th>Roll No</th><th>Team</th><th>Attendance</th></tr></thead>
          <tbody>${regRows}</tbody>
        </table>
      </div>
    `;

    container.appendChild(card);
  });
}

async function handleChangeStatus(activityId, newStatus) {
  try {
    const response = await fetch(`${API_BASE}/api/activities/${activityId}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus })
    });

    const data = await response.json();
    if (!response.ok) return alert(data.detail || `Cannot change to ${newStatus}.`);
    
    loadAdminDashboard();
  } catch (error) {
    alert('Error updating status.');
  }
}

async function handleCheckIn(registrationId) {
  try {
    const response = await fetch(`${API_BASE}/api/registrations/${registrationId}/checkin`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ checked_in: true })
    });

    if (response.ok) loadAdminDashboard();
  } catch (error) {
    alert('Error during check-in.');
  }
}

async function handleCreateActivity(event) {
  event.preventDefault();

  const startRaw = document.getElementById('new-start').value;
  const endRaw = document.getElementById('new-end').value;
  const reqItem = document.getElementById('new-req-item').value.trim();

  const payload = {
    title: document.getElementById('new-title').value.trim(),
    category: document.getElementById('new-category').value.trim(),
    venue: document.getElementById('new-venue').value.trim(),
    participation_type: document.getElementById('new-part-type').value,
    start_time: startRaw.length === 16 ? `${startRaw}:00` : startRaw,
    end_time: endRaw.length === 16 ? `${endRaw}:00` : endRaw,
    participant_instructions: document.getElementById('new-instructions').value.trim(),
    requirements: reqItem ? [{ item_name: reqItem, quantity: 1, assigned_to: 'Coach' }] : []
  };

  try {
    const response = await fetch(`${API_BASE}/api/activities`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const data = await response.json();
      return alert(data.detail || 'Failed to create activity.');
    }

    alert(`Activity "${payload.title}" created as Draft.`);
    document.getElementById('new-title').value = '';
    loadAdminDashboard();
  } catch (error) {
    alert('Error creating activity.');
  }
}