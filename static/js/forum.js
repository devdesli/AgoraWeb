document.addEventListener("DOMContentLoaded", function () {
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
          icon.classList.remove("bxs-like", "bx-like");
          icon.classList.add(data.liked ? "bxs-like" : "bx-like");
          icon.classList.toggle("liked", data.liked);
          icon.classList.toggle("unliked", !data.liked);
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


document.addEventListener("DOMContentLoaded", function () {
  // Event delegation for like buttons
  document.addEventListener("click", function (event) {
    let likeButton = event.target.closest(".like-button button"); // Selecteer de like-knop
    if (likeButton) {
      let icon = likeButton.querySelector("i");
      if (icon) {
        icon.classList.toggle("bx-like");
        icon.classList.toggle("bxs-like");
      }
      return;
    }
  });
});
