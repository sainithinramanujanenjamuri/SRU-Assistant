/**
 * SRU Assistant — Client-Side Application Logic (Phase 10)
 */

document.addEventListener("DOMContentLoaded", () => {
    // DOM Elements
    const queryForm = document.getElementById("query-form");
    const queryInput = document.getElementById("query-input");
    const sendBtn = document.getElementById("send-btn");
    const messagesContainer = document.getElementById("messages-container");
    const welcomeCard = document.getElementById("welcome-card");
    const clearBtn = document.getElementById("clear-btn");
    const systemStatus = document.getElementById("system-status");
    const chunksVal = document.getElementById("chunks-val");
    const documentList = document.getElementById("document-list");
    const docCount = document.getElementById("doc-count");
    const pipelineTag = document.getElementById("current-pipeline-tag");

    // Modal Elements
    const modalBackdrop = document.getElementById("modal-backdrop");
    const modalClose = document.getElementById("modal-close");
    const modalCiteId = document.getElementById("modal-cite-id");
    const modalDocTitle = document.getElementById("modal-doc-title");
    const modalPage = document.getElementById("modal-page");
    const modalSection = document.getElementById("modal-section");
    const modalScore = document.getElementById("modal-score");
    const modalClaimText = document.getElementById("modal-claim-text");
    const modalPassageText = document.getElementById("modal-passage-text");

    let currentMode = "enhanced";
    let activeCitationsMap = new Map();

    // Initialize System Status & Catalog
    fetchSystemHealth();
    fetchDocuments();

    // Upload Document Handlers
    const uploadTriggerBtn = document.getElementById("upload-trigger-btn");
    const docUploadInput = document.getElementById("doc-upload-input");
    const uploadStatus = document.getElementById("upload-status");

    if (uploadTriggerBtn && docUploadInput) {
        uploadTriggerBtn.addEventListener("click", () => {
            docUploadInput.click();
        });

        docUploadInput.addEventListener("change", async () => {
            const file = docUploadInput.files[0];
            if (!file) return;

            uploadStatus.style.display = "block";
            uploadStatus.style.color = "var(--text-muted)";
            uploadStatus.textContent = `Uploading ${file.name}...`;

            const formData = new FormData();
            formData.append("file", file);

            try {
                const res = await fetch("/api/documents/upload?auto_index=true", {
                    method: "POST",
                    body: formData,
                });
                const data = await res.json();
                if (!res.ok) {
                    throw new Error(data.detail || "Upload failed");
                }
                if (data.is_duplicate) {
                    uploadStatus.style.color = "#f59e0b";
                    uploadStatus.textContent = `⚠️ ${file.name} already exists (duplicate hash)`;
                } else {
                    uploadStatus.style.color = "#10b981";
                    uploadStatus.textContent = `✓ ${file.name} uploaded and indexed successfully!`;
                    fetchDocuments();
                    fetchSystemHealth();
                }
            } catch (err) {
                uploadStatus.style.color = "#ef4444";
                uploadStatus.textContent = `✗ Upload failed: ${err.message}`;
            } finally {
                docUploadInput.value = "";
                setTimeout(() => {
                    uploadStatus.style.display = "none";
                }, 5000);
            }
        });
    }


    // Mode Radio Buttons
    document.querySelectorAll(".mode-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".mode-btn").forEach((b) => b.classList.remove("active"));
            btn.classList.add("active");
            currentMode = btn.dataset.mode;
            const titles = {
                enhanced: "Enhanced (RRF + Rerank)",
                hybrid: "Hybrid (Dense + BM25)",
                dense: "Dense Vector Only",
            };
            pipelineTag.textContent = `Mode: ${titles[currentMode] || currentMode}`;
        });
    });

    // Sample Query Buttons
    document.querySelectorAll(".sample-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            const query = btn.dataset.query;
            if (query) {
                queryInput.value = query;
                handleSubmitQuery(query);
            }
        });
    });

    // Clear Chat
    clearBtn.addEventListener("click", () => {
        messagesContainer.innerHTML = "";
        if (welcomeCard) {
            messagesContainer.appendChild(welcomeCard);
            welcomeCard.style.display = "flex";
        }
        activeCitationsMap.clear();
    });

    // Form Submit
    queryForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const query = queryInput.value.trim();
        if (!query) return;
        handleSubmitQuery(query);
    });

    // Modal Close
    modalClose.addEventListener("click", closeModal);
    modalBackdrop.addEventListener("click", (e) => {
        if (e.target === modalBackdrop) closeModal();
    });

    function openModal(citeDetail) {
        if (!citeDetail) return;
        modalCiteId.textContent = `Citation [${citeDetail.citation_id}]`;
        modalDocTitle.textContent = citeDetail.document_name || "Official Document";
        modalPage.textContent = citeDetail.page_info || `Page ${citeDetail.page || "N/A"}`;
        modalSection.textContent = `Section: ${citeDetail.section || "General"}`;
        modalScore.textContent = citeDetail.is_verified ? "100% Verified Grounding" : "Grounding Unverified";
        modalClaimText.textContent = citeDetail.claim_text || "Academic fact supported by institutional evidence.";
        modalPassageText.textContent = citeDetail.source_label || citeDetail.chunk_id;
        modalBackdrop.classList.add("show");
    }

    function closeModal() {
        modalBackdrop.classList.remove("show");
    }

    // Healthcheck
    async function fetchSystemHealth() {
        try {
            const res = await fetch("/api/health");
            if (!res.ok) throw new Error("Health API error");
            const data = await res.json();
            systemStatus.textContent = `Core Online (${data.llm_provider})`;
            chunksVal.textContent = data.vectorstore_records;
        } catch (err) {
            systemStatus.textContent = "Offline / Standby";
        }
    }

    // Document Catalog
    async function fetchDocuments() {
        try {
            const res = await fetch("/api/documents");
            if (!res.ok) throw new Error("Documents API error");
            const docs = await res.json();
            docCount.textContent = docs.length;
            documentList.innerHTML = "";

            if (docs.length === 0) {
                documentList.innerHTML = `<div class="doc-sub">No indexed documents found.</div>`;
                return;
            }

            docs.forEach((doc) => {
                const el = document.createElement("div");
                el.className = "doc-item";
                const icon = doc.document_type === ".pdf" ? "📕" : "📄";
                el.innerHTML = `
                    <span class="doc-icon">${icon}</span>
                    <div class="doc-meta">
                        <span class="doc-name" title="${doc.document_name}">${doc.document_name}</span>
                        <span class="doc-sub">${doc.category.toUpperCase()} • ${doc.chunk_count} Chunks</span>
                    </div>
                `;
                documentList.appendChild(el);
            });
        } catch (err) {
            documentList.innerHTML = `<div class="doc-sub">Error loading catalog.</div>`;
        }
    }

    // Query Resolution Handler
    async function handleSubmitQuery(queryText) {
        if (welcomeCard) {
            welcomeCard.style.display = "none";
        }

        // Render User Message
        appendUserMessage(queryText);
        queryInput.value = "";
        sendBtn.disabled = true;

        // Render Assistant Loading State
        const loadingCard = appendLoadingAssistantMessage();
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        try {
            const res = await fetch("/api/query", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    query: queryText,
                    top_k: 5,
                    retrieval_mode: currentMode,
                    verify_citations: true,
                }),
            });

            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || `Server returned HTTP ${res.status}`);
            }

            const data = await res.json();
            loadingCard.remove();
            appendAssistantResponse(data);
        } catch (err) {
            loadingCard.remove();
            appendErrorMessage(err.message || "Failed to communicate with RAG pipeline.");
        } finally {
            sendBtn.disabled = false;
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
    }

    function appendUserMessage(text) {
        const row = document.createElement("div");
        row.className = "message-row user-row";
        row.innerHTML = `<div class="message-bubble user-bubble">${escapeHtml(text)}</div>`;
        messagesContainer.appendChild(row);
    }

    function appendLoadingAssistantMessage() {
        const row = document.createElement("div");
        row.className = "message-row";
        row.innerHTML = `
            <div class="assistant-card">
                <div class="assistant-header">
                    <span class="telemetry-tag">Searching Institutional Vector DB & BM25 Index...</span>
                </div>
                <div class="loading-dots">
                    <span></span><span></span><span></span>
                </div>
            </div>
        `;
        messagesContainer.appendChild(row);
        return row;
    }

    function appendErrorMessage(errorMsg) {
        const row = document.createElement("div");
        row.className = "message-row";
        row.innerHTML = `
            <div class="assistant-card" style="border-color: var(--accent-red);">
                <div class="assistant-header">
                    <span style="color: var(--accent-red); font-weight: 700;">⚠️ Resolution Error</span>
                </div>
                <div class="answer-body">${escapeHtml(errorMsg)}</div>
            </div>
        `;
        messagesContainer.appendChild(row);
    }

    function appendAssistantResponse(data) {
        const row = document.createElement("div");
        row.className = "message-row";

        // Store citations in session map
        const citations = data.citations || [];
        citations.forEach((c) => activeCitationsMap.set(String(c.citation_id), c));

        // Format Answer text to replace [1], [2] with clickable chips
        let formattedAnswer = escapeHtml(data.cited_answer || data.answer);
        formattedAnswer = formattedAnswer.replace(/\[(\d+)\]/g, (match, p1) => {
            return `<button class="citation-chip" data-cite-id="${p1}" title="Click to view official document evidence">[${p1}]</button>`;
        });

        // Telemetry string
        const lat = data.latency_ms || {};
        const totalMs = lat.total ? lat.total.toFixed(1) : "—";
        const retMs = lat.retrieval ? lat.retrieval.toFixed(1) : "—";
        const genMs = lat.generation ? lat.generation.toFixed(1) : "—";

        // Shield status
        const isGrounded = data.is_grounded;
        const shieldLabel = isGrounded
            ? "🛡️ Verified Institutional Evidence (0% Hallucination)"
            : "⚠️ Caution: Low Grounding Support";

        // Sources list HTML
        let sourcesHtml = "";
        if (citations.length > 0) {
            sourcesHtml = `
                <div class="sources-tray">
                    <div class="sources-title">Verified Sources (${citations.length})</div>
                    <div class="sources-pills-list">
                        ${citations.map(c => `
                            <button class="source-pill-card" data-cite-id="${c.citation_id}">
                                <span class="pill-id">[${c.citation_id}]</span>
                                <span>${escapeHtml(c.document_name)} — ${escapeHtml(c.page_info || 'p. N/A')}</span>
                            </button>
                        `).join("")}
                    </div>
                </div>
            `;
        }

        row.innerHTML = `
            <div class="assistant-card">
                <div class="assistant-header">
                    <div class="trust-shield">${shieldLabel}</div>
                    <div class="telemetry-tag">${data.engine_info.model} • ${totalMs} ms</div>
                </div>

                <div class="answer-body">${formattedAnswer}</div>

                ${sourcesHtml}

                <div class="latency-bar">
                    <span class="latency-item">Retrieval: <strong>${retMs} ms</strong></span>
                    <span class="latency-item">Synthesis: <strong>${genMs} ms</strong></span>
                    <span class="latency-item">Total Pipeline: <strong>${totalMs} ms</strong></span>
                    <span class="latency-item">Mode: <strong>${escapeHtml(data.engine_info.retrieval_mode)}</strong></span>
                </div>
            </div>
        `;

        messagesContainer.appendChild(row);

        // Bind click events on all citation chips & source cards in this message
        row.querySelectorAll(".citation-chip, .source-pill-card").forEach((btn) => {
            btn.addEventListener("click", () => {
                const citeId = btn.dataset.citeId;
                const detail = activeCitationsMap.get(String(citeId));
                if (detail) openModal(detail);
            });
        });
    }

    function escapeHtml(str) {
        if (!str) return "";
        return str
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
});
