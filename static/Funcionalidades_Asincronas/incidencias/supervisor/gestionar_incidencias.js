document.addEventListener("DOMContentLoaded", () => {

    const select_tipos_incidencias = document.getElementById("tipos_incidencias");
    const select_fechas_incidencias = document.getElementById("fechas_incidencias");
    const contenedor_incidencias = document.getElementById("contenedor_incidencias");

    const dialogo_incidencia = document.getElementById("dialogo_incidencia");
    const btn_cerrar_incidencia = document.getElementById("btn_cerrar_incidencia");

    const input_id_incidencia_v = document.getElementById("id_incidencia_v");
    const input_tipo_incidencia_v = document.getElementById("tipo_incidencia_v");
    const input_titulo_incidencia_v = document.getElementById("titulo_incidencia_v");
    const input_descripcion_incidencia_v = document.getElementById("descripcion_incidencia_v");
    const input_fecha_incidencia_v = document.getElementById("fecha_incidencia_v");

    const dialogo_actualizar = document.getElementById("dialogo_actualizar");
    const btn_cerrar_actualizar = document.getElementById("btn_cerrar_actualizar");
    const formulario_actualizar = document.getElementById("formulario_actualizar");

    const input_id_incidencia_m = document.getElementById("id_incidencia_m");
    const select_tipos_incidencias_m = document.getElementById("tipos_incidencias_m");
    const input_fecha_hora_incidencia_m = document.getElementById("fecha_hora_incidencia_m");
    const input_titulo_incidencia_m = document.getElementById("titulo_incidencia_m");
    const textarea_descripcion_incidencia_m = document.getElementById("descripcion_incidencia_m");

    const contador_descripcion_incidencia = document.getElementById("contador_descripcion_incidencia");

    const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

    const btn_incidencias_pdf = document.getElementById("lista_incidencias_pdf");

    const btn_retroceder = document.querySelector(".btn_retroceder");
    const btn_avanzar = document.querySelector(".btn_avanzar");

    let tipo_incidencia = "", fecha_incidencia = "";

    let incidencias = [];
    let pagina_actual = 1;

    const FILAS_POR_PAGINA = 10;

    async function tipos_incidencias() {
        try {
            const respuesta = await fetch("/incidencias/tipos_incidencias/");
            const resultado = await respuesta.json();
            console.log(resultado);

            select_tipos_incidencias.innerHTML = "<option value='' selected>Selecciona el Tipo de Incidencia</option>";

            select_tipos_incidencias_m.innerHTML = "";

            resultado.forEach(incidencia => {
                const option_busqueda = document.createElement("option");
                option_busqueda.value = incidencia.id_tipo;
                option_busqueda.textContent = incidencia.nombre;
                select_tipos_incidencias.append(option_busqueda);

                const option_modificar = document.createElement("option");
                option_modificar.value = incidencia.id_tipo;
                option_modificar.textContent = incidencia.nombre;
                select_tipos_incidencias_m.append(option_modificar);
            });
        } catch (error) {
            console.error(error);
        }
    }
    tipos_incidencias();

    async function fechas_incidencias() {
        try {
            const respuesta = await fetch("/incidencias/fechas_incidencias/");
            const resultado = await respuesta.json();
            console.log(resultado);

            select_fechas_incidencias.innerHTML = "<option value='' selected>Selecciona la Fecha de Incidencia</option>";

            if (resultado.estado != "exito") {
                await Swal.fire({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon
                });
                return;
            }

            resultado.fechas.forEach(fecha => {
                const option = document.createElement("option");
                option.value = fecha.value;
                option.textContent = fecha.texto;
                select_fechas_incidencias.append(option);
            });
        } catch (error) {
            console.error(error);
        }
    }
    fechas_incidencias();

    select_tipos_incidencias.addEventListener("change", async () => {
        tipo_incidencia = select_tipos_incidencias.value;

        await incidencias_registradas();
    });

    select_fechas_incidencias.addEventListener("change", async () => {
        fecha_incidencia = select_fechas_incidencias.value;

        await incidencias_registradas();
    });

    function mostrar_incidencias() {
        contenedor_incidencias.innerHTML = "";

        const inicio = (pagina_actual - 1) * FILAS_POR_PAGINA;
        const fin = inicio + FILAS_POR_PAGINA;

        const incidencias_pagina = incidencias.slice(inicio, fin);

        incidencias_pagina.forEach((registro, index) => {
            const fila = document.createElement("tr");

            fila.dataset.id_incidencia = registro.id;

            fila.innerHTML = `
                <td>${index + 1}</td>
                <td>${registro.titulo}</td>
                <td>${registro.tipo}</td>
                <td>${registro.fecha_hora}</td>
                <td>
                    <button
                        type="button"
                        class="btn_tabla"
                        title="Modificar incidencia"
                        aria-label="Modificar incidencia"
                    >
                        <i class="fa-solid fa-pen-to-square"></i>
                        Modificar
                    </button>
                </td>
            `;

            contenedor_incidencias.appendChild(fila);
        });

        btn_retroceder.disabled = pagina_actual === 1;
        btn_avanzar.disabled = fin >= incidencias.length;
    }

    async function incidencias_registradas() {
        try {
            const formulario = new FormData();
            formulario.append("tipo_incidencia", tipo_incidencia);
            formulario.append("fecha_incidencia", fecha_incidencia);

            const respuesta = await fetch("/incidencias/incidencias_vigilante/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken
                },
                body: formulario
            });
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

            incidencias = resultado.incidencias;
            pagina_actual = 1;

            mostrar_incidencias();
        } catch (error) {
            console.error(error);
        }
    }
    incidencias_registradas();

    btn_retroceder.addEventListener("click", () => {
        if (pagina_actual > 1) {
            pagina_actual--;

            mostrar_incidencias();
        }
    });

    btn_avanzar.addEventListener("click", () => {
        const total_paginas = Math.ceil(incidencias.length / FILAS_POR_PAGINA);

        if (pagina_actual < total_paginas) {
            pagina_actual++;

            mostrar_incidencias();
        }
    });

    textarea_descripcion_incidencia_m.addEventListener("input", () => {
        textarea_descripcion_incidencia_m.value = textarea_descripcion_incidencia_m.value.replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑ0-9\s.,:;()\-*]/g, "");

        actualizarContador(textarea_descripcion_incidencia_m, contador_descripcion_incidencia);
    });

    function actualizarContador(textarea, contador) {
        contador.textContent = textarea.value.length;
    }

    contenedor_incidencias.addEventListener("click", async (e) => {
        const tr = e.target.closest("tr");
        if (!tr) return;

        const id_incidencia = tr.dataset.id_incidencia;

        const boton_modificar = e.target.closest(".btn_tabla");

        try {
            const formulario = new FormData();
            formulario.append("id_incidencia", id_incidencia);

            const respuesta = await fetch("/incidencias/buscar_datos_incidencia/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            if (resultado.estado === "fallo") {
                await Swal.fire({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon
                });
                return;
            }

            if (boton_modificar) {
                input_id_incidencia_m.value = resultado.incidencia.id_incidencia;

                const option = document.createElement("option");
                option.value = resultado.incidencia.id_tipo;
                option.textContent = resultado.incidencia.tipo;
                option.selected = true;
                option.hidden = true;
                select_tipos_incidencias_m.append(option);

                input_fecha_hora_incidencia_m.value = resultado.incidencia.fecha_hora;

                input_titulo_incidencia_m.value = resultado.incidencia.titulo;
                textarea_descripcion_incidencia_m.value = resultado.incidencia.descripcion;

                actualizarContador(textarea_descripcion_incidencia_m, contador_descripcion_incidencia);

                dialogo_actualizar.showModal();
                return;
            } else {
                input_id_incidencia_v.value = resultado.incidencia.id_incidencia;

                input_tipo_incidencia_v.value = resultado.incidencia.tipo;
                input_titulo_incidencia_v.value = resultado.incidencia.titulo;
                input_descripcion_incidencia_v.value = resultado.incidencia.descripcion;
                input_fecha_incidencia_v.value = resultado.incidencia.fecha_hora;

                dialogo_incidencia.showModal();
                return;
            }
        } catch (error) {
            console.error(error);
        }
    });


    formulario_actualizar.addEventListener("submit", async (e) => {
        e.preventDefault();

        if (!formulario_actualizar.reportValidity()) {
            return;
        }

        const boton_submit = formulario_actualizar.querySelector(
            'button[type="submit"]'
        );

        if (boton_submit.disabled) {
            return;
        }

        boton_submit.disabled = true;

        try {
            const formulario = new FormData(formulario_actualizar);

            mostrar_mensaje_dialogo(
                "contenedor_mensajes_actualizar",
                "Procesando actualización...",
                "informacion"
            );

            const respuesta = await fetch("/incidencias/modificar_datos_incidencia/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            const tipos_mensaje = {
                success: "exito",
                warning: "advertencia",
                error: "error",
                info: "informacion"
            };

            const tipo_mensaje =
                tipos_mensaje[resultado.icon] || "error";

            await mostrar_mensaje_temporal(
                "contenedor_mensajes_actualizar",
                resultado.descripcion,
                tipo_mensaje,
                4
            );

            if (resultado.estado !== "exito") {
                return;
            }

            ocultar_mensaje_dialogo("contenedor_mensajes_actualizar");

            dialogo_actualizar.close();

            await incidencias_registradas();

            formulario_actualizar.reset();

            contador_descripcion_incidencia.textContent = "0";

        } catch (error) {
            console.error(error);

            ocultar_mensaje_dialogo("contenedor_mensajes_actualizar");
        } finally {
            boton_submit.disabled = false;
        }
    });


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

    btn_cerrar_incidencia.addEventListener("click", () => {
        dialogo_incidencia.close();
    });

    btn_cerrar_actualizar.addEventListener("click", () => {
        dialogo_actualizar.close();
    });


    btn_incidencias_pdf.addEventListener("click", async () => {
        const datos = new FormData();
        datos.append("csrfmiddlewaretoken", csrfToken);
        datos.append("fecha_incidencia", select_fechas_incidencias.value);
        datos.append("tipo_incidencia", select_tipos_incidencias.value);

        try {
            const respuesta = await fetch("/incidencias/lista_incidencias_pdf/", {
                method: "POST",
                body: datos
            });
            const tipoRespuesta = respuesta.headers.get("Content-Type");
            if (tipoRespuesta?.includes("application/json")) {
                const resultado = await respuesta.json();
                Swal.fire({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon
                });
                return;
            }

            const archivo = await respuesta.blob();
            const url = URL.createObjectURL(archivo);

            window.open(url, "_blank");

            setTimeout(() => {
                URL.revokeObjectURL(url);
            }, 1000);
        } catch (error) {
            console.error(error);
        }
    });
});