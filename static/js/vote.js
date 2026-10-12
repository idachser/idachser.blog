document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("vote");
    if (!form) return;

    const formatScore = (score) =>
        score < 0 ? `−${Math.abs(score)}` : `+${score}`;
    const scoreClass = (score) =>
        score > 0 ? "score--pos" : score < 0 ? "score--neg" : "score--zero";

    form.addEventListener("submit", async (event) => {
        const button = event.submitter;
        if (!button || !button.value) return;
        event.preventDefault();

        const body = new FormData(form);
        body.set("value", button.value);

        let response;
        try {
            response = await fetch(form.action, {
                method: "POST",
                body,
                headers: {
                    Accept: "application/json",
                    "X-CSRFToken": body.get("csrfmiddlewaretoken"),
                },
                credentials: "same-origin",
            });
        } catch {
            // form.submit() does not send the clicked button's value.
            const input = document.createElement("input");
            input.type = "hidden";
            input.name = "value";
            input.value = button.value;
            form.appendChild(input);
            form.submit();
            return;
        }
        if (!response.ok) return;
        const data = await response.json();

        document.querySelectorAll("[data-score]").forEach((el) => {
            el.textContent =
                el.dataset.score === "plain" && data.score >= 0
                    ? data.score
                    : formatScore(data.score);
            el.classList.remove("score--pos", "score--neg", "score--zero");
            el.classList.add(scoreClass(data.score));
        });
        form.querySelectorAll(".vote-btn").forEach((btn) => {
            btn.classList.toggle(
                "is-active",
                data.vote !== null && Number(btn.value) === data.vote
            );
        });
    });
});
