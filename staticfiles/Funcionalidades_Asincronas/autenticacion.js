document.addEventListener("DOMContentLoaded", () => {

    const formulario_autenticacion = document.getElementById(
        "formulario_autenticacion"
    );

    formulario_autenticacion.addEventListener("submit", async (e) => {
        e.preventDefault();

        try {
            const formulario = new FormData(
                formulario_autenticacion
            );

            // Identificador único de esta pestaña
            let tab_id = sessionStorage.getItem("tab_id");

            if (!tab_id) {
                tab_id = crypto.randomUUID();
                sessionStorage.setItem("tab_id", tab_id);
            }

            // Enviar el identificador de la pestaña
            formulario.append("tab_id", tab_id);

            Swal.fire({
                title: "Iniciando sesión...",
                html: "Espere un momento por favor.",
                allowOutsideClick: false,
                allowEscapeKey: false,
                didOpen: () => {
                    Swal.showLoading();
                }
            });

            const respuesta = await fetch("", {
                method: "POST",
                body: formulario
            });

            const resultado = await respuesta.json();

            console.log(resultado);

            if (
                resultado.estado == "exito" ||
                resultado.estado == "incompleto"
            ) {
                sessionStorage.removeItem("tab_bloqueada");
                window.location.href = resultado.url;
                return;
            }

            Swal.fire({
                title: resultado.title,
                text: resultado.descripcion,
                icon: resultado.icon
            });

            formulario_autenticacion.reset();

        } catch (error) {

            console.error(error);

            Swal.fire({
                title: "Error",
                text: "Ocurrió un error al intentar iniciar sesión.",
                icon: "error"
            });
        }
    });

});
