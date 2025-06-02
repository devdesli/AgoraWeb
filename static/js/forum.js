document.addEventListener("click", function (event) {
  const button = event.target.closest(".like-button");

  if (button) {
    event.preventDefault();
    const icon = button.querySelector("i");
    const likeCountElement = button.querySelector(".like-count");
    const todoId = button.getAttribute("data-id");

    // Prevent multiple rapid clicks
    if (button.dataset.processing === "true") {
      return;
    }
    button.dataset.processing = "true";

    fetch(`/like/${todoId}`, {
      method: "POST",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
      },
    })
      .then((res) => {
        if (!res.ok) {
          throw new Error("Network response was not ok");
        }
        return res.json();
      })
      .then((data) => {
        if (data.success) {
          // Update the like count with validation
          const likes = Math.max(0, data.likes);
          likeCountElement.textContent = likes;

          // Toggle the icon class based on liked status
          icon.classList.remove("bxs-like", "bx-like");
          icon.classList.add(data.liked ? "bxs-like" : "bx-like");
        } else {
          console.error("Error toggling like:", data.error);
        }
      })
      .catch((err) => console.error("Fetch error:", err))
      .finally(() => {
        button.dataset.processing = "false";
      });
  }
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
