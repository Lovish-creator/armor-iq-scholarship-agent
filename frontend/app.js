const API_BASE = "http://127.0.0.1:8000";

async function triggerAgentWorkflow() {
    const rawPrompt = document.getElementById("raw-prompt").value;
    const scholarshipType = document.getElementById("scholarship-type").value;
    const targetState = document.getElementById("target-state").value;
    const simulateOutOfScope = document.getElementById("simulate-out-of-scope").checked;
    
    const runBtn = document.getElementById("run-btn");
    const workflowBadge = document.getElementById("workflow-badge");
    const timelineList = document.getElementById("timeline-list");
    const securityAlert = document.getElementById("security-alert");
    
    // Reset UI State
    runBtn.disabled = true;
    runBtn.innerHTML = "⏳ Executing Governed Steps...";
    workflowBadge.className = "badge-live";
    workflowBadge.textContent = "Executing...";
    securityAlert.classList.add("hidden");
    timelineList.innerHTML = `<li class="timeline-placeholder">Initializing Agent Intent & ArmorIQ Plan Capture...</li>`;
    
    try {
        const response = await fetch(`${API_BASE}/api/agent/run`, {
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
        runBtn.innerHTML = "🚀 Launch Governed Workflow";
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
    
    // Add Token Minting Entry
    const tokenItem = document.createElement("li");
    tokenItem.className = "timeline-item";
    tokenItem.innerHTML = `
        <div class="step-circle success"></div>
        <div class="step-title">🔑 ArmorIQ Cryptographic Intent Token Minted</div>
        <div class="step-meta">Plan Hash Signed • Token ID: ${summary.intent_token ? summary.intent_token.substring(0, 24) + "..." : "TOKEN-GEN"}</div>
        <div class="step-code">Intent Constraints: { type: '${summary.step_results[0].details.tool === 'search_scholarships' ? 'government' : 'custom'}', state: 'Punjab' }</div>
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
            // Display Security Governance Alert Banner
            document.getElementById("alert-action").textContent = step.action;
            document.getElementById("alert-target").textContent = step.details.inputs ? step.details.inputs.scholarship_id : "SCH-PRV-GLOBAL-03";
            document.getElementById("alert-reason").textContent = step.error_message || "Target action violates signed user intent constraint.";
            securityAlert.classList.remove("hidden");
        }
    });
    
    // Update Non-Execution Proof Text
    if (summary.proof_of_non_execution) {
        proofText.innerHTML = `Consequential Submissions Executed: <strong>${summary.proof_of_non_execution.executed_tool_submissions || 1}</strong> | Blocked Un-authorized Attempts: <strong style="color:#ef4444;">${summary.proof_of_non_execution.blocked_non_executed_attempts || summary.blocked_steps}</strong>`;
    }
}
