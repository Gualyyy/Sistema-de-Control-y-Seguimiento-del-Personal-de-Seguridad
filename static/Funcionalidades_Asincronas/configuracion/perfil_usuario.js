document.addEventListener("DOMContentLoaded", () => {

    const formulario_actualizar = document.getElementById("formulario_actualizar");

    const input_foto_perfil = document.getElementById("foto_perfil");
    const imagen_perfil = document.getElementById("imagen_perfil");

    const input_id_usuario = document.getElementById("id_usuario");

    const input_nombres_usuario = document.getElementById("nombres_usuario");
    const input_apellidos_usuario = document.getElementById("apellidos_usuario");
    const input_ci_usuario = document.getElementById("ci_usuario");
    const input_genero_usuario = document.getElementById("genero_usuario");
    const input_estado_civil_usuario = document.getElementById("estado_civil_usuario");

    const input_telefono_principal = document.getElementById("num_telefono_principal");
    const select_prefijo_principal = document.getElementById("prefijo_principal");
    const contenedor_mensaje_telefono_principal = document.getElementById("contenedor_mensaje_telefono_principal");

    const input_telefono_secundario = document.getElementById("num_telefono_secundario");
    const select_prefijo_secundario = document.getElementById("prefijo_secundario");
    const contenedor_mensaje_telefono_secundario = document.getElementById("contenedor_mensaje_telefono_secundario");

    const input_correo_principal = document.getElementById("correo_principal");
    const select_dominio_principal = document.getElementById("dominio_principal");
    const contenedor_mensaje_correo_principal = document.getElementById("contenedor_mensaje_correo_principal");

    const input_correo_secundario = document.getElementById("correo_secundario");
    const select_dominio_secundaria = document.getElementById("dominio_secundaria");
    const contenedor_mensaje_correo_secundario = document.getElementById("contenedor_mensaje_correo_secundario");

    const select_condicion_residencia = document.getElementById("condicion_residencia_usuario");
    const select_municipio_residencia = document.getElementById("municipio_residencia");
    const select_parroquia_residencia = document.getElementById("parroquia_residencia");
    const textarea_direccion_domicilio = document.getElementById("direccion_domicilio");

    const contador_residencia = document.getElementById("contador_residencia");

    const btn_actualizar = document.getElementById("btn_actualizar");

    configurarTelefono(input_telefono_principal, select_prefijo_principal);
    configurarTelefono(input_telefono_secundario, select_prefijo_secundario);

    configurarCorreo(input_correo_principal, select_dominio_principal);
    configurarCorreo(input_correo_secundario, select_dominio_secundaria);

    const municipios = [
        "Barinas", "Pedraza", "Antonio José de Sucre", "Ezequiel Zamora", "Bolívar", "Alberto Arvelo Torrealba", "Rojas", "Obispo", "Sosa", "Cruz Paredes", "Arismendi", "Andrés Eloy Blanco"
    ];

    const parroquiasPorMunicipioResidencia = {
        "Barinas": ["Alfredo Arvelo Larriva", "San Silvestre", "Santa Inés", "Santa Lucía", "Torunos", "El Carmen", "Alto Barinas", "Rómulo Betancourt", "Corazón de Jesús", "Ramón Ignacio Méndez", "Manuel Palacio Fajardo", "Juan Antonio Rodríguez Domínguez", "Domingo Ortiz de Páez"],

        "Pedraza": ["Ciudad Bolivia", "Ignacio Briceño", "José Félix Ribas", "Páez"],

        "Antonio José de Sucre": ["Ticoporo", "Andrés Bello", "Nicolás Pulido"],

        "Ezequiel Zamora": ["Santa Bárbara", "José Ignacio del Pumar", "Pedro Briceño Méndez", "Ramón Ignacio Méndez"],

        "Bolívar": ["Barinitas", "Altamira de Cáceres", "Calderas"],

        "Alberto Arvelo Torrealba": ["Sabaneta", "El Real"],

        "Rojas": ["Libertad", "Dolores", "Palacios Fajardo", "Santa Rosa", "Simón Rodríguez"],

        "Obispo": ["Obispos", "El Real", "La Luz", "Los Guasimitos"],

        "Sosa": ["Ciudad de Nutrias", "El Regalo", "Puerto de Nutrias", "Santa Catalina", "Simón Bolívar"],

        "Cruz Paredes": ["Barrancas", "El Socorro", "Masparrito"],

        "Arismendi": ["Arismendi", "Guadarrama", "La Unión", "San Antonio"],

        "Andrés Eloy Blanco": ["El Cantón", "Santa Cruz de Guacas", "Puerto Vivas", "Dominga Ortiz de Páez"]
    };

    function cargarMunicipiosResidencia(municipioSeleccionado = "") {
        select_municipio_residencia.innerHTML = "";

        municipios.forEach(municipio => {
            const option = document.createElement("option");
            option.value = municipio;
            option.textContent = municipio;
            if (municipio === municipioSeleccionado) {
                option.selected = true;
            }
            select_municipio_residencia.appendChild(option);
        });

        if (!municipioSeleccionado) {
            select_municipio_residencia.selectedIndex = 0;
        }
    }
    cargarMunicipiosResidencia();

    select_municipio_residencia.addEventListener("change", () => {
        cargarParroquiasResidencia();
    });

    function cargarParroquiasResidencia(parroquiaSeleccionada = "") {
        const municipio = select_municipio_residencia.value;

        select_parroquia_residencia.innerHTML = "";

        if (municipio in parroquiasPorMunicipioResidencia) {

            parroquiasPorMunicipioResidencia[municipio].forEach(parroquia => {
                const option = document.createElement("option");
                option.value = parroquia;
                option.textContent = parroquia;
                if (parroquia === parroquiaSeleccionada) {
                    option.selected = true;
                }
                select_parroquia_residencia.appendChild(option);
            });

            if (!parroquiaSeleccionada) {
                select_parroquia_residencia.selectedIndex = 0;
            }
        }
    }
    cargarParroquiasResidencia();

    textarea_direccion_domicilio.addEventListener("input", () => {
        textarea_direccion_domicilio.value =
            textarea_direccion_domicilio.value.replace(
                /[^a-zA-ZáéíóúÁÉÍÓÚñÑ0-9\s.,:;()\-*]/g,
                ""
            );

        actualizarContador(textarea_direccion_domicilio, contador_residencia);
    });

    function actualizarContador(textarea, contador) {
        contador.textContent = textarea.value.length;
    }

    // VALIDACIONES CAMPOS CRITICOS

    let controlador_telefono_principal = null;
    let controlador_telefono_secundario = null;

    async function validar_telefono(prefijo, numero, msg, otro_prefijo, otro_numero, tipo) {
        const valorPrefijo = prefijo.value.trim();
        const valorNumero = numero.value.trim();

        // Cancelar petición anterior
        if (tipo === "principal") {
            if (controlador_telefono_principal) {
                controlador_telefono_principal.abort();
            }

        } else {
            if (controlador_telefono_secundario) {
                controlador_telefono_secundario.abort();
            }
        }


        // Prefijo o número vacío
        if (!valorPrefijo || !valorNumero) {
            msg.textContent = "";
            msg.classList.remove("exito", "error");
            numero.setCustomValidity("");
            numero.classList.remove("is-valid", "is-invalid");
            return;
        }

        // COMPROBAR SI PRINCIPAL Y SECUNDARIO SON IGUALES
        const otroPrefijo = otro_prefijo.value.trim();
        const otroNumero = otro_numero.value.trim();

        if (otroPrefijo &&
            otroNumero &&
            valorPrefijo === otroPrefijo &&
            valorNumero === otroNumero) {

            numero.setCustomValidity("El teléfono principal y secundario no pueden ser iguales.");
            numero.classList.add("is-invalid");
            numero.classList.remove("is-valid");

            msg.textContent = "El teléfono principal y secundario no pueden ser iguales.";
            msg.classList.add("error");
            msg.classList.remove("exito");
            return;
        }

        // CREAR CONTROLADOR
        const controlador = new AbortController();

        if (tipo === "principal") {
            controlador_telefono_principal = controlador;
        } else {
            controlador_telefono_secundario = controlador;
        }

        try {
            const formulario = new FormData();
            formulario.append("prefijo", valorPrefijo);
            formulario.append("numeros", valorNumero);
            formulario.append("id_usuario", input_id_usuario.value);

            const respuesta = await fetch("/validar_telefono/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector(
                        "[name=csrfmiddlewaretoken]"
                    ).value
                },
                body: formulario,
                signal: controlador.signal
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            // Comprobar que los valores siguen siendo los mismos
            if (prefijo.value.trim() !== valorPrefijo ||
                numero.value.trim() !== valorNumero) {
                return;
            }

            // TELÉFONO YA EXISTE
            if (resultado.existe) {
                numero.setCustomValidity("Ya existe un usuario con este número telefónico.");
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
            if (error.name === "AbortError") {
                return;
            }
            console.error(error);
        }
    }

    // TELÉFONO PRINCIPAL
    input_telefono_principal.addEventListener("input", async () => {
        await validar_telefono(
            select_prefijo_principal,
            input_telefono_principal,
            contenedor_mensaje_telefono_principal,

            select_prefijo_secundario,
            input_telefono_secundario,

            "principal"
        );
    });

    select_prefijo_principal.addEventListener("change", async () => {
        await validar_telefono(
            select_prefijo_principal,
            input_telefono_principal,
            contenedor_mensaje_telefono_principal,

            select_prefijo_secundario,
            input_telefono_secundario,

            "principal"
        );
    });

    // TELÉFONO SECUNDARIO
    input_telefono_secundario.addEventListener("input", async () => {
        await validar_telefono(
            select_prefijo_secundario,
            input_telefono_secundario,
            contenedor_mensaje_telefono_secundario,

            select_prefijo_principal,
            input_telefono_principal,

            "secundario"
        );
    });

    select_prefijo_secundario.addEventListener("change", async () => {
        await validar_telefono(
            select_prefijo_secundario,
            input_telefono_secundario,
            contenedor_mensaje_telefono_secundario,

            select_prefijo_principal,
            input_telefono_principal,

            "secundario"
        );
    });

    let controlador_correo_principal = null;
    let controlador_correo_secundario = null;

    async function validar_correo(correo, dominio, msg, otro_correo, otro_dominio, tipo) {
        const valorCorreo = correo.value.trim().toLowerCase();
        const valorDominio = dominio.value.trim().toLowerCase();

        // CANCELAR PETICIÓN ANTERIOR DEL MISMO CORREO
        if (tipo === "principal") {
            if (controlador_correo_principal) {
                controlador_correo_principal.abort();
            }
        } else {
            if (controlador_correo_secundario) {
                controlador_correo_secundario.abort();
            }
        }

        // CORREO O DOMINIO VACÍO
        if (!valorDominio || !valorCorreo) {
            msg.textContent = "";
            msg.classList.remove("exito", "error");
            correo.setCustomValidity("");
            correo.classList.remove("is-valid", "is-invalid");
            return;
        }

        // COMPROBAR SI PRINCIPAL Y SECUNDARIO SON IGUALES
        const otroValorCorreo = otro_correo.value.trim().toLowerCase();
        const otroValorDominio = otro_dominio.value.trim().toLowerCase();

        if (otroValorCorreo &&
            otroValorDominio &&
            valorCorreo === otroValorCorreo &&
            valorDominio === otroValorDominio) {
            correo.setCustomValidity("El correo electrónico principal y secundario no pueden ser iguales.");
            correo.classList.add("is-invalid");
            correo.classList.remove("is-valid");
            msg.textContent = "El correo electrónico principal y secundario no pueden ser iguales.";
            msg.classList.add("error");
            msg.classList.remove("exito");
            return;
        }

        // CREAR CONTROLADOR
        const controlador = new AbortController();

        if (tipo === "principal") {
            controlador_correo_principal = controlador;
        } else {
            controlador_correo_secundario = controlador;
        }

        try {
            const formulario = new FormData();
            formulario.append("correo", valorCorreo);
            formulario.append("dominio", valorDominio);
            formulario.append("id_usuario", input_id_usuario.value);

            const respuesta = await fetch("/validar_email/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario,
                signal: controlador.signal
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            // COMPROBAR QUE NO CAMBIÓ DURANTE LA PETICIÓN
            if (correo.value.trim().toLowerCase() !== valorCorreo ||
                dominio.value.trim().toLowerCase() !== valorDominio) {
                return;
            }

            // CORREO YA EXISTE
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

    // CORREO PRINCIPAL
    input_correo_principal.addEventListener("input", async () => {
        await validar_correo(
            input_correo_principal,
            select_dominio_principal,
            contenedor_mensaje_correo_principal,

            input_correo_secundario,
            select_dominio_secundaria,

            "principal"
        );
    });

    select_dominio_principal.addEventListener("change", async () => {
        await validar_correo(
            input_correo_principal,
            select_dominio_principal,
            contenedor_mensaje_correo_principal,

            input_correo_secundario,
            select_dominio_secundaria,

            "principal"
        );
    });

    // CORREO SECUNDARIO
    input_correo_secundario.addEventListener("input", async () => {
        await validar_correo(
            input_correo_secundario,
            select_dominio_secundaria,
            contenedor_mensaje_correo_secundario,

            input_correo_principal,
            select_dominio_principal,

            "secundario"
        );
    });

    select_dominio_secundaria.addEventListener("change", async () => {
        await validar_correo(
            input_correo_secundario,
            select_dominio_secundaria,
            contenedor_mensaje_correo_secundario,

            input_correo_principal,
            select_dominio_principal,

            "secundario"
        );
    });

    async function datos_usuario() {
        try {
            const respuesta = await fetch("/datos_usuario_sistema/");
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

            input_id_usuario.value = resultado.usuario.id_usuario;

            input_nombres_usuario.value = resultado.usuario.nombres;
            input_apellidos_usuario.value = resultado.usuario.apellidos;
            input_ci_usuario.value = resultado.usuario.cedula_identidad;
            input_genero_usuario.value = resultado.usuario.genero;
            input_estado_civil_usuario.value = resultado.usuario.estado_civil;

            if (resultado.usuario.foto_perfil) {
                imagen_perfil.src = resultado.usuario.foto_perfil;
            } else {
                imagen_perfil.src = imagen_perfil.dataset.fotoPredeterminada;
            }

            const [prefijo_principal, telefono_principal] = resultado.contacto.telefono_principal.split("-");

            input_telefono_principal.value = telefono_principal;

            const option_prefijo_principal = document.createElement("option");
            option_prefijo_principal.value = prefijo_principal;
            option_prefijo_principal.textContent = prefijo_principal;
            option_prefijo_principal.selected = true;
            option_prefijo_principal.hidden = true;
            select_prefijo_principal.append(option_prefijo_principal);

            if (resultado.contacto.telefono_secundario != "N/A") {
                const [prefijo_secundaria, telefono_secundaria] = resultado.contacto.telefono_secundario.split("-");

                input_telefono_principal.value = telefono_secundaria;

                const option_prefijo_secundaria = document.createElement("option");
                option_prefijo_secundaria.value = prefijo_secundaria;
                option_prefijo_secundaria.textContent = prefijo_secundaria;
                option_prefijo_secundaria.selected = true;
                option_prefijo_secundaria.hidden = true;
                select_prefijo_secundario.append(option_prefijo_secundaria);
            }

            const [correo_principal, dominio_principal] = resultado.contacto.correo_principal.split("@");

            input_correo_principal.value = correo_principal;

            const option_dominio_principal = document.createElement("option");
            option_dominio_principal.value = "@" + dominio_principal;
            option_dominio_principal.textContent = "@" + dominio_principal;
            option_dominio_principal.selected = true;
            option_dominio_principal.hidden = true;
            select_dominio_principal.append(option_dominio_principal);

            if (resultado.contacto.correo_secundario != "N/A") {
                const [correo_secundaria, dominio_secundaria] = resultado.contacto.correo_secundario.split("@");

                input_correo_secundario.value = correo_secundaria;

                const option_dominio_secundaria = document.createElement("option");
                option_dominio_secundaria.value = "@" + dominio_secundaria;
                option_dominio_secundaria.textContent = "@" + dominio_secundaria;
                option_dominio_secundaria.selected = true;
                option_dominio_secundaria.hidden = true;
                select_dominio_secundaria.append(option_dominio_secundaria);
            }

            const option_condicion_residencia = document.createElement("option");
            option_condicion_residencia.value = resultado.residencia.condicion_residencia;
            option_condicion_residencia.textContent = resultado.residencia.condicion_residencia;
            option_condicion_residencia.selected = true;
            option_condicion_residencia.hidden = true;
            select_condicion_residencia.append(option_condicion_residencia);

            const option_municipio_residencia = document.createElement("option");
            option_municipio_residencia.value = resultado.residencia.municipio;
            option_municipio_residencia.textContent = resultado.residencia.municipio;
            option_municipio_residencia.selected = true;
            option_municipio_residencia.hidden = true;
            select_municipio_residencia.append(option_municipio_residencia);

            const option_parroquia_residencia = document.createElement("option");
            option_parroquia_residencia.value = resultado.residencia.parroquia;
            option_parroquia_residencia.textContent = resultado.residencia.parroquia;
            option_parroquia_residencia.selected = true;
            option_parroquia_residencia.hidden = true;
            select_parroquia_residencia.append(option_parroquia_residencia);

            textarea_direccion_domicilio.value = resultado.residencia.direccion;

            actualizarContador(textarea_direccion_domicilio, contador_residencia);

            cargarMunicipiosResidencia(resultado.residencia.municipio);

            cargarParroquiasResidencia(resultado.residencia.parroquia);
        } catch (error) {
            console.error(error);
        }
    }
    datos_usuario();

    input_foto_perfil.addEventListener("change", function () {
        const archivo = this.files[0];

        if (!archivo) return;

        const formatos_permitidos = ["image/png", "image/jpeg"];

        if (!formatos_permitidos.includes(archivo.type)) {
            this.value = "";
            Swal.fire({
                title: "Formato no permitido",
                text: "Seleccione una imagen en formato PNG o JPG.",
                icon: "warning"
            });
            return;
        }

        imagen_perfil.src = URL.createObjectURL(archivo);

        Swal.fire({
            title: "Fotografía seleccionada",
            text: "Presione el botón Actualizar para guardar su foto de perfil.",
            icon: "info",
            confirmButtonText: "Entendido"
        });
    });

    formulario_actualizar.addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
            const formulario = new FormData(formulario_actualizar);

            const respuesta = await fetch("/actualizar_datos_sistema/", {
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

            if (resultado.estado === "exito") {
                formulario_actualizar.reset();

                document.querySelectorAll(".is-valid, .is-invalid").forEach(campo => {
                    campo.classList.remove("is-valid", "is-invalid");
                    campo.setCustomValidity("");
                });

                document.querySelectorAll(".exito, .error").forEach(msg => {
                    msg.textContent = "";
                    msg.classList.remove("exito", "error");
                });

                await datos_usuario();
            }
        } catch (error) {
            console.error(error);
        }
    });

});