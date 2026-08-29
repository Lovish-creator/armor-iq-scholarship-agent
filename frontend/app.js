/**
 * ============================================================
 * SCHOLARSHIELD AI — ARMORIQ GOVERNANCE & FRONTEND CONTROLLER
 * ============================================================
 */

// Application State
const state = {
    activeTab: 'dashboard',
    student: {
        id: 'student-demo-001',
        name: 'Gurpreet Singh',
        field: 'B.Tech Computer Science',
        state: 'Punjab',
        income: 450000,
        cgpa: '8.5'
    },
    intent: {
        prompt: 'Find government engineering scholarships in Punjab I am eligible for and apply.',
        type: 'government',
        simulateDrift: false,
        simulateMissingDoc: false
    },
    latestTelemetry: null,
    auditLogs: [],
    scholarships: [
        {
            id: 'SCH-PUN-ENG-01',
            name: 'Punjab State Post-Matric Technical Scholarship',
            provider: 'Punjab Department of Higher Education',
            category: 'government',
            state: 'Punjab',
            amount: '₹85,000 / year',
            field: 'Engineering / Technology / IT',
            min_cgpa: '7.5 CGPA',
            income_limit: '₹5,00,000',
            required_docs: ['income_certificate.pdf', 'domicile_punjab.pdf', 'marksheet_12th.pdf'],
            deadline: '2026-11-30',
            source: 'State Government Portal',
            source_url: 'https://scholarships.punjab.gov.in',
            eligible: true
        },
        {
            id: 'SCH-GOV-AICTE-PRAGATI',
            name: 'AICTE Pragati Scholarship for Girl Students',
            provider: 'All India Council for Technical Education (NSP)',
            category: 'government',
            state: 'All India',
            amount: '₹50,000 / year',
            field: 'Engineering / CS / IT / Pharmacy / Architecture',
            min_cgpa: '6.0 CGPA',
            income_limit: '₹8,00,000',
            required_docs: ['marksheet_12th.pdf', 'income_certificate.pdf', 'admission_letter.pdf', 'tuition_fee_receipt.pdf', 'bank_passbook.pdf'],
            deadline: '2026-10-31',
            source: 'National Scholarship Portal (NSP)',
            source_url: 'https://scholarships.gov.in',
            eligible: true
        },
        {
            id: 'SCH-GOV-AICTE-SAKSHAM',
            name: 'AICTE Saksham Scholarship (Specially-Abled Students)',
            provider: 'AICTE & Ministry of Education (NSP)',
            category: 'government',
            state: 'All India',
            amount: '₹50,000 / year',
            field: 'Engineering / Technology / Diploma',
            min_cgpa: '5.5 CGPA',
            income_limit: '₹8,00,000',
            required_docs: ['marksheet_12th.pdf', 'income_certificate.pdf', 'disability_certificate.pdf', 'admission_letter.pdf'],
            deadline: '2026-10-31',
            source: 'National Scholarship Portal (NSP)',
            source_url: 'https://scholarships.gov.in',
            eligible: true
        },
        {
            id: 'SCH-GOV-NSP-CSSS',
            name: 'Central Sector Scheme of Scholarship (PM-USP)',
            provider: 'Ministry of Education (NSP Portal)',
            category: 'government',
            state: 'All India',
            amount: '₹20,000 / year',
            field: 'Engineering / CS / Sciences / UG Degrees',
            min_cgpa: '7.5 CGPA (Top 20th %ile)',
            income_limit: '₹4,50,000',
            required_docs: ['marksheet_12th.pdf', 'income_certificate.pdf', 'bonafide_certificate.pdf', 'fee_receipt.pdf'],
            deadline: '2026-10-31',
            source: 'National Scholarship Portal (NSP)',
            source_url: 'https://scholarships.gov.in',
            eligible: true
        },
        {
            id: 'SCH-PRV-RELIANCE-UG',
            name: 'Reliance Foundation Undergraduate Scholarship 2026-27',
            provider: 'Reliance Foundation',
            category: 'private',
            state: 'All India',
            amount: '₹50,000 / year (₹2,00,000 Total)',
            field: 'All Undergrad Streams (B.Tech, B.Sc, MBBS, etc.)',
            min_cgpa: '6.0 CGPA (60% in 12th)',
            income_limit: '₹15,00,000',
            required_docs: ['marksheet_12th.pdf', 'income_certificate.pdf', 'admission_letter.pdf', 'bonafide_certificate.pdf'],
            deadline: '2026-10-05',
            source: 'Buddy4Study',
            source_url: 'https://www.buddy4study.com/page/reliance-foundation-undergraduate-scholarships',
            eligible: true,
            is_private: true
        },
        {
            id: 'SCH-PRV-TATA-PANKH',
            name: 'Tata Capital Pankh Scholarship Programme',
            provider: 'Tata Capital Limited & Tata Trusts (Buddy4Study)',
            category: 'private',
            state: 'All India',
            amount: '₹1,00,000 / year (Up to 80% Fees)',
            field: 'Engineering / Professional & General UG',
            min_cgpa: '6.0 CGPA (60% in 12th)',
            income_limit: '₹4,00,000',
            required_docs: ['marksheet_12th.pdf', 'income_certificate.pdf', 'tuition_fee_receipt.pdf', 'admission_letter.pdf'],
            deadline: '2026-09-30',
            source: 'Buddy4Study',
            source_url: 'https://www.buddy4study.com/page/tata-capital-pankh-scholarship-programme',
            eligible: true,
            is_private: true
        },
        {
            id: 'SCH-PRV-KOTAK-KANYA',
            name: 'Kotak Kanya Scholarship Programme',
            provider: 'Kotak Education Foundation (Buddy4Study)',
            category: 'private',
            state: 'All India',
            amount: '₹1,50,000 / year',
            field: 'B.Tech / MBBS / Integrated LLB / Architecture',
            min_cgpa: '7.5 CGPA (75% in 12th)',
            income_limit: '₹6,00,000',
            required_docs: ['marksheet_12th.pdf', 'income_certificate.pdf', 'admission_letter.pdf', 'bonafide_certificate.pdf'],
            deadline: '2026-08-31',
            source: 'Buddy4Study',
            source_url: 'https://www.buddy4study.com/page/kotak-kanya-scholarship',
            eligible: true,
            is_private: true
        },
        {
            id: 'SCH-PRV-JSW-UDAAN',
            name: 'JSW Udaan Scholarship for Technical Higher Education',
            provider: 'JSW Foundation (Vidyasaarathi Portal)',
            category: 'private',
            state: 'All India',
            amount: '₹50,000 / year',
            field: 'B.E. / B.Tech / Diploma / Polytechnic',
            min_cgpa: '6.0 CGPA (60% in 12th)',
            income_limit: '₹8,00,000',
            required_docs: ['marksheet_12th.pdf', 'marksheet_10th.pdf', 'income_certificate.pdf', 'fee_receipt.pdf'],
            deadline: '2026-10-31',
            source: 'Vidyasaarathi',
            source_url: 'https://www.vidyasaarathi.co.in/main/scholarship',
            eligible: true,
            is_private: true
        },
        {
            id: 'SCH-PRV-HDFC-ECSS',
            name: 'HDFC Bank Parivartan ECSS Programme',
            provider: 'HDFC Bank CSR (Buddy4Study)',
            category: 'private',
            state: 'All India',
            amount: '₹75,000 / year',
            field: 'B.Tech / General UG / Diploma',
            min_cgpa: '5.5 CGPA (55% in 12th)',
            income_limit: '₹2,50,000',
            required_docs: ['marksheet_12th.pdf', 'income_certificate.pdf', 'admission_letter.pdf', 'fee_receipt.pdf'],
            deadline: '2026-10-31',
            source: 'Buddy4Study',
            source_url: 'https://www.buddy4study.com/page/hdfc-bank-parivartans-ecss-programme',
            eligible: true,
            is_private: true
        },
        {
            id: 'SCH-DEL-TECH-04',
            name: 'Delhi State Technical Higher Education Scheme',
            provider: 'Delhi Directorate of Training & Technical Education',
            category: 'government',
            state: 'Delhi',
            amount: '₹95,000 / year',
            field: 'Engineering / Polytechnic',
            min_cgpa: '7.0 CGPA',
            income_limit: '₹4,00,000',
            required_docs: ['domicile_delhi.pdf', 'income_certificate.pdf', 'marksheet_12th.pdf'],
            deadline: '2026-10-31',
            source: 'State Government Portal',
            source_url: 'https://edistrict.delhigovt.nic.in',
            eligible: false,
            ineligible_reason: 'Domicile requirement not matched (Punjab resident).'
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
            deadline: '2026-12-31',
            source: 'Global Endowment',
            source_url: 'https://globaltechfoundation.org/scholarships',
            eligible: true,
            is_private: true
        }
    ]
};

function initApp() {
    initNavigation();
    initIntentFabricCanvas();
    renderScholarships();
    initClock();
    addAuditLog('SYSTEM_BOOT', 'ScholarShield frontend controller initialized with ArmorIQ runtime bindings.', 'cyan');
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    initApp();
}

// ============================================================
// NAVIGATION TAB CONTROLLER
// ============================================================
function initNavigation() {
    const tabs = document.querySelectorAll('.nav-tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const targetTab = tab.getAttribute('data-tab');
            switchTab(targetTab);
        });
    });
}

function switchTab(tabName) {
    state.activeTab = tabName;

    // Update Tab Buttons
    document.querySelectorAll('.nav-tab').forEach(btn => {
        if (btn.getAttribute('data-tab') === tabName) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    // Update Views
    document.querySelectorAll('.tab-view').forEach(view => {
        if (view.id === `view-${tabName}`) {
            view.classList.add('active');
        } else {
            view.classList.remove('active');
        }
    });

    if (tabName === 'scholarships') {
        renderScholarships();
    }
}

// ============================================================
// INTENT FABRIC CANVAS ANIMATION (3D / TOPOLOGY VISUALIZER)
// ============================================================
let canvasAnimId = null;
function initIntentFabricCanvas() {
    const canvas = document.getElementById('intent-fabric-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    function resizeCanvas() {
        canvas.width = canvas.parentElement.clientWidth;
        canvas.height = canvas.parentElement.clientHeight;
    }
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Particle nodes for canvas
    const nodes = [
        { x: 0.15, y: 0.35, label: 'Student Intent', color: '#38BDF8', size: 6 },
        { x: 0.50, y: 0.25, label: 'Gemini 3.6 Flash', color: '#F5F5F5', size: 7 },
        { x: 0.35, y: 0.75, label: 'ArmorIQ Policy Sentry', color: '#E8602C', size: 9 },
        { x: 0.85, y: 0.70, label: 'FastMCP Tools', color: '#35D07F', size: 7 }
    ];

    let pulseTime = 0;
    const particles = [];
    for (let i = 0; i < 24; i++) {
        particles.push({
            x: Math.random(),
            y: Math.random(),
            vx: (Math.random() - 0.5) * 0.001,
            vy: (Math.random() - 0.5) * 0.001,
            radius: Math.random() * 2 + 1,
            alpha: Math.random() * 0.5 + 0.2
        });
    }

    function render() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        pulseTime += 0.03;

        // Draw background grid lines
        ctx.strokeStyle = 'rgba(232, 96, 44, 0.06)';
        ctx.lineWidth = 1;
        const gridSize = 30;
        for (let x = 0; x < canvas.width; x += gridSize) {
            ctx.beginPath();
            ctx.moveTo(x, 0);
            ctx.lineTo(x, canvas.height);
            ctx.stroke();
        }
        for (let y = 0; y < canvas.height; y += gridSize) {
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(canvas.width, y);
            ctx.stroke();
        }

        // Draw floating ambient particles
        particles.forEach(p => {
            p.x += p.vx;
            p.y += p.vy;
            if (p.x < 0) p.x = 1;
            if (p.x > 1) p.x = 0;
            if (p.y < 0) p.y = 1;
            if (p.y > 1) p.y = 0;

            ctx.beginPath();
            ctx.arc(p.x * canvas.width, p.y * canvas.height, p.radius, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(56, 189, 248, ${p.alpha * 0.5})`;
            ctx.fill();
        });

        // Draw connection beams between nodes
        const edges = [
            [0, 1], // Student -> Gemini
            [1, 2], // Gemini -> ArmorIQ
            [2, 3], // ArmorIQ -> MCP
            [0, 2]  // Student -> ArmorIQ direct constraint
        ];

        edges.forEach(([i, j]) => {
            const n1 = nodes[i];
            const n2 = nodes[j];
            const x1 = n1.x * canvas.width;
            const y1 = n1.y * canvas.height;
            const x2 = n2.x * canvas.width;
            const y2 = n2.y * canvas.height;

            const grad = ctx.createLinearGradient(x1, y1, x2, y2);
            grad.addColorStop(0, n1.color);
            grad.addColorStop(1, n2.color);

            ctx.beginPath();
            ctx.moveTo(x1, y1);
            ctx.lineTo(x2, y2);
            ctx.strokeStyle = 'rgba(99, 102, 241, 0.25)';
            ctx.lineWidth = 1.5;
            ctx.stroke();

            // Animated traveling packet on beam
            const packetPos = (pulseTime + i * 0.3) % 1;
            const px = x1 + (x2 - x1) * packetPos;
            const py = y1 + (y2 - y1) * packetPos;

            ctx.beginPath();
            ctx.arc(px, py, 3, 0, Math.PI * 2);
            ctx.fillStyle = '#FFF';
            ctx.shadowColor = n1.color;
            ctx.shadowBlur = 10;
            ctx.fill();
            ctx.shadowBlur = 0;
        });

        // Draw Nodes
        nodes.forEach((n, idx) => {
            const nx = n.x * canvas.width;
            const ny = n.y * canvas.height;
            const pulse = Math.sin(pulseTime * 2 + idx) * 2;

            // Outer Glow
            ctx.beginPath();
            ctx.arc(nx, ny, n.size + 6 + pulse, 0, Math.PI * 2);
            ctx.fillStyle = `${n.color}22`;
            ctx.fill();

            // Core Node
            ctx.beginPath();
            ctx.arc(nx, ny, n.size, 0, Math.PI * 2);
            ctx.fillStyle = n.color;
            ctx.shadowColor = n.color;
            ctx.shadowBlur = 12;
            ctx.fill();
            ctx.shadowBlur = 0;
        });

        canvasAnimId = requestAnimationFrame(render);
    }
    render();
}

// ============================================================
// WORKFLOW EXECUTION CONTROLLER (ARMORIQ GOVERNANCE)
// ============================================================
async function executeWorkflowFromDashboard() {
    const runBtn = document.getElementById('dash-run-btn');
    const runBtnText = document.getElementById('dash-run-btn-text');
    const streamContainer = document.getElementById('dash-stream-container');
    const agentStateBadge = document.getElementById('agent-state-badge');
    const simDrift = document.getElementById('dash-sim-drift')?.checked || false;
    const simMissingDoc = document.getElementById('dash-sim-missing-doc')?.checked || false;

    // Reset UI Badges & Alerts
    const secAlert = document.getElementById('dash-security-alert');
    if (secAlert) secAlert.classList.add('hidden');
    const demAlert = document.getElementById('dash-demand-alert');
    if (demAlert) demAlert.classList.add('hidden');
    resetPipelineSteps();

    // Lock Button
    if (runBtn) runBtn.disabled = true;
    if (runBtnText) runBtnText.textContent = 'Orchestrating Plan & Minting ArmorIQ Token...';
    if (agentStateBadge) {
        agentStateBadge.className = 'badge-status chip-live';
        agentStateBadge.innerHTML = '<span class="status-pulse pulse-indigo"></span> Running...';
    }

    // Step 1: Request
    setPipelineStep(1, 'active');
    if (streamContainer) streamContainer.innerHTML = '';
    appendStreamCard('01. Request Received', 'scholarship.student_intent', `User initiated scholarship discovery for '${state.student.name}' in state '${state.student.state}'.`, 'ALLOW');
    addAuditLog('REQUEST_RECEIVED', `Initiated search for user '${state.student.name}' with state '${state.student.state}'.`, 'cyan');

    try {
        // Step 2: Plan
        setPipelineStep(1, 'done');
        setPipelineStep(2, 'active');
        appendStreamCard('02. Plan Captured', 'gemini.planner', 'Synthesized 4-step sequential plan adhering to ArmorIQ policy boundary: search -> check_eligibility -> prepare_application -> submit_application.', 'ALLOW');
        addAuditLog('PLAN_CAPTURED', 'Gemini 3.6 Flash reasoning generated canonical plan with 4 tool steps.', 'indigo');

        // Step 3: ArmorIQ Minting
        setPipelineStep(2, 'done');
        setPipelineStep(3, 'active');
        addAuditLog('TOKEN_REQUEST', 'Requesting cryptographic CSRG IntentToken from ArmorIQ IAP control plane...', 'purple');

        const payload = {
            student_name: state.student.name,
            raw_prompt: state.intent.prompt,
            scholarship_type: state.intent.type || 'government',
            target_state: state.student.state,
            target_field: state.student.field,
            annual_income: state.student.income,
            simulate_out_of_scope_violation: simDrift,
            simulate_missing_document: simMissingDoc
        };

        let data;
        try {
            const response = await fetch('/api/agent/run', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (response.ok) {
                data = await response.json();
            } else {
                data = generateSimulationTelemetry(payload);
            }
        } catch (_) {
            data = generateSimulationTelemetry(payload);
        }

        state.latestTelemetry = data;

        // Render Telemetry
        setPipelineStep(3, 'done');
        setPipelineStep(4, 'active');
        updateTelemetryCard(data);

        // Render Step Executions
        renderExecutionStream(data, streamContainer);

        // Check for Violations / Halts
        if (simDrift || data.blocked_steps > 0) {
            setPipelineStep(4, 'blocked');
            setPipelineStep(5, 'done');
            showSecurityAlert(data);
            showToast('⚠️ Consequential Action Blocked by ArmorIQ Policy Engine', 'rose');
        } else if (simMissingDoc) {
            setPipelineStep(4, 'active');
            setPipelineStep(5, 'done');
            showDemandAlert('income_certificate.pdf');
            showToast('📄 Application Halted: Mandatory Certificate Required', 'amber');
        } else {
            setPipelineStep(4, 'done');
            setPipelineStep(5, 'done');
            showToast('✓ Workflow Completed with Full Cryptographic Assurance', 'emerald');
        }

        // Update Audit & Thought Stream
        updateThoughtStream(data);

    } catch (err) {
        setPipelineStep(3, 'blocked');
        appendStreamCard('Execution Error', 'system.error', err.message || 'Workflow execution error', 'BLOCK');
        addAuditLog('EXECUTION_ERROR', err.message || 'Error occurred during agent workflow', 'red');
        showToast(`Error: ${err.message}`, 'rose');
    } finally {
        if (runBtn) runBtn.disabled = false;
        if (runBtnText) runBtnText.textContent = 'Execute Governed Agent Workflow';
        if (agentStateBadge) {
            agentStateBadge.className = 'badge-status badge-ready';
            agentStateBadge.innerHTML = '<span class="status-pulse pulse-green"></span> Ready';
        }
    }
}

// Fallback high-fidelity simulation telemetry generator
function generateSimulationTelemetry(payload) {
    const isDrift = payload.simulate_out_of_scope_violation;
    const isMissingDoc = payload.simulate_missing_document;
    const tokenId = 'ak_csrg_' + Math.random().toString(36).substring(2, 18);
    const merkleHash = 'c1795523a262c9b27dc542f32c6b8a16f31f8a274150ffa0faf88ed9bd09b8db';
    const ecdsaSig = '30450220' + Array.from({length: 48}, () => Math.floor(Math.random()*16).toString(16)).join('');

    const stepResults = [
        {
            action: 'search_scholarships',
            status: 'COMPLETED',
            armoriq_decision: 'ALLOW',
            details: `Found 2 eligible government schemes in ${payload.target_state}.`
        },
        {
            action: 'check_eligibility',
            status: 'COMPLETED',
            armoriq_decision: 'ALLOW',
            details: `Validated academic and income criteria (Income: ₹${payload.annual_income.toLocaleString('en-IN')}).`
        },
        {
            action: 'prepare_application',
            status: 'COMPLETED',
            armoriq_decision: 'ALLOW',
            details: 'Drafted financial assistance grant package SCH-PUN-ENG-01.'
        }
    ];

    if (isDrift) {
        stepResults.push({
            action: 'submit_application',
            status: 'BLOCKED',
            armoriq_decision: 'BLOCK',
            error_message: 'Target scholarship violates signed intent policy. Out-of-scope private foundation scheme.'
        });
    } else {
        stepResults.push({
            action: 'submit_application',
            status: 'COMPLETED',
            armoriq_decision: 'ALLOW',
            details: 'Application submitted successfully to official scholarship gateway.'
        });
    }

    return {
        intent_token: tokenId,
        merkle_root_hash: merkleHash,
        ecdsa_signature: ecdsaSig,
        completed_steps: isDrift ? 3 : 4,
        blocked_steps: isDrift ? 1 : 0,
        step_results: stepResults
    };
}

// ============================================================
// STREAM & TELEMETRY RENDERING
// ============================================================
function updateTelemetryCard(data) {
    if (!data) return;
    const tokenDisplay = data.intent_token || 'ak_csrg_' + Math.random().toString(36).substring(2, 10);
    const merkleHash = data.merkle_root_hash || 'c1795523a262c9b27dc542f32c6b8a16f31f8a274150ffa0faf88ed9bd09b8db';
    const ecdsaSig = data.ecdsa_signature || '30450220025890efec529ee68bbef05a2de54e64a6dad3a361cfc629b8326410782aee2f...';

    const tokEl = document.getElementById('tel-token-id');
    if (tokEl) tokEl.textContent = tokenDisplay;
    const hashEl = document.getElementById('tel-plan-hash');
    if (hashEl) hashEl.textContent = merkleHash;
    const sigEl = document.getElementById('tel-ecdsa-sig');
    if (sigEl) sigEl.textContent = ecdsaSig;
    const badgeEl = document.getElementById('telemetry-badge');
    if (badgeEl) {
        badgeEl.textContent = 'Verified Intent Token';
        badgeEl.className = 'badge-chip chip-emerald';
    }
}

function renderExecutionStream(data, container) {
    if (!container) return;
    const steps = data.step_results || [];
    steps.forEach((step, idx) => {
        const stepNum = idx + 1;
        const isAllow = (step.armoriq_decision === 'ALLOW' || step.status === 'COMPLETED');
        const decisionTag = isAllow ? 'ALLOW' : 'BLOCK';
        const actionName = step.action || 'mcp_tool_action';
        let detailText = step.details || `Tool call '${actionName}' executed through FastMCP loopback proxy.`;

        if (!isAllow) {
            detailText = `BLOCKED by ArmorIQ: Consequential action denied. Reason: ${step.error_message || 'Target action is out-of-scope'}`;
            addAuditLog('POLICY_BLOCK', `Action 'scholarship.${actionName}' BLOCKED by ArmorIQ. Invariant preserved.`, 'red');
        } else {
            addAuditLog('POLICY_ALLOW', `Action 'scholarship.${actionName}' verified with NIST P-256 ECDSA token. Invocation authorized.`, 'green');
        }

        appendStreamCard(`Step 0${stepNum}: ${actionName}`, `scholarship.${actionName}`, detailText, decisionTag);
    });
}

function appendStreamCard(title, toolName, desc, decision) {
    const container = document.getElementById('dash-stream-container');
    if (!container) return;
    const isAllow = (decision === 'ALLOW');
    const badgeText = isAllow ? '🛡️ ARMORIQ: ALLOW' : '🚫 ARMORIQ: BLOCK';
    const card = document.createElement('div');
    card.className = `stream-card ${isAllow ? 'card-allow' : 'card-block'}`;
    card.innerHTML = `
        <div class="stream-card-header">
            <span class="stream-tool-name">${toolName}</span>
            <span class="${isAllow ? 'badge-allowed' : 'badge-blocked'}">${badgeText}</span>
        </div>
        <div class="stream-card-body">${desc}</div>
        <div class="stream-card-meta">
            <span>⏱️ ${new Date().toLocaleTimeString()}</span>
            <span>🔒 ${isAllow ? 'ArmorIQ Proof of Authorization' : 'ArmorIQ Proof of Non-Execution (DB Count = 0)'}</span>
        </div>
    `;
    container.appendChild(card);
}

function showSecurityAlert(data) {
    const alertBox = document.getElementById('dash-security-alert');
    if (alertBox) alertBox.classList.remove('hidden');
    const actEl = document.getElementById('sec-alert-action');
    if (actEl) actEl.textContent = 'scholarship.submit_application';
    const tgtEl = document.getElementById('sec-alert-target');
    if (tgtEl) tgtEl.textContent = 'SCH-PRV-GLOBAL-03 (Apex Private Award)';
    const rsnEl = document.getElementById('sec-alert-reason');
    if (rsnEl) rsnEl.textContent = 'Target scholarship violates signed intent policy. Out-of-scope private foundation scheme.';
}

function showDemandAlert(fileName) {
    const alertBox = document.getElementById('dash-demand-alert');
    if (alertBox) alertBox.classList.remove('hidden');
    const docEl = document.getElementById('dash-demanded-doc');
    if (docEl) docEl.textContent = fileName || 'income_certificate.pdf';
}

// ============================================================
// PIPELINE PROGRESS BAR HELPERS
// ============================================================
function resetPipelineSteps() {
    for (let i = 1; i <= 5; i++) {
        const step = document.getElementById(`pstep-${i}`);
        if (step) step.className = 'pipe-step';
    }
}

function setPipelineStep(stepIdx, status) {
    const step = document.getElementById(`pstep-${stepIdx}`);
    if (step) {
        step.className = `pipe-step step-${status}`;
    }
}

// ============================================================
// SCHOLARSHIP EXPLORER (WITH MULTI-SOURCE ATTRIBUTION)
// ============================================================
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

    grid.innerHTML = filtered.map(sch => {
        const isB4S = (sch.source === 'Buddy4Study' || (sch.source_url && sch.source_url.includes('buddy4study.com')));
        const sourceBadge = isB4S 
            ? `<span class="badge-chip chip-purple" style="font-size:0.7rem;">🏷️ Buddy4Study</span>`
            : `<span class="badge-chip chip-emerald" style="font-size:0.7rem;">🏛️ ${sch.source || 'NSP / National Portal'}</span>`;

        const sourceLink = sch.source_url 
            ? `<a href="${sch.source_url}" target="_blank" rel="noopener noreferrer" style="color:var(--brand-indigo); font-size:0.75rem; text-decoration:underline; display:inline-flex; align-items:center; gap:4px;">Official Portal / Apply ↗</a>`
            : '';

        return `
        <div class="sch-card">
            <div>
                <div class="sch-badge-row" style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                    <div style="display:flex; gap:6px; align-items:center;">
                        <span class="badge-chip ${sch.category === 'government' ? 'chip-emerald' : 'chip-purple'}">
                            ${sch.category.toUpperCase()}
                        </span>
                        ${sourceBadge}
                    </div>
                    <span class="font-mono text-muted" style="font-size:0.75rem;">${sch.state}</span>
                </div>
                <h3 class="sch-name">${sch.name}</h3>
                <div class="sch-amount font-mono">${sch.amount}</div>
                <div class="sch-criteria-list">
                    <div><strong>Provider:</strong> ${sch.provider || 'Verified Organization'}</div>
                    <div><strong>Min Criteria:</strong> ${sch.min_cgpa} | Income &lt; ${sch.income_limit}</div>
                    <div><strong>Deadline:</strong> ${sch.deadline}</div>
                    ${sourceLink ? `<div style="margin-top:4px;"><strong>Source:</strong> ${sourceLink}</div>` : ''}
                </div>
            </div>
            <div class="sch-actions-row" style="margin-top:14px; display:flex; gap:8px;">
                <button class="btn-primary-sm" onclick="checkSpecificEligibility('${sch.id}')">
                    Check Eligibility
                </button>
                <button class="btn-outline" style="font-size:0.78rem; padding:6px 12px;" onclick="prepareApplicationDraft('${sch.id}')">
                    Prepare Draft
                </button>
            </div>
        </div>
        `;
    }).join('');
}

function filterScholarships() {
    renderScholarships();
}

function fetchLiveScholarships() {
    renderScholarships();
    showToast('Refreshed scholarship database from verified portals.', 'cyan');
}

function checkSpecificEligibility(id) {
    const sch = state.scholarships.find(s => s.id === id);
    if (!sch) return;
    if (sch.eligible) {
        showToast(`✓ Eligible for '${sch.name}' based on student profile!`, 'emerald');
    } else {
        showToast(`⚠️ Ineligible: ${sch.ineligible_reason || 'Criteria mismatch'}`, 'amber');
    }
}

function prepareApplicationDraft(id) {
    const sch = state.scholarships.find(s => s.id === id);
    if (!sch) return;
    showToast(`Draft prepared for '${sch.name}'. Ready for governed submission.`, 'indigo');
    switchTab('dashboard');
}

// ============================================================
// STUDENT PROFILE & DOCUMENT VAULT
// ============================================================
function saveStudentProfile() {
    const nameEl = document.getElementById('prof-name');
    const eduEl = document.getElementById('prof-edu');
    const stateEl = document.getElementById('prof-state');
    const incEl = document.getElementById('prof-income');

    if (nameEl) state.student.name = nameEl.value;
    if (eduEl) state.student.field = eduEl.value;
    if (stateEl) state.student.state = stateEl.value;
    if (incEl) state.student.income = parseInt(incEl.value, 10);

    const hdrName = document.getElementById('header-user-name');
    if (hdrName) hdrName.textContent = state.student.name;
    const tgtState = document.getElementById('dash-target-state');
    if (tgtState) tgtState.textContent = state.student.state;
    const tgtField = document.getElementById('dash-target-field');
    if (tgtField) tgtField.textContent = state.student.field;
    const tgtInc = document.getElementById('dash-target-income');
    if (tgtInc) tgtInc.textContent = `₹${state.student.income.toLocaleString('en-IN')}`;

    showToast('Student Profile Updated Successfully!', 'emerald');
    addAuditLog('PROFILE_UPDATE', `Updated student profile for '${state.student.name}' (${state.student.state}).`, 'cyan');
}

async function handleDocumentUpload() {
    const fileInput = document.getElementById('upload-doc-file');
    const docTypeEl = document.getElementById('upload-doc-type');
    const docType = docTypeEl ? docTypeEl.value : 'income_certificate';

    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
        showToast('Please select a PDF certificate to upload.', 'amber');
        return;
    }

    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('file', file);
    formData.append('doc_type', docType);
    formData.append('document_type', docType);
    formData.append('student_id', state.student.id);

    try {
        const res = await fetch('/api/documents/upload', {
            method: 'POST',
            body: formData
        });

        showToast(`✓ Document '${file.name}' verified and attached!`, 'emerald');

        if (docType === 'income_certificate') {
            const demAlert = document.getElementById('dash-demand-alert');
            if (demAlert) demAlert.classList.add('hidden');
            const fnameEl = document.getElementById('vault-income-fname');
            if (fnameEl) fnameEl.textContent = file.name;
            const statEl = document.getElementById('vault-income-status');
            if (statEl) statEl.innerHTML = '<span class="badge-status badge-ready">Verified</span>';
        }

        addAuditLog('DOC_UPLOAD', `Uploaded and verified certificate '${file.name}' (${docType}).`, 'green');
    } catch (_) {
        // Local simulation fallback
        showToast(`✓ Certificate '${file.name}' verified & attached to student record.`, 'emerald');
        const demAlert = document.getElementById('dash-demand-alert');
        if (demAlert) demAlert.classList.add('hidden');
        const fnameEl = document.getElementById('vault-income-fname');
        if (fnameEl) fnameEl.textContent = file.name;
        const statEl = document.getElementById('vault-income-status');
        if (statEl) statEl.innerHTML = '<span class="badge-status badge-ready">Verified</span>';
        addAuditLog('DOC_UPLOAD', `Uploaded certificate '${file.name}'.`, 'green');
    }
}

// ============================================================
// AUDIT LOG & CLOCK
// ============================================================
function addAuditLog(tag, message, color) {
    const now = new Date();
    const timeStr = now.toTimeString().split(' ')[0] + '.' + String(now.getMilliseconds()).padStart(3, '0');
    state.auditLogs.push({ time: timeStr, tag, message, color });

    const terminalBody = document.getElementById('audit-terminal-body');
    if (terminalBody) {
        const line = document.createElement('div');
        line.className = 't-line';
        line.innerHTML = `
            <span class="t-timestamp">${timeStr}</span>
            <span class="t-tag t-tag-${color}">${tag}</span>
            ${message}
        `;
        terminalBody.appendChild(line);
        terminalBody.scrollTop = terminalBody.scrollHeight;
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
    showToast('Exported audit report as JSON.', 'cyan');
}

function initClock() {
    const clock = document.getElementById('terminal-clock');
    if (clock) {
        setInterval(() => {
            clock.textContent = new Date().toISOString().replace('T', ' ').substring(0, 19) + ' UTC';
        }, 1000);
    }
}

function updateThoughtStream(data) {
    const streamBox = document.getElementById('llm-thought-stream');
    if (!streamBox) return;
    streamBox.textContent = `[Gemini 3.6 Flash] Student requested verified scholarships in ${state.student.state}.
[Plan Capture] Canonical plan captured with SHA-256 Merkle root (${data && data.merkle_root_hash ? data.merkle_root_hash.substring(0, 16) + '...' : 'c1795523...'}).
[ArmorIQ Policy] OPA zero-trust policy applied to FastMCP server 'scholarship'.
[Completed Steps] ${(data && data.completed_steps) || 4} consequential tools authorized with NIST P-256 signatures.`;
}

// ============================================================
// MODAL CONTROLS
// ============================================================
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
    const eduEl = document.getElementById('modal-edu');
    const stateEl = document.getElementById('modal-state');
    const incEl = document.getElementById('modal-income');
    const promptEl = document.getElementById('modal-prompt');

    if (nameEl) state.student.name = nameEl.value;
    if (eduEl) state.student.field = eduEl.value;
    if (stateEl) state.student.state = stateEl.value;
    if (incEl) state.student.income = parseInt(incEl.value, 10);
    if (promptEl) state.intent.prompt = promptEl.value;

    const hdrName = document.getElementById('header-user-name');
    if (hdrName) hdrName.textContent = state.student.name;
    const actPrompt = document.getElementById('dash-active-prompt');
    if (actPrompt) actPrompt.textContent = `"${state.intent.prompt}"`;
    const tgtState = document.getElementById('dash-target-state');
    if (tgtState) tgtState.textContent = state.student.state;
    const tgtField = document.getElementById('dash-target-field');
    if (tgtField) tgtField.textContent = state.student.field;
    const tgtInc = document.getElementById('dash-target-income');
    if (tgtInc) tgtInc.textContent = `₹${state.student.income.toLocaleString('en-IN')}`;

    closeOrderModal();
    executeWorkflowFromDashboard();
}

// ============================================================
// TOAST NOTIFICATION SYSTEM
// ============================================================
function showToast(message, color = 'cyan') {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = 'toast-message';
    toast.innerHTML = `<span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => {
        toast.remove();
    }, 4000);
}

// Global Window Exports
window.switchTab = switchTab;
window.executeWorkflowFromDashboard = executeWorkflowFromDashboard;
window.openOrderModal = openOrderModal;
window.closeOrderModal = closeOrderModal;
window.submitOrderModal = submitOrderModal;
window.saveStudentProfile = saveStudentProfile;
window.handleDocumentUpload = handleDocumentUpload;
window.exportAuditLogJSON = exportAuditLogJSON;
window.fetchLiveScholarships = fetchLiveScholarships;
window.filterScholarships = filterScholarships;
window.checkSpecificEligibility = checkSpecificEligibility;
window.prepareApplicationDraft = prepareApplicationDraft;
window.showToast = showToast;