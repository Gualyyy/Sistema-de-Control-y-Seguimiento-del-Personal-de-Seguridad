document.addEventListener("DOMContentLoaded", () => {
    const formulario = document.getElementById("formulario_autenticacion");
    const boton = formulario.querySelector('button[type="submit"]');

    const campo_contrasenia = formulario.querySelector(".password_contenedor");
    configurarContrasenia(campo_contrasenia);

    const inicializarAutenticacion = () => {
        const textoBoton = boton.textContent;

        const mostrarMensaje = (
            texto,
            tipo = "error",
            titulo = tipo === "warning" ? "Aviso" : "No se pudo iniciar sesión"
        ) => {
            if (window.Swal) {
                window.Swal.fire({
                    title: titulo,
                    text: texto,
                    icon: tipo
                });
                return;
            }

            window.alert(texto);
        };

        formulario.addEventListener("submit", async (evento) => {
            evento.preventDefault();
            boton.disabled = true;
            boton.textContent = "Validando...";

            if (window.Swal) {
                window.Swal.fire({
                    title: "Iniciando sesión...",
                    html: "Espere un momento por favor.",
                    allowOutsideClick: false,
                    allowEscapeKey: false,
                    didOpen: () => window.Swal.showLoading()
                });
            }

            try {
                const datosFormulario = new FormData(formulario);
                let tabId = sessionStorage.getItem("tab_id");

                if (!tabId) {
                    tabId = crypto.randomUUID();
                    sessionStorage.setItem("tab_id", tabId);
                }

                datosFormulario.set("tab_id", tabId);

                const respuesta = await fetch("", {
                    method: "POST",
                    body: datosFormulario
                });
                const tipoContenido = respuesta.headers.get("content-type") || "";

                if (!tipoContenido.includes("application/json")) {
                    throw new Error(`El servidor respondió con HTTP ${respuesta.status}.`);
                }

                const resultado = await respuesta.json();

                if (!respuesta.ok) {
                    throw new Error(resultado.descripcion || `Error HTTP ${respuesta.status}.`);
                }

                if (resultado.estado === "exito" || resultado.estado === "incompleto") {
                    if (window.Swal) {
                        window.Swal.close();
                    }
                    window.vigilanciaReemplazar(resultado.url);
                    return;
                }

                const descripcion = resultado.descripcion || "No se pudo iniciar sesión.";
                mostrarMensaje(
                    descripcion,
                    resultado.icon || "error",
                    resultado.title || "No se pudo iniciar sesión"
                );
            } catch (error) {
                const descripcion = error.message || "Error de conexión al iniciar sesión.";
                mostrarMensaje(descripcion, "error", "Error al iniciar sesión");
            } finally {
                boton.disabled = false;
                boton.textContent = textoBoton;
            }
        });
    };

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", inicializarAutenticacion, { once: true });
    } else {
        inicializarAutenticacion();
    }
});
