function configurarFormularioPasos(formulario) {
    if (!formulario) return;

    const contenedor = formulario.closest(".contenedor_campos") || formulario.parentElement;
    if (!contenedor) return;

    const pasos = formulario.querySelectorAll(".paso");
    const indicadores = contenedor.querySelectorAll(".paso_progreso");
    const avance = contenedor.querySelector(".avance");

    // CORRECCIÓN AQUÍ: Se actualizaron los selectores para coincidir con tu HTML
    const btnSiguiente = contenedor.querySelector(".btn_avanzar");
    const btnAtras = contenedor.querySelector(".btn_retroceder");
    const btnSubmit = formulario.querySelector(".btn_registro");

    if (!pasos.length) return;

    let pasoActual = 0;

    function actualizarRequired() {
        pasos.forEach((paso, indice) => {
            const campos = paso.querySelectorAll("input, select, textarea");

            campos.forEach(campo => {
                if (
                    campo.hidden ||
                    campo.classList.contains("campo_opcional") ||
                    ["checkbox", "hidden", "button", "submit"].includes(campo.type)
                ) {
                    campo.removeAttribute("required");
                    return;
                }

                if (indice === pasoActual) {
                    campo.setAttribute("required", "");
                } else {
                    campo.removeAttribute("required");
                }
            });
        });
    }

    function desplazarAlPaso() {
        const paso = pasos[pasoActual];
        if (!paso) return;

        const contenedorScroll = formulario.closest(".contenedor_datos_contenido");

        if (contenedorScroll) {
            const pasoRect = paso.getBoundingClientRect();
            const contenedorRect = contenedorScroll.getBoundingClientRect();
            const posicion = contenedorScroll.scrollTop + pasoRect.top - contenedorRect.top - 10;

            contenedorScroll.scrollTo({
                top: Math.max(0, posicion),
                behavior: "smooth"
            });
            return;
        }

        if (contenedor.scrollHeight > contenedor.clientHeight) {
            const pasoRect = paso.getBoundingClientRect();
            const contenedorRect = contenedor.getBoundingClientRect();
            const posicion = contenedor.scrollTop + pasoRect.top - contenedorRect.top - 10;

            contenedor.scrollTo({
                top: Math.max(0, posicion),
                behavior: "smooth"
            });
            return;
        }

        const posicion = paso.getBoundingClientRect().top + window.scrollY - 20;
        window.scrollTo({
            top: Math.max(0, posicion),
            behavior: "smooth"
        });
    }

    function actualizarFormulario() {
        pasoActual = Math.max(0, Math.min(pasoActual, pasos.length - 1));

        pasos.forEach((paso, indice) => {
            paso.classList.toggle("activo", indice === pasoActual);
        });

        actualizarRequired();

        indicadores.forEach((indicador, indice) => {
            indicador.classList.toggle("activo", indice <= pasoActual);
        });

        if (avance && indicadores.length) {
            const linea = avance.parentElement;
            const circuloActual = indicadores[pasoActual].querySelector("span");

            if (circuloActual) {
                const lineaRect = linea.getBoundingClientRect();
                const actualRect = circuloActual.getBoundingClientRect();
                let fin = (pasoActual === pasos.length - 1)
                    ? lineaRect.width
                    : actualRect.right - lineaRect.left;

                avance.style.left = "0px";
                avance.style.width = `${fin}px`;
            }
        }

        // Visibilidad de botones según paso
        if (btnAtras) {
            btnAtras.style.visibility = pasoActual === 0 ? "hidden" : "visible";
        }

        if (btnSiguiente) {
            const ultimo = pasoActual === pasos.length - 1;
            btnSiguiente.style.display = ultimo ? "none" : "inline-block";
        }

        requestAnimationFrame(() => {
            desplazarAlPaso();
        });
    }

    function evaluarContrasenia(contraseña) {
        let puntos = 0;
        if (contraseña.length >= 5) puntos++;
        if (contraseña.length >= 8) puntos++;
        if (/[a-z]/.test(contraseña)) puntos++;
        if (/[A-Z]/.test(contraseña)) puntos++;
        if (/[0-9]/.test(contraseña)) puntos++;
        if (/[^a-zA-Z0-9]/.test(contraseña)) puntos++;
        return puntos;
    }

    function validarPaso() {
        const paso = pasos[pasoActual];

        if (!paso) return true;

        const campos = paso.querySelectorAll("input, select, textarea");

        for (const campo of campos) {
            if (
                campo.disabled ||
                campo.hidden ||
                ["hidden", "button", "submit", "checkbox"].includes(campo.type)
            ) {
                continue;
            }

            if (campo.checkValidity()) {
                campo.setCustomValidity("");
            }

            if (campo.id === "clave") {
                const clave = campo.value.trim();

                if (!clave && campo.classList.contains("campo_opcional")) {
                    campo.setCustomValidity("");
                    continue;
                }

                const puntos = evaluarContrasenia(clave);

                if (!clave) {
                    campo.setCustomValidity(
                        "Debe ingresar una contraseña."
                    );
                    campo.reportValidity();
                    return false;
                }

                if (puntos <= 2) {
                    campo.setCustomValidity(
                        "La contraseña es débil. Debe ser más segura."
                    );
                    campo.reportValidity();
                    return false;
                }
            }

            if (!campo.checkValidity()) {
                campo.reportValidity();
                return false;
            }
        }

        return true;
    }

    // EVENTOS DE NAVEGACIÓN
    if (btnSiguiente) {
        btnSiguiente.addEventListener("click", function (evento) {
            evento.preventDefault();

            if (!validarPaso()) {
                return;
            }
            if (pasoActual < pasos.length - 1) {
                pasoActual++;
                actualizarFormulario();
            }
        });
    }

    if (btnAtras) {
        btnAtras.addEventListener("click", function (evento) {
            evento.preventDefault();

            if (pasoActual > 0) {
                pasoActual--;
                actualizarFormulario();
            }
        });
    }

    // Manejo opcional del submit en el paso final
    formulario.addEventListener("submit", function (evento) {
        if (!validarPaso()) {
            evento.preventDefault();
        }
    });

    function reiniciar() {
        formulario.reset();
        pasoActual = 0;
        actualizarFormulario();
    }

    actualizarFormulario();

    return { reiniciar };
}