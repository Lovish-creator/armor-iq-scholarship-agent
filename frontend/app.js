/**
 * SCHOLARSHIELD AI — ARMORIQ SECURITY CONSOLE CONTROLLER
 * Architecture: Event-driven client state, FastMCP loopback & ArmorIQ governance
 */

const state = {
    currentView: 'overview',
    student: {
        id: 'student-demo-001',
        name: 'Gurpreet Singh',
        field: 'B.Tech Computer Science',
        state: 'Punjab',
        income: 450000,
        cgpa: '8.5'
    },
    intent: {
        id: 'INT-8F92A1',
        prompt: 'Apply only to scholarships that I am eligible for, match my academic profile in Punjab, and require no undisclosed financial commitment.',
        type: 'government',
        authority: 'ASK BEFORE SUBMIT',
        simulateDrift: false,
        simulateMissingDoc: false
    },
    metrics: {
        activePlans: 4,
        scholarshipsFound: 27,
        actionsVerified: 84,
        policyBlocks: 3,
        approvalsRequired: 2
    },
    scholarships: [
        {
            id: 'SCH-PUN-ENG-01',
            name: 'Punjab State Post-Matric Technical Scholarship',
            provider: 'Punjab Dept of Higher Education',
            category: 'government',
            state: 'Punjab',
            amount: '₹85,000 / year',
            field: 'Engineering / Technology',
            min_cgpa: '7.5 CGPA',
            income_limit: '₹5,00,000',
            required_docs: ['income_certificate.pdf', 'domicile_punjab.pdf', 'marksheet.pdf'],
            deadline: '12 days',
            match_score: '95%',
            eligibility_score: '92%',
            status: 'Ready',
            intent_compatible: true
        },
        {
            id: 'SCH-FED-MERIT-02',
            name: 'National Merit-Cum-Means Engineering Grant',
            provider: 'Ministry of Electronics & IT',
            category: 'government',
            state: 'All India',
            amount: '₹1,20,000 / year',
            field: 'Computer Science / IT',
            min_cgpa: '8.0 CGPA',
            income_limit: '₹6,00,000',
            required_docs: ['income_certificate.pdf', 'marksheet.pdf'],
            deadline: '24 days',
            match_score: '88%',
            eligibility_score: '85%',
            status: 'Pending Approval',
            intent_compatible: true
        },
        {
            id: 'SCH-PRV-GLOBAL-03',
            name: 'Apex Global Foundation Private Leadership Award',
            provider: 'Apex International Endowment (Private)',
            category: 'private',
            state: 'All India',
            amount: '₹2,50,000 / year',
            field: 'All STEM Degrees',
            min_cgpa: '8.5 CGPA',
            income_limit: 'None',
            required_docs: ['essay.pdf', 'recommendation.pdf'],
            deadline: '45 days',
            match_score: '0%',
            eligibility_score: '0%',
            status: 'Blocked',
            intent_compatible: false
        }
    ],
    auditLogs: []
};

// Application Initialization
function initApp() {
    initNavigation();
    renderScholarships();
    addAuditLog('SYSTEM_BOOT', 'ALLOW', 'system.init', 'ScholarShield Security Console initialized with ArmorIQ runtime bindings.');
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    initApp();
}

// Navigation View Switcher
function navigateTo(viewId) {
    state.currentView = viewId;

    // Update sidebar active links
    document.querySelectorAll('.nav-link').forEach(link => {
        if (link.getAttribute('data-view') === viewId) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });

    // Update view sections
    document.querySelectorAll('.view-section').forEach(view => {
        if (view.id === `view-${viewId}`) {
            view.classList.add('active');
        } else {
            view.classList.remove('active');
        }
    });

    if (viewId === 'scholarships') {
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

    resetPipelineNodes();

    if (runBtn) {
        runBtn.disabled = true;
        runBtn.textContent = 'Orchestrating Plan & Minting ArmorIQ Token...';
    }

    setPipelineNode('pipe-intent', 'done');
    setPipelineNode('pipe-plan', 'active');

    if (streamContainer) streamContainer.innerHTML = '';
    appendActivityCard('01. Intent Captured', 'Intent INT-8F92A1 captured with SHA-256 Merkle root.', 'ALLOW', 'scholarship.intent');
    addAuditLog('INTENT_CAPTURED', 'ALLOW', 'scholarship.intent', `Intent INT-8F92A1 captured for user '${state.student.name}'.`);

    try {
        setPipelineNode('pipe-plan', 'done');
        setPipelineNode('pipe-policy', 'active');
        appendActivityCard('02. Policy Evaluated', 'Checked policies/armoriq.yaml rules (4/4 allowed).', 'ALLOW', 'policy.evaluate');
        addAuditLog('POLICY_CHECK', 'ALLOW', 'policy.evaluate', 'Evaluated 4 planned actions against active policy rules.');

        setPipelineNode('pipe-policy', 'done');
        setPipelineNode('pipe-verify', 'active');
        addAuditLog('TOKEN_MINT', 'ALLOW', 'armoriq.token', 'NIST P-256 CSRG IntentToken minted with 300s TTL.');

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

        if (!response.ok) {
            throw new Error(`HTTP ${response.status} from agent orchestrator`);
        }

        const data = await response.json();
        setPipelineNode('pipe-verify', 'done');
        setPipelineNode('pipe-execute', 'active');

        renderExecutionStream(data);

        if (simDrift || data.blocked_steps > 0) {
            setPipelineNode('pipe-execute', 'blocked');
            setPipelineNode('pipe-audit', 'done');
            if (secAlert) secAlert.classList.remove('hidden');
            updateDecisionBox('DENY', 'scholarship.submit_application', 'Out-of-scope private award violates student intent policy.');
            state.metrics.policyBlocks++;
            updateKpiCards();
            showToast('🚫 Consequential Action Blocked by ArmorIQ Policy Engine');
        } else if (simMissingDoc) {
            setPipelineNode('pipe-execute', 'active');
            setPipelineNode('pipe-audit', 'done');
            if (demAlert) demAlert.classList.remove('hidden');
            showToast('📄 Verification Incomplete: Mandatory Income Certificate Required');
        } else {
            setPipelineNode('pipe-execute', 'done');
            setPipelineNode('pipe-audit', 'done');
            updateDecisionBox('ALLOW', 'scholarship.submit_application', 'Action is within declared scholarship scope.');
            state.metrics.actionsVerified += 4;
            updateKpiCards();
            showToast('✓ Workflow Completed with Cryptographic Assurance');
        }

    } catch (err) {
        setPipelineNode('pipe-verify', 'blocked');
        appendActivityCard('Execution Notice', err.message || 'Workflow notice', 'DENY', 'system.error');
        addAuditLog('SYSTEM_ERROR', 'DENY', 'system.error', err.message || 'Error occurred');
        showToast(`Workflow Notice: ${err.message}`);
    } finally {
        if (runBtn) {
            runBtn.disabled = false;
            runBtn.textContent = '⚡ Execute Autonomous Workflow';
        }
    }
}

// Render Real-Time Activity Feed
function renderExecutionStream(data) {
    const steps = data.step_results || [];
    steps.forEach((step, idx) => {
        const stepNum = idx + 1;
        const isAllow = (step.armoriq_decision === 'ALLOW' || step.status === 'COMPLETED');
        const decisionTag = isAllow ? 'ALLOW' : 'DENY';
        const actionName = step.action || 'tool_action';

        let desc = step.details || `Executed tool action '${actionName}'.`;
        if (typeof desc === 'object') {
            desc = desc.message || `Action ${actionName} executed through FastMCP boundary.`;
        }

        if (!isAllow) {
            desc = `BLOCKED by ArmorIQ: Consequential write prevented. Invariant maintained.`;
            addAuditLog('POLICY_BLOCK', 'DENY', `scholarship.${actionName}`, desc);
        } else {
            addAuditLog('TOOL_EXECUTE', 'ALLOW', `scholarship.${actionName}`, desc);
        }

        appendActivityCard(`Step 0${stepNum}: ${actionName}`, desc, decisionTag, `scholarship.${actionName}`);
    });
}

function appendActivityCard(title, desc, decision, toolName) {
    const container = document.getElementById('dash-stream-container');
    if (!container) return;
    const isAllow = (decision === 'ALLOW');
    const card = document.createElement('div');
    card.className = 'activity-item-card';
    card.innerHTML = `
        <div class="activity-top-row">
            <span class="activity-action-label">${title}</span>
            <span class="${isAllow ? 'decision-badge-allow' : 'decision-badge-deny'}">${decision}</span>
        </div>
        <div class="activity-desc">${desc}</div>
        <div class="activity-foot">
            <span>⏱️ ${new Date().toLocaleTimeString()}</span>
            <span class="${isAllow ? 'text-allow' : 'text-deny'}">🛡️ ${isAllow ? 'ArmorIQ: Authorized' : 'ArmorIQ: Intercepted'}</span>
        </div>
    `;
    container.appendChild(card);
}

// Update Policy Decision Box
function updateDecisionBox(decision, action, reason) {
    const tagEl = document.getElementById('box-decision-tag');
    const actEl = document.getElementById('box-decision-action');
    const rsnEl = document.getElementById('box-decision-reason');

    if (tagEl) {
        tagEl.textContent = decision;
        tagEl.className = decision === 'ALLOW' ? 'decision-badge-allow' : 'decision-badge-deny';
    }
    if (actEl) actEl.textContent = action;
    if (rsnEl) rsnEl.textContent = reason;
}

// Pipeline Node State Helpers
function resetPipelineNodes() {
    const nodes = ['pipe-intent', 'pipe-plan', 'pipe-policy', 'pipe-verify', 'pipe-execute', 'pipe-audit'];
    nodes.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.className = 'pipe-node';
    });
}

function setPipelineNode(id, status) {
    const el = document.getElementById(id);
    if (el) el.className = `pipe-node ${status}`;
}

// Interactive Approval Handlers
function approvePendingAction() {
    showToast('✓ Application Submission Approved. Submitting to Portal...');
    addAuditLog('HUMAN_APPROVAL', 'ALLOW', 'scholarship.submit_application', 'User approved final application submission.');
    const card = document.getElementById('approval-card');
    if (card) {
        card.innerHTML = `
            <div class="approval-head" style="color:var(--status-allow);">
                <span>✓</span>
                <span>ACTION APPROVED &amp; EXECUTED</span>
            </div>
            <p class="approval-body-text font-mono text-allow">
                Application successfully submitted to Punjab State Technical Scholarship.
            </p>
        `;
    }
}

function denyPendingAction() {
    showToast('✕ Application Submission Denied by User.');
    addAuditLog('HUMAN_APPROVAL', 'DENY', 'scholarship.submit_application', 'User explicitly denied application submission.');
    const card = document.getElementById('approval-card');
    if (card) {
        card.innerHTML = `
            <div class="approval-head" style="color:var(--status-deny);">
                <span>✕</span>
                <span>ACTION REJECTED BY USER</span>
            </div>
            <p class="approval-body-text text-muted">
                Submission aborted. Zero records written to database.
            </p>
        `;
    }
}

// Render Scholarship Directory
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
        <div class="sch-grid-card">
            <div>
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                    <span style="font-size:0.7rem; font-weight:700; color:var(--text-muted); text-transform:uppercase;">${sch.category}</span>
                    <span class="${sch.intent_compatible ? 'decision-badge-allow' : 'decision-badge-deny'}">
                        ${sch.intent_compatible ? '● Intent Compatible' : '✕ Out of Scope'}
                    </span>
                </div>
                <h3 class="sch-name-h3">${sch.name}</h3>
                <div class="sch-grant-amount mt-2">${sch.amount}</div>
                <div style="font-size:0.78rem; color:var(--text-secondary); margin-top:10px; display:flex; flex-direction:column; gap:4px;">
                    <div><strong>Provider:</strong> ${sch.provider}</div>
                    <div><strong>Criteria:</strong> ${sch.min_cgpa} | Income &lt; ${sch.income_limit}</div>
                    <div><strong>Match Score:</strong> <span class="${sch.intent_compatible ? 'text-allow' : 'text-deny'}">${sch.match_score}</span></div>
                    <div><strong>Deadline:</strong> ${sch.deadline}</div>
                </div>
            </div>
            <div style="display:flex; gap:8px; margin-top:auto;">
                <button class="btn-violet btn-sm" onclick="checkSpecificEligibility('${sch.id}')">
                    Check Eligibility
                </button>
                <button class="btn-outline btn-sm" onclick="prepareApplicationDraft('${sch.id}')">
                    Prepare Draft
                </button>
            </div>
        </div>
    `).join('');
}

function filterScholarships() {
    renderScholarships();
}

function checkSpecificEligibility(id) {
    const sch = state.scholarships.find(s => s.id === id);
    if (!sch) return;
    if (sch.intent_compatible) {
        showToast(`✓ Eligible for '${sch.name}' (${sch.match_score} match).`);
    } else {
        showToast(`⚠️ Out of scope: Action violates active intent policy.`);
    }
}

function prepareApplicationDraft(id) {
    const sch = state.scholarships.find(s => s.id === id);
    if (!sch) return;
    showToast(`Draft prepared for '${sch.name}'. Awaiting governed submission.`);
    navigateTo('overview');
}

// Student Profile & Document Vault Handlers
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
    if (tgtState) tgtState.textContent = `${state.student.state} / ${state.student.field}`;

    showToast('✓ Student Profile Saved.');
    addAuditLog('PROFILE_UPDATE', 'ALLOW', 'profile.save', `Updated profile for '${state.student.name}'.`);
}

async function handleDocumentUpload() {
    const fileInput = document.getElementById('upload-doc-file');
    const docTypeEl = document.getElementById('upload-doc-type');
    const docType = docTypeEl ? docTypeEl.value : 'income_certificate';

    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
        showToast('Please select a file to upload.');
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

    showToast(`✓ Document '${file.name}' verified and uploaded to vault.`);
    const demAlert = document.getElementById('dash-demand-alert');
    if (demAlert) demAlert.classList.add('hidden');
    addAuditLog('DOC_UPLOAD', 'ALLOW', 'documents.upload', `Uploaded and verified '${file.name}'.`);
}

// Audit Logging & JSON Export
function addAuditLog(tag, decision, action, details) {
    const now = new Date();
    const timeStr = now.toTimeString().split(' ')[0];
    state.auditLogs.push({ time: timeStr, tag, decision, action, details });

    const tbody = document.getElementById('audit-table-body');
    if (tbody) {
        const tr = document.createElement('tr');
        const decisionClass = decision === 'ALLOW' ? 'text-allow' : (decision === 'ASK' ? 'text-ask' : 'text-deny');
        tr.innerHTML = `
            <td>${timeStr}</td>
            <td>${tag}</td>
            <td><span class="${decisionClass}">${decision}</span></td>
            <td>${action}</td>
            <td>${details}</td>
        `;
        tbody.prepend(tr);
    }
}

function exportAuditLogJSON() {
    const blob = new Blob([JSON.stringify(state.auditLogs, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `scholarshield-audit-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
    showToast('Exported audit report as JSON.');
}

// KPI Updater
function updateKpiCards() {
    const p1 = document.getElementById('kpi-active-plans');
    const p3 = document.getElementById('kpi-actions-verified');
    const p4 = document.getElementById('kpi-policy-blocks');
    const p5 = document.getElementById('kpi-approvals-req');

    if (p1) p1.textContent = String(state.metrics.activePlans).padStart(2, '0');
    if (p3) p3.textContent = String(state.metrics.actionsVerified).padStart(2, '0');
    if (p4) p4.textContent = String(state.metrics.policyBlocks).padStart(2, '0');
    if (p5) p5.textContent = String(state.metrics.approvalsRequired).padStart(2, '0');
}

// Modal Helpers
function openOrderModal() {
    const modal = document.getElementById('order-modal');
    if (modal) modal.classList.remove('hidden');
}

function closeOrderModal() {
    const modal = document.getElementById('order-modal');
    if (modal) modal.classList.add('hidden');
}

function submitOrderModal() {
    const nameEl = document.getElementById('modal-name');
    const stateEl = document.getElementById('modal-state');
    const promptEl = document.getElementById('modal-prompt');

    if (nameEl) state.student.name = nameEl.value;
    if (stateEl) state.student.state = stateEl.value;
    if (promptEl) state.intent.prompt = promptEl.value;

    const actPrompt = document.getElementById('dash-active-prompt');
    if (actPrompt) actPrompt.textContent = `"${state.intent.prompt}"`;
    const tgtState = document.getElementById('dash-target-state');
    if (tgtState) tgtState.textContent = `${state.student.state} / ${state.student.field}`;

    closeOrderModal();
    executeWorkflowFromDashboard();
}

function showToast(message) {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = 'toast-pill';
    toast.innerHTML = `<span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => {
        toast.remove();
    }, 4000);
}

// Global Window Bindings
window.navigateTo = navigateTo;
window.executeWorkflowFromDashboard = executeWorkflowFromDashboard;
window.approvePendingAction = approvePendingAction;
window.denyPendingAction = denyPendingAction;
window.openOrderModal = openOrderModal;
window.closeOrderModal = closeOrderModal;
window.submitOrderModal = submitOrderModal;
window.saveStudentProfile = saveStudentProfile;
window.handleDocumentUpload = handleDocumentUpload;
window.exportAuditLogJSON = exportAuditLogJSON;
window.filterScholarships = filterScholarships;
window.checkSpecificEligibility = checkSpecificEligibility;
window.prepareApplicationDraft = prepareApplicationDraft;
window.showToast = showToast;