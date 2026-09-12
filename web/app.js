const el = (id) => document.getElementById(id);

const KEYS = { "1": "yes", "2": "probably", "3": "idk", "4": "probably not", "5": "no" };

let history = [];
let pending = null;   // the question, or the hero once it is a guess
let state = null;
let busy = false;     // one request at a time, or a fast click answers the old question

async function step() {
  busy = true;
  document.body.classList.add("busy");
  try {
    const res = await fetch("/api/next", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ history }),
    });
    if (!res.ok) throw new Error("server said " + res.status);
    render(await res.json());
  } finally {
    busy = false;
    document.body.classList.remove("busy");
  }
}

function render(s) {
  state = s;
  el("asked").textContent = `${s.asked} of ${s.max_questions} questions`;
  el("progress").style.width = (100 * s.asked / s.max_questions) + "%";
  renderTop(s.top);

  el("asking").hidden = s.done;
  el("guess").hidden = !s.done || s.gave_up;
  el("over").hidden = !s.gave_up;

  if (s.gave_up) {
    el("over-title").textContent = "I give up. Who was it tho?";
    return;
  }
  if (s.done) {
    el("guess-image").src = s.guess.image;
    el("guess-image").alt = s.guess.hero;
    el("guess-name").textContent = s.guess.hero;
    el("guess-p").textContent = Math.round(s.guess.p * 100) + "%";
    el("guess-q").textContent = s.asked;
    pending = s.guess.index;
    return;
  }
  el("question").textContent = s.question;
  pending = s.question_index;
}

function renderTop(top) {
  el("top").innerHTML = top.map((c) => `
    <li>
      <span class="name"></span>
      <span class="p">${(c.p * 100).toFixed(1)}%</span>
      <span class="bar"><i class="fill" style="width:${Math.min(100, c.p * 100)}%"></i></span>
    </li>`).join("");
  // names come from the dataset, set them as text rather than markup
  el("top").querySelectorAll(".name").forEach((node, i) => { node.textContent = top[i].hero; });
}

function answer(value) {
  if (busy || !state || state.done) return;
  history.push([pending, value]);
  step();
}

function confirm(correct) {
  if (busy || !state || !state.done) return;
  if (correct) {
    el("guess").hidden = true;
    el("over").hidden = false;
    el("over-title").textContent = `Guessed it in ${state.asked} questions. (EZ)`;
    state = null;
    return;
  }
  // a wrong guess is one more observation, not a restart
  history.push([pending, "reject"]);
  step();
}

function restart() {
  history = [];
  step();
}

el("answers").addEventListener("click", (e) => {
  if (e.target.dataset.answer) answer(e.target.dataset.answer);
});
el("right").addEventListener("click", () => confirm(true));
el("wrong").addEventListener("click", () => confirm(false));
el("again").addEventListener("click", restart);

// same keys the desktop client uses
document.addEventListener("keydown", (e) => {
  const key = e.key.toLowerCase();
  if (key === "r") restart();
  else if (KEYS[key]) answer(KEYS[key]);
  else if (key === "y") confirm(true);
  else if (key === "n") confirm(false);
});

step();
