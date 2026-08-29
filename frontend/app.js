const AGENT_API = window.location.origin;
const PORTAL_API = window.location.origin;

function safeSetText(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text ?? "";
}

function safeSetHTML(id, html) {
    const el = document.getElementById(id);
    if (el) el.innerHTML = html ?? "";
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

    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
        alert("Please select a file to upload.");
        return;
    }

    const file = fileInput.files[0];
    const formData = new FormData();

    formData.append("file", file);
    formData.append("student_id", "student-demo-001");
    formData.append(
        "doc_type",
        docTypeSelect ? docTypeSelect.value : "general"
    );

    if (uploadBtn) {
        uploadBtn.disabled = true;
        uploadBtn.innerHTML = "⏳ Uploading & AI Parsing via Gemini...";
    }

    safeShow("upload-log", true);
    safeSetHTML(
        "upload-log",
        `Extracting text and verifying certificate metadata with Gemini Vision...`
    );

    try {
        const resp = await fetch(`${PORTAL_API}/api/documents/upload`, {
            method: "POST",
            body: formData
        });

        const data = await resp.json();

        if (resp.ok) {
            let aiMetaFormatted = "";

            try {
                aiMetaFormatted = JSON.stringify(
                    data.ai_parsed_metadata,
                    null,
                    2
                );
            } catch (e) {
                aiMetaFormatted = String(data.ai_parsed_metadata);
            }

            safeSetHTML(
                "upload-log",
                `
                ✅ <strong>Upload & Document Verification Success!</strong><br>
                File: <code>${data.filename ?? "Unknown"}</code> |
                Type: <code>${data.doc_type ?? "general"}</code><br>

                <div style="margin-top:6px;">
                    <strong>AI Parsed Metadata:</strong>
                    <pre style="background:rgba(0,0,0,0.3); padding:6px; border-radius:6px;">${aiMetaFormatted}</pre>
                </div>
                `
            );

            safeShow("demand-alert", false);
        } else {
            safeSetHTML(
                "upload-log",
                `❌ Error: ${data?.detail || "Upload failed."}`
            );
        }
    } catch (err) {
        safeSetHTML(
            "upload-log",
            `❌ Upload Exception: ${err?.message || "Unknown error"}`
        );
    } finally {
        if (uploadBtn) {
            uploadBtn.disabled = false;
            uploadBtn.innerHTML = "📤 Upload & Fulfill Document Requirement";
        }
    }
}

async function triggerAgentWorkflow() {
    const studentName =
        document.getElementById("student-name")?.value ||
        "Gurpreet Singh";

    const studentEdu =
        document.getElementById("student-edu")?.value ||
        "B.Tech Computer Science";

    const targetState =
        document.getElementById("target-state")?.value ||
        "Punjab";

    const annualIncome =
        parseInt(document.getElementById("annual-income")?.value) ||
        450000;

    const scholarshipType =
        document.getElementById("scholarship-type")?.value ||
        "government";

    const rawPrompt =
        document.getElementById("raw-prompt")?.value ||
        "Perform live search";

    const simulateOutOfScope =
        document.getElementById("simulate-out-of-scope")?.checked ||
        false;

    const simulateMissingDoc =
        document.getElementById("simulate-missing-doc")?.checked ||
        false;

    const runBtn = document.getElementById("run-btn");
    const workflowBadge = document.getElementById("workflow-badge");
    const timelineList = document.getElementById("timeline-list");

    if (runBtn) {
        runBtn.disabled = true;
        runBtn.innerHTML =
            "⏳ Gemini 3.6 Flash Reasoning & Authenticating ArmorIQ Key...";
    }

    if (workflowBadge) {
        workflowBadge.className = "badge-live";
        workflowBadge.textContent = "Executing...";
    }

    safeShow("security-alert", false);
    safeShow("demand-alert", false);
    safeShow("web-results-box", false);
    safeShow("gemini-reasoning-box", false);

    if (timelineList) {
        timelineList.innerHTML = `
            <li class="timeline-placeholder">
                Registering user '${studentName}' for state '${targetState}'
                and executing Gemini 3.6 Flash reasoning...
            </li>
        `;
    }

    try {
        const response = await fetch(`${AGENT_API}/api/agent/run`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                student_name: studentName,
                raw_prompt: rawPrompt,
                scholarship_type: scholarshipType,
                target_state: targetState,
                target_field: studentEdu,
                annual_income: annualIncome,
                simulate_out_of_scope_violation: simulateOutOfScope,
                simulate_missing_document: simulateMissingDoc
            })
        });

        if (!response.ok) {
            let errorMessage = `Server returned HTTP ${response.status}`;

            try {
                const errorData = await response.json();

                errorMessage =
                    errorData?.detail ||
                    errorData?.message ||
                    errorMessage;
            } catch (_) {
                // Keep HTTP status message.
            }

            throw new Error(errorMessage);
        }

        const data = await response.json();

        renderResults(data);

    } catch (err) {
        if (timelineList) {
            timelineList.innerHTML = `
                <li class="timeline-item" style="border-left: 4px solid #ef4444; background: rgba(239, 68, 68, 0.05); padding: 12px; border-radius: 6px;">
                    <div class="step-title" style="color:#ef4444; font-weight: bold; margin-bottom: 6px;">
                        ⚠️ Workflow Execution Error
                    </div>
                    <div class="step-desc" style="color:#cbd5e1; font-size: 13px; line-height: 1.5;">
                        ${err?.message || "Unknown error"}
                    </div>
                </li>
            `;
        }
    } finally {
        if (runBtn) {
            runBtn.disabled = false;
            runBtn.innerHTML =
                "🌐 Register & Execute Governed Agent Workflow";
        }
    }
}


function renderResults(summary) {

    /*
     * ---------------------------------------------------------
     * DEFENSIVE NORMALIZATION
     * ---------------------------------------------------------
     */

    // Prevent renderResults() from crashing if the API returns
    // null, undefined, or a non-object response.
    if (!summary || typeof summary !== "object") {
        summary = {};
    }

    // step_results may be missing, null, or the wrong type.
    const stepResults = Array.isArray(summary.step_results)
        ? summary.step_results
        : [];

    const workflowBadge =
        document.getElementById("workflow-badge");

    const timelineList =
        document.getElementById("timeline-list");

    const webResultsList =
        document.getElementById("web-results-list");


    /*
     * ---------------------------------------------------------
     * CLEAR PREVIOUS RESULTS
     * ---------------------------------------------------------
     */

    if (timelineList) {
        timelineList.innerHTML = "";
    }

    if (webResultsList) {
        webResultsList.innerHTML = "";
    }


    /*
     * ---------------------------------------------------------
     * GEMINI REASONING
     * ---------------------------------------------------------
     */

    if (summary.gemini_reasoning) {
        safeSetText(
            "gemini-reasoning-text",
            summary.gemini_reasoning
        );

        safeShow("gemini-reasoning-box", true);
    }


    /*
     * ---------------------------------------------------------
     * ARMORIQ TELEMETRY
     * ---------------------------------------------------------
     */

    const telemetry =
        summary.armoriq_telemetry &&
        typeof summary.armoriq_telemetry === "object"
            ? summary.armoriq_telemetry
            : null;

    if (telemetry) {

        const apiKey =
            telemetry.api_key_used ||
            "ak_live_f247...";

        const provider =
            telemetry.provider ||
            "ArmorIQ";

        const apiKeyDomain =
            telemetry.api_key_domain ||
            "Unknown";

        const apiKeyTier =
            String(
                telemetry.api_key_tier ||
                "unknown"
            ).toUpperCase();

        const merkleRoot =
            telemetry.merkle_root ||
            "c1795523a262c9b27dc542f32c6b8a16f31f8a274150ffa0faf88ed9bd09b8db";

        const signature =
            telemetry.ecdsa_signature ||
            "30450220025890efec529ee68bbef05a2de54e64a6dad3a361cfc629b8326410782aee2f...";

        safeSetText(
            "telemetry-key",
            apiKey
        );

        safeSetText(
            "tel-key-full",
            `${apiKey} (${provider})`
        );

        safeSetText(
            "tel-domain",
            `${apiKeyDomain} (${apiKeyTier} Tier)`
        );

        safeSetText(
            "tel-merkle",
            merkleRoot
        );

        safeSetText(
            "tel-sig",
            signature
        );
    }


    /*
     * ---------------------------------------------------------
     * WORKFLOW STATUS BADGE
     * ---------------------------------------------------------
     */

    if (workflowBadge) {

        if (summary.status === "COMPLETED") {

            workflowBadge.className = "badge-live";
            workflowBadge.style.background =
                "rgba(16, 185, 129, 0.2)";
            workflowBadge.style.color =
                "#10b981";

            workflowBadge.textContent =
                "✅ ArmorIQ Key Verified & Workflow Passed";

        } else {

            workflowBadge.className = "badge-live";
            workflowBadge.style.background =
                "rgba(239, 68, 68, 0.2)";
            workflowBadge.style.color =
                "#ef4444";

            workflowBadge.textContent =
                "🛡️ ArmorIQ Governance Block Triggered";
        }
    }


    /*
     * ---------------------------------------------------------
     * ARMORIQ INTENT TOKEN ENTRY
     * ---------------------------------------------------------
     */

    if (timelineList) {

        const tokenItem =
            document.createElement("li");

        tokenItem.className =
            "timeline-item";


        // Safe access to the first step.
        const firstStep =
            stepResults[0] || null;


        // Safely attempt to retrieve the authorized state.
        const eligibleState =
            firstStep?.details?.scholarships?.[0]
                ?.eligible_states?.[0] ||

            summary.target_state ||

            "Authorized";


        const userName =
            summary.user_name ||
            summary.student_name ||
            "Registered Student";


        const apiKey =
            telemetry?.api_key_used ||
            "ak_live_f247...";


        const tokenId =
            summary.intent_token
                ? `${String(summary.intent_token).substring(0, 24)}...`
                : "LIVE-TOKEN";


        tokenItem.innerHTML = `
            <div class="step-circle success"></div>

            <div class="step-title">
                🔑 ArmorIQ Intent Token Signed for User:
                '${userName}'
            </div>

            <div class="step-meta">
                API Key: ${apiKey}
                • Token ID: ${tokenId}
            </div>

            <div class="step-code">
                Signed Plan Constraints: {
                    student: '${userName}',
                    state: '${eligibleState}'
                }
            </div>
        `;

        timelineList.appendChild(tokenItem);
    }


    /*
     * ---------------------------------------------------------
     * RENDER STEP RESULTS
     * ---------------------------------------------------------
     */

    stepResults.forEach((step) => {

        // Defensive normalization for individual steps.
        if (!step || typeof step !== "object") {
            return;
        }

        const isBlocked =
            step.status === "BLOCKED";


        /*
         * Safely normalize step.details.
         */

        const details =
            step.details &&
            typeof step.details === "object"
                ? step.details
                : {};


        /*
         * -----------------------------------------------------
         * TIMELINE ITEM
         * -----------------------------------------------------
         */

        if (timelineList) {

            const item =
                document.createElement("li");

            item.className =
                "timeline-item";


            let detailsFormatted = "";

            try {

                detailsFormatted =
                    JSON.stringify(
                        details,
                        null,
                        2
                    );

            } catch (e) {

                detailsFormatted =
                    String(details);
            }


            const stepId =
                step.step_id ??
                "Unknown";

            const action =
                step.action ||
                "Unknown Action";

            const armorDecision =
                step.armoriq_decision ||
                "UNKNOWN";

            const executionStatus =
                step.executed
                    ? "EXECUTED"
                    : "ABORTED / NOT EXECUTED";


            item.innerHTML = `
                <div class="step-circle ${
                    isBlocked
                        ? "blocked"
                        : "success"
                }"></div>

                <div class="step-title">
                    Step ${stepId}:
                    ${action}

                    <span class="${
                        isBlocked
                            ? "badge-blocked"
                            : "badge-subtle"
                    }">
                        ${armorDecision}
                    </span>
                </div>

                <div class="step-meta">
                    Execution Status:
                    <strong>
                        ${executionStatus}
                    </strong>
                </div>

                <div class="step-code">
                    <pre>${detailsFormatted}</pre>
                </div>
            `;

            timelineList.appendChild(item);
        }


        /*
         * -----------------------------------------------------
         * ELIGIBILITY / MISSING DOCUMENT
         * -----------------------------------------------------
         */

        if (
            step.action === "check_eligibility" &&
            details?.result
        ) {

            const res =
                details.result;


            const missingDocuments =
                Array.isArray(res.missing_documents)
                    ? res.missing_documents
                    : [];


            if (
                res.action_required ===
                    "DEMAND_DOCUMENT" ||
                missingDocuments.length > 0
            ) {

                const missingDocName =
                    missingDocuments.length > 0
                        ? missingDocuments.join(", ")
                        : "income_certificate.pdf";


                safeSetText(
                    "demanded-doc-name",
                    missingDocName
                );

                safeShow(
                    "demand-alert",
                    true
                );
            }
        }


        /*
         * -----------------------------------------------------
         * SCHOLARSHIP SEARCH RESULTS
         * -----------------------------------------------------
         */

        const scholarships =
            Array.isArray(
                details?.scholarships
            )
                ? details.scholarships
                : [];


        if (
            step.action === "search_scholarships" &&
            scholarships.length > 0 &&
            webResultsList
        ) {

            safeShow(
                "web-results-box",
                true
            );


            scholarships.forEach((sch) => {

                if (
                    !sch ||
                    typeof sch !== "object"
                ) {
                    return;
                }


                const card =
                    document.createElement("div");


                card.style.cssText =
                    "background:#1a2233; border:1px solid #26334d; padding:12px; border-radius:10px; font-size:0.85rem;";


                const scholarshipName =
                    sch.name ||
                    "Unnamed Scholarship";


                const scholarshipType =
                    sch.scholarship_type ||
                    "unknown";


                const webSnippet =
                    sch.web_snippet ||
                    "Verified scheme eligible for engineering students";


                const sourceUrl =
                    sch.source_url ||
                    "#";


                /*
                 * Prevent amount.toLocaleString()
                 * from crashing when amount is missing.
                 */

                const numericAmount =
                    Number(sch.amount);


                const formattedAmount =
                    Number.isFinite(numericAmount)
                        ? numericAmount.toLocaleString("en-IN")
                        : "Not specified";


                const isGovernment =
                    scholarshipType ===
                    "government";


                card.innerHTML = `
                    <div
                        style="
                            font-weight:600;
                            color:#f1f5f9;
                            display:flex;
                            justify-content:space-between;
                        "
                    >

                        <span>
                            ${scholarshipName}
                        </span>

                        <span
                            class="tag"
                            style="
                                background:${
                                    isGovernment
                                        ? "rgba(16,185,129,0.2)"
                                        : "rgba(239,68,68,0.2)"
                                };

                                color:${
                                    isGovernment
                                        ? "#6ee7b7"
                                        : "#fca5a5"
                                };
                            "
                        >
                            ${String(
                                scholarshipType
                            ).toUpperCase()}
                        </span>

                    </div>


                    <div
                        style="
                            color:#94a3b8;
                            margin:4px 0;
                            font-size:0.78rem;
                        "
                    >
                        ${webSnippet}
                    </div>


                    <div
                        style="
                            display:flex;
                            justify-content:space-between;
                            font-size:0.75rem;
                            color:#a5b4fc;
                        "
                    >

                        <span>
                            Source:

                            <a
                                href="${sourceUrl}"
                                target="_blank"
                                rel="noopener noreferrer"
                                style="color:#60a5fa;"
                            >
                                ${
                                    sch.source_url ||
                                    "scholarships.gov.in"
                                }
                            </a>
                        </span>

                        <span>
                            Award: ₹${formattedAmount}
                        </span>

                    </div>
                `;


                webResultsList.appendChild(
                    card
                );
            });
        }


        /*
         * -----------------------------------------------------
         * ARMORIQ BLOCKED ACTION
         * -----------------------------------------------------
         */

        if (isBlocked) {

            const inputs =
                details?.inputs &&
                typeof details.inputs === "object"
                    ? details.inputs
                    : {};


            const alertTarget =
                inputs.scholarship_id ||
                "SCH-WEB-002 (Private Award)";


            const alertReason =
                step.error_message ||
                "Target action violates signed user intent constraint.";


            safeSetText(
                "alert-action",
                step.action ||
                "Unknown action"
            );


            safeSetText(
                "alert-target",
                alertTarget
            );


            safeSetText(
                "alert-reason",
                alertReason
            );


            safeShow(
                "security-alert",
                true
            );
        }
    });


    /*
     * ---------------------------------------------------------
     * PROOF OF NON-EXECUTION
     * ---------------------------------------------------------
     */

    const proof =
        summary.proof_of_non_execution &&
        typeof summary.proof_of_non_execution === "object"
            ? summary.proof_of_non_execution
            : null;


    if (proof) {

        const executedSubmissions =
            proof.executed_tool_submissions ?? 0;


        const blockedAttempts =
            proof.blocked_non_executed_attempts ??
            summary.blocked_steps ??
            0;


        safeSetHTML(
            "proof-text",

            `
            Consequential Submissions Executed:
            <strong>
                ${executedSubmissions}
            </strong>

            |

            Blocked Unauthorized Attempts:
            <strong style="color:#ef4444;">
                ${blockedAttempts}
            </strong>
            `
        );
    }
}