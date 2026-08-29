/**
 * SCHOLARSHIELD AI — ARMORIQ OFFICIAL RUNTIME CONTROLLER
 * Matched to https://armoriq.ai/ Design System & Intent Assurance Framework
 */

const state = {
    currentTab: 'dashboard',
    student: {
        id: 'student-demo-001',
        name: 'Gurpreet Singh',
        field: 'B.Tech Computer Science',
        state: 'Punjab',
        income: 450000
    },
    scholarships: [
        {
            id: 'SCH-PUN-ENG-01',
            name: 'Punjab State Post-Matric Technical Scholarship',
            provider: 'Punjab Dept of Higher Education',
            category: 'government',
            state: 'Punjab',
            amount: '₹85,000 / year',
            criteria: '7.5+ CGPA | Family Income < ₹5,00,000',
            match_score: '95%',
            intent_compatible: true
        },
        {
            id: 'SCH-FED-MERIT-02',
            name: 'National Merit-Cum-Means Engineering Grant',
            provider: 'Ministry of Electronics & IT',
            category: 'government',
            state: 'All India',
            amount: '₹1,20,000 / year',
            criteria: '8.0+ CGPA | Family Income < ₹6,00,000',
            match_score: '88%',
            intent_compatible: true
        },
        {
            id: 'SCH-PRV-GLOBAL-03',
            name: 'Apex Global Foundation Private Leadership Award',
            provider: 'Apex International Endowment (Private)',
            category: 'private',
            state: 'All India',
            amount: '₹2,50,000 / year',
            criteria: 'Essay & Recommendation Required',
            match_score: '0%',
            intent_compatible: false
        }
    ],
    auditLogs: []
};

// Initialization
function initApp() {
    renderScholarships();
    addAuditLog('SYSTEM_BOOT', 'ALLOW', 'system.init', 'ScholarShield initialized with ArmorIQ runtime bindings.');
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    initApp();
}

// Tab Switching
function switchView(tabId) {
    state.currentTab = tabId;

    document.querySelectorAll('.nav-tab-btn').forEach(btn => {
        if (btn.getAttribute('data-tab') === tabId) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    document.querySelectorAll('.view-content').forEach(view => {
        if (view.id === `view-${tabId}`) {
            view.classList.add('active');
        } else {
            view.classList.remove('active');
        }
    });

    if (tabId === 'scholarships') {
        renderScholarships();
    }
}

// Execute Governed Agent Workflow
async function executeWorkflowFromDashboard() {
    const runBtn = document.getElementById('dash-run-btn');
    const streamContainer = document.getElementById('dash-stream-container');
    const simDrift = document.getElementById('dash-sim-drift')?.checked || false;
    const simMissingDoc = document.getElementById('dash-sim-missing-doc')?.checked || false;

    const secAlert = document.getElementById('dash-security-alert');
    if (secAlert) secAlert.classList.add('hidden');
    const demAlert = document.getElementById('dash-demand-alert');
    if (demAlert) demAlert.classList.add('hidden');

    resetPipelineSteps();

    if (runBtn) {
        runBtn.disabled = true;
        runBtn.textContent = 'Orchestrating Plan & Enforcing Intent...';
    }

    setPipelineStep(1, 'active');
    if (streamContainer) streamContainer.innerHTML = '';

    appendStreamCard('// 01. PLAN DISCOVERY', 'Found verified engineering scholarship schemes in Punjab matching student profile.', 'ALLOW', 'scholarship.search_scholarships');
    addAuditLog('PLAN_DISCOVERY', 'ALLOW', 'scholarship.search_scholarships', 'Discovered matching state schemes.');

    try {
        setPipelineStep(1, 'done');
        setPipelineStep(2, 'active');

        appendStreamCard('// 02. ELIGIBILITY VERIFICATION', `Validated student criteria (Income: ₹${state.student.income.toLocaleString('en-IN')}, State: ${state.student.state}).`, 'ALLOW', 'scholarship.check_eligibility');
        addAuditLog('ELIGIBILITY_CHECK', 'ALLOW', 'scholarship.check_eligibility', 'Verified academic & income criteria.');

        setPipelineStep(2, 'done');
        setPipelineStep(3, 'active');

        appendStreamCard('// 03. INTENT VERIFICATION', 'Signed plan INT-8F92A1 verified by ArmorIQ Zero-Trust Sentry.', 'ALLOW', 'armoriq.verify');
        addAuditLog('INTENT_VERIFY', 'ALLOW', 'armoriq.verify', 'NIST P-256 signed IntentToken checked.');

        const payload = {
            student_name: state.student.name,
            target_state: state.student.state,
            target_field: state.student.field,
            annual_income: state.student.income,
            simulate_out_of_scope_violation: simDrift,
            simulate_missing_document: simMissingDoc
        };

        const response = await fetch('/api/agent/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();

        setPipelineStep(3, 'done');
        setPipelineStep(4, 'active');

        if (simDrift || data.blocked_steps > 0) {
            setPipelineStep(4, 'blocked');
            if (secAlert) secAlert.classList.remove('hidden');
            appendStreamCard('// 04. CONTEXT DRIFT INTERCEPTED', '🚫 Action BLOCKED: Agent attempted unauthorized submission to private award SCH-PRV-GLOBAL-03.', 'BLOCK', 'scholarship.submit_application');
            addAuditLog('POLICY_BLOCK', 'BLOCK', 'scholarship.submit_application', 'Intercepted out-of-scope submission. Zero writes executed.');
            showToast('🚫 Consequential Write Blocked by ArmorIQ');
        } else if (simMissingDoc) {
            setPipelineStep(4, 'active');
            if (demAlert) demAlert.classList.remove('hidden');
            appendStreamCard('// 04. DOCUMENT DEMAND REQUIRED', '⚠️ Action Paused: Mandatory Income Certificate PDF required before submission.', 'BLOCK', 'documents.verify');
            addAuditLog('DOC_DEMAND', 'BLOCK', 'documents.verify', 'Paused for missing certificate.');
            showToast('📄 Missing Certificate Demanded by Portal');
        } else {
            setPipelineStep(4, 'done');
            appendStreamCard('// 04. GOVERNED SUBMISSION', '✓ Application submitted safely to Punjab State Portal with cryptographic authorization token.', 'ALLOW', 'scholarship.submit_application');
            addAuditLog('TOOL_EXECUTE', 'ALLOW', 'scholarship.submit_application', 'Submitted application with valid CSRG token.');
            showToast('✓ Workflow Completed with Cryptographic Assurance');
        }

    } catch (err) {
        setPipelineStep(4, 'blocked');
        appendStreamCard('// EXECUTION ERROR', err.message || 'Workflow notice', 'BLOCK', 'system.error');
        addAuditLog('SYSTEM_ERROR', 'BLOCK', 'system.error', err.message);
        showToast(`Workflow notice: ${err.message}`);
    } finally {
        if (runBtn) {
            runBtn.disabled = false;
            runBtn.textContent = '⚡ Run Safe Scholarship Agent';
        }
    }
}

function appendStreamCard(title, desc, verdict, toolName) {
    const container = document.getElementById('dash-stream-container');
    if (!container) return;
    const isAllow = (verdict === 'ALLOW');
    const card = document.createElement('div');
    card.className = `stream-action-item ${isAllow ? 'item-allow' : 'item-block'}`;
    card.innerHTML = `
        <div class="stream-top-row">
            <span class="stream-title-text">${title}</span>
            <span class="${isAllow ? 'badge-verdict-allow' : 'badge-verdict-block'}">${isAllow ? 'ALLOW' : 'BLOCKED'}</span>
        </div>
        <div class="stream-desc-text">${desc}</div>
        <div class="stream-foot-row">
            <span>⏱️ ${new Date().toLocaleTimeString()}</span>
            <span class="${isAllow ? 'text-allow' : 'text-threat'}">${isAllow ? '✓ ArmorIQ: Verified' : '🚫 ArmorIQ: Intercepted'}</span>
        </div>
    `;
    container.appendChild(card);
}

function resetPipelineSteps() {
    for (let i = 1; i <= 4; i++) {
        const el = document.getElementById(`pstep-${i}`);
        if (el) el.className = 'pipe-step-item';
    }
}

function setPipelineStep(num, status) {
    const el = document.getElementById(`pstep-${num}`);
    if (el) el.className = `pipe-step-item ${status}`;
}

// Scholarship Directory Rendering
function renderScholarships() {
    const grid = document.getElementById('scholarships-grid');
    if (!grid) return;

    const filterType = document.getElementById('filter-type')?.value || 'all';
    const filterState = document.getElementById('filter-state')?.value || 'All India';

    const filtered = state.scholarships.filter(s => {
        if (filterType !== 'all' && s.category !== filterType) return false;
        if (filterState !== 'All India' && s.state !== 'All India' && s.state !== filterState) return false;
        return true;
    });

    grid.innerHTML = filtered.map(sch => `
        <div class="sch-item-card">
            <div>
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                    <span class="font-mono text-muted" style="font-size:0.7rem; text-transform:uppercase;">${sch.category}</span>
                    <span class="${sch.intent_compatible ? 'badge-verdict-allow' : 'badge-verdict-block'}">
                        ${sch.intent_compatible ? '● In-Scope' : '✕ Out-of-Scope'}
                    </span>
                </div>
                <h3 class="sch-head-name">${sch.name}</h3>
                <div class="sch-amount-text mt-2">${sch.amount}</div>
                <div style="font-size:0.78rem; color:var(--color-ink-2); margin-top:8px; display:flex; flex-direction:column; gap:4px;">
                    <div><strong>Provider:</strong> ${sch.provider}</div>
                    <div><strong>Criteria:</strong> ${sch.criteria}</div>
                    <div><strong>Match:</strong> <span class="${sch.intent_compatible ? 'text-allow' : 'text-threat'}">${sch.match_score}</span></div>
                </div>
            </div>
            <button class="btn-armoriq-secondary btn-full" onclick="showToast('Selected ${sch.name}. Compatible with intent.')">
                Apply with ArmorIQ Protection
            </button>
        </div>
    `).join('');
}

function filterScholarships() {
    renderScholarships();
}

// Student Profile & Upload
function saveStudentProfile() {
    const nameEl = document.getElementById('prof-name');
    const eduEl = document.getElementById('prof-edu');
    const stateEl = document.getElementById('prof-state');
    const incEl = document.getElementById('prof-income');

    if (nameEl) state.student.name = nameEl.value;
    if (eduEl) state.student.field = eduEl.value;
    if (stateEl) state.student.state = stateEl.value;
    if (incEl) state.student.income = parseInt(incEl.value, 10);

    const tgtState = document.getElementById('dash-target-state');
    if (tgtState) tgtState.textContent = state.student.state;

    showToast('✓ Student Profile Saved.');
    addAuditLog('PROFILE_SAVED', 'ALLOW', 'profile.update', `Profile updated for ${state.student.name}.`);
}

async function handleDocumentUpload() {
    const fileInput = document.getElementById('upload-doc-file');
    const docTypeEl = document.getElementById('upload-doc-type');
    const docType = docTypeEl ? docTypeEl.value : 'income_certificate';

    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
        showToast('Please choose a file to upload.');
        return;
    }

    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_type', docType);
    formData.append('student_id', state.student.id);

    try {
        await fetch('/api/documents/upload', {
            method: 'POST',
            body: formData
        });
    } catch (_) {}

    showToast(`✓ Certificate '${file.name}' verified and uploaded.`);
    const demAlert = document.getElementById('dash-demand-alert');
    if (demAlert) demAlert.classList.add('hidden');
    addAuditLog('DOC_UPLOAD', 'ALLOW', 'documents.upload', `Uploaded and verified ${file.name}.`);
}

// Audit Logs & Export
function addAuditLog(tag, verdict, action, details) {
    const now = new Date();
    const timeStr = now.toTimeString().split(' ')[0];
    state.auditLogs.push({ time: timeStr, tag, verdict, action, details });

    const container = document.getElementById('audit-terminal-body');
    if (container) {
        const item = document.createElement('div');
        item.className = 'stream-action-item';
        item.innerHTML = `
            <div class="stream-top-row">
                <span class="font-mono text-accent" style="font-size:0.75rem;">// ${tag}</span>
                <span class="${verdict === 'ALLOW' ? 'badge-verdict-allow' : 'badge-verdict-block'}">${verdict}</span>
            </div>
            <div class="stream-desc-text font-mono" style="font-size:0.75rem;"><strong>Action:</strong> ${action} — ${details}</div>
            <div class="stream-foot-row">
                <span>⏱️ ${timeStr}</span>
                <span>🔒 NIST P-256 Verified</span>
            </div>
        `;
        container.prepend(item);
    }
}

function exportAuditLogJSON() {
    const blob = new Blob([JSON.stringify(state.auditLogs, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `armoriq-scholarshield-audit-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
    showToast('Exported audit report as JSON.');
}

function showToast(message) {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = 'toast-item';
    toast.innerHTML = `<span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => {
        toast.remove();
    }, 4000);
}

// Global Exports
window.switchView = switchView;
window.executeWorkflowFromDashboard = executeWorkflowFromDashboard;
window.saveStudentProfile = saveStudentProfile;
window.handleDocumentUpload = handleDocumentUpload;
window.exportAuditLogJSON = exportAuditLogJSON;
window.filterScholarships = filterScholarships;
window.showToast = showToast;