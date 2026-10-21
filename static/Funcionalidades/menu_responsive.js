document.addEventListener("DOMContentLoaded", () => {

    const headerLogueado = document.querySelector(".header-logueado");

    const btnMenuLateral = document.getElementById("btnMenuLateral");
    const asideMenu = document.getElementById("asideMenu");

    const btnMenuPublico = document.getElementById("boton-menu");
    const menuPublico = document.querySelector(".nav-publico .list-foro");


    if (btnMenuLateral && asideMenu && headerLogueado) {

        function ajustarMenuLateral() {

            const alturaHeader = headerLogueado.getBoundingClientRect().height;

            asideMenu.style.top = `${alturaHeader}px`;
            asideMenu.style.height = `calc(100vh - ${alturaHeader}px)`;
        }


        btnMenuLateral.addEventListener("click", () => {

            const menuAbierto =
                asideMenu.classList.toggle("menu-abierto");

            btnMenuLateral.classList.toggle(
                "menu-activo",
                menuAbierto
            );

            btnMenuLateral.setAttribute(
                "aria-expanded",
                String(menuAbierto)
            );

            btnMenuLateral.setAttribute(
                "aria-label",
                menuAbierto
                    ? "Cerrar menú lateral"
                    : "Abrir menú lateral"
            );

            ajustarMenuLateral();
        });


        window.addEventListener("resize", () => {

            ajustarMenuLateral();

            if (window.innerWidth > 992) {

                asideMenu.classList.remove("menu-abierto");

                btnMenuLateral.classList.remove("menu-activo");

                btnMenuLateral.setAttribute(
                    "aria-expanded",
                    "false"
                );

                btnMenuLateral.setAttribute(
                    "aria-label",
                    "Abrir menú lateral"
                );
            }
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