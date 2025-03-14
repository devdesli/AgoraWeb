document.addEventListener("DOMContentLoaded", function () {
    let challengeForm = document.getElementById("challengeForm"); // Formulier
    let container = document.getElementById("challengesContainer"); // Waar de posts komen

    if (challengeForm && container) {
        challengeForm.addEventListener("submit", function (event) {
            event.preventDefault(); // Voorkom pagina herladen

            // Invoervelden ophalen
            let name = document.getElementById("name").value.trim();
            let title = document.getElementById("title").value.trim();
            let mainQuestion = document.getElementById("mainQuestion").value.trim();
            let subQuestions = document.getElementById("subQuestions").value.trim();
            let description = document.getElementById("description").value.trim();
            let endProduct = document.getElementById("endProduct").value.trim();
            let category = document.getElementById("categorie").value;

            // Controleer of alles is ingevuld
            if (!name || !title || !mainQuestion || !subQuestions || !description || !endProduct || category === "placeholder") {
                alert("Vul alle velden in en kies een categorie!");
                return;
            }

            // Maak een nieuwe card aan
            let card = document.createElement("div");
            card.classList.add("card");
            card.innerHTML = `
                <h2 class="title">${title}</h2>
                <p class="author">door ${name}</p>
                <p><strong>Hoofdvraag:</strong> ${mainQuestion}</p>
                <p><strong>Deelvragen:</strong> ${subQuestions}</p>
                <p><strong>Beschrijving:</strong> ${description}</p>
                <p><strong>Eindproduct:</strong> ${endProduct}</p>
                <p><strong>Categorie:</strong> ${category}</p>
                <button class="like-button"><i class='bx bx-like'></i></button>
            `;

            // Voeg de nieuwe post toe aan de container
            container.appendChild(card);
            challengeForm.reset();
        });
    }
});


    // Event delegation voor like-knoppen zodat het werkt voor nieuwe en bestaande posts
    document.addEventListener("click", function (event) {
        if (event.target.closest(".like-button")) {
            let icon = event.target.closest(".like-button").querySelector("i");
            icon.classList.toggle("bx-like");
            icon.classList.toggle("bxs-like");
        }
    });

document.getElementById("uploadForm").addEventListener("submit", async function (event) {
    event.preventDefault();
    
    let formData = new FormData();
    let fileInput = document.getElementById("fileInput");
    
    if (fileInput.files.length === 0) {
        alert("Please select a file.");
        return;
    }

    formData.append("file", fileInput.files[0]);

    let response = await fetch("/upload", {
        method: "POST",
        body: formData
    });

    let result = await response.json();
    alert(result.message);
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
