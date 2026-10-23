// SlothSort Frontend Logic with Animated Runner Monkey

let currentProvider = "auto";
let currentPlans = [];
let defaultPaths = {};
let monkeyInterval = null;

// Load on initialization
document.addEventListener("DOMContentLoaded", async () => {
    loadSettings();
    await fetchDefaultPaths();
    checkProviders();
});

async function fetchDefaultPaths() {
    try {
        const res = await fetch("/api/default-paths");
        defaultPaths = await res.json();
        const input = document.getElementById("folder-path-input");
        if (input && !input.value) {
            input.value = defaultPaths.demo_folder || "./demo_messy_folder";
        }
    } catch (e) {
        console.error("Failed to load default paths", e);
    }
}

function setProvider(provider) {
    currentProvider = provider;
    ["auto", "ollama", "gemini", "groq", "builtin"].forEach(p => {
        const btn = document.getElementById(`provider-${p}`);
        if (!btn) return;
        if (p === provider) {
            btn.className = "px-2.5 py-1 rounded-md bg-emerald-600 text-white font-medium transition shadow";
        } else {
            btn.className = "px-2.5 py-1 rounded-md text-slate-300 hover:text-white transition";
        }
    });
    showToast(`Switched active provider to: ${provider.toUpperCase()}`);
}

async function checkProviders() {
    try {
        const res = await fetch("/api/providers");
        const data = await res.json();
        console.log("Provider readiness:", data);
    } catch (e) {
        console.warn("Could not check providers status");
    }
}

function usePreset(type) {
    const input = document.getElementById("folder-path-input");
    if (!input) return;
    if (type === "downloads" && defaultPaths.downloads) {
        input.value = defaultPaths.downloads;
    } else if (type === "desktop" && defaultPaths.desktop) {
        input.value = defaultPaths.desktop;
    } else if (type === "demo" && defaultPaths.demo_folder) {
        input.value = defaultPaths.demo_folder;
    }
    showToast(`Loaded ${type} path`);
}

function showMonkeyLoader(title, subtitle, actions) {
    const card = document.getElementById("monkey-loading-card") || document.getElementById("loading-state");
    const results = document.getElementById("results-section");
    const titleEl = document.getElementById("monkey-title");
    const subEl = document.getElementById("monkey-subtitle");
    const actionEl = document.getElementById("monkey-action-text");

    if (titleEl) titleEl.textContent = title;
    if (subEl) subEl.textContent = subtitle;

    if (card) card.classList.remove("hidden");
    if (results) results.classList.add("hidden");

    let idx = 0;
    if (actionEl && actions && actions.length) {
        actionEl.textContent = actions[0];
        clearInterval(monkeyInterval);
        monkeyInterval = setInterval(() => {
            idx = (idx + 1) % actions.length;
            actionEl.textContent = actions[idx];
        }, 600);
    }
}

function hideMonkeyLoader() {
    clearInterval(monkeyInterval);
    const card = document.getElementById("monkey-loading-card") || document.getElementById("loading-state");
    const results = document.getElementById("results-section");
    if (card) card.classList.add("hidden");
    if (results) results.classList.remove("hidden");
}

async function generateDemoAndScan() {
    showToast("Generating chaotic sample files...");
    try {
        const folderTarget = defaultPaths.demo_folder || "./demo_messy_folder";
        const res = await fetch("/api/generate-demo", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ folder_path: folderTarget })
        });
        const data = await res.json();
        if (data.success) {
            const input = document.getElementById("folder-path-input");
            if (input) input.value = data.folder_path;
            showToast(`Created ${data.files_created} messy files! Starting scan...`);
            await startScan();
        } else {
            showToast("Failed to generate demo files", true);
        }
    } catch (e) {
        showToast("Error generating demo files: " + e.message, true);
    }
}

async function startScan() {
    const folderInput = document.getElementById("folder-path-input");
    const folderPath = folderInput ? folderInput.value.trim() : "";
    if (!folderPath) {
        alert("Please enter a folder path.");
        return;
    }

    const scanBtn = document.getElementById("scan-btn");
    if (scanBtn) scanBtn.disabled = true;

    showMonkeyLoader(
        "Monkey is racing to scan your clutter! 🐒",
        "The sloth stays comfy in the hammock while the monkey inspects every messy file...",
        [
            "Examining text snippets & invoices...",
            "Detecting receipts & amounts due...",
            "Standardizing messy screenshots with dates...",
            "Evaluating with local open-weight AI...",
            "Finalizing clean folder suggestions..."
        ]
    );

    try {
        const payload = {
            folder_path: folderPath,
            provider: currentProvider,
            ollama_url: localStorage.getItem("sloth_ollama_url") || "http://localhost:11434",
            ollama_model: localStorage.getItem("sloth_ollama_model") || "llama3.2",
            gemini_api_key: localStorage.getItem("sloth_gemini_key") || undefined,
            groq_api_key: localStorage.getItem("sloth_groq_key") || undefined
        };

        const [res] = await Promise.all([
            fetch("/api/scan", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            }),
            new Promise(r => setTimeout(r, 700))
        ]);

        const data = await res.json();
        if (!res.ok) {
            throw new Error(data.detail || "Scan failed");
        }

        currentPlans = data.plans || [];
        renderPlans(currentPlans);
        showToast(`Found and analyzed ${currentPlans.length} files!`);
    } catch (e) {
        showToast(e.message, true);
    } finally {
        hideMonkeyLoader();
        if (scanBtn) scanBtn.disabled = false;
    }
}

function renderPlans(plans) {
    const tbody = document.getElementById("plans-table-body");
    if (!tbody) return;
    tbody.innerHTML = "";

    const statCount = document.getElementById("stat-count");
    if (statCount) statCount.textContent = plans.length;

    const uniqueCategories = new Set(plans.map(p => p.target_folder));
    const statCats = document.getElementById("stat-categories");
    if (statCats) statCats.textContent = uniqueCategories.size;

    if (plans.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="py-8 text-center text-slate-500">No unorganized files found in this directory. Everything is tidy!</td></tr>`;
        return;
    }

    plans.forEach((p, idx) => {
        const tr = document.createElement("tr");
        tr.className = "hover:bg-slate-800/40 transition";

        const icon = getFileIcon(p.group, p.original_name);
        const badgeColor = getCategoryColor(p.target_folder);

        tr.innerHTML = `
            <td class="py-3 px-4 font-mono text-xs flex items-center gap-2">
                <span class="text-slate-400">${icon}</span>
                <span class="text-slate-200 truncate max-w-xs" title="${p.original_name}">${p.original_name}</span>
            </td>
            <td class="py-3 px-4 font-mono text-xs text-emerald-400 font-semibold truncate max-w-xs" title="${p.new_name}">
                ${p.new_name}
            </td>
            <td class="py-3 px-4">
                <span class="inline-block px-2.5 py-0.5 rounded-full text-xs font-medium ${badgeColor}">
                    ${p.target_folder}
                </span>
            </td>
            <td class="py-3 px-4 text-xs text-slate-400">
                <div class="line-clamp-2" title="${p.reasoning}">${p.reasoning}</div>
                <div class="flex items-center gap-2 mt-1">
                    <div class="w-16 bg-slate-800 h-1 rounded-full overflow-hidden">
                        <div class="bg-emerald-500 h-full" style="width: ${Math.round(p.confidence * 100)}%"></div>
                    </div>
                    <span class="text-[10px] text-slate-500 font-mono">${Math.round(p.confidence * 100)}%</span>
                </div>
            </td>
            <td class="py-3 px-4 text-xs text-right text-slate-500 font-mono">
                <span class="px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-[11px] text-slate-300">
                    ${p.provider}
                </span>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

async function executeSort() {
    if (!currentPlans.length) {
        showToast("No files to tidy.", true);
        return;
    }

    const folderInput = document.getElementById("folder-path-input");
    const folderPath = folderInput ? folderInput.value.trim() : "";
    const btn = document.getElementById("execute-btn");
    if (btn) btn.disabled = true;

    showMonkeyLoader(
        "Monkey is slotting files into neat folders! 🐒📦",
        "Sloth is asleep. Monkey is moving, renaming, and filing everything right now...",
        [
            "Slotting financial receipts into Financial_and_Receipts...",
            "Renaming screenshots with standard dates...",
            "Organizing resumes and credentials...",
            "Filing code snippets into Developer_Code...",
            "Writing atomic rollback transaction log..."
        ]
    );

    try {
        const [res] = await Promise.all([
            fetch("/api/execute", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ folder_path: folderPath, plans: currentPlans })
            }),
            new Promise(r => setTimeout(r, 900))
        ]);

        const data = await res.json();
        if (data.success) {
            showToast(`🎉 Success! Moved & organized ${data.moved_count} files into clean categories.`);
            await startScan();
        } else {
            showToast("Errors occurred during sort.", true);
        }
    } catch (e) {
        showToast("Failed to execute: " + e.message, true);
    } finally {
        hideMonkeyLoader();
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = `<i class="fa-solid fa-check-double"></i> Tidy Up Now`;
        }
    }
}

async function undoLastSort() {
    const folderInput = document.getElementById("folder-path-input");
    const folderPath = folderInput ? folderInput.value.trim() : "";
    if (!confirm("Restore files back to their exact original locations and names?")) return;

    showMonkeyLoader(
        "Monkey is putting everything back! 🐒↩️",
        "Rollback in progress. Restoring files to their exact previous paths...",
        ["Reading history log...", "Moving files back...", "Cleaning empty folders..."]
    );

    try {
        const [res] = await Promise.all([
            fetch("/api/undo", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ folder_path: folderPath })
            }),
            new Promise(r => setTimeout(r, 600))
        ]);

        const data = await res.json();
        if (data.success) {
            showToast(`Restored ${data.restored_count} files back to original positions!`);
            await startScan();
        } else {
            showToast(data.message || "Undo failed.", true);
        }
    } catch (e) {
        showToast("Undo error: " + e.message, true);
    } finally {
        hideMonkeyLoader();
    }
}

function getFileIcon(group, name) {
    if (group === "images") return `<i class="fa-regular fa-image text-purple-400"></i>`;
    if (group === "code") return `<i class="fa-solid fa-code text-blue-400"></i>`;
    if (group === "spreadsheets") return `<i class="fa-solid fa-table text-emerald-400"></i>`;
    if (group === "archives") return `<i class="fa-regular fa-file-zipper text-amber-400"></i>`;
    if (group === "installers") return `<i class="fa-solid fa-box text-rose-400"></i>`;
    return `<i class="fa-regular fa-file-lines text-slate-400"></i>`;
}

function getCategoryColor(cat) {
    if (cat.includes("Financial") || cat.includes("Receipts")) return "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30";
    if (cat.includes("Screenshots")) return "bg-sky-500/15 text-sky-400 border border-sky-500/30";
    if (cat.includes("Media") || cat.includes("Memes")) return "bg-purple-500/15 text-purple-400 border border-purple-500/30";
    if (cat.includes("Code") || cat.includes("Developer")) return "bg-indigo-500/15 text-indigo-400 border border-indigo-500/30";
    if (cat.includes("Career") || cat.includes("Resume")) return "bg-amber-500/15 text-amber-400 border border-amber-500/30";
    if (cat.includes("Meeting")) return "bg-teal-500/15 text-teal-400 border border-teal-500/30";
    return "bg-slate-800 text-slate-300 border border-slate-700";
}

function openSettingsModal() {
    const modal = document.getElementById("settings-modal");
    if (modal) modal.classList.remove("hidden");
}

function closeSettingsModal() {
    const modal = document.getElementById("settings-modal");
    if (modal) modal.classList.add("hidden");
}

function saveSettings() {
    const ollamaUrl = document.getElementById("cfg-ollama-url")?.value.trim();
    const ollamaModel = document.getElementById("cfg-ollama-model")?.value.trim();
    const geminiKey = document.getElementById("cfg-gemini-key")?.value.trim();
    const groqKey = document.getElementById("cfg-groq-key")?.value.trim();

    if (ollamaUrl) localStorage.setItem("sloth_ollama_url", ollamaUrl);
    if (ollamaModel) localStorage.setItem("sloth_ollama_model", ollamaModel);
    if (geminiKey) localStorage.setItem("sloth_gemini_key", geminiKey);
    if (groqKey) localStorage.setItem("sloth_groq_key", groqKey);

    closeSettingsModal();
    showToast("Settings saved successfully!");
}

function loadSettings() {
    if (localStorage.getItem("sloth_ollama_url")) {
        const el = document.getElementById("cfg-ollama-url");
        if (el) el.value = localStorage.getItem("sloth_ollama_url");
    }
    if (localStorage.getItem("sloth_ollama_model")) {
        const el = document.getElementById("cfg-ollama-model");
        if (el) el.value = localStorage.getItem("sloth_ollama_model");
    }
    if (localStorage.getItem("sloth_gemini_key")) {
        const el = document.getElementById("cfg-gemini-key");
        if (el) el.value = localStorage.getItem("sloth_gemini_key");
    }
    if (localStorage.getItem("sloth_groq_key")) {
        const el = document.getElementById("cfg-groq-key");
        if (el) el.value = localStorage.getItem("sloth_groq_key");
    }
}

function showToast(message, isError = false) {
    const toast = document.getElementById("toast");
    const content = document.getElementById("toast-content");
    const msg = document.getElementById("toast-msg");

    if (!toast || !content || !msg) return;

    msg.textContent = message;
    content.className = isError
        ? "bg-rose-600 text-white px-4 py-2.5 rounded-lg shadow-xl text-xs font-medium flex items-center gap-2"
        : "bg-emerald-600 text-white px-4 py-2.5 rounded-lg shadow-xl text-xs font-medium flex items-center gap-2";

    toast.classList.remove("translate-y-20", "opacity-0");
    setTimeout(() => {
        toast.classList.add("translate-y-20", "opacity-0");
    }, 3500);
}
