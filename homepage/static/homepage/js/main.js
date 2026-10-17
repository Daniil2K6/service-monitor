const yearElement = document.getElementById("current-year");

if (yearElement) {
    yearElement.textContent = new Date().getFullYear();
}

function showToast(card) {
    const toast = card.querySelector(".upd-toast");

    if (toast) {
        toast.classList.add("show");

        setTimeout(function () {
            toast.classList.remove("show");
        }, 2000);
    }
}

async function checkOne(card) {
    const slug = card.dataset.slug;
    const response = await fetch(
        "/services/" + slug + "/check/",
        {
            headers: {
                "X-Requested-With": "XMLHttpRequest",
            },
        }
    );
    const data = await response.json();
    const badge = card.querySelector(".badge");

    if (badge) {
        badge.className = "badge service-status " + data.badge;
        badge.textContent = data.status;
    }

    showToast(card);
}

document.querySelectorAll(".js-check").forEach(function (link) {
    link.addEventListener("click", function (event) {
        event.preventDefault();
        checkOne(link.closest("[data-slug]"));
    });
});

const checkAll = document.getElementById("check-all");

if (checkAll) {
    checkAll.addEventListener("click", function (event) {
        event.preventDefault();
        document.querySelectorAll("[data-slug]").forEach(checkOne);
    });
}
