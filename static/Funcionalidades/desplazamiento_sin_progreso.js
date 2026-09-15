function configurarPasos() {

    const contenedor = document.querySelector(".modulo_datos");

    if (!contenedor) {
        return;
    }

    const pasos = contenedor.querySelectorAll(".paso");

    const btnSiguiente = document.querySelector(".btn_avanzar");
    const btnAtras = document.querySelector(".btn_retroceder");

    const formulario = contenedor.querySelector("form");

    let pasoActual = 0;


    function actualizarPaso() {

        if (!pasos.length) {
            return;
        }

        pasoActual = Math.max(
            0,
            Math.min(pasoActual, pasos.length - 1)
        );


        pasos.forEach((paso, indice) => {

            paso.classList.toggle(
                "activo",
                indice === pasoActual
            );

        });


        // Mostrar / ocultar Retroceder
        if (btnAtras) {

            btnAtras.style.visibility =
                pasoActual === 0
                    ? "hidden"
                    : "visible";
        }


        // Mostrar / ocultar Avanzar
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


        /*
         * VALIDACIÓN ESPECIAL DE CÉDULA
         */

        const campoCedula = paso.querySelector(
            "#input_actualizar_cedula"
        );

        if (campoCedula) {

            if (!cedulaValida) {

                campoCedula.setCustomValidity(
                    "Debe ingresar una cédula válida y disponible."
                );

                campoCedula.reportValidity();

                return false;
            }

            campoCedula.setCustomValidity("");
        }


        /*
         * VALIDACIÓN HTML
         */

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


    /*
     * AVANZAR
     */

    if (btnSiguiente) {

        btnSiguiente.addEventListener(
            "click",
            function (e) {

                e.preventDefault();


                if (!validarPasoActual()) {
                    return;
                }


                if (pasoActual < pasos.length - 1) {

                    pasoActual++;

                    actualizarPaso();
                }

            }
        );
    }


    /*
     * RETROCEDER
     */

    if (btnAtras) {

        btnAtras.addEventListener(
            "click",
            function (e) {

                e.preventDefault();


                if (pasoActual > 0) {

                    pasoActual--;

                    actualizarPaso();
                }

            }
        );
    }


    /*
     * INICIAR EN EL PRIMER PASO
     */

    actualizarPaso();
}


configurarPasos();

