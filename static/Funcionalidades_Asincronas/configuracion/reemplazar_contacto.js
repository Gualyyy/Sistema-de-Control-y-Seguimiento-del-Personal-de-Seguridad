document.addEventListener("DOMContentLoaded", () => {

    const input_num_telefono = document.getElementById("num_telefono");
    const select_prefijo = document.getElementById("prefijo");

    const input_correo = document.getElementById("correo");
    const select_dominio = document.getElementById("dominio");

    const textaree_direccion = document.getElementById("direccion_domicilio");

    const formulario_registrar = document.getElementById("formulario_registrar");

    const contenedor_telefono = document.getElementById("telefono");
    const contenedor_correo_electronico = document.getElementById("correo_electronico");
    const contenedor_direccion = document.getElementById("direccion");

    const contador_residencia = document.getElementById("contador_residencia");
    const contenedor_mensaje_telefono = document.getElementById("contenedor_mensaje_telefono");
    const contenedor_mensaje_correo = document.getElementById("contenedor_mensaje_correo");

    configurarTelefono(input_num_telefono, select_prefijo);
    configurarCorreo(input_correo, select_dominio);

    let controlador_telefono = null;

    async function validar_telefono(prefijo, numero, msg) {
        const valor_prefijo = prefijo.value.trim();
        const valor_numero = numero.value.trim();

        if (controlador_telefono) {
            controlador_telefono.abort();
        }

        if (!valor_prefijo || !valor_numero) {
            msg.textContent = "";
            msg.classList.remove("exito", "error");
            numero.setCustomValidity("");
            numero.classList.remove("is-valid", "is-invalid");
            return;
        }

        controlador_telefono = new AbortController();

        try {
            const formulario = new FormData();
            formulario.append("prefijo", valor_prefijo);
            formulario.append("numeros", valor_numero);

            const respuesta = await fetch("/validar_telefono/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector(
                        "[name=csrfmiddlewaretoken]"
                    ).value
                },
                body: formulario,
                signal: controlador_telefono.signal
            });

            const resultado = await respuesta.json();

            if (prefijo.value.trim() !== valor_prefijo ||
                numero.value.trim() !== valor_numero) {
                return;
            }

            if (resultado.existe) {
                numero.setCustomValidity(
                    "Ya existe un usuario con este número telefónico."
                );

                numero.classList.add("is-invalid");
                numero.classList.remove("is-valid");

                msg.textContent = "Ya existe un usuario con este número telefónico.";
                msg.classList.add("error");
                msg.classList.remove("exito");

            } else {
                numero.setCustomValidity("");

                numero.classList.add("is-valid");
                numero.classList.remove("is-invalid");

                msg.textContent = "El número telefónico está disponible.";
                msg.classList.add("exito");
                msg.classList.remove("error");
            }

        } catch (error) {
            if (error.name !== "AbortError") {
                console.error(error);
            }
        }
    }

    // TELÉFONO 
    input_num_telefono.addEventListener("input", () => {
        validar_telefono(
            select_prefijo,
            input_num_telefono,
            contenedor_mensaje_telefono
        );
    });

    select_prefijo.addEventListener("change", () => {
        validar_telefono(
            select_prefijo,
            input_num_telefono,
            contenedor_mensaje_telefono
        );
    });

    let controlador_correo = null;

    async function validar_correo(correo, dominio, msg) {
        const valor_correo = correo.value.trim().toLowerCase();
        const valor_dominio = dominio.value.trim().toLowerCase();

        if (controlador_correo) {
            controlador_correo.abort();
        }

        if (!valor_correo || !valor_dominio) {
            msg.textContent = "";
            msg.classList.remove("exito", "error");

            correo.setCustomValidity("");
            correo.classList.remove("is-valid", "is-invalid");

            return;
        }

        controlador_correo = new AbortController();

        try {
            const formulario = new FormData();

            formulario.append("correo", valor_correo);
            formulario.append("dominio", valor_dominio);

            const respuesta = await fetch("/validar_email/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector(
                        "[name=csrfmiddlewaretoken]"
                    ).value
                },
                body: formulario,
                signal: controlador_correo.signal
            });

            const resultado = await respuesta.json();

            if (correo.value.trim().toLowerCase() !== valor_correo ||
                dominio.value.trim().toLowerCase() !== valor_dominio) {
                return;
            }

            if (resultado.existe) {
                correo.setCustomValidity(
                    "Ya existe un usuario con este correo electrónico."
                );

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
            if (error.name !== "AbortError") {
                console.error(error);
            }
        }
    }

    // CORREO 
    input_correo.addEventListener("input", () => {
        validar_correo(
            input_correo,
            select_dominio,
            contenedor_mensaje_correo
        );
    });

    select_dominio.addEventListener("change", () => {
        validar_correo(
            input_correo,
            select_dominio,
            contenedor_mensaje_correo
        );
    });

    textaree_direccion.addEventListener("input", () => {
        textaree_direccion.value = textaree_direccion.value.replace(
            /[^a-zA-ZáéíóúÁÉÍÓÚñÑ0-9\s.,:;()\-]/g,
            ""
        );

        contador_residencia.textContent = textaree_direccion.value.length;
    });

    function soloTexto(input) {
        input.value = input.value
            .replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑüÜ0-9\s.,#\-\/]/g, '')
            .replace(/^\s+/, '')
            .replace(/^\d+/, '');
    }

    textaree_direccion.addEventListener("input", () => {
        soloTexto(textaree_direccion);
    });

    async function datos_contacto() {
        try {
            const respuesta = await fetch("/datos_contacto_foro/");
            const resultado = await respuesta.json();
            console.log(resultado);

            if (resultado.estado != "exito") {
                await Swal.fire({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon
                });
                return;
            }

            if (resultado.estado === "exito") {
                const contacto = resultado.contacto;

                contenedor_telefono.textContent = contacto.telefono?.trim() || "N/A";
                contenedor_correo_electronico.textContent = contacto.correo_electronico?.trim() || "N/A";
                contenedor_direccion.textContent = contacto.direccion?.trim() || "N/A";
            } else {
                contenedor_telefono.textContent = "N/A";
                contenedor_correo_electronico.textContent = "N/A";
                contenedor_direccion.textContent = "N/A";
            }
        } catch (error) {
            console.error(error);

            contenedor_telefono.textContent = "N/A";
            contenedor_correo_electronico.textContent = "N/A";
            contenedor_direccion.textContent = "N/A";
        }
    }
    datos_contacto();

    formulario_registrar.addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
            const formulario = new FormData(formulario_registrar);

            const respuesta = await fetch("/reemplazar_contactos_foro/", {
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

            formulario_registrar.reset();
            contenedor_mensaje_correo.innerHTML = "";
            contenedor_mensaje_telefono.innerHTML = "";
            await datos_contacto();
        } catch (error) {
            console.error(error);
        }
    });


});