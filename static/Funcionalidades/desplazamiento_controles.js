function configurarFormularioPasos(formulario) {
    if (!formulario) return;

    const contenedor = formulario.closest(".modulo_registro")
        || formulario.closest(".contenedor_campos")
        || formulario.parentElement;

    if (!contenedor) return;

    const pasos = Array.from(formulario.querySelectorAll(".paso"));
    const indicadores = Array.from(contenedor.querySelectorAll(".paso_progreso"));

    const botones_registrar = formulario.querySelectorAll('button[type="submit"]');

    const avance = contenedor.querySelector(".avance");
    const btnSiguiente = contenedor.querySelector(".btn_avanzar");
    const btnAtras = contenedor.querySelector(".btn_retroceder");

    let pasoActual = 0;
    let formulario_validado = false;

    const obtenerPasosVisibles = () => pasos.filter(paso => !paso.hidden);

    function desplazarAlPaso(paso) {
        if (typeof window.desplazarAlPasoCompleto === "function") {
            window.desplazarAlPasoCompleto(paso);
        } else {
            paso.scrollIntoView({ block: "start", behavior: "smooth" });
        }
    }

    function actualizarProgreso() {
        const visibles = indicadores.filter(indicador => !indicador.hidden);

        indicadores.forEach(indicador => indicador.classList.remove("activo"));

        visibles.forEach((indicador, indice) => {
            indicador.classList.toggle("activo", indice <= pasoActual);
        });

        const circulo = visibles[pasoActual]?.querySelector("span");

        if (!avance || !circulo) return;

        const linea = avance.parentElement.getBoundingClientRect();
        const posicion = circulo.getBoundingClientRect();

        avance.style.width = `${pasoActual === visibles.length - 1
            ? linea.width
            : posicion.left + posicion.width / 2 - linea.left
            }px`;
    }

    function actualizarFormulario() {
        const visibles = obtenerPasosVisibles();

        pasoActual = Math.max(0, Math.min(pasoActual, visibles.length - 1));

        pasos.forEach(paso => {
            paso.classList.toggle("activo", paso === visibles[pasoActual]);
        });

        pasos.forEach(paso => {
            paso.querySelectorAll("input, select, textarea").forEach(campo => {
                campo.required =
                    paso === visibles[pasoActual] &&
                    !campo.disabled &&
                    !campo.hidden &&
                    !campo.classList.contains("campo_opcional") &&
                    !["hidden", "button", "submit", "checkbox", "radio"].includes(campo.type);
            });
        });

        btnAtras.style.visibility = pasoActual === 0 ? "hidden" : "visible";

        btnSiguiente.style.display =
            pasoActual === visibles.length - 1 ? "none" : "";

        botones_registrar.forEach(boton => {
            boton.style.display = "none";
        });

        visibles[visibles.length - 1]
            ?.querySelector('button[type="submit"]')
            ?.style.removeProperty("display");

        actualizarProgreso();

        requestAnimationFrame(() => {
            actualizarProgreso();
            desplazarAlPaso(visibles[pasoActual]);
        });
    }

    function evaluarContrasenia(clave) {
        return [
            clave.length >= 5,
            clave.length >= 8,
            /[a-z]/.test(clave),
            /[A-Z]/.test(clave),
            /[0-9]/.test(clave),
            /[^a-zA-Z0-9]/.test(clave)
        ].filter(Boolean).length;
    }

    async function validarPaso() {
        const paso = obtenerPasosVisibles()[pasoActual];

        for (const campo of paso.querySelectorAll("input, select, textarea")) {
            if (
                campo.disabled ||
                campo.hidden ||
                ["hidden", "button", "submit", "checkbox", "radio"].includes(campo.type)
            ) {
                continue;
            }

            while (campo.dataset.validando === "true") {
                await new Promise(resolve => setTimeout(resolve, 50));
            }

            if (!campo.checkValidity()) {
                campo.reportValidity();
                return false;
            }

            if (
                campo.id === "clave" &&
                evaluarContrasenia(campo.value.trim()) <= 2
            ) {
                campo.setCustomValidity(
                    "La contraseña es débil. Debe ser más segura."
                );

                campo.reportValidity();
                return false;
            }
        }

        return true;
    }

    btnSiguiente.addEventListener("click", async evento => {
        evento.preventDefault();

        if (await validarPaso()) {
            pasoActual++;
            actualizarFormulario();
        }
    });

    btnAtras.addEventListener("click", evento => {
        evento.preventDefault();

        pasoActual--;
        actualizarFormulario();
    });

    formulario.addEventListener("submit", async evento => {
        if (formulario_validado) {
            formulario_validado = false;
            return;
        }

        evento.preventDefault();

        for (let indice = 0; indice < obtenerPasosVisibles().length; indice++) {
            pasoActual = indice;
            actualizarFormulario();

            if (!await validarPaso()) return;
        }

        formulario_validado = true;
        formulario.requestSubmit(evento.submitter);
    });

    window.addEventListener("resize", actualizarProgreso);

    function reiniciar() {
        formulario.reset();
        pasoActual = 0;

        actualizarFormulario();
    }

    actualizarFormulario();

    return { reiniciar };
}