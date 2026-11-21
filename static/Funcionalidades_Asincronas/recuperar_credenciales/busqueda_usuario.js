document.addEventListener("DOMContentLoaded", () => {

    const formulario_busqueda = document.getElementById("formulario_busqueda");

    const select_nacionalidad = document.getElementById("nacionalidad");
    const input_cedula_identidad = document.getElementById("cedula_identidad");

    const dialogo_correos_usuario = document.getElementById("correos_usuario");
    const formulario_seleccion = document.getElementById("formulario_seleccion");

    const input_radius_correo_principal = document.getElementById("correo_principal");
    const label_nombre_principal = document.getElementById("nombre_principal");

    const input_radius_correo_secundario = document.getElementById("correo_secundario");
    const label_nombre_secundario = document.getElementById("nombre_secundario");

    configurarCedula(input_cedula_identidad, select_nacionalidad);

    formulario_busqueda.addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
            const formulario = new FormData(formulario_busqueda);

            const respuesta = await fetch("/buscar_usuario/", {
                method: "POST",
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            await Swal.fire({
                title: resultado.title,
                text: resultado.descripcion,
                icon: resultado.icon
            });

            if (resultado.estado == "exito") {
                const correos_cargados = await correos_usuario();
                if (correos_cargados) {
                    dialogo_correos_usuario.showModal();
                }
            }

            formulario_busqueda.reset();
        } catch (error) {
            console.error(error);
        }
    });

    async function correos_usuario() {
        try {
            const respuesta = await fetch("/correos_usuario/");
            const resultado = await respuesta.json();

            if (resultado.estado !== "exito") {
                mostrar_mensaje_dialogo(
                    "contenedor_mensajes_seleccion",
                    resultado.notificacion,
                    resultado.tipo
                );
                return false;
            }

            input_radius_correo_principal.value = resultado.correo_principal;
            label_nombre_principal.textContent = resultado.correo_principal;

            input_radius_correo_secundario.disabled = true;
            input_radius_correo_secundario.checked = false;
            input_radius_correo_secundario.value = "";
            label_nombre_secundario.textContent = "Correo secundario no disponible";

            const correo_secundario = resultado.correo_secundario?.trim();

            if (correo_secundario && correo_secundario !== "N/A") {
                input_radius_correo_secundario.value = correo_secundario;
                label_nombre_secundario.textContent = correo_secundario;
                input_radius_correo_secundario.disabled = false;
            }

            ocultar_mensaje_dialogo("contenedor_mensajes_seleccion");

            return true;

        } catch (error) {
            console.error(error);

            mostrar_mensaje_dialogo(
                "contenedor_mensajes_seleccion",
                "Ocurrió un error al consultar los correos electrónicos.",
                "error"
            );

            return false;
        }
    }

    formulario_seleccion.addEventListener("submit", async (e) => {
        e.preventDefault();

        const boton = formulario_seleccion.querySelector(
            'button[type="submit"]'
        );

        try {
            if (boton) {
                boton.disabled = true;
            }

            mostrar_mensaje_dialogo(
                "contenedor_mensajes_seleccion",
                "Enviando código de verificación...",
                "cargando"
            );

            const formulario = new FormData(formulario_seleccion);

            const respuesta = await fetch("/enviar_codigo/", {
                method: "POST",
                body: formulario
            });
            const resultado = await respuesta.json();

            if (!respuesta.ok || resultado.estado !== "exito") {
                mostrar_mensaje_dialogo(
                    "contenedor_mensajes_seleccion",
                    resultado.descripcion || "No fue posible enviar el código de verificación.",
                    resultado.icon === "warning" ? "advertencia" : "error"
                );

                return;
            }

            await mostrar_mensaje_temporal(
                "contenedor_mensajes_seleccion",
                resultado.descripcion || "¡El código de seguridad fue enviado correctamente a tu correo electrónico!",
                "exito",
                3
            );

            dialogo_correos_usuario.close();
            formulario_seleccion.reset();

            if (resultado.url) {
                window.vigilanciaReemplazar(resultado.url);
            }

        } catch (error) {
            console.error(error);

            mostrar_mensaje_dialogo(
                "contenedor_mensajes_seleccion",
                "Ocurrió un error al enviar el código de verificación. Inténtelo nuevamente.",
                "error"
            );

        } finally {
            if (boton) {
                boton.disabled = false;
            }
        }
    });

    // FUNCIONES NOTIFICACIONES

    function mostrar_mensaje_dialogo(id_contenedor, mensaje, tipo = "informacion") {
        const contenedor = document.getElementById(id_contenedor);

        if (!contenedor) return;

        contenedor.className = `contenedor_mensajes ${tipo}`;
        contenedor.replaceChildren();

        const reloj = document.createElement("i");
        reloj.className = "fa-solid fa-hourglass-half reloj_procesamiento";
        reloj.setAttribute("aria-hidden", "true");

        const texto = document.createElement("span");
        texto.textContent = mensaje;

        contenedor.append(reloj, texto);
        contenedor.hidden = false;
    }

    function mostrar_mensaje_temporal(id_contenedor, mensaje, tipo = "exito", segundos = 4) {
        return new Promise((resolve) => {
            const contenedor = document.getElementById(id_contenedor);

            if (!contenedor) {
                resolve();
                return;
            }

            contenedor.className = `contenedor_mensajes ${tipo}`;
            contenedor.replaceChildren();

            const reloj = document.createElement("i");
            reloj.className = "fa-solid fa-hourglass-half reloj_procesamiento";
            reloj.setAttribute("aria-hidden", "true");

            const texto = document.createElement("span");
            texto.textContent = mensaje;

            const contador = document.createElement("span");
            contador.className = "contador_notificacion";
            contador.setAttribute("aria-live", "off");

            contenedor.append(reloj, texto, contador);
            contenedor.hidden = false;

            let restante = segundos;
            contador.textContent = ` ${restante} s`;

            const intervalo = setInterval(() => {
                restante--;

                if (restante <= 0) {
                    clearInterval(intervalo);
                    ocultar_mensaje_dialogo(id_contenedor);
                    resolve();
                    return;
                }

                contador.textContent = ` ${restante} s`;
            }, 1000);
        });
    }

    function ocultar_mensaje_dialogo(id_contenedor) {
        const contenedor = document.getElementById(id_contenedor);

        if (!contenedor) return;

        contenedor.hidden = true;
        contenedor.replaceChildren();
    }

});