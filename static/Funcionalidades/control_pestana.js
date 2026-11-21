(() => {
    const generarIdentificador = () => {
        if (window.crypto && typeof window.crypto.randomUUID === "function") {
            return window.crypto.randomUUID();
        }

        return `tab-${Date.now()}-${Math.random().toString(36).slice(2)}${Math.random().toString(36).slice(2)}`;
    };

    window.vigilanciaGenerarIdentificador = generarIdentificador;

    const urlInicial = new URL(window.location.href);
    const tabIdServidor = document.body.dataset.tabId;
    const claveIdentificadorPestania = "vigilancia-tab-id";
    const claveUrlRecuperacion = "vigilancia-recovery-url";
    const recuperacionActiva =
        document.body.dataset.recoveryActive === "true";
    const rutasRecuperacion = new Set([
        "/enviar_codigo/",
        "/reenviar_codigo/",
        "/vigencia_codigo/",
        "/correos_usuario/",
        "/verificar_codigo/",
        "/enviar_usuario/",
        "/menu_recuperar_credenciales/",
        "/cambiar_contrasenia/",
        "/recuperar_nombre_usuario/"
    ]);
    const esRutaRecuperacion = rutasRecuperacion.has(urlInicial.pathname);
    const esPaginaNoEncontrada =
        document.body.classList.contains("body-404");
    let rutaRecuperacionGuardada = null;
    const identificadorInicial = urlInicial.searchParams.get("tab_id")
        || tabIdServidor
        || generarIdentificador();
    let identificadorGuardado = null;
    let sessionStorageDisponible = true;

    try {
        identificadorGuardado = sessionStorage.getItem(
            claveIdentificadorPestania
        );
        rutaRecuperacionGuardada = sessionStorage.getItem(
            claveUrlRecuperacion
        );
    } catch {
        sessionStorageDisponible = false;
    }

    let identificador_pestania = identificadorInicial;

    if (
        sessionStorageDisponible &&
        identificadorGuardado &&
        identificadorGuardado !== identificadorInicial &&
        (
            esRutaRecuperacion ||
            (
                esPaginaNoEncontrada &&
                rutasRecuperacion.has(rutaRecuperacionGuardada)
            )
        )
    ) {
        const urlRestaurada = new URL(urlInicial.href);

        if (esPaginaNoEncontrada) {
            urlRestaurada.pathname = rutaRecuperacionGuardada;
        }

        urlRestaurada.searchParams.set(
            "tab_id",
            identificadorGuardado
        );
        window.location.replace(urlRestaurada.href);
        return;
    }

    if (
        recuperacionActiva &&
        sessionStorageDisponible &&
        (
            !identificadorGuardado ||
            identificadorGuardado !== identificadorInicial
        )
    ) {
        try {
            const nuevoIdentificador = generarIdentificador();
            sessionStorage.setItem(
                claveIdentificadorPestania,
                nuevoIdentificador
            );
            identificador_pestania = nuevoIdentificador;

            const urlInicioRecuperacion = new URL(
                "/buscar_usuario/",
                window.location.origin
            );
            urlInicioRecuperacion.searchParams.set(
                "tab_id",
                identificador_pestania
            );
            window.location.replace(urlInicioRecuperacion.href);
            return;
        } catch {
            sessionStorageDisponible = false;
        }
    }

    if (sessionStorageDisponible) {
        try {
            sessionStorage.setItem(
                claveIdentificadorPestania,
                identificador_pestania
            );
            if (recuperacionActiva && esRutaRecuperacion) {
                sessionStorage.setItem(
                    claveUrlRecuperacion,
                    urlInicial.pathname
                );
            } else if (!recuperacionActiva && !esPaginaNoEncontrada) {
                sessionStorage.removeItem(claveUrlRecuperacion);
            }
        } catch {
            sessionStorageDisponible = false;
        }
    }

    document.body.dataset.tabId = identificador_pestania;

    const urlConIdPestana = (valor) => {
        const url = new URL(valor, window.location.href);

        if (url.origin === window.location.origin) {
            url.searchParams.set("tab_id", identificador_pestania);
        }

        return url.href;
    };

    window.vigilanciaUrlConPestana = urlConIdPestana;

    window.vigilanciaNavegar = (valor) => {
        window.location.assign(urlConIdPestana(valor));
    };

    window.vigilanciaReemplazar = (valor) => {
        window.location.replace(urlConIdPestana(valor));
    };

    if (urlInicial.origin === window.location.origin) {
        const urlActualizada = urlConIdPestana(urlInicial.href);
        if (urlActualizada !== urlInicial.href) {
            window.history.replaceState(null, "", urlActualizada);
        }
    }

    if (document.body.dataset.recoveryStep === "verificacion") {
        const estadoBloqueoRecuperacion = {
            bloqueoRecuperacion: true
        };
        window.history.pushState(
            estadoBloqueoRecuperacion,
            "",
            window.location.href
        );
        window.addEventListener("popstate", () => {
            window.history.pushState(
                estadoBloqueoRecuperacion,
                "",
                window.location.href
            );
        });
    }

    const agregarIdAlEnlace = (enlace) => {
        if (!enlace.href || enlace.origin !== window.location.origin) {
            return;
        }

        const url = new URL(enlace.href);
        if (url.pathname.startsWith("/static/") || url.pathname.startsWith("/media/")) {
            return;
        }

        url.searchParams.set("tab_id", identificador_pestania);
        enlace.href = url.href;
    };

    document.querySelectorAll("a[href]").forEach(agregarIdAlEnlace);
    document.addEventListener("click", (evento) => {
        const enlace = evento.target.closest("a[href]");
        if (enlace) {
            agregarIdAlEnlace(enlace);
        }
    }, true);

    const agregarIdAlFormulario = (formulario) => {
        const accion = new URL(formulario.action || window.location.href);
        if (accion.origin !== window.location.origin) {
            return;
        }

        let campo = formulario.querySelector('input[name="tab_id"]');
        if (!campo) {
            campo = document.createElement("input");
            campo.type = "hidden";
            campo.name = "tab_id";
            formulario.append(campo);
        }
        campo.value = identificador_pestania;
    };

    document.querySelectorAll("form").forEach(agregarIdAlFormulario);
    document.addEventListener("submit", (evento) => {
        agregarIdAlFormulario(evento.target);
    }, true);

    const fetchOriginal = window.fetch.bind(window);
    window.fetch = (recurso, opciones = {}) => {
        const url = new URL(
            recurso instanceof Request ? recurso.url : recurso,
            window.location.href
        );

        if (url.origin !== window.location.origin) {
            return fetchOriginal(recurso, opciones);
        }

        const headers = new Headers(
            opciones.headers || (recurso instanceof Request ? recurso.headers : undefined)
        );
        headers.set("X-Tab-ID", identificador_pestania);

        return fetchOriginal(recurso, { ...opciones, headers });
    };

    const instanciaPestana = generarIdentificador();
    const canalPestanas = "BroadcastChannel" in window
        ? new BroadcastChannel("vigilancia-pestanas")
        : null;
    const instanciasConMismoId = new Set([instanciaPestana]);

    if (canalPestanas) {
        canalPestanas.addEventListener("message", (evento) => {
            if (evento.data?.tab_id !== identificador_pestania) {
                return;
            }

            if (evento.data.tipo === "consulta") {
                instanciasConMismoId.add(evento.data.instancia);
                canalPestanas.postMessage({
                    tipo: "respuesta",
                    tab_id: identificador_pestania,
                    instancia: instanciaPestana
                });
            } else if (evento.data.tipo === "respuesta") {
                instanciasConMismoId.add(evento.data.instancia);
            }
        });

        canalPestanas.postMessage({
            tipo: "consulta",
            tab_id: identificador_pestania,
            instancia: instanciaPestana
        });

        window.setTimeout(() => {
            if (instanciasConMismoId.size < 2) {
                return;
            }

            const instanciaPrincipal = [...instanciasConMismoId].sort()[0];
            if (instanciaPestana === instanciaPrincipal) {
                return;
            }

            identificador_pestania = generarIdentificador();
            if (sessionStorageDisponible) {
                try {
                    sessionStorage.setItem(
                        claveIdentificadorPestania,
                        identificador_pestania
                    );
                } catch {
                    sessionStorageDisponible = false;
                }
            }

            if (recuperacionActiva) {
                const urlInicioRecuperacion = new URL(
                    "/buscar_usuario/",
                    window.location.origin
                );
                urlInicioRecuperacion.searchParams.set(
                    "tab_id",
                    identificador_pestania
                );
                window.location.replace(urlInicioRecuperacion.href);
                return;
            }

            urlInicial.searchParams.set("tab_id", identificador_pestania);
            window.location.replace(urlInicial.href);
        }, 150);
    }

    window.addEventListener("pagehide", () => {
        if (canalPestanas) {
            canalPestanas.close();
        }
    });

    window.addEventListener("pageshow", (evento) => {
        if (evento.persisted) {
            window.location.reload();
        }
    });

    const usuario = document.body.dataset.sessionUser;
    if (!usuario || document.body.classList.contains("body-404")) {
        return;
    }

    const duracionInactividad = 60 * 60 * 1000;
    let temporizadorInactividad;
    let ultimaActividad = Date.now();

    const verificarInactividad = () => {
        const tiempoRestante = duracionInactividad - (Date.now() - ultimaActividad);

        if (tiempoRestante <= 0) {
            window.vigilanciaNavegar("/cerrar_sesion/");
            return;
        }

        window.clearTimeout(temporizadorInactividad);
        temporizadorInactividad = window.setTimeout(verificarInactividad, tiempoRestante);
    };

    const registrarActividad = () => {
        ultimaActividad = Date.now();
        verificarInactividad();
    };

    ["pointerdown", "keydown", "scroll", "touchstart", "click"].forEach((evento) => {
        document.addEventListener(evento, registrarActividad, { passive: true });
    });

    document.addEventListener("visibilitychange", () => {
        if (document.visibilityState === "visible") {
            verificarInactividad();
        }
    });

    verificarInactividad();
})();
