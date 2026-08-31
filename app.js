const THSC_VIEWER_WORKER = "AKfycbyzcBH0M5Np7XQf4aaGktd0zgHt5Sa0CRAXiG-XiUyWd5jzEN1qLDcjXbpVgu0LKQbJ";

const [curriculum, bank, thscTrials] = await Promise.all([
  fetch("data/curriculum.json").then((response) => response.json()),
  fetch("data/questions.json").then((response) => response.json()),
  fetch("data/thsc-standard-trials.json").then((response) => response.json()),
]);

const doneStorageKey = "hsc-standard-2-question-engine-done";
const doneIds = new Set(JSON.parse(localStorage.getItem(doneStorageKey) || "[]"));
const state = { library: "hsc", topic: "all", year: "all", section: "all", practice: "all", thscSearch: "", thscYear: "all", selectedId: null };
const byCode = new Map(curriculum.streams.flatMap((stream) => stream.topics).map((topic) => [topic.code, topic]));
const elements = {
  map: document.querySelector("#curriculum-map"),
  scope: document.querySelector("#curriculum-scope"),
  topic: document.querySelector("#topic-filter"),
  year: document.querySelector("#year-filter"),
  section: document.querySelector("#section-filter"),
  practice: document.querySelector("#state-filter"),
  hscFilters: document.querySelector("#hsc-filters"),
  thscFilters: document.querySelector("#thsc-filters"),
  thscSearch: document.querySelector("#thsc-search"),
  thscYear: document.querySelector("#thsc-year-filter"),
  list: document.querySelector("#question-list"),
  summary: document.querySelector("#results-summary"),
  hint: document.querySelector("#results-hint"),
  empty: document.querySelector("#empty-state"),
  progress: document.querySelector("#progress-value"),
  heroCount: document.querySelector("#hero-item-count"),
  viewer: document.querySelector("#pdf-viewer"),
  viewerTitle: document.querySelector("#viewer-title"),
  viewerMeta: document.querySelector("#viewer-meta"),
  viewerSource: document.querySelector("#viewer-source"),
  viewerDownload: document.querySelector("#viewer-download"),
  libraryButtons: [...document.querySelectorAll("[data-library]")],
};

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[character]));
}

function saveProgress() {
  localStorage.setItem(doneStorageKey, JSON.stringify([...doneIds]));
  elements.progress.textContent = `${doneIds.size} / ${bank.length}`;
}

function selectedTopicName() {
  return state.topic === "all" ? "All topics" : byCode.get(state.topic).name;
}

function filteredQuestions() {
  return bank.filter((question) => {
    if (state.topic !== "all" && !question.topic_codes.includes(state.topic)) return false;
    if (state.year !== "all" && String(question.year) !== state.year) return false;
    if (state.section !== "all" && question.section !== state.section) return false;
    if (state.practice === "done" && !doneIds.has(question.id)) return false;
    if (state.practice === "open" && doneIds.has(question.id)) return false;
    return true;
  });
}

function filteredTrials() {
  const query = state.thscSearch.trim().toLowerCase();
  return thscTrials.filter((trial) => {
    if (state.thscYear !== "all" && String(trial.year) !== state.thscYear) return false;
    return !query || `${trial.title} ${trial.school} ${trial.year}`.toLowerCase().includes(query);
  });
}

function officialPaperLink(question) {
  return `${question.official_paper_url}#page=${question.paper_page}`;
}

function thscEmbedLink(trial) {
  return `https://thsconline.github.io/s/viewer.html?field=${encodeURIComponent(trial.title)}&base=${trial.viewer_id}&w=${THSC_VIEWER_WORKER}`;
}

function thscSourceLink(trial) {
  return `https://thsconline.github.io/s/v/${trial.viewer_id}/${encodeURIComponent(trial.title)}`;
}

function questionTopics(question) {
  return question.topic_codes.map((code) => byCode.get(code)).filter(Boolean);
}

function renderTopicOptions() {
  elements.topic.innerHTML = [
    '<option value="all">All syllabus topics</option>',
    ...curriculum.streams.map((stream) => `<optgroup label="${escapeHtml(stream.label)}">${stream.topics.map((topic) => `<option value="${topic.code}">${escapeHtml(topic.name)}</option>`).join("")}</optgroup>`),
  ].join("");
  elements.thscYear.innerHTML = ["<option value=\"all\">All years</option>", ...[...new Set(thscTrials.map((trial) => trial.year))].sort((a, b) => b - a).map((year) => `<option value="${year}">${year}</option>`)].join("");
}

function renderCurriculum() {
  elements.scope.textContent = curriculum.scope;
  elements.map.innerHTML = curriculum.streams.map((stream) => `
    <article class="stream-card">
      <h3>${escapeHtml(stream.label)}</h3>
      <div class="topic-grid">
        ${stream.topics.map((topic) => {
          const count = bank.filter((question) => question.topic_codes.includes(topic.code)).length;
          const active = state.topic === topic.code ? " active" : "";
          return `<button class="topic-button${active}" type="button" data-topic="${topic.code}" aria-pressed="${state.topic === topic.code}">${escapeHtml(topic.name)} <small>${count}</small></button>`;
        }).join("")}
      </div>
    </article>
  `).join("");
  elements.map.querySelectorAll("[data-topic]").forEach((button) => {
    button.addEventListener("click", () => setTopic(button.dataset.topic, true));
  });
}

function setViewer(item, kind) {
  const question = kind === "hsc" ? item : null;
  const trial = kind === "thsc" ? item : null;
  state.selectedId = `${kind}:${item.id}`;
  const sourceUrl = question ? officialPaperLink(question) : thscSourceLink(trial);
  const embedUrl = question ? officialPaperLink(question) : thscEmbedLink(trial);
  elements.viewerTitle.textContent = question ? `Question ${question.question}` : trial.title;
  elements.viewerMeta.textContent = question
    ? `${question.year} HSC · Section ${question.section} · ${question.marks} mark${question.marks === 1 ? "" : "s"} · PDF page ${question.paper_page}`
    : `THSC Standard 2 trial paper · ${trial.year}${trial.includes_solutions ? " · includes solutions" : ""}`;
  elements.viewerSource.href = sourceUrl;
  elements.viewerSource.textContent = question ? "Open official source ↗" : "Open THSC source ↗";
  elements.viewerDownload.href = trial ? sourceUrl : question.official_marking_guideline_url;
  elements.viewerDownload.textContent = trial ? "Local-cache guide" : "Marking guide ↗";
  elements.viewer.src = embedUrl;
}

function renderHscQuestions() {
  const questions = filteredQuestions();
  const noun = questions.length === 1 ? "item" : "items";
  elements.summary.textContent = `${selectedTopicName()} · ${questions.length} ${noun}`;
  elements.hint.textContent = "Choose a card to move the viewer to its exact official PDF page. The list scrolls independently.";
  elements.empty.hidden = questions.length !== 0;
  elements.list.innerHTML = questions.map((question) => {
    const complete = doneIds.has(question.id);
    const topics = questionTopics(question);
    const selected = state.selectedId === `hsc:${question.id}` ? " selected" : "";
    return `
      <article class="question-card${complete ? " done" : ""}${selected}" id="${question.id}">
        <button class="question-open" type="button" data-open-question="${question.id}" aria-label="View Question ${escapeHtml(question.question)}">
          <span class="question-kicker"><span>${question.year} HSC · Section ${question.section}</span><span>${question.marks} mark${question.marks === 1 ? "" : "s"}</span></span>
          <strong>Question ${escapeHtml(question.question)}</strong>
          <span class="question-meta">PDF page ${question.paper_page} · ${escapeHtml(question.outcomes.join(", "))}</span>
        </button>
        <div class="tag-row">
          ${topics.map((topic) => `<span class="tag topic">${escapeHtml(topic.name)}</span><span class="tag"><code>${topic.code}</code></span>`).join("")}
        </div>
        <div class="card-footer">
          <button class="card-link" type="button" data-open-question="${question.id}">View in workspace</button>
          <label class="complete-control"><input type="checkbox" data-complete="${question.id}" ${complete ? "checked" : ""}> Done</label>
        </div>
      </article>
    `;
  }).join("");
  elements.list.querySelectorAll("[data-open-question]").forEach((button) => {
    button.addEventListener("click", () => {
      const question = bank.find((entry) => entry.id === button.dataset.openQuestion);
      setViewer(question, "hsc");
      renderHscQuestions();
    });
  });
  elements.list.querySelectorAll("[data-complete]").forEach((input) => {
    input.addEventListener("change", () => {
      if (input.checked) doneIds.add(input.dataset.complete);
      else doneIds.delete(input.dataset.complete);
      saveProgress();
      renderHscQuestions();
    });
  });
  if (!state.selectedId && questions.length) {
    setViewer(questions[0], "hsc");
    document.getElementById(questions[0].id)?.classList.add("selected");
  }
}

function renderThscTrials() {
  const trials = filteredTrials();
  elements.summary.textContent = `THSC Standard 2 trial library · ${trials.length} papers`;
  elements.hint.textContent = "THSC papers are a separate source library. Use the local cache script for personal offline copies and page captures.";
  elements.empty.hidden = trials.length !== 0;
  elements.list.innerHTML = trials.map((trial) => {
    const selected = state.selectedId === `thsc:${trial.id}` ? " selected" : "";
    return `
      <article class="question-card trial-card${selected}" id="${trial.id}">
        <button class="question-open" type="button" data-open-trial="${trial.id}" aria-label="View ${escapeHtml(trial.title)}">
          <span class="question-kicker"><span>THSC trial paper</span><span>${trial.year}</span></span>
          <strong>${escapeHtml(trial.school)}</strong>
          <span class="question-meta">${escapeHtml(trial.title)}${trial.includes_solutions ? " · solutions included" : ""}</span>
        </button>
        <div class="card-footer"><button class="card-link" type="button" data-open-trial="${trial.id}">View in workspace</button></div>
      </article>
    `;
  }).join("");
  elements.list.querySelectorAll("[data-open-trial]").forEach((button) => {
    button.addEventListener("click", () => {
      const trial = thscTrials.find((entry) => entry.id === button.dataset.openTrial);
      setViewer(trial, "thsc");
      renderThscTrials();
    });
  });
  if (!state.selectedId && trials.length) {
    setViewer(trials[0], "thsc");
    document.getElementById(trials[0].id)?.classList.add("selected");
  }
}

function renderWorkspace() {
  const isHsc = state.library === "hsc";
  elements.hscFilters.hidden = !isHsc;
  elements.thscFilters.hidden = isHsc;
  elements.map.closest(".curriculum-section").hidden = !isHsc;
  elements.libraryButtons.forEach((button) => {
    const active = button.dataset.library === state.library;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", active);
  });
  state.selectedId = null;
  if (isHsc) renderHscQuestions();
  else renderThscTrials();
}

function render() {
  renderCurriculum();
  renderWorkspace();
}

function setTopic(topic, scrollToQuestions = false) {
  state.library = "hsc";
  state.topic = topic;
  elements.topic.value = topic;
  render();
  if (scrollToQuestions) document.querySelector("#questions").scrollIntoView({ behavior: "smooth", block: "start" });
}

elements.libraryButtons.forEach((button) => {
  button.addEventListener("click", () => {
    state.library = button.dataset.library;
    renderWorkspace();
  });
});

elements.hscFilters.addEventListener("change", () => {
  state.topic = elements.topic.value;
  state.year = elements.year.value;
  state.section = elements.section.value;
  state.practice = elements.practice.value;
  state.selectedId = null;
  renderWorkspace();
});

elements.hscFilters.addEventListener("reset", () => {
  window.setTimeout(() => {
    state.topic = "all";
    state.year = "all";
    state.section = "all";
    state.practice = "all";
    state.selectedId = null;
    render();
  });
});

elements.thscFilters.addEventListener("input", () => {
  state.thscSearch = elements.thscSearch.value;
  state.thscYear = elements.thscYear.value;
  state.selectedId = null;
  renderWorkspace();
});

elements.thscFilters.addEventListener("reset", () => {
  window.setTimeout(() => {
    state.thscSearch = "";
    state.thscYear = "all";
    state.selectedId = null;
    renderWorkspace();
  });
});

document.querySelector("#clear-progress").addEventListener("click", () => {
  if (doneIds.size === 0) return;
  doneIds.clear();
  saveProgress();
  if (state.library === "hsc") renderHscQuestions();
});

document.querySelector("#random-question").addEventListener("click", () => {
  state.library = "hsc";
  renderWorkspace();
  const questions = filteredQuestions();
  if (!questions.length) return;
  const question = questions[Math.floor(Math.random() * questions.length)];
  document.querySelector("#questions").scrollIntoView({ behavior: "smooth", block: "start" });
  window.setTimeout(() => {
    setViewer(question, "hsc");
    renderHscQuestions();
    document.getElementById(question.id)?.scrollIntoView({ behavior: "smooth", block: "center" });
  }, 300);
});

renderTopicOptions();
elements.heroCount.textContent = bank.length;
saveProgress();
render();
