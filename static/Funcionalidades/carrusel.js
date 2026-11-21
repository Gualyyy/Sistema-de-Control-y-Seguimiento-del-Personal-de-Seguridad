document.addEventListener("DOMContentLoaded", () => {

    const carrusel = document.getElementById("carrusel_publicitario");
    const diapositivas = document.querySelectorAll(".diapositiva_publicitaria");
    const btn_anterior = document.getElementById("anterior_publicidad");
    const btn_siguiente = document.getElementById("siguiente_publicidad");
    const indicadores = document.querySelectorAll(".indicador");
    const mensaje = document.getElementById("mensaje_carrusel");

    if (
        !carrusel ||
        diapositivas.length === 0 ||
        !btn_anterior ||
        !btn_siguiente ||
        indicadores.length === 0
    ) {
        return;
    }

    let indice_actual = 0;
    let intervalo_carrusel = null;

    const tiempo_cambio = 5000;

    function mostrar_diapositiva(indice) {

        diapositivas.forEach((diapositiva, posicion) => {

            const activa = posicion === indice;

            diapositiva.classList.toggle("activa", activa);
            diapositiva.setAttribute("aria-hidden", !activa);

        });

        indicadores.forEach((indicador, posicion) => {

            const activo = posicion === indice;

            indicador.classList.toggle("activo", activo);

            if (activo) {
                indicador.setAttribute("aria-current", "true");
            } else {
                indicador.removeAttribute("aria-current");
            }

        });

        indice_actual = indice;

        if (mensaje) {
            mensaje.textContent =
                `Mostrando publicidad ${indice_actual + 1} de ${diapositivas.length}.`;
        }

    }

    function siguiente_diapositiva() {

        const siguiente = (indice_actual + 1) % diapositivas.length;

        mostrar_diapositiva(siguiente);

    }

    function anterior_diapositiva() {

        const anterior =
            (indice_actual - 1 + diapositivas.length) % diapositivas.length;

        mostrar_diapositiva(anterior);

    }

    function iniciar_carrusel() {

        detener_carrusel();

        intervalo_carrusel = setInterval(() => {
            siguiente_diapositiva();
        }, tiempo_cambio);

    }

    function detener_carrusel() {

        if (intervalo_carrusel !== null) {

            clearInterval(intervalo_carrusel);
            intervalo_carrusel = null;

        }

    }

    function reiniciar_carrusel() {

        detener_carrusel();
        iniciar_carrusel();

    }

    btn_siguiente.addEventListener("click", () => {

        siguiente_diapositiva();
        reiniciar_carrusel();

    });

    btn_anterior.addEventListener("click", () => {

        anterior_diapositiva();
        reiniciar_carrusel();

    });

    indicadores.forEach((indicador, indice) => {

        indicador.addEventListener("click", () => {

            mostrar_diapositiva(indice);
            reiniciar_carrusel();

        });

    });

    carrusel.addEventListener("mouseenter", detener_carrusel);
    carrusel.addEventListener("mouseleave", iniciar_carrusel);

    document.addEventListener("visibilitychange", () => {

        if (document.hidden) {
            detener_carrusel();
        } else {
            iniciar_carrusel();
        }

    });

    mostrar_diapositiva(0);
    iniciar_carrusel();

});