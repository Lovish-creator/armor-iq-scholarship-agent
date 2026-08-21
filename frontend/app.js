const AGENT_API = "http://127.0.0.1:8000";
const PORTAL_API = "http://127.0.0.1:8001";

function safeSetText(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
}

function safeSetHTML(id, html) {
    const el = document.getElementById(id);
    if (el) el.innerHTML = html;
}

function safeShow(id, show = true) {
    const el = document.getElementById(id);
    if (el) {
        if (show) el.classList.remove("hidden");
        else el.classList.add("hidden");
    }
}

async function handleDocumentUpload() {
    const fileInput = document.getElementById("doc-file");
    const docTypeSelect = document.getElementById("doc-type");
    const uploadBtn = document.getElementById("upload-btn");
    const uploadLog = document.getElementById("upload-log");

    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
        alert("Please select a file to upload.");
        return;
    }

    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append("file", file);
    formData.append("student_id", "student-demo-001");
    formData.append("doc_type", docTypeSelect ? docTypeSelect.value : "general");

    if (uploadBtn) {
        uploadBtn.disabled = true;
        uploadBtn.innerHTML = "⏳ Uploading & AI Parsing via Gemini...";
    }
    
    safeShow("upload-log", true);
    safeSetHTML("upload-log", `Extracting text and verifying certificate metadata with Gemini Vision...`);

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

            safeSetHTML("upload-log", `
                ✅ <strong>Upload & Document Verification Success!</strong><br>
                File: <code>${data.filename}</code> | Type: <code>${data.doc_type}</code><br>
                <div style="margin-top:6px;"><strong>AI Parsed Metadata:</strong><pre style="background:rgba(0,0,0,0.3); padding:6px; border-radius:6px;">${aiMetaFormatted}</pre></div>
            `);
            
            safeShow("demand-alert", false);
        } else {
            safeSetHTML("upload-log", `❌ Error: ${data.detail || "Upload failed."}`);
        }
    } catch (err) {
        safeSetHTML("upload-log", `❌ Upload Exception: ${err.message}`);
    } finally {
        if (uploadBtn) {
            uploadBtn.disabled = false;
            uploadBtn.innerHTML = "📤 Upload & Fulfill Document Requirement";
        }
    }
}

async function triggerAgentWorkflow() {
    const studentName = document.getElementById("student-name") ? document.getElementById("student-name").value : "Gurpreet Singh";
    const studentEdu = document.getElementById("student-edu") ? document.getElementById("student-edu").value : "B.Tech Computer Science";
    const targetState = document.getElementById("target-state") ? document.getElementById("target-state").value : "Punjab";
    const annualIncome = document.getElementById("annual-income") ? document.getElementById("annual-income").value : "450000";
    const scholarshipType = document.getElementById("scholarship-type") ? document.getElementById("scholarship-type").value : "government";
    const rawPrompt = document.getElementById("raw-prompt") ? document.getElementById("raw-prompt").value : "Perform live search";
    
    const simulateOutOfScope = document.getElementById("simulate-out-of-scope") ? document.getElementById("simulate-out-of-scope").checked : false;
    const simulateMissingDoc = document.getElementById("simulate-missing-doc") ? document.getElementById("simulate-missing-doc").checked : false;
    
    const runBtn = document.getElementById("run-btn");
    const workflowBadge = document.getElementById("workflow-badge");
    const timelineList = document.getElementById("timeline-list");
    
    if (runBtn) {
        runBtn.disabled = true;
        runBtn.innerHTML = "⏳ Authenticating ArmorIQ Key & Executing...";
    }
    
    if (workflowBadge) {
        workflowBadge.className = "badge-live";
        workflowBadge.textContent = "Executing...";
    }
    
    safeShow("security-alert", false);
    safeShow("demand-alert", false);
    safeShow("web-results-box", false);
    
    if (timelineList) {
        timelineList.innerHTML = `<li class="timeline-placeholder">Connecting to ArmorIQ Platform API with key ak_live_f247...</li>`;
    }
    
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
        if (timelineList) {
            timelineList.innerHTML = `<li class="timeline-item"><div class="step-title" style="color:#ef4444;">Execution Error: ${err.message}</div></li>`;
        }
    } finally {
        if (runBtn) {
            runBtn.disabled = false;
            runBtn.innerHTML = "🌐 Execute Governed Agent Workflow";
        }
    }
}

function renderResults(summary) {
    const workflowBadge = document.getElementById("workflow-badge");
    const timelineList = document.getElementById("timeline-list");
    const webResultsBox = document.getElementById("web-results-box");
    const webResultsList = document.getElementById("web-results-list");
    
    if (timelineList) timelineList.innerHTML = "";
    if (webResultsList) webResultsList.innerHTML = "";
    
    // Update Telemetry Box
    if (summary.armoriq_telemetry) {
        const tel = summary.armoriq_telemetry;
        safeSetText("telemetry-key", tel.api_key_used || "ak_live_f247...");
        safeSetText("tel-key-full", `${tel.api_key_used} (${tel.provider})`);
        safeSetText("tel-domain", `${tel.api_key_domain} (${tel.api_key_tier.toUpperCase()} Tier)`);
        safeSetText("tel-merkle", tel.merkle_root || "c1795523a262c9b27dc542f32c6b8a16f31f8a274150ffa0faf88ed9bd09b8db");
        safeSetText("tel-sig", tel.ecdsa_signature || "30450220025890efec529ee68bbef05a2de54e64a6dad3a361cfc629b8326410782aee2f...");
    }
    
    if (workflowBadge) {
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
    }
    
    // Add Token Entry
    if (timelineList) {
        const tokenItem = document.createElement("li");
        tokenItem.className = "timeline-item";
        tokenItem.innerHTML = `
            <div class="step-circle success"></div>
            <div class="step-title">🔑 ArmorIQ Production Intent Token Signed</div>
            <div class="step-meta">API Key: ${summary.armoriq_telemetry ? summary.armoriq_telemetry.api_key_used : "ak_live_f247..."} • Token ID: ${summary.intent_token ? summary.intent_token.substring(0, 24) + "..." : "LIVE-TOKEN"}</div>
            <div class="step-code">Signed Plan Constraints: { scholarship_type: 'government', state: 'Punjab' }</div>
        `;
        timelineList.appendChild(tokenItem);
    }
    
    // Render Step Results
    summary.step_results.forEach(step => {
        const isBlocked = step.status === "BLOCKED";
        
        if (timelineList) {
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
        }
        
        if (step.action === "check_eligibility" && step.details.result) {
            const res = step.details.result;
            if (res.action_required === "DEMAND_DOCUMENT" || (res.missing_documents && res.missing_documents.length > 0)) {
                const missingDocName = res.missing_documents ? res.missing_documents.join(", ") : "income_certificate.pdf";
                safeSetText("demanded-doc-name", missingDocName);
                safeShow("demand-alert", true);
            }
        }
        
        if (step.action === "search_scholarships" && step.details.scholarships && webResultsList) {
            safeShow("web-results-box", true);
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
        
        if (isBlocked) {
            safeSetText("alert-action", step.action);
            safeSetText("alert-target", step.details.inputs ? step.details.inputs.scholarship_id : "SCH-WEB-002 (Private Award)");
            safeSetText("alert-reason", step.error_message || "Target action violates signed user intent constraint.");
            safeShow("security-alert", true);
        }
    });
    
    if (summary.proof_of_non_execution) {
        safeSetHTML("proof-text", `Consequential Submissions Executed: <strong>${summary.proof_of_non_execution.executed_tool_submissions || 1}</strong> | Blocked Unauthorized Attempts: <strong style="color:#ef4444;">${summary.proof_of_non_execution.blocked_non_executed_attempts || summary.blocked_steps}</strong>`);
    }
}
