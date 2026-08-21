const AGENT_API = "http://127.0.0.1:8000";
const PORTAL_API = "http://127.0.0.1:8001";

// Load active student profile on startup
document.addEventListener("DOMContentLoaded", () => {
    fetchStudentProfile();
});

async function fetchStudentProfile() {
    try {
        const resp = await fetch(`${PORTAL_API}/api/student/student-demo-001`);
        if (resp.ok) {
            const data = await resp.json();
            document.getElementById("st-name").textContent = data.name;
            document.getElementById("st-edu").textContent = data.education;
            document.getElementById("st-state").textContent = data.state;
            document.getElementById("st-income").textContent = `₹${data.annual_income.toLocaleString('en-IN')}`;
            document.getElementById("st-cgpa").textContent = `${data.cgpa} CGPA`;
            
            const docsContainer = document.getElementById("st-docs");
            docsContainer.innerHTML = "";
            data.documents.forEach(doc => {
                const tag = document.createElement("span");
                tag.className = "tag";
                tag.textContent = doc;
                docsContainer.appendChild(tag);
            });
        }
    } catch (e) {
        console.warn("Could not fetch initial student profile:", e);
    }
}

async function handleDocumentUpload() {
    const fileInput = document.getElementById("doc-file");
    const docTypeSelect = document.getElementById("doc-type");
    const uploadBtn = document.getElementById("upload-btn");
    const uploadLog = document.getElementById("upload-log");

    if (!fileInput.files || fileInput.files.length === 0) {
        alert("Please select a file to upload.");
        return;
    }

    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append("file", file);
    formData.append("student_id", "student-demo-001");
    formData.append("doc_type", docTypeSelect.value);

    uploadBtn.disabled = true;
    uploadBtn.innerHTML = "⏳ Uploading & AI Parsing via Gemini...";
    uploadLog.classList.remove("hidden");
    uploadLog.innerHTML = `Extracting text and verifying certificate metadata with Gemini Vision...`;

    try {
        const resp = await fetch(`${PORTAL_API}/api/documents/upload`, {
            method: "POST",
            body: formData
        });

        const data = await resp.json();
        if (resp.ok) {
            let aiMetaFormatted = "";
            try {
                aiMetaFormatted = JSON.stringify(data.ai_parsed_metadata, null, 2);
            } catch(e) {
                aiMetaFormatted = String(data.ai_parsed_metadata);
            }

            uploadLog.innerHTML = `
                ✅ <strong>Upload & Verification Success!</strong><br>
                File: <code>${data.filename}</code> | Type: <code>${data.doc_type}</code><br>
                <div style="margin-top:6px;"><strong>AI Parsed Metadata:</strong><pre style="background:rgba(0,0,0,0.3); padding:6px; border-radius:6px;">${aiMetaFormatted}</pre></div>
            `;
            // Refresh student profile badge
            await fetchStudentProfile();
        } else {
            uploadLog.innerHTML = `❌ Error: ${data.detail || "Upload failed."}`;
        }
    } catch (err) {
        uploadLog.innerHTML = `❌ Upload Exception: ${err.message}`;
    } finally {
        uploadBtn.disabled = false;
        uploadBtn.innerHTML = "📤 Upload & Extract Document Data";
    }
}

async function triggerAgentWorkflow() {
    const rawPrompt = document.getElementById("raw-prompt").value;
    const scholarshipType = document.getElementById("scholarship-type").value;
    const targetState = document.getElementById("target-state").value;
    const simulateOutOfScope = document.getElementById("simulate-out-of-scope").checked;
    
    const runBtn = document.getElementById("run-btn");
    const workflowBadge = document.getElementById("workflow-badge");
    const timelineList = document.getElementById("timeline-list");
    const securityAlert = document.getElementById("security-alert");
    const demandAlert = document.getElementById("demand-alert");
    
    runBtn.disabled = true;
    runBtn.innerHTML = "⏳ Executing Governed Steps...";
    workflowBadge.className = "badge-live";
    workflowBadge.textContent = "Executing...";
    securityAlert.classList.add("hidden");
    demandAlert.classList.add("hidden");
    timelineList.innerHTML = `<li class="timeline-placeholder">Initializing Agent Intent & ArmorIQ Plan Capture...</li>`;
    
    try {
        const response = await fetch(`${AGENT_API}/api/agent/run`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                raw_prompt: rawPrompt,
                scholarship_type: scholarshipType,
                target_state: targetState,
                simulate_out_of_scope_violation: simulateOutOfScope
            })
        });
        
        if (!response.ok) {
            throw new Error(`Server returned HTTP ${response.status}`);
        }
        
        const data = await response.json();
        renderResults(data);
        
    } catch (err) {
        timelineList.innerHTML = `<li class="timeline-item"><div class="step-title" style="color:#ef4444;">Execution Error: ${err.message}</div></li>`;
    } finally {
        runBtn.disabled = false;
        runBtn.innerHTML = "🚀 Launch Governed Agent Workflow";
    }
}

function renderResults(summary) {
    const workflowBadge = document.getElementById("workflow-badge");
    const timelineList = document.getElementById("timeline-list");
    const securityAlert = document.getElementById("security-alert");
    const proofText = document.getElementById("proof-text");
    
    timelineList.innerHTML = "";
    
    if (summary.status === "COMPLETED") {
        workflowBadge.className = "badge-live";
        workflowBadge.style.background = "rgba(16, 185, 129, 0.2)";
        workflowBadge.style.color = "#10b981";
        workflowBadge.textContent = "✅ Workflow Passed";
    } else {
        workflowBadge.className = "badge-live";
        workflowBadge.style.background = "rgba(239, 68, 68, 0.2)";
        workflowBadge.style.color = "#ef4444";
        workflowBadge.textContent = "🛡️ Intent Violation Blocked";
    }
    
    // Add Intent Token Entry
    const tokenItem = document.createElement("li");
    tokenItem.className = "timeline-item";
    tokenItem.innerHTML = `
        <div class="step-circle success"></div>
        <div class="step-title">🔑 ArmorIQ Production Intent Token Minted</div>
        <div class="step-meta">Token Signed • ID: ${summary.intent_token ? summary.intent_token.substring(0, 24) + "..." : "LIVE-TOKEN"}</div>
        <div class="step-code">Signed Plan Constraints: { scholarship_type: 'government', state: 'Punjab' }</div>
    `;
    timelineList.appendChild(tokenItem);
    
    // Render Step Execution Results
    summary.step_results.forEach(step => {
        const isBlocked = step.status === "BLOCKED";
        const item = document.createElement("li");
        item.className = "timeline-item";
        
        let detailsFormatted = "";
        try {
            detailsFormatted = JSON.stringify(step.details, null, 2);
        } catch(e) {
            detailsFormatted = String(step.details);
        }
        
        item.innerHTML = `
            <div class="step-circle ${isBlocked ? 'blocked' : 'success'}"></div>
            <div class="step-title">
                Step ${step.step_id}: ${step.action} 
                <span class="${isBlocked ? 'badge-blocked' : 'badge-subtle'}">${step.armoriq_decision}</span>
            </div>
            <div class="step-meta">Execution Status: <strong>${step.executed ? 'EXECUTED' : 'ABORTED / NOT EXECUTED'}</strong></div>
            <div class="step-code"><pre>${detailsFormatted}</pre></div>
        `;
        timelineList.appendChild(item);
        
        if (isBlocked) {
            document.getElementById("alert-action").textContent = step.action;
            document.getElementById("alert-target").textContent = step.details.inputs ? step.details.inputs.scholarship_id : "SCH-PRV-GLOBAL-03";
            document.getElementById("alert-reason").textContent = step.error_message || "Target action violates signed user intent constraint.";
            securityAlert.classList.remove("hidden");
        }
    });
    
    if (summary.proof_of_non_execution) {
        proofText.innerHTML = `Consequential Submissions Executed: <strong>${summary.proof_of_non_execution.executed_tool_submissions || 1}</strong> | Blocked Unauthorized Attempts: <strong style="color:#ef4444;">${summary.proof_of_non_execution.blocked_non_executed_attempts || summary.blocked_steps}</strong>`;
    }
}
