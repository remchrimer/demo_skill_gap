// --- State ---
let masterSkills = [];
let userSkills = [];
let selectedRoleId = null;
let selectedLevel = null;
let activeAutocompleteIdx = -1;

// --- DOM refs ---
const skillInput = document.getElementById("skill-input");
const skillTags = document.getElementById("skill-tags");
const autocompleteList = document.getElementById("autocomplete-list");
const categoryFilter = document.getElementById("category-filter");
const roleSearch = document.getElementById("role-search");
const roleList = document.getElementById("role-list");
const levelSelect = document.getElementById("level-select");
const analyzeBtn = document.getElementById("analyze-btn");
const resultsSection = document.getElementById("results-section");
const resultsMeta = document.getElementById("results-meta");
const resultsSkills = document.getElementById("results-skills");
const coursesContainer = document.getElementById("courses-container");
const loading = document.getElementById("loading");

// --- Init ---
async function init() {
    const [skillsRes, rolesRes] = await Promise.all([
        fetch("/api/skills"),
        fetch("/api/roles"),
    ]);
    masterSkills = await skillsRes.json();
    const roles = await rolesRes.json();
    renderRoles(roles);

    categoryFilter.addEventListener("change", () => filterRoles());
    roleSearch.addEventListener("input", () => filterRoles());
    skillInput.addEventListener("input", onSkillInput);
    skillInput.addEventListener("keydown", onSkillKeydown);
    analyzeBtn.addEventListener("click", runAnalysis);

    document.addEventListener("click", (e) => {
        if (!e.target.closest(".skill-input-wrapper")) hideAutocomplete();
    });

    document.querySelectorAll(".level-btn").forEach((btn) => {
        btn.addEventListener("click", () => selectLevel(btn.dataset.level));
    });
}

// --- Skill Input ---
function onSkillInput() {
    const val = skillInput.value.trim().toLowerCase();
    activeAutocompleteIdx = -1;
    if (!val) { hideAutocomplete(); return; }

    const existing = new Set(userSkills.map((s) => s.toLowerCase()));
    const matches = masterSkills
        .filter((s) => s.toLowerCase().includes(val) && !existing.has(s.toLowerCase()))
        .slice(0, 6);

    if (matches.length === 0) { hideAutocomplete(); return; }

    autocompleteList.innerHTML = matches
        .map((s, i) => `<div class="autocomplete-item" data-index="${i}">${s}</div>`)
        .join("");
    autocompleteList.style.display = "block";

    autocompleteList.querySelectorAll(".autocomplete-item").forEach((el) => {
        el.addEventListener("click", () => addSkill(el.textContent, true));
    });
}

function onSkillKeydown(e) {
    const items = autocompleteList.querySelectorAll(".autocomplete-item");

    if (e.key === "ArrowDown") {
        e.preventDefault();
        activeAutocompleteIdx = Math.min(activeAutocompleteIdx + 1, items.length - 1);
        updateAutocompleteHighlight(items);
    } else if (e.key === "ArrowUp") {
        e.preventDefault();
        activeAutocompleteIdx = Math.max(activeAutocompleteIdx - 1, 0);
        updateAutocompleteHighlight(items);
    } else if (e.key === "Enter") {
        e.preventDefault();
        if (activeAutocompleteIdx >= 0 && items[activeAutocompleteIdx]) {
            addSkill(items[activeAutocompleteIdx].textContent, true);
        } else if (skillInput.value.trim()) {
            addSkill(skillInput.value.trim(), false);
        }
    }
}

function updateAutocompleteHighlight(items) {
    items.forEach((el, i) => el.classList.toggle("active", i === activeAutocompleteIdx));
}

function addSkill(name, fromMaster) {
    const lower = name.toLowerCase();
    if (userSkills.some((s) => s.toLowerCase() === lower)) return;
    if (userSkills.length >= 20) return;

    userSkills.push(name);
    renderSkillTags();
    skillInput.value = "";
    hideAutocomplete();
    updateAnalyzeBtn();
}

function removeSkill(index) {
    userSkills.splice(index, 1);
    renderSkillTags();
    updateAnalyzeBtn();
}

function renderSkillTags() {
    const masterLower = new Set(masterSkills.map((s) => s.toLowerCase()));
    skillTags.innerHTML = userSkills
        .map((s, i) => {
            const isMaster = masterLower.has(s.toLowerCase());
            return `<span class="skill-tag ${isMaster ? "" : "custom"}">
                ${s}<button onclick="removeSkill(${i})">×</button>
            </span>`;
        })
        .join("");
}

function hideAutocomplete() {
    autocompleteList.style.display = "none";
    autocompleteList.innerHTML = "";
    activeAutocompleteIdx = -1;
}

// --- Role Selection ---
async function filterRoles() {
    const category = categoryFilter.value;
    const q = roleSearch.value.trim();
    const params = new URLSearchParams();
    if (category) params.set("category", category);
    if (q) params.set("q", q);

    const res = await fetch(`/api/roles?${params}`);
    const roles = await res.json();
    renderRoles(roles);
}

function renderRoles(roles) {
    roleList.innerHTML = roles
        .map(
            (r) => `<div class="role-card" data-id="${r.id}" onclick="selectRole('${r.id}')">
            <h4>${r.title}</h4>
            <p>${r.description.slice(0, 100)}...</p>
            <span class="category-badge">${r.category}</span>
        </div>`
        )
        .join("");

    if (selectedRoleId) {
        const el = roleList.querySelector(`[data-id="${selectedRoleId}"]`);
        if (el) el.classList.add("selected");
    }
}

function selectRole(roleId) {
    selectedRoleId = roleId;
    selectedLevel = null;

    roleList.querySelectorAll(".role-card").forEach((el) => {
        el.classList.toggle("selected", el.dataset.id === roleId);
    });

    levelSelect.style.display = "block";
    document.querySelectorAll(".level-btn").forEach((btn) => btn.classList.remove("selected"));
    updateAnalyzeBtn();
}

function selectLevel(level) {
    selectedLevel = level;
    document.querySelectorAll(".level-btn").forEach((btn) => {
        btn.classList.toggle("selected", btn.dataset.level === level);
    });
    updateAnalyzeBtn();
}

// --- Analysis ---
function updateAnalyzeBtn() {
    analyzeBtn.disabled = !(userSkills.length > 0 && selectedRoleId && selectedLevel);
}

async function runAnalysis() {
    analyzeBtn.disabled = true;
    loading.style.display = "block";
    resultsSection.style.display = "none";

    try {
        // Step 1: Gap analysis
        const analysisRes = await fetch("/api/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                skills: userSkills,
                target_role_id: selectedRoleId,
                target_level: selectedLevel,
            }),
        });

        if (!analysisRes.ok) {
            const err = await analysisRes.json();
            throw new Error(err.detail || "Analysis failed");
        }

        const analysis = await analysisRes.json();

        // Step 2: Fetch courses for recommended skills
        const skillNames = analysis.skills.map((s) => s.name);
        const courseParams = new URLSearchParams();
        skillNames.forEach((s) => courseParams.append("skill", s));
        courseParams.append("level", selectedLevel);

        const coursesRes = await fetch(`/api/courses?${courseParams}`);
        const courses = await coursesRes.json();

        // Render results
        renderResults(analysis, courses);
    } catch (err) {
        alert(`Error: ${err.message}`);
    } finally {
        loading.style.display = "none";
        analyzeBtn.disabled = false;
    }
}

function renderResults(analysis, courses) {
    const level = analysis.level.charAt(0).toUpperCase() + analysis.level.slice(1);
    const matchCount = analysis.matching_skills.length;
    const totalRequired = analysis.total_required;
    const gapCount = analysis.skills.length;
    const readiness = Math.round((matchCount / Math.max(totalRequired, 1)) * 100);

    // Build the full report
    let reportHtml = `
        <div class="report">
            <div class="report-header">
                <div class="report-title">
                    <h3>Gap Analysis Report</h3>
                    <span class="report-badge ${analysis.used_fallback ? "badge-fallback" : "badge-ai"}">
                        ${analysis.used_fallback ? "Rule-Based Analysis" : "AI-Powered Analysis"}
                    </span>
                </div>
                <div class="report-target">
                    <span class="report-role">${analysis.role}</span>
                    <span class="report-level">${level} Level</span>
                </div>
            </div>

            ${analysis.used_fallback ? `
            <div class="fallback-notice">
                AI was unavailable — results generated using rule-based analysis.
                Skill matching is exact-string only; synonym and context detection are limited.
            </div>` : ""}

            <div class="report-section">
                <h4>Priority Skills to Develop</h4>
                <p class="section-desc">These are the top ${gapCount} skills you should focus on, ordered by importance for the ${level} ${analysis.role} role.</p>
                <div class="skill-roadmap">
                    ${analysis.skills.map((s, i) => {
                        const courseGroup = courses.find(g => g.skill === s.name);
                        const courseHtml = courseGroup ? `
                            <div class="skill-courses">
                                ${courseGroup.courses.slice(0, 3).map((c) => `
                                    <a class="course-card" href="${c.url}" target="_blank" rel="noopener">
                                        ${c.thumbnail ? `<img src="${c.thumbnail}" alt="${c.title}">` : '<div class="course-placeholder">▶</div>'}
                                        <div class="course-info">
                                            <h5>${c.title}</h5>
                                            <span class="channel">${c.channel}</span>
                                        </div>
                                    </a>
                                `).join("")}
                            </div>
                        ` : "";
                        return `
                        <div class="roadmap-item">
                            <div class="roadmap-marker">
                                <span class="roadmap-num">${i + 1}</span>
                                ${i < analysis.skills.length - 1 ? '<div class="roadmap-line"></div>' : ""}
                            </div>
                            <div class="roadmap-content">
                                <h5>${s.name}</h5>
                                <p>${s.reason}</p>
                                ${courseHtml}
                            </div>
                        </div>
                    `}).join("")}
                </div>
            </div>
        </div>
    `;

    resultsMeta.innerHTML = "";
    resultsSkills.innerHTML = reportHtml;
    coursesContainer.innerHTML = "";

    resultsSection.style.display = "block";
    resultsSection.scrollIntoView({ behavior: "smooth" });
}

// Expose to onclick handlers in HTML
window.removeSkill = removeSkill;
window.selectRole = selectRole;

// Go
init();