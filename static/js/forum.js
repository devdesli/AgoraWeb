document.addEventListener("click", function (event) {
    const button = event.target.closest(".like-button");

    if (button) {
        const icon = button.querySelector("i");
        const likeCountElement = button.querySelector(".like-count");
        const todoId = button.getAttribute("data-id");

        fetch(`/togglelike/${todoId}`, {
            method: 'POST'
        })
        .then(res => res.json())
        .then(data => {
            if (data.likes !== undefined) {
                // Update the like count
                likeCountElement.textContent = data.likes;

                // Toggle the icon class based on liked status
                icon.classList.remove("bxs-like", "bx-like");
                icon.classList.add(data.liked ? "bxs-like" : "bx-like");
            } else {
                console.error("Error toggling like:", data);
            }
        })
        .catch(err => console.error("Fetch error:", err));
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
