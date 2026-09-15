(() => {
    const clavePestana = "tab_id";

    if (document.getElementById("formulario_autenticacion")) {
        return;
    }

    const usuario = document.body.dataset.sessionUser;

    if (!usuario) {
        return;
    }

    const claveBloqueo = `vigilancia-panel-${usuario}`;
    const duracionBloqueo = 15000;

    let identificadorPestana = sessionStorage.getItem(clavePestana);

    if (!identificadorPestana) {
        identificadorPestana = crypto.randomUUID();
        sessionStorage.setItem(clavePestana, identificadorPestana);
    }

    let navegando = false;

    const leerBloqueo = () => {
        try {
            return JSON.parse(localStorage.getItem(claveBloqueo));
        } catch {
            return null;
        }
    };

    const bloquearPestana = () => {
        sessionStorage.setItem("tab_bloqueada", "1");
        sessionStorage.removeItem(clavePestana);

        document.body.innerHTML = "";

        window.location.replace("/");
    };

    const verificarBloqueo = () => {
        const bloqueo = leerBloqueo();

        if (
            bloqueo &&
            bloqueo.pestana !== identificadorPestana &&
            bloqueo.expira > Date.now()
        ) {
            bloquearPestana();
            return false;
        }

        return true;
    };

    if (!verificarBloqueo()) {
        return;
    }

    const renovarBloqueo = () => {
        const bloqueo = leerBloqueo();

        if (
            bloqueo &&
            bloqueo.pestana !== identificadorPestana &&
            bloqueo.expira > Date.now()
        ) {
            bloquearPestana();
            return;
        }

        localStorage.setItem(
            claveBloqueo,
            JSON.stringify({
                pestana: identificadorPestana,
                expira: Date.now() + duracionBloqueo
            })
        );
    };

    renovarBloqueo();

    const intervalo = window.setInterval(() => {
        if (!verificarBloqueo()) {
            window.clearInterval(intervalo);
            return;
        }

        renovarBloqueo();
    }, 5000);

    window.addEventListener("storage", (evento) => {
        if (evento.key !== claveBloqueo) {
            return;
        }

        if (!verificarBloqueo()) {
            window.clearInterval(intervalo);
        }
    });

    document.querySelectorAll('a[href*="cerrar_sesion"]').forEach((enlace) => {
        enlace.addEventListener("click", () => {
            navegando = true;

            const bloqueo = leerBloqueo();

            if (
                bloqueo &&
                bloqueo.pestana === identificadorPestana
            ) {
                localStorage.removeItem(claveBloqueo);
            }

            window.clearInterval(intervalo);
        });
    });

    document.querySelectorAll("a").forEach((enlace) => {
        enlace.addEventListener("click", () => {
            navegando = true;
        });
    });

    document.querySelectorAll("form").forEach((formulario) => {
        formulario.addEventListener("submit", () => {
            navegando = true;
        });
    });

    window.addEventListener("beforeunload", () => {
        if (!navegando) {
            const bloqueo = leerBloqueo();

            if (
                bloqueo &&
                bloqueo.pestana === identificadorPestana
            ) {
                localStorage.removeItem(claveBloqueo);
            }
        }

        window.clearInterval(intervalo);
    });
})();