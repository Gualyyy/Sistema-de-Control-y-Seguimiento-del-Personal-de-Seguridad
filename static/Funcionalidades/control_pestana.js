(() => {
    const clavePestana = "tab_id";
    const urlInicial = new URL(window.location.href);
    const tabIdServidor = document.body.dataset.tabId;
    let tabId = sessionStorage.getItem(clavePestana)
        || urlInicial.searchParams.get("tab_id")
        || tabIdServidor
        || crypto.randomUUID();

    sessionStorage.setItem(clavePestana, tabId);
    document.body.dataset.tabId = tabId;

    const urlConIdPestana = (valor) => {
        const url = new URL(valor, window.location.href);

        if (url.origin === window.location.origin) {
            url.searchParams.set("tab_id", tabId);
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

    const agregarIdAlEnlace = (enlace) => {
        if (!enlace.href || enlace.origin !== window.location.origin) {
            return;
        }

        const url = new URL(enlace.href);
        if (url.pathname.startsWith("/static/") || url.pathname.startsWith("/media/")) {
            return;
        }

        url.searchParams.set("tab_id", tabId);
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
        campo.value = tabId;
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
        headers.set("X-Tab-ID", tabId);

        return fetchOriginal(recurso, { ...opciones, headers });
    };

    const instanciaPestana = crypto.randomUUID();
    const canalPestanas = "BroadcastChannel" in window
        ? new BroadcastChannel("vigilancia-pestanas")
        : null;
    const instanciasConMismoId = new Set([instanciaPestana]);

    if (canalPestanas) {
        canalPestanas.addEventListener("message", (evento) => {
            if (evento.data?.tab_id !== tabId) {
                return;
            }

            if (evento.data.tipo === "consulta") {
                instanciasConMismoId.add(evento.data.instancia);
                canalPestanas.postMessage({
                    tipo: "respuesta",
                    tab_id: tabId,
                    instancia: instanciaPestana
                });
            } else if (evento.data.tipo === "respuesta") {
                instanciasConMismoId.add(evento.data.instancia);
            }
        });

        canalPestanas.postMessage({
            tipo: "consulta",
            tab_id: tabId,
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

            tabId = crypto.randomUUID();
            sessionStorage.setItem(clavePestana, tabId);
            urlInicial.searchParams.set("tab_id", tabId);
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
