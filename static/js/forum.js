document.addEventListener("DOMContentLoaded", function () {
  // 1. Fetch current like states from backend on page load
  document.querySelectorAll(".like-button").forEach(button => {
    const todoId = button.getAttribute("data-id");

    fetch(`/like_status/${todoId}`, {
      headers: { "X-Requested-With": "XMLHttpRequest" }
    })
      .then(res => res.json())
      .then(data => {
        const icon = button.querySelector("i");
        const likeCountElement = button.querySelector(".like-count");

        if (data.success) {
          likeCountElement.textContent = data.likes;
          icon.classList.remove("bx-heart", "bxs-heart");
          icon.classList.add(data.liked ? "bxs-heart" : "bx-heart");
        }
      });
  });

  // 2. Handle like button clicks
  document.addEventListener("click", function (event) {
    const button = event.target.closest(".like-button");
    if (!button) return;

    event.preventDefault();

    const icon = button.querySelector("i");
    const likeCountElement = button.querySelector(".like-count");
    const todoId = button.getAttribute("data-id");

    if (button.dataset.processing === "true") return;
    button.dataset.processing = "true";

    fetch(`/like/${todoId}`, {
      method: "POST",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
      },
    })
      .then((response) => {
        if (response.status === 401) {
          alert("You must be logged in to like challenges.");
          window.location.href = "/login?next=" + encodeURIComponent(window.location.pathname);
          return;
        }
        return response.json();
      })
      .then((data) => {
        if (!data) return;

        if (data.success) {
          likeCountElement.textContent = Math.max(0, data.likes);
          icon.classList.remove("bxs-heart", "bx-heart");
          icon.classList.add(data.liked ? "bxs-heart" : "bx-heart");
        } else {
          console.error("Server error:", data.error);
        }
      })
      .catch((err) => console.error("Fetch error:", err))
      .finally(() => {
        button.dataset.processing = "false";
      });
  });
});