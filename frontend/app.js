/**
 * SRU Assistant — Client-Side Application Architecture & Controller
 * Academic Query Resolution System | SR University
 */

document.addEventListener("DOMContentLoaded", () => {
    // =========================================================================
    // DOM Element References
    // =========================================================================
    
    // Viewport & Views
    const viewStudent = document.getElementById("view-student");
    const viewAdmin = document.getElementById("view-admin");
    const tabStudent = document.getElementById("tab-student-view");
    const tabAdmin = document.getElementById("tab-admin-view");
    const btnReturnChat = document.getElementById("btn-return-chat");
    const currentViewTitle = document.getElementById("current-view-title");
    const pipelineTag = document.getElementById("current-pipeline-tag");

    // Mobile Sidebar Elements
    const mobileMenuBtn = document.getElementById("mobile-menu-btn");
    const sidebarCloseBtn = document.getElementById("sidebar-close-btn");
    const appSidebar = document.getElementById("app-sidebar");
    const sidebarOverlay = document.getElementById("sidebar-overlay");

    // Chat Experience Elements
    const queryForm = document.getElementById("query-form");
    const queryInput = document.getElementById("query-input");
    const sendBtn = document.getElementById("send-btn");
    const messagesContainer = document.getElementById("messages-container");
    const welcomeCard = document.getElementById("welcome-card");
    const clearBtn = document.getElementById("clear-btn");
    const newChatBtn = document.getElementById("new-chat-btn");
    const recentQueriesList = document.getElementById("recent-queries-list");
    const clearHistoryBtn = document.getElementById("clear-history-btn");

    // System Status & Metric Elements
    const systemStatus = document.getElementById("system-status");
    const systemStatusDot = document.getElementById("system-status-dot");
    const chunksVal = document.getElementById("chunks-val");
    const docCount = document.getElementById("doc-count");
    const documentList = document.getElementById("document-list");

    // Admin Telemetry Elements
    const adminLlmProvider = document.getElementById("admin-llm-provider");
    const adminLlmModel = document.getElementById("admin-llm-model");
    const adminEmbedProvider = document.getElementById("admin-embed-provider");
    const adminVectorRecords = document.getElementById("admin-vector-records");
    const adminBm25Status = document.getElementById("admin-bm25-status");

    // Document Upload Elements
    const uploadTriggerBtn = document.getElementById("upload-trigger-btn");
    const uploadDropzone = document.getElementById("upload-dropzone");
    const docUploadInput = document.getElementById("doc-upload-input");
    const uploadStatus = document.getElementById("upload-status");

    // Citation Evidence Modal Elements
    const modalBackdrop = document.getElementById("modal-backdrop");
    const modalClose = document.getElementById("modal-close");
    const modalDoneBtn = document.getElementById("modal-done-btn");
    const modalCiteId = document.getElementById("modal-cite-id");
    const modalDocTitle = document.getElementById("modal-doc-title");
    const modalPage = document.getElementById("modal-page");
    const modalSection = document.getElementById("modal-section");
    const modalScore = document.getElementById("modal-score");
    const modalClaimText = document.getElementById("modal-claim-text");
    const modalPassageText = document.getElementById("modal-passage-text");

    // =========================================================================
    // State Management
    // =========================================================================
    let currentMode = "enhanced";
    const activeCitationsMap = new Map();
    let recentQueries = [];

    // Load recent queries from sessionStorage if available
    try {
        const stored = sessionStorage.getItem("sru_recent_queries");
        if (stored) {
            recentQueries = JSON.parse(stored);
        }
    } catch {
        recentQueries = [];
    }

    // =========================================================================
    // Initialization
    // =========================================================================
    fetchSystemHealth();
    fetchDocuments();
    renderRecentQueries();

    // =========================================================================
    // Navigation & View Switching
    // =========================================================================
    function switchView(targetView) {
        if (targetView === "admin-view") {
            viewStudent.classList.remove("active");
            viewAdmin.classList.add("active");
            tabStudent.classList.remove("active");
            tabAdmin.classList.add("active");
            currentViewTitle.textContent = "System & Administration";
        } else {
            viewAdmin.classList.remove("active");
            viewStudent.classList.add("active");
            tabAdmin.classList.remove("active");
            tabStudent.classList.add("active");
            currentViewTitle.textContent = "Academic Assistant";
            queryInput.focus();
        }
        closeMobileSidebar();
    }

    tabStudent.addEventListener("click", () => switchView("student-view"));
    tabAdmin.addEventListener("click", () => switchView("admin-view"));
    if (btnReturnChat) {
        btnReturnChat.addEventListener("click", () => switchView("student-view"));
    }

    // Mobile Drawer Handlers
    function openMobileSidebar() {
        appSidebar.classList.add("open");
        sidebarOverlay.classList.add("active");
    }

    function closeMobileSidebar() {
        appSidebar.classList.remove("open");
        sidebarOverlay.classList.remove("active");
    }

    if (mobileMenuBtn) mobileMenuBtn.addEventListener("click", openMobileSidebar);
    if (sidebarCloseBtn) sidebarCloseBtn.addEventListener("click", closeMobileSidebar);
    if (sidebarOverlay) sidebarOverlay.addEventListener("click", closeMobileSidebar);

    // =========================================================================
    // Retrieval Mode Selection (Admin View)
    // =========================================================================
    const modeTitles = {
        enhanced: "Enhanced (RRF + Rerank)",
        hybrid: "Hybrid (Dense + BM25)",
        dense: "Dense Vector Only",
    };

    document.querySelectorAll(".mode-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".mode-btn").forEach((b) => {
                b.classList.remove("active");
                const radio = b.querySelector('input[type="radio"]');
                if (radio) radio.checked = false;
            });

            btn.classList.add("active");
            const radio = btn.querySelector('input[type="radio"]');
            if (radio) radio.checked = true;

            currentMode = btn.dataset.mode || "enhanced";
            pipelineTag.querySelector(".text").textContent = `Mode: ${modeTitles[currentMode] || currentMode}`;
        });
    });

    // =========================================================================
    // Starter Question Cards & Recent Queries
    // =========================================================================
    document.querySelectorAll(".sample-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            const query = btn.dataset.query;
            if (query) {
                switchView("student-view");
                queryInput.value = query;
                handleSubmitQuery(query);
            }
        });
    });

    function saveRecentQuery(queryText) {
        if (!queryText) return;
        const trimmed = queryText.trim();
        // Remove existing occurrence to place at top
        recentQueries = recentQueries.filter((q) => q.toLowerCase() !== trimmed.toLowerCase());
        recentQueries.unshift(trimmed);
        if (recentQueries.length > 8) recentQueries.pop();

        try {
            sessionStorage.setItem("sru_recent_queries", JSON.stringify(recentQueries));
        } catch {
            // Ignore storage quota errors
        }
        renderRecentQueries();
    }

    function renderRecentQueries() {
        if (!recentQueriesList) return;
        if (recentQueries.length === 0) {
            recentQueriesList.innerHTML = `<div class="empty-history-hint">No queries asked yet this session.</div>`;
            return;
        }

        recentQueriesList.innerHTML = "";
        recentQueries.forEach((q) => {
            const btn = document.createElement("button");
            btn.type = "button";
            btn.className = "recent-query-item";
            btn.title = q;
            btn.innerHTML = `
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <polyline points="12 6 12 12 16 14"></polyline>
                </svg>
                <span>${escapeHtml(q)}</span>
            `;
            btn.addEventListener("click", () => {
                switchView("student-view");
                queryInput.value = q;
                handleSubmitQuery(q);
            });
            recentQueriesList.appendChild(btn);
        });
    }

    if (clearHistoryBtn) {
        clearHistoryBtn.addEventListener("click", () => {
            recentQueries = [];
            try {
                sessionStorage.removeItem("sru_recent_queries");
            } catch {}
            renderRecentQueries();
        });
    }

    // =========================================================================
    // Reset / New Chat Conversation
    // =========================================================================
    function resetChat() {
        messagesContainer.innerHTML = "";
        if (welcomeCard) {
            messagesContainer.appendChild(welcomeCard);
            welcomeCard.style.display = "flex";
        }
        activeCitationsMap.clear();
        queryInput.value = "";
        queryInput.style.height = "auto";
        queryInput.focus();
    }

    if (clearBtn) clearBtn.addEventListener("click", resetChat);
    if (newChatBtn) newChatBtn.addEventListener("click", () => {
        resetChat();
        switchView("student-view");
    });

    // =========================================================================
    // Input Auto-Resize & Keyboard Handling
    // =========================================================================
    if (queryInput) {
        queryInput.addEventListener("input", () => {
            queryInput.style.height = "auto";
            queryInput.style.height = Math.min(queryInput.scrollHeight, 120) + "px";
        });

        queryInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                queryForm.dispatchEvent(new Event("submit", { cancelable: true }));
            }
        });
    }

    // =========================================================================
    // Form Query Submission
    // =========================================================================
    queryForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const query = queryInput.value.trim();
        if (!query) return;
        handleSubmitQuery(query);
    });

    async function handleSubmitQuery(queryText) {
        if (welcomeCard) {
            welcomeCard.style.display = "none";
        }

        // Render User Message
        appendUserMessage(queryText);
        saveRecentQuery(queryText);
        queryInput.value = "";
        queryInput.style.height = "auto";
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
                    citation_style: "inline_bracket",
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
            appendErrorMessage(err.message || "Failed to communicate with the RAG pipeline.");
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
            <div class="loading-assistant-card">
                <div class="loading-pulse-ring"></div>
                <div class="loading-text-group">
                    <span class="loading-text-primary">Searching official university documents...</span>
                    <span class="loading-text-sub">Retrieving evidence from SQLite vector store & BM25 indices</span>
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
            <div class="error-assistant-card">
                <div class="error-title">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polygon points="7.86 2 16.14 2 22 7.86 22 16.14 16.14 22 7.86 22 2 16.14 2 7.86 7.86 2"></polygon>
                        <line x1="12" y1="8" x2="12" y2="12"></line>
                        <line x1="12" y1="16" x2="12.01" y2="16"></line>
                    </svg>
                    <span>Resolution Error</span>
                </div>
                <p class="error-message-text">${escapeHtml(errorMsg)}</p>
            </div>
        `;
        messagesContainer.appendChild(row);
    }

    // =========================================================================
    // Assistant Response Presentation & Citation Integration
    // =========================================================================
    function appendAssistantResponse(data) {
        const row = document.createElement("div");
        row.className = "message-row";

        // Store citations in session map for interactive lookup
        const citations = data.citations || [];
        citations.forEach((c) => activeCitationsMap.set(String(c.citation_id), c));

        // Format Answer markdown safely
        let rawAnswer = data.cited_answer || data.answer || "";
        let formattedAnswer = formatAcademicMarkdown(rawAnswer);

        // Convert inline bracket references like [1], [2] to clickable interactive chips
        formattedAnswer = formattedAnswer.replace(/\[(\d+)\]/g, (match, p1) => {
            return `<button type="button" class="citation-chip" data-cite-id="${p1}" title="Click to view official evidence for [${p1}]" aria-label="View citation source ${p1}">[${p1}]</button>`;
        });

        // Telemetry Metrics
        const lat = data.latency_ms || {};
        const totalMs = lat.total ? lat.total.toFixed(1) : "—";
        const retMs = lat.retrieval ? lat.retrieval.toFixed(1) : "—";
        const genMs = lat.generation ? lat.generation.toFixed(1) : "—";
        const modelName = (data.engine_info && data.engine_info.model) ? data.engine_info.model : "LLM Core";
        const activeMode = (data.engine_info && data.engine_info.retrieval_mode) ? data.engine_info.retrieval_mode : currentMode;

        // Grounding Shield Badge
        const isGrounded = data.is_grounded;
        const shieldClass = isGrounded ? "grounded" : "unverified";
        const shieldText = isGrounded
            ? "Verified Institutional Evidence"
            : "Caution: Partial Grounding Support";

        // Citations Tray HTML (Under the Answer)
        let citationsTrayHtml = "";
        if (citations.length > 0) {
            citationsTrayHtml = `
                <div class="citations-tray">
                    <div class="citations-tray-title">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                        </svg>
                        <span>Official Sources & Provenance (${citations.length})</span>
                    </div>
                    <div class="citations-chips-grid">
                        ${citations.map((c) => {
                            const docName = escapeHtml(c.document_name || "Official Document");
                            const pageProvenance = escapeHtml(c.page_info || (c.page ? `Page ${c.page}` : `Chunk ${c.chunk_id || ''}`));
                            return `
                                <button type="button" class="citation-source-card" data-cite-id="${c.citation_id}" title="Inspect evidence for ${docName}" aria-label="Inspect citation source ${c.citation_id}">
                                    <span class="chip-id">[${c.citation_id}]</span>
                                    <span class="chip-name">${docName}</span>
                                    <span class="chip-provenance">· ${pageProvenance}</span>
                                </button>
                            `;
                        }).join("")}
                    </div>
                </div>
            `;
        }

        row.innerHTML = `
            <div class="assistant-card">
                <div class="assistant-header">
                    <div class="trust-shield-badge ${shieldClass}">
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                        </svg>
                        <span>${shieldText}</span>
                    </div>
                    <span class="assistant-meta-tag">${escapeHtml(modelName)} · ${totalMs} ms</span>
                </div>

                <div class="answer-body">${formattedAnswer}</div>

                ${citationsTrayHtml}

                <div class="telemetry-row">
                    <div class="telemetry-items">
                        <span>Retrieval: <strong>${retMs} ms</strong></span>
                        <span>Synthesis: <strong>${genMs} ms</strong></span>
                        <span>Total: <strong>${totalMs} ms</strong></span>
                    </div>
                    <div class="telemetry-items">
                        <span>Mode: <strong>${escapeHtml(activeMode)}</strong></span>
                    </div>
                </div>
            </div>
        `;

        messagesContainer.appendChild(row);

        // Bind click events on all citation chips and source cards in this message
        row.querySelectorAll(".citation-chip, .citation-source-card").forEach((btn) => {
            btn.addEventListener("click", () => {
                const citeId = btn.dataset.citeId;
                const detail = activeCitationsMap.get(String(citeId));
                if (detail) openModal(detail);
            });
        });
    }

    // Lightweight Academic Markdown Formatter (HTML-Safe)
    function formatAcademicMarkdown(text) {
        if (!text) return "";
        let escaped = escapeHtml(text);

        // Headings: ### Title -> <h3>Title</h3>
        escaped = escaped.replace(/^### (.*$)/gim, "<h3>$1</h3>");
        escaped = escaped.replace(/^## (.*$)/gim, "<h3>$1</h3>");

        // Bold: **text** -> <strong>text</strong>
        escaped = escaped.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

        // Code snippets: `code` -> <code>code</code>
        escaped = escaped.replace(/`([^`]+)`/g, "<code>$1</code>");

        // Bullet lists: - item or * item
        const lines = escaped.split("\n");
        let inList = false;
        let formattedLines = [];

        for (let line of lines) {
            const trimmed = line.trim();
            if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
                if (!inList) {
                    formattedLines.push("<ul>");
                    inList = true;
                }
                formattedLines.push(`<li>${trimmed.substring(2)}</li>`);
            } else if (/^\d+\.\s/.test(trimmed)) {
                if (!inList) {
                    formattedLines.push("<ol>");
                    inList = true;
                }
                const content = trimmed.replace(/^\d+\.\s/, "");
                formattedLines.push(`<li>${content}</li>`);
            } else {
                if (inList) {
                    formattedLines.push("</ul>");
                    inList = false;
                }
                if (trimmed.length > 0) {
                    if (trimmed.startsWith("<h3>") || trimmed.startsWith("<h4>")) {
                        formattedLines.push(trimmed);
                    } else {
                        formattedLines.push(`<p>${trimmed}</p>`);
                    }
                }
            }
        }
        if (inList) {
            formattedLines.push("</ul>");
        }

        return formattedLines.join("\n");
    }

    // =========================================================================
    // Citation Evidence Modal Dialog
    // =========================================================================
    function openModal(citeDetail) {
        if (!citeDetail) return;
        modalCiteId.textContent = `Citation [${citeDetail.citation_id}]`;
        modalDocTitle.textContent = citeDetail.document_name || "Official University Document";
        modalPage.textContent = citeDetail.page_info || (citeDetail.page ? `Page ${citeDetail.page}` : "Location: Document Section");
        modalSection.textContent = `Section: ${citeDetail.section || "General Academic"}`;
        modalScore.textContent = citeDetail.is_verified ? "100% Verified Grounding" : "Grounding Unverified";
        modalClaimText.textContent = citeDetail.claim_text || "Academic claim supported by institutional evidence.";
        modalPassageText.textContent = citeDetail.source_label || citeDetail.chunk_id || "Direct institutional excerpt registered in vector index.";

        modalBackdrop.classList.add("show");
        modalDoneBtn.focus();
    }

    function closeModal() {
        modalBackdrop.classList.remove("show");
    }

    if (modalClose) modalClose.addEventListener("click", closeModal);
    if (modalDoneBtn) modalDoneBtn.addEventListener("click", closeModal);
    if (modalBackdrop) {
        modalBackdrop.addEventListener("click", (e) => {
            if (e.target === modalBackdrop) closeModal();
        });
    }

    window.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && modalBackdrop.classList.contains("show")) {
            closeModal();
        }
    });

    // =========================================================================
    // System Health & Telemetry Fetching
    // =========================================================================
    async function fetchSystemHealth() {
        try {
            const res = await fetch("/api/health");
            if (!res.ok) throw new Error("Health API error");
            const data = await res.json();

            // Student Status indicator
            systemStatus.textContent = `Knowledge Core Online (${data.llm_provider})`;
            systemStatusDot.classList.remove("standby");
            chunksVal.textContent = data.vectorstore_records;

            // Admin Dashboard Telemetry
            if (adminLlmProvider) adminLlmProvider.textContent = data.llm_provider ? data.llm_provider.toUpperCase() : "Ollama";
            if (adminLlmModel) adminLlmModel.textContent = data.llm_model || "qwen3.5:4b";
            if (adminEmbedProvider) adminEmbedProvider.textContent = data.embedding_provider || "FastHash";
            if (adminVectorRecords) adminVectorRecords.textContent = data.vectorstore_records;
            if (adminBm25Status) {
                adminBm25Status.textContent = data.bm25_indexed ? "Synchronized" : "Standby";
                adminBm25Status.className = data.bm25_indexed ? "stat-value text-success" : "stat-value text-accent";
            }
        } catch {
            systemStatus.textContent = "Offline / Standby";
            systemStatusDot.classList.add("standby");
        }
    }

    // =========================================================================
    // Document Catalog Integration
    // =========================================================================
    async function fetchDocuments() {
        try {
            const res = await fetch("/api/documents");
            if (!res.ok) throw new Error("Documents API error");
            const docs = await res.json();
            
            docCount.textContent = docs.length;
            documentList.innerHTML = "";

            if (docs.length === 0) {
                documentList.innerHTML = `<tr><td colspan="5" class="table-loading">No indexed documents found in catalog.</td></tr>`;
                return;
            }

            docs.forEach((doc) => {
                const tr = document.createElement("tr");
                const docType = (doc.document_type || "").toLowerCase();
                let badgeClass = "badge-pdf";
                let typeLabel = "PDF";

                if (docType.includes("docx") || docType.includes("doc")) {
                    badgeClass = "badge-docx";
                    typeLabel = "DOCX";
                } else if (docType.includes("txt")) {
                    badgeClass = "badge-txt";
                    typeLabel = "TXT";
                }

                tr.innerHTML = `
                    <td><span class="doc-badge-pill ${badgeClass}">${typeLabel}</span></td>
                    <td><strong>${escapeHtml(doc.document_name)}</strong></td>
                    <td><span style="text-transform: capitalize;">${escapeHtml(doc.category || "General")}</span></td>
                    <td><span style="font-family: var(--font-mono); font-weight: 600;">${doc.chunk_count}</span></td>
                    <td style="font-size: 0.78rem; color: var(--text-dim);">${escapeHtml(doc.source_file || doc.document_id)}</td>
                `;
                documentList.appendChild(tr);
            });
        } catch {
            documentList.innerHTML = `<tr><td colspan="5" class="table-loading">Error loading institutional document catalog.</td></tr>`;
        }
    }

    // =========================================================================
    // Document Upload & Ingestion Integration
    // =========================================================================
    if (uploadTriggerBtn && docUploadInput) {
        uploadTriggerBtn.addEventListener("click", () => {
            docUploadInput.click();
        });

        if (uploadDropzone) {
            uploadDropzone.addEventListener("dragover", (e) => {
                e.preventDefault();
                uploadDropzone.style.borderColor = "var(--sru-blue-light)";
            });

            uploadDropzone.addEventListener("dragleave", () => {
                uploadDropzone.style.borderColor = "";
            });

            uploadDropzone.addEventListener("drop", (e) => {
                e.preventDefault();
                uploadDropzone.style.borderColor = "";
                if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                    handleDocumentUpload(e.dataTransfer.files[0]);
                }
            });
        }

        docUploadInput.addEventListener("change", () => {
            const file = docUploadInput.files[0];
            if (file) handleDocumentUpload(file);
        });
    }

    async function handleDocumentUpload(file) {
        if (!file) return;

        uploadStatus.style.display = "block";
        uploadStatus.style.backgroundColor = "var(--sru-blue-subtle)";
        uploadStatus.style.color = "var(--sru-blue-light)";
        uploadStatus.textContent = `Uploading and indexing ${file.name}...`;

        const formData = new FormData();
        formData.append("file", file);

        try {
            const res = await fetch("/api/documents/upload?auto_index=true", {
                method: "POST",
                body: formData,
            });
            const data = await res.json();

            if (!res.ok) {
                throw new Error(data.detail || "Upload validation failed");
            }

            if (data.is_duplicate) {
                uploadStatus.style.backgroundColor = "var(--status-amber-subtle)";
                uploadStatus.style.color = "var(--status-amber)";
                uploadStatus.textContent = `⚠️ Document ${file.name} already exists (duplicate SHA-256 hash).`;
            } else {
                uploadStatus.style.backgroundColor = "var(--status-green-subtle)";
                uploadStatus.style.color = "var(--status-green)";
                uploadStatus.textContent = `✓ Document ${file.name} uploaded and indexed successfully!`;
                fetchDocuments();
                fetchSystemHealth();
            }
        } catch (err) {
            uploadStatus.style.backgroundColor = "var(--status-red-subtle)";
            uploadStatus.style.color = "var(--status-red)";
            uploadStatus.textContent = `✗ Upload failed: ${err.message}`;
        } finally {
            docUploadInput.value = "";
            setTimeout(() => {
                uploadStatus.style.display = "none";
            }, 6000);
        }
    }

    // =========================================================================
    // Utility Helpers
    // =========================================================================
    function escapeHtml(str) {
        if (!str) return "";
        return String(str)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
});
