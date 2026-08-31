const [curriculum, bank] = await Promise.all([
  fetch("data/curriculum.json").then((response) => response.json()),
  fetch("data/questions.json").then((response) => response.json()),
]);

const doneStorageKey = "hsc-standard-2-question-engine-done";
const doneIds = new Set(JSON.parse(localStorage.getItem(doneStorageKey) || "[]"));
const state = { topic: "all", year: "all", section: "all", practice: "all" };
const byCode = new Map(curriculum.streams.flatMap((stream) => stream.topics).map((topic) => [topic.code, topic]));
const elements = {
  map: document.querySelector("#curriculum-map"),
  scope: document.querySelector("#curriculum-scope"),
  topic: document.querySelector("#topic-filter"),
  year: document.querySelector("#year-filter"),
  section: document.querySelector("#section-filter"),
  practice: document.querySelector("#state-filter"),
  list: document.querySelector("#question-list"),
  summary: document.querySelector("#results-summary"),
  empty: document.querySelector("#empty-state"),
  progress: document.querySelector("#progress-value"),
  heroCount: document.querySelector("#hero-item-count"),
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

function renderTopicOptions() {
  elements.topic.innerHTML = [
    '<option value="all">All syllabus topics</option>',
    ...curriculum.streams.map((stream) => `<optgroup label="${escapeHtml(stream.label)}">${stream.topics.map((topic) => `<option value="${topic.code}">${escapeHtml(topic.name)}</option>`).join("")}</optgroup>`),
  ].join("");
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

function officialPaperLink(question) {
  return `${question.official_paper_url}#page=${question.paper_page}`;
}

function questionTopics(question) {
  return question.topic_codes.map((code) => byCode.get(code)).filter(Boolean);
}

function renderQuestions() {
  const questions = filteredQuestions();
  const noun = questions.length === 1 ? "item" : "items";
  elements.summary.textContent = `${selectedTopicName()} · ${questions.length} ${noun}`;
  elements.empty.hidden = questions.length !== 0;
  elements.list.innerHTML = questions.map((question) => {
    const complete = doneIds.has(question.id);
    const topics = questionTopics(question);
    return `
      <article class="question-card${complete ? " done" : ""}" id="${question.id}">
        <div class="question-kicker"><span>${question.year} HSC · Section ${question.section}</span><span>${question.marks} mark${question.marks === 1 ? "" : "s"}</span></div>
        <h3>Question ${escapeHtml(question.question)}</h3>
        <p class="question-meta">Official PDF page ${question.paper_page} · ${escapeHtml(question.outcomes.join(", "))}</p>
        <div class="tag-row">
          ${topics.map((topic) => `<span class="tag topic">${escapeHtml(topic.name)}</span><span class="tag"><code>${topic.code}</code></span>`).join("")}
        </div>
        <div class="card-footer">
          <div class="card-links">
            <a class="card-link" href="${officialPaperLink(question)}" target="_blank" rel="noreferrer">Open question ↗</a>
            <a class="card-link" href="${question.official_marking_guideline_url}" target="_blank" rel="noreferrer">Marking guide ↗</a>
          </div>
          <label class="complete-control"><input type="checkbox" data-complete="${question.id}" ${complete ? "checked" : ""}> Done</label>
        </div>
      </article>
    `;
  }).join("");
  elements.list.querySelectorAll("[data-complete]").forEach((input) => {
    input.addEventListener("change", () => {
      if (input.checked) doneIds.add(input.dataset.complete);
      else doneIds.delete(input.dataset.complete);
      saveProgress();
      renderQuestions();
    });
  });
}

function render() {
  renderCurriculum();
  renderQuestions();
}

function setTopic(topic, scrollToQuestions = false) {
  state.topic = topic;
  elements.topic.value = topic;
  render();
  if (scrollToQuestions) document.querySelector("#questions").scrollIntoView({ behavior: "smooth", block: "start" });
}

document.querySelector("#filters").addEventListener("change", () => {
  state.topic = elements.topic.value;
  state.year = elements.year.value;
  state.section = elements.section.value;
  state.practice = elements.practice.value;
  render();
});

document.querySelector("#filters").addEventListener("reset", () => {
  window.setTimeout(() => {
    state.topic = "all";
    state.year = "all";
    state.section = "all";
    state.practice = "all";
    render();
  });
});

document.querySelector("#clear-progress").addEventListener("click", () => {
  if (doneIds.size === 0) return;
  doneIds.clear();
  saveProgress();
  renderQuestions();
});

document.querySelector("#random-question").addEventListener("click", () => {
  const questions = filteredQuestions();
  if (!questions.length) return;
  const question = questions[Math.floor(Math.random() * questions.length)];
  document.querySelector("#questions").scrollIntoView({ behavior: "smooth", block: "start" });
  window.setTimeout(() => document.getElementById(question.id)?.scrollIntoView({ behavior: "smooth", block: "center" }), 300);
});

renderTopicOptions();
elements.heroCount.textContent = bank.length;
saveProgress();
render();
