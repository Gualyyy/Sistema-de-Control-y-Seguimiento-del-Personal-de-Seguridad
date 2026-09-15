document.addEventListener("DOMContentLoaded", () => {

    const formulario_registrar = document.getElementById("formulario_completar_registrar")

    const nombre_usuario = document.getElementById("nombre_usuario_visualizar")
    const apellido_usuario = document.getElementById("apellido_usuario_visualizar")
    const cedula_usuario = document.getElementById("cedula_usuario_visualizar")
    const genero_usuario = document.getElementById("genero_usuario_visualizar")
    const estado_civil_usuario = document.getElementById("estado_civil_usuario_visualizar")

    const input_numerico_principal = document.getElementById("num_telefono_principal");
    const select_prefijo_principal = document.getElementById("prefijo_principal");

    const input_numerico_secundaria = document.getElementById("num_telefono_secundario");
    const select_prefijo_secundaria = document.getElementById("prefijo_secundario");

    const input_correo_principal = document.getElementById("correo_principal");
    const select_dominio_correo_principal = document.getElementById("dominio_principal");

    const input_correo_secundario = document.getElementById("correo_secundario");
    const select_dominio_correo_secundario = document.getElementById("dominio_secundaria");

    const contenedor_mensaje_correo_principal = document.getElementById("contenedor_mensaje_correo_principal");
    const contenedor_mensaje_correo_secundario = document.getElementById("contenedor_mensaje_correo_secundario");

    const btn_cerrar = document.getElementById("btn_cerrar");

    const textarea_direccion_nacimiento = document.getElementById("direccion_nacimiento");
    const contador_nacimiento = document.getElementById("contador_nacimiento");

    const textarea_direccion_domicilioo = document.getElementById("direccion_domicilio");
    const contador_residencia = document.getElementById("contador_residencia");

    configurarTelefono(input_numerico_principal, select_prefijo_principal);
    configurarTelefono(input_numerico_secundaria, select_prefijo_secundaria);

    configurarCorreo(input_correo_principal, select_dominio_correo_principal);
    configurarCorreo(input_correo_secundario, select_dominio_correo_secundario);

    textarea_direccion_nacimiento.addEventListener("input", () => {
        textarea_direccion_nacimiento.value = textarea_direccion_nacimiento.value.replace(
            /[^a-zA-ZáéíóúÁÉÍÓÚñÑ0-9\s.,:;()\-]/g,
            ""
        );

        contador_nacimiento.textContent = textarea_direccion_nacimiento.value.length;
    });

    textarea_direccion_domicilioo.addEventListener("input", () => {
        textarea_direccion_domicilioo.value = textarea_direccion_domicilioo.value.replace(
            /[^a-zA-ZáéíóúÁÉÍÓÚñÑ0-9\s.,:;()\-]/g,
            ""
        );

        contador_residencia.textContent = textarea_direccion_domicilioo.value.length;
    });

    let controlador_correo = null;

    async function validar_correos(correo, dominio, msg) {
        const valorCorreo = correo.value.trim();
        const valorDominio = dominio.value;

        if (controlador_correo) { // Cancelar petición anterior
            controlador_correo.abort();
        }

        if (!valorDominio || !valorCorreo) { // Correo o dominio vacío
            msg.textContent = "";
            msg.classList.remove("exito", "error");

            correo.setCustomValidity("");
            correo.classList.remove("is-valid", "is-invalid");
            return;
        }

        controlador_correo = new AbortController();

        try {
            const formulario = new FormData();
            formulario.append("correo", correo.value);
            formulario.append("dominio", dominio.value);

            const respuesta = await fetch("/validar_email/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector(
                        "[name=csrfmiddlewaretoken]"
                    ).value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            if (correo.value.trim() !== valorCorreo || dominio.value !== valorDominio) {
                return;
            }

            if (resultado.existe) {
                correo.setCustomValidity("Ya existe un usuario con este correo electrónico.");

                correo.classList.add("is-invalid");
                correo.classList.remove("is-valid");

                msg.textContent = "Ya existe un usuario con este correo electrónico.";

                msg.classList.add("error");
                msg.classList.remove("exito");

            } else {
                correo.setCustomValidity("");

                correo.classList.add("is-valid");
                correo.classList.remove("is-invalid");

                msg.textContent = "El correo electrónico está disponible.";

                msg.classList.add("exito");
                msg.classList.remove("error");
            }
        } catch (error) {
            if (error.name === "AbortError") {
                return;
            }
            console.error(error);
        }
    }

    input_correo_secundario.addEventListener("input", async () => {
        validar_correos(input_correo_secundario, select_dominio_correo_secundario, contenedor_mensaje_correo_secundario);
    });

    select_dominio_correo_secundario.addEventListener("change", async () => {
        validar_correos(input_correo_secundario, select_dominio_correo_secundario, contenedor_mensaje_correo_secundario);
    });

    input_correo_principal.addEventListener("input", async () => {
        validar_correos(input_correo_principal, select_dominio_correo_principal, contenedor_mensaje_correo_principal);
    });

    select_dominio_correo_principal.addEventListener("change", async () => {
        validar_correos(input_correo_principal, select_dominio_correo_principal, contenedor_mensaje_correo_principal);
    });

    btn_cerrar.addEventListener("click", () => {
        window.location.href = "/cerrar_sesion/";
    });

    async function datos_usuario() {
        try {
            const respuesta = await fetch("/buscar_datos_pre_registrado/");
            const resultado = await respuesta.json();
            console.log(resultado);

            if (resultado.estado == "fallo") {
                Swal.fire({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon
                });
                return;
            }

            // Datos básicos
            nombre_usuario.value = resultado.usuario.nombre;
            apellido_usuario.value = resultado.usuario.apellido;
            cedula_usuario.value = resultado.usuario.cedula_identidad;
            genero_usuario.value = resultado.usuario.genero;
            estado_civil_usuario.value = resultado.usuario.estado_civil;

            // Datos de contacto
            const telefono_principal = document.getElementById("num_telefono_principal");
            const select_prefijo_principal = document.getElementById("prefijo_principal");

            const input_correo_principal = document.getElementById("correo_principal");
            const select_dominio_principal = document.getElementById("dominio_principal");

            if (resultado.contacto.telefono_principal && resultado.contacto.correo_principal) {
                const [prefijo, numero] = resultado.contacto.telefono_principal.split("-");

                select_prefijo_principal.innerHTML = "";

                const opcion_prefijo = document.createElement("option");
                opcion_prefijo.value = prefijo;
                opcion_prefijo.textContent = prefijo;
                opcion_prefijo.selected = true;

                select_prefijo_principal.append(opcion_prefijo);

                telefono_principal.value = numero;

                const [usuario_correo, dominio] = resultado.contacto.correo_principal.split("@");

                input_correo_principal.value = usuario_correo;

                const opcion_dominio = document.createElement("option");
                opcion_dominio.value = "@" + dominio;
                opcion_dominio.textContent = "@" + dominio;
                opcion_dominio.selected = true;

                select_dominio_principal.append(opcion_dominio);

                telefono_principal.readOnly = true;
                select_prefijo_principal.disabled = true;

                input_correo_principal.readOnly = true;
                select_dominio_principal.disabled = true;
            } else {
                telefono_principal.readOnly = false;
                select_prefijo_principal.disabled = false;
                input_correo_principal.readOnly = false;
                select_dominio_principal.disabled = false;
            }

        } catch (error) {
            console.error(error);
        }
    }
    datos_usuario();

    configurarFormularioPasos(formulario_registrar);

    formulario_registrar.addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
            const formulario = new FormData(formulario_registrar);
            const respuesta = await fetch("/completar_registro/", {
                method: "POST",
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            await Swal.fire({
                title: resultado.title,
                text: resultado.descripcion,
                icon: resultado.icon,
                confirmButtonText: "Aceptar"
            });

            if (resultado.estado === "exito") {
                formulario_registrar.reset();
                window.location.href = resultado.url;

                contador_nacimiento.textContent = "0"
                contador_residencia.textContent = "0"
            }
        } catch (error) {
            console.error(error);
        }
    });

});