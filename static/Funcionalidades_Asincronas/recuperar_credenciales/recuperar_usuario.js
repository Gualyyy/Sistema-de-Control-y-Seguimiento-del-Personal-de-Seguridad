document.addEventListener("DOMContentLoaded", () => {

    const btn_recuperar_usuario = document.getElementById(
        "btn_recuperar_usuario"
    );

    if (!btn_recuperar_usuario) {
        return;
    }

    btn_recuperar_usuario.addEventListener("click", async (e) => {
        e.preventDefault();

        if (btn_recuperar_usuario.dataset.procesando === "true") {
            return;
        }

        btn_recuperar_usuario.dataset.procesando = "true";

        try {
            const token = document.querySelector(
                "[name=csrfmiddlewaretoken]"
            )?.value || "";

            const respuesta = await fetch("/enviar_usuario/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": token,
                    "X-Requested-With": "XMLHttpRequest"
                }
            });

            const tipoContenido = respuesta.headers.get("Content-Type") || "";
            if (!tipoContenido.includes("application/json")) {
                console.error(
                    "El servidor devolvió una respuesta no JSON.",
                    respuesta.status,
                    respuesta.url
                );
                await Swal.fire({
                    title: "Respuesta inesperada",
                    text: (
                        "Actualice el módulo e inténtelo nuevamente."
                    ),
                    icon: "error"
                });
                return;
            }

            const resultado = await respuesta.json();

            await Swal.fire({
                title: resultado.title,
                text: resultado.descripcion,
                icon: resultado.icon
            });

            if (resultado.estado === "exito" && resultado.url) {
                window.vigilanciaReemplazar(resultado.url);
            }

        } catch (error) {
            console.error(error);

            await Swal.fire({
                title: "Error de conexión",
                text: "No fue posible completar la solicitud.",
                icon: "error"
            });

        } finally {
            btn_recuperar_usuario.dataset.procesando = "false";
        }
    });

});