document.addEventListener("DOMContentLoaded", () => {
    const formulario_autenticacion = document.getElementById("formulario_autenticacion");
    const campo_contrasenia = formulario_autenticacion.querySelector(".password_contenedor");
    const boton = formulario_autenticacion.querySelector('button[type="submit"]');
    configurarContrasenia(campo_contrasenia);

    formulario_autenticacion.addEventListener("submit", async (e) => {
        e.preventDefault();
        const contenido_original_boton = boton.innerHTML;
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
            const identificador_pestania = document.body.dataset.tabId;

            const formulario = new FormData(formulario_autenticacion);
            formulario.set("tab_id", identificador_pestania);

            const respuesta = await fetch("/inicio_sesion/", {
                method: "POST",
                body: formulario
            });
            const tipo_contenido = respuesta.headers.get("content-type") || "";
            if (!tipo_contenido.includes("application/json")) {
                throw new Error(
                    `El servidor respondió con HTTP ${respuesta.status} en lugar de JSON.`
                );
            }

            let resultado;
            try {
                resultado = await respuesta.json();
            } catch {
                throw new Error("El servidor devolvió una respuesta no válida.");
            }

            if (!respuesta.ok) {
                throw new Error(
                    resultado.descripcion
                    || `No se pudo completar la solicitud (HTTP ${respuesta.status}).`
                );
            }

            if (resultado.estado !== "exito" && resultado.estado !== "incompleto") {
                if (window.Swal) {
                    await window.Swal.fire({
                        title: resultado.title || "No se pudo iniciar sesión",
                        text: resultado.descripcion || "Verifique sus datos e intente nuevamente.",
                        icon: resultado.icon || "error"
                    });
                } else {
                    window.alert(resultado.descripcion || "No se pudo iniciar sesión.");
                }
                return;
            }

            if (window.Swal) {
                window.Swal.close();
            }
            window.vigilanciaReemplazar(resultado.url);
        } catch (error) {
            console.error(error);
            if (window.Swal) {
                window.Swal.close();
                await window.Swal.fire({
                    title: "Error al iniciar sesión",
                    text: error.message
                        || "Ocurrió un error de conexión. Intente nuevamente.",
                    icon: "error"
                });
            } else {
                window.alert(error.message || "Ocurrió un error de conexión. Intente nuevamente.");
            }
        } finally {
            boton.disabled = false;
            boton.innerHTML = contenido_original_boton;
        }
    });
});
