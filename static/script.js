function updateClock() {
    const el = document.getElementById("current-time");
    if (!el) return;
    const now = new Date();
    const dateStr = now.toLocaleDateString("en-US", { weekday: "long", month: "short", day: "numeric" });
    const timeStr = now.toLocaleTimeString({ hour: "2-digit", minute: "2-digit", second: "2-digit" });
    el.textContent = `${dateStr} · ${timeStr}`;
}
updateClock();
setInterval(updateClock, 1000);

document.getElementById("scrape-button").addEventListener("click", function() {
    const btn = this;
    btn.disabled = true;
    btn.textContent = "Scraping...";

    fetch("/scrape", { method: "POST" })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Server returned ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log("Scrape complete:", data);
            location.reload();
        })
        .catch(error => {
            console.error("Scrape failed:", error);
            btn.textContent = "Failed — try again";
            btn.disabled = false;
        });
});


function applyCompletionOrder() {
    const taskList = document.querySelector(".task-list");
    if (!taskList) return;

    const rows = [...taskList.querySelectorAll(".task-row")];

    rows.sort((a, b) => {
        const aDone = a.classList.contains("completed");
        const bDone = b.classList.contains("completed");
        if (aDone !== bDone) return aDone ? 1 : -1;

        const aDue = new Date(a.dataset.due).getTime();
        const bDue = new Date(b.dataset.due).getTime();
        return aDue - bDue;
    });

    rows.forEach(row => taskList.appendChild(row));
}

document.querySelectorAll(".task-checkbox").forEach(checkbox => {
    checkbox.addEventListener("change", () => {
        const row = checkbox.closest(".task-row");
        const taskId = row.dataset.taskId;
        const isComplete = checkbox.checked;

        row.classList.toggle("completed", isComplete); // optimistic UI update
        applyCompletionOrder();

        fetch("/complete", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ task_id: taskId, completed: isComplete })
        })
            .then(response => {
                if (!response.ok) throw new Error(`Server returned ${response.status}`);
            })
            .catch(error => {
                console.error("Failed to save completion state:", error);
                checkbox.checked = !isComplete;
                row.classList.toggle("completed", !isComplete);
                applyCompletionOrder();
            });
    });
});


const FILTER_KEY = "syla-excluded-courses";

function getExcludedCourses() {
    try {
        return new Set(JSON.parse(localStorage.getItem(FILTER_KEY) || "[]"));
    } catch {
        return new Set();
    }
}

function saveExcludedCourses(set) {
    localStorage.setItem(FILTER_KEY, JSON.stringify([...set]));
}

function applyCourseFilter() {
    const excluded = getExcludedCourses();

    document.querySelectorAll(".course-card").forEach(card => {
        card.setAttribute("aria-pressed", String(!excluded.has(card.dataset.course)));
    });

    document.querySelectorAll(".task-row").forEach(row => {
        row.style.display = excluded.has(row.dataset.course) ? "none" : "";
    });

    applyCompletionOrder();
}

document.querySelectorAll(".course-card").forEach(card => {
    card.addEventListener("click", () => {
        const course = card.dataset.course;
        const excluded = getExcludedCourses();

        excluded.has(course) ? excluded.delete(course) : excluded.add(course);

        saveExcludedCourses(excluded);
        applyCourseFilter();
    });
});

applyCourseFilter();