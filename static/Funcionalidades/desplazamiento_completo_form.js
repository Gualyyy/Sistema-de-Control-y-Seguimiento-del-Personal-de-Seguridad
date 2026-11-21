
function configurarDesplazamientoPasos(formulario) {
    if (!formulario) return;

    const contenedor = formulario.closest(".modulo_registro")
        || formulario.closest(".contenedor_campos")
        || formulario.parentElement;

    if (!contenedor) return;

    const pasos = Array.from(formulario.querySelectorAll(".paso"));
    const indicadores = Array.from(
        contenedor.querySelectorAll(".paso_progreso")
    );

    const btnSiguiente = contenedor.querySelector(".btn_avanzar");
    const btnAtras = contenedor.querySelector(".btn_retroceder");

    const botonesRegistrar = Array.from(
        formulario.querySelectorAll('button[type="submit"]')
    );

    const avance = contenedor.querySelector(".avance");

    if (!pasos.length) return;

    const radiosPerfiles = formulario.querySelectorAll(
        'input[name="perfil"]'
    );

    const perfilesConDatosCompletos = [
        "vigilante",
        "despachador",
        "personal_limpieza"
    ];

    const camposBloqueados = new WeakMap();

    pasos.forEach(paso => {
        paso.querySelectorAll("input, select, textarea").forEach(campo => {
            camposBloqueados.set(campo, campo.disabled);
        });
    });

    let pasoActual = 0;

    function obtenerPasosVisibles() {
        return pasos.filter(paso => !paso.hidden);
    }

    function obtenerMensajeAdvertencia(campo) {
        const descripcion = campo.getAttribute("aria-describedby");

        if (descripcion) {
            const elementos = descripcion
                .split(/\s+/)
                .map(id => document.getElementById(id))
                .filter(Boolean);

            const mensaje = elementos
                .map(elemento => elemento.textContent.trim())
                .find(texto => texto);

            if (mensaje) return mensaje;
        }

        const grupo = campo.closest(
            ".grupo_campo, .campo_formulario, .contenedor_campo, .campo"
        ) || campo.parentElement;

        const elementoMensaje = grupo?.querySelector(
            ".mensaje-feedback.error, .mensaje-validacion.error, .mensaje-error"
        );

        return elementoMensaje?.textContent.trim() || "";
    }

    function mostrarAdvertencia(campo, mensaje) {
        campo.setCustomValidity(
            mensaje || "Debe corregir este campo antes de continuar."
        );

        campo.reportValidity();
        campo.focus();

        return false;
    }

    function obtenerCamposDelPaso(paso) {
        return Array.from(
            paso.querySelectorAll("input, select, textarea")
        ).filter(campo => {
            return !campo.disabled
                && campo.type !== "hidden"
                && campo.offsetParent !== null;
        });
    }

    function validarPaso(paso) {
        const campos = obtenerCamposDelPaso(paso);

        for (const campo of campos) {
            const esOpcional = campo.classList.contains("campo_opcional");

            // Esperar a que terminen las validaciones asíncronas.
            if (campo.dataset.validando === "true") {
                return mostrarAdvertencia(
                    campo,
                    "Espere mientras se verifica la información de este campo."
                );
            }

            // Comprobar advertencias de cédula, correo y teléfono.
            const tieneAdvertencia =
                campo.classList.contains("is-invalid")
                || campo.getAttribute("aria-invalid") === "true";

            if (tieneAdvertencia) {
                return mostrarAdvertencia(
                    campo,
                    campo.validationMessage
                    || obtenerMensajeAdvertencia(campo)
                );
            }

            // Comprobar validaciones HTML y setCustomValidity().
            if (!campo.checkValidity()) {
                campo.reportValidity();
                campo.focus();
                return false;
            }

            // Los campos opcionales pueden permanecer vacíos.
            if (esOpcional) {
                continue;
            }

            // Comprobar campos obligatorios vacíos.
            if (
                campo.type !== "checkbox"
                && campo.type !== "radio"
                && !campo.value.trim()
            ) {
                return mostrarAdvertencia(
                    campo,
                    "Este campo es obligatorio."
                );
            }
        }

        return true;
    }

    function actualizarVisibilidadPasos() {
        const perfilSeleccionado = formulario.querySelector(
            'input[name="perfil"]:checked'
        );

        const mostrarDatosCompletos = perfilesConDatosCompletos.includes(
            perfilSeleccionado?.value
        );

        [3, 4].forEach(indice => {
            const paso = pasos[indice];
            const indicador = indicadores[indice];

            if (!paso) return;

            paso.hidden = !mostrarDatosCompletos;

            if (indicador) {
                indicador.hidden = !mostrarDatosCompletos;
            }

            paso.querySelectorAll("input, select, textarea").forEach(campo => {
                campo.disabled = mostrarDatosCompletos
                    ? camposBloqueados.get(campo)
                    : true;
            });
        });

        actualizarFormulario();
    }

    function desplazarAlPaso() {
        const pasosVisibles = obtenerPasosVisibles();
        const paso = pasosVisibles[pasoActual];

        if (!paso) return;

        requestAnimationFrame(() => {
            if (typeof window.desplazarAlPasoCompleto === "function") {
                window.desplazarAlPasoCompleto(paso);
            } else {
                paso.scrollIntoView({
                    behavior: "smooth",
                    block: "start"
                });
            }
        });
    }

    function actualizarProgreso() {
        const indicadoresVisibles = indicadores.filter(
            indicador => !indicador.hidden
        );

        indicadores.forEach(indicador => {
            indicador.classList.remove("activo");
        });

        indicadoresVisibles.forEach((indicador, indice) => {
            indicador.classList.toggle(
                "activo",
                indice <= pasoActual
            );
        });

        const circulo = indicadoresVisibles[pasoActual]?.querySelector("span");

        if (!avance || !circulo) return;

        const linea = avance.parentElement.getBoundingClientRect();
        const posicion = circulo.getBoundingClientRect();

        avance.style.width = `${pasoActual === indicadoresVisibles.length - 1
            ? linea.width
            : posicion.left + posicion.width / 2 - linea.left
            }px`;
    }

    function actualizarFormulario() {
        const pasosVisibles = obtenerPasosVisibles();
        const ultimoPaso = pasosVisibles.length - 1;

        pasoActual = Math.max(
            0,
            Math.min(pasoActual, ultimoPaso)
        );

        pasos.forEach(paso => {
            paso.classList.toggle(
                "activo",
                paso === pasosVisibles[pasoActual]
            );
        });

        if (btnAtras) {
            btnAtras.style.visibility =
                pasoActual === 0 ? "hidden" : "visible";
        }

        if (btnSiguiente) {
            btnSiguiente.style.display =
                pasoActual === ultimoPaso ? "none" : "";
        }

        botonesRegistrar.forEach(boton => {
            boton.style.display = "none";
        });

        const botonFinal = pasosVisibles[ultimoPaso]?.querySelector(
            'button[type="submit"]'
        );

        if (botonFinal) {
            botonFinal.style.display = "";
        }

        actualizarProgreso();
        desplazarAlPaso();
    }

    btnSiguiente?.addEventListener("click", evento => {
        evento.preventDefault();

        const pasosVisibles = obtenerPasosVisibles();
        const paso = pasosVisibles[pasoActual];

        if (!paso || !validarPaso(paso)) {
            return;
        }

        if (pasoActual < pasosVisibles.length - 1) {
            pasoActual++;
            actualizarFormulario();
        }
    });

    btnAtras?.addEventListener("click", evento => {
        evento.preventDefault();

        if (pasoActual > 0) {
            pasoActual--;
            actualizarFormulario();
        }
    });

    radiosPerfiles.forEach(radio => {
        radio.addEventListener("change", actualizarVisibilidadPasos);
    });

    formulario.addEventListener("submit", evento => {
        const pasosVisibles = obtenerPasosVisibles();

        for (const paso of pasosVisibles) {
            if (!validarPaso(paso)) {
                evento.preventDefault();

                pasoActual = pasosVisibles.indexOf(paso);
                actualizarFormulario();

                // Localizar el campo que presenta la advertencia.
                const campoInvalido = obtenerCamposDelPaso(paso).find(
                    campo =>
                        campo.dataset.validando === "true"
                        || campo.classList.contains("is-invalid")
                        || campo.getAttribute("aria-invalid") === "true"
                        || !campo.checkValidity()
                        || (
                            !campo.classList.contains("campo_opcional")
                            && campo.type !== "checkbox"
                            && campo.type !== "radio"
                            && !campo.value.trim()
                        )
                );

                campoInvalido?.focus();

                return;
            }
        }
    });

    window.addEventListener("resize", actualizarProgreso);

    function reiniciar() {
        pasoActual = 0;
        actualizarVisibilidadPasos();
    }

    actualizarVisibilidadPasos();

    return { reiniciar };
}
