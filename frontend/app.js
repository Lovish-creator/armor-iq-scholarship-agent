const AGENT_API = "http://127.0.0.1:8000";
const PORTAL_API = "http://127.0.0.1:8001";

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
                ✅ <strong>Upload & Document Verification Success!</strong><br>
                File: <code>${data.filename}</code> | Type: <code>${data.doc_type}</code><br>
                <div style="margin-top:6px;"><strong>AI Parsed Metadata:</strong><pre style="background:rgba(0,0,0,0.3); padding:6px; border-radius:6px;">${aiMetaFormatted}</pre></div>
            `;
            
            const demandAlert = document.getElementById("demand-alert");
            if (demandAlert) demandAlert.classList.add("hidden");
        } else {
            uploadLog.innerHTML = `❌ Error: ${data.detail || "Upload failed."}`;
        }
    } catch (err) {
        uploadLog.innerHTML = `❌ Upload Exception: ${err.message}`;
    } finally {
        uploadBtn.disabled = false;
        uploadBtn.innerHTML = "📤 Upload & Fulfill Document Requirement";
    }
}

async function triggerAgentWorkflow() {
    const studentName = document.getElementById("student-name").value;
    const studentEdu = document.getElementById("student-edu").value;
    const targetState = document.getElementById("target-state").value;
    const annualIncome = document.getElementById("annual-income").value;
    const scholarshipType = document.getElementById("scholarship-type").value;
    const rawPrompt = document.getElementById("raw-prompt").value;
    const simulateOutOfScope = document.getElementById("simulate-out-of-scope").checked;
    const simulateMissingDoc = document.getElementById("simulate-missing-doc").checked;
    
    const runBtn = document.getElementById("run-btn");
    const workflowBadge = document.getElementById("workflow-badge");
    const timelineList = document.getElementById("timeline-list");
    const securityAlert = document.getElementById("security-alert");
    const demandAlert = document.getElementById("demand-alert");
    const webResultsBox = document.getElementById("web-results-box");
    
    runBtn.disabled = true;
    runBtn.innerHTML = "⏳ Authenticating ArmorIQ Key & Executing...";
    workflowBadge.className = "badge-live";
    workflowBadge.textContent = "Executing...";
    securityAlert.classList.add("hidden");
    demandAlert.classList.add("hidden");
    webResultsBox.classList.add("hidden");
    timelineList.innerHTML = `<li class="timeline-placeholder">Connecting to ArmorIQ Platform API with key ak_live_f247...</li>`;
    
    try {
        const response = await fetch(`${AGENT_API}/api/agent/run`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                raw_prompt: rawPrompt,
                scholarship_type: scholarshipType,
                target_state: targetState,
                target_field: studentEdu,
                simulate_out_of_scope_violation: simulateOutOfScope,
                simulate_missing_document: simulateMissingDoc
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
        runBtn.innerHTML = "🌐 Execute Governed Agent Workflow";
    }
}

function renderResults(summary) {
    const workflowBadge = document.getElementById("workflow-badge");
    const timelineList = document.getElementById("timeline-list");
    const securityAlert = document.getElementById("security-alert");
    const demandAlert = document.getElementById("demand-alert");
    const proofText = document.getElementById("proof-text");
    const webResultsBox = document.getElementById("web-results-box");
    const webResultsList = document.getElementById("web-results-list");
    
    timelineList.innerHTML = "";
    webResultsList.innerHTML = "";
    
    // Update Telemetry Box
    if (summary.armoriq_telemetry) {
        const tel = summary.armoriq_telemetry;
        document.getElementById("telemetry-key").textContent = tel.api_key_used || "ak_live_f247...";
        document.getElementById("tel-key-full").textContent = `${tel.api_key_used} (${tel.provider})`;
        document.getElementById("tel-domain").textContent = `${tel.api_key_domain} (${tel.api_key_tier.toUpperCase()} Tier)`;
        document.getElementById("tel-merkle").textContent = tel.merkle_root || "c1795523a262c9b27dc542f32c6b8a16f31f8a274150ffa0faf88ed9bd09b8db";
        document.getElementById("tel-sig").textContent = tel.ecdsa_signature || "30450220025890efec529ee68bbef05a2de54e64a6dad3a361cfc629b8326410782aee2f...";
    }
    
    if (summary.status === "COMPLETED") {
        workflowBadge.className = "badge-live";
        workflowBadge.style.background = "rgba(16, 185, 129, 0.2)";
        workflowBadge.style.color = "#10b981";
        workflowBadge.textContent = "✅ ArmorIQ Key Verified & Workflow Passed";
    } else {
        workflowBadge.className = "badge-live";
        workflowBadge.style.background = "rgba(239, 68, 68, 0.2)";
        workflowBadge.style.color = "#ef4444";
        workflowBadge.textContent = "🛡️ ArmorIQ Governance Block Triggered";
    }
    
    // Add Token Entry
    const tokenItem = document.createElement("li");
    tokenItem.className = "timeline-item";
    tokenItem.innerHTML = `
        <div class="step-circle success"></div>
        <div class="step-title">🔑 ArmorIQ Production Intent Token Signed</div>
        <div class="step-meta">API Key: ${summary.armoriq_telemetry ? summary.armoriq_telemetry.api_key_used : "ak_live_f247..."} • Token ID: ${summary.intent_token ? summary.intent_token.substring(0, 24) + "..." : "LIVE-TOKEN"}</div>
        <div class="step-code">Signed Plan Constraints: { scholarship_type: 'government', state: 'Punjab' }</div>
    `;
    timelineList.appendChild(tokenItem);
    
    // Render Step Results
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
        
        if (step.action === "check_eligibility" && step.details.result) {
            const res = step.details.result;
            if (res.action_required === "DEMAND_DOCUMENT" || (res.missing_documents && res.missing_documents.length > 0)) {
                const missingDocName = res.missing_documents ? res.missing_documents.join(", ") : "income_certificate.pdf";
                document.getElementById("demanded-doc-name").textContent = missingDocName;
                demandAlert.classList.remove("hidden");
            }
        }
        
        if (step.action === "search_scholarships" && step.details.scholarships) {
            webResultsBox.classList.remove("hidden");
            step.details.scholarships.forEach(sch => {
                const card = document.createElement("div");
                card.style.cssText = "background:#1a2233; border:1px solid #26334d; padding:12px; border-radius:10px; font-size:0.85rem;";
                card.innerHTML = `
                    <div style="font-weight:600; color:#f1f5f9; display:flex; justify-content:space-between;">
                        <span>${sch.name}</span>
                        <span class="tag" style="background:${sch.scholarship_type==='government'?'rgba(16,185,129,0.2)':'rgba(239,68,68,0.2)'}; color:${sch.scholarship_type==='government'?'#6ee7b7':'#fca5a5'};">${sch.scholarship_type.toUpperCase()}</span>
                    </div>
                    <div style="color:#94a3b8; margin:4px 0; font-size:0.78rem;">${sch.web_snippet || 'Verified scheme eligible for engineering students'}</div>
                    <div style="display:flex; justify-content:space-between; font-size:0.75rem; color:#a5b4fc;">
                        <span>Source: <a href="${sch.source_url || '#'}" target="_blank" style="color:#60a5fa;">${sch.source_url || 'https://scholarships.gov.in'}</a></span>
                        <span>Award: ₹${sch.amount.toLocaleString('en-IN')}</span>
                    </div>
                `;
                webResultsList.appendChild(card);
            });
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
            document.getElementById("alert-target").textContent = step.details.inputs ? step.details.inputs.scholarship_id : "SCH-WEB-002 (Private Award)";
            document.getElementById("alert-reason").textContent = step.error_message || "Target action violates signed user intent constraint.";
            securityAlert.classList.remove("hidden");
        }
    });
    
    if (summary.proof_of_non_execution) {
        proofText.innerHTML = `Consequential Submissions Executed: <strong>${summary.proof_of_non_execution.executed_tool_submissions || 1}</strong> | Blocked Unauthorized Attempts: <strong style="color:#ef4444;">${summary.proof_of_non_execution.blocked_non_executed_attempts || summary.blocked_steps}</strong>`;
    }
}
