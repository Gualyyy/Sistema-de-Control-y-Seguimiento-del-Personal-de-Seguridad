function configurarPasos(raizBusqueda = document) {

    const botones = raizBusqueda.querySelectorAll(
        ".btn_avanzar, .btn_retroceder"
    );

    const contenedores = new Set();
    let navegacionResultado = null;

    botones.forEach(function (boton) {

        let elemento = boton.parentElement;

        while (elemento && elemento !== document.body) {

            const tienePasos = elemento.querySelector(".paso");
            const tieneAvanzar = elemento.querySelector(".btn_avanzar");
            const tieneRetroceder = elemento.querySelector(".btn_retroceder");

            if (
                tienePasos &&
                (tieneAvanzar || tieneRetroceder)
            ) {
                contenedores.add(elemento);
                break;
            }

            elemento = elemento.parentElement;
        }
    });

    contenedores.forEach(function (contenedor) {

        if (contenedor.dataset.pasosConfigurados === "true") {

            if (!navegacionResultado && contenedor._navegacion) {
                navegacionResultado = contenedor._navegacion;
            }

            return;
        }

        const pasos = Array.from(
            contenedor.querySelectorAll(".paso")
        );

        if (!pasos.length) {
            return;
        }

        contenedor.dataset.pasosConfigurados = "true";

        const btnSiguiente = contenedor.querySelector(".btn_avanzar");
        const btnAtras = contenedor.querySelector(".btn_retroceder");

        const dialogo = contenedor.closest("dialog");

        let pasoActual = pasos.findIndex(function (paso) {
            return paso.classList.contains("activo");
        });

        if (pasoActual < 0) {
            pasoActual = 0;
        }

        function actualizarPaso() {

            pasoActual = Math.max(
                0,
                Math.min(pasoActual, pasos.length - 1)
            );

            pasos.forEach(function (paso, indice) {

                paso.classList.toggle(
                    "activo",
                    indice === pasoActual
                );
            });

            if (btnAtras) {

                btnAtras.style.visibility =
                    pasoActual === 0 ? "hidden" : "visible";
            }

            if (btnSiguiente) {

                btnSiguiente.style.visibility =
                    pasoActual === pasos.length - 1
                        ? "hidden"
                        : "visible";
            }
        }

        function validarPasoActual() {

            const paso = pasos[pasoActual];

            if (!paso) {
                return false;
            }

            const campoCedula = paso.querySelector(
                "#input_actualizar_cedula"
            );

            if (campoCedula) {

                if (
                    typeof cedulaValida !== "undefined" &&
                    !cedulaValida
                ) {
                    campoCedula.setCustomValidity(
                        "Debe ingresar una cédula válida y disponible."
                    );

                    campoCedula.reportValidity();

                    return false;
                }

                campoCedula.setCustomValidity("");
            }

            const campos = paso.querySelectorAll(
                "input:not([type='hidden']), select, textarea"
            );

            for (const campo of campos) {

                if (campo.disabled) {
                    continue;
                }

                if (!campo.checkValidity()) {

                    campo.reportValidity();

                    return false;
                }
            }

            return true;
        }

        function reiniciarPasos() {

            pasoActual = 0;

            actualizarPaso();
        }

        const navegacion = {
            reiniciar: reiniciarPasos
        };

        contenedor._navegacion = navegacion;

        if (!navegacionResultado) {
            navegacionResultado = navegacion;
        }

        if (btnSiguiente) {

            btnSiguiente.addEventListener("click", function (evento) {

                evento.preventDefault();

                if (!validarPasoActual()) {
                    return;
                }

                if (pasoActual < pasos.length - 1) {

                    pasoActual++;

                    actualizarPaso();
                }
            });
        }

        if (btnAtras) {

            btnAtras.addEventListener("click", function (evento) {

                evento.preventDefault();

                if (pasoActual > 0) {

                    pasoActual--;

                    actualizarPaso();
                }
            });
        }

        if (dialogo) {
            dialogo.addEventListener("close", reiniciarPasos);
        }

        actualizarPaso();
    });

    return navegacionResultado || {
        reiniciar: function () { }
    };
}

configurarPasos();