
function configurarPasos() {

    const contenedores = document.querySelectorAll(
        ".modulo_datos, .modulo_dialogo_detallado"
    );

    if (!contenedores.length) {
        return;
    }

    contenedores.forEach(function (contenedor) {

        if (contenedor.dataset.pasosConfigurados === "true") {
            return;
        }

        contenedor.dataset.pasosConfigurados = "true";

        const pasos = contenedor.querySelectorAll(".paso");

        if (!pasos.length) {
            return;
        }

        const contexto = contenedor.closest("dialog") || contenedor;

        const btnSiguiente = contexto.querySelector(".btn_avanzar");
        const btnAtras = contexto.querySelector(".btn_retroceder");

        let pasoActual = 0;

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

                if (typeof cedulaValida !== "undefined" && !cedulaValida) {

                    campoCedula.setCustomValidity(
                        "Debe ingresar una cédula válida y disponible."
                    );

                    campoCedula.reportValidity();

                    return false;
                }

                campoCedula.setCustomValidity("");
            }

            const campos = paso.querySelectorAll(
                "input, select, textarea"
            );

            for (const campo of campos) {

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

        if (btnSiguiente) {

            btnSiguiente.addEventListener("click", function (e) {

                e.preventDefault();

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

            btnAtras.addEventListener("click", function (e) {

                e.preventDefault();

                if (pasoActual > 0) {

                    pasoActual--;

                    actualizarPaso();
                }

            });
        }

        const dialogo = contenedor.closest("dialog");

        if (dialogo) {
            dialogo.addEventListener("close", reiniciarPasos);
        }

        actualizarPaso();

    });
}

configurarPasos();
