document.addEventListener("DOMContentLoaded", () => {

    const headerLogueado = document.querySelector(".header-logueado");

    const btnMenuLateral = document.getElementById("btnMenuLateral");
    const asideMenu = document.getElementById("asideMenu");

    const btnMenuPublico = document.getElementById("boton-menu");
    const menuPublico = document.querySelector(".nav-publico .list-foro");

    const actualizarBotonMenuLateral = (menuAbierto) => {
        const icono = btnMenuLateral.querySelector("i");

        btnMenuLateral.classList.toggle("menu-activo", menuAbierto);
        btnMenuLateral.setAttribute("aria-expanded", String(menuAbierto));
        btnMenuLateral.setAttribute(
            "aria-label",
            menuAbierto ? "Cerrar menú lateral" : "Abrir menú lateral"
        );

        if (icono) {
            icono.classList.toggle("fa-bars", !menuAbierto);
            icono.classList.toggle("fa-xmark", menuAbierto);
        }
    };

    if (btnMenuLateral && asideMenu && headerLogueado) {

        function ajustarMenuLateral() {

            const alturaHeader = headerLogueado.getBoundingClientRect().height;

            asideMenu.style.top = `${alturaHeader}px`;
            asideMenu.style.height = `calc(100dvh - ${alturaHeader}px)`;
        }

        const cerrarMenuLateral = () => {
            asideMenu.classList.remove("menu-abierto");
            actualizarBotonMenuLateral(false);
        };

        btnMenuLateral.addEventListener("click", () => {

            const menuAbierto =
                asideMenu.classList.toggle("menu-abierto");

            actualizarBotonMenuLateral(menuAbierto);
            ajustarMenuLateral();
        });

        asideMenu.querySelectorAll("a").forEach((enlace) => {
            enlace.addEventListener("click", cerrarMenuLateral);
        });

        document.addEventListener("keydown", (evento) => {
            if (evento.key === "Escape" && asideMenu.classList.contains("menu-abierto")) {
                cerrarMenuLateral();
                btnMenuLateral.focus();
            }
        });

        window.addEventListener("resize", () => {
            ajustarMenuLateral();
        });


        ajustarMenuLateral();
    }


    if (btnMenuPublico && menuPublico) {

        btnMenuPublico.addEventListener("click", () => {

            const menuAbierto =
                menuPublico.classList.toggle("menu-abierto");

            btnMenuPublico.classList.toggle(
                "menu-activo",
                menuAbierto
            );

            btnMenuPublico.setAttribute(
                "aria-expanded",
                String(menuAbierto)
            );

            btnMenuPublico.setAttribute(
                "aria-label",
                menuAbierto
                    ? "Cerrar menú"
                    : "Abrir menú"
            );
        });


        const enlacesPublicos =
            menuPublico.querySelectorAll("a");


        enlacesPublicos.forEach((enlace) => {

            enlace.addEventListener("click", () => {

                menuPublico.classList.remove("menu-abierto");

                btnMenuPublico.classList.remove("menu-activo");

                btnMenuPublico.setAttribute(
                    "aria-expanded",
                    "false"
                );

                btnMenuPublico.setAttribute(
                    "aria-label",
                    "Abrir menú"
                );
            });

        });


        window.addEventListener("resize", () => {

            if (window.innerWidth > 768) {

                menuPublico.classList.remove("menu-abierto");

                btnMenuPublico.classList.remove("menu-activo");

                btnMenuPublico.setAttribute(
                    "aria-expanded",
                    "false"
                );

                btnMenuPublico.setAttribute(
                    "aria-label",
                    "Abrir menú"
                );
            }
        });
    }

});