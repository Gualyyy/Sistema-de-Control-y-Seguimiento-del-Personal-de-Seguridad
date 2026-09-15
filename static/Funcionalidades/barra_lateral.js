document.addEventListener("DOMContentLoaded", () => {
    const btnToggle = document.querySelector(".btn-menu-toggle");
    const overlay = document.querySelector(".overlay-menu");
    const aside = document.getElementById("asideMenu");
    if (!aside) return;

    function abrirMenu() {
        aside.classList.add("menu-abierto");

        if (overlay) {
            overlay.classList.add("activo");
        }

        document.body.style.overflow = "hidden";
    }

    function cerrarMenu() {
        aside.classList.remove("menu-abierto");

        if (overlay) {
            overlay.classList.remove("activo");
        }

        document.body.style.overflow = "";
    }

    function toggleMenu() {
        if (aside.classList.contains("menu-abierto")) {
            cerrarMenu();
        } else {
            abrirMenu();
        }
    }

    if (btnToggle) {
        btnToggle.addEventListener("click", toggleMenu);
    }

    if (overlay) {
        overlay.addEventListener("click", cerrarMenu);
    }

    window.addEventListener("resize", () => {
        if (window.innerWidth > 992) {
            cerrarMenu();
        }
    });

});