document.addEventListener("DOMContentLoaded", () => {

    const select_tipos_incidencias = document.getElementById("tipos_incidencias");
    const select_turno_laboral = document.getElementById("turno_laboral");

    const contenedor_incidencias = document.getElementById("contenedor_incidencias");

    const btn_retroceder = document.querySelector(".btn_retroceder");
    const btn_avanzar = document.querySelector(".btn_avanzar");

    const input_vigilante_incidencia = document.getElementById("vigilante_incidencia");
    const input_ci_vigilante = document.getElementById("ci_vigilante");
    const input_turno_laboral = document.getElementById("turno_laboral_vigilante");
    const input_titulo_v = document.getElementById("titulo_incidencia_visualizar");
    const input_tipo_incidencia_v = document.getElementById("tipo_incidencia_v");
    const textarea_descripcion_incidencia_v = document.getElementById("descripcion_incidencia_v");
    const input_fecha_incidencia_v = document.getElementById("fecha_incidencia_v");

    const dialogo_incidencia = document.getElementById("dialogo_incidencia");
    const btn_cerrar_incidencia = document.getElementById("btn_cerrar_incidencia");

    const btn_lista_incidencias_pdf = document.getElementById("lista_incidencias_pdf");

    const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

    let tipo_incidencia = "", turno_laboral = "";

    let incidencias_recibidas = [];
    let pagina_actual = 1;
    const filas_por_pagina = 10;

    async function tipos_incidencias() {
        try {
            const respuesta = await fetch("/incidencias/tipos_incidencias/");
            const resultado = await respuesta.json();
            console.log(resultado);

            select_tipos_incidencias.innerHTML = "<option value='' selected>Selecciona el Tipo de Incidencia</option>";

            resultado.forEach(incidencia => {
                const option = document.createElement("option");
                option.value = incidencia.id_tipo;
                option.textContent = incidencia.nombre;
                select_tipos_incidencias.append(option);
            });
        } catch (error) {
            console.error(error);
        }
    }
    tipos_incidencias();

    async function turnos_registrados() {
        try {
            const respuesta = await fetch("/turnos_registrados/");
            const resultado = await respuesta.json();
            console.log(resultado);

            select_turno_laboral.innerHTML = "<option value='' selected>Seleccione un Turno</option>";

            resultado.forEach(turno => {
                const option = document.createElement("option");
                option.value = turno.id_turno;
                option.textContent = turno.nombre;
                select_turno_laboral.append(option);
            });
        } catch (error) {
            console.error(error);
        }
    }
    turnos_registrados();

    select_tipos_incidencias.addEventListener("change", async () => {
        tipo_incidencia = select_tipos_incidencias.value;

        await incidencia_recibida();
    });

    select_turno_laboral.addEventListener("change", async () => {
        turno_laboral = select_turno_laboral.value;

        await incidencia_recibida();
    });

    function mostrarIncidencias() {
        contenedor_incidencias.innerHTML = "";

        const inicio = (pagina_actual - 1) * filas_por_pagina;
        const final = inicio + filas_por_pagina;

        const incidencias_pagina = incidencias_recibidas.slice(inicio, final);

        if (incidencias_pagina.length === 0) {
            contenedor_incidencias.innerHTML = `
                <tr>
                    <td colspan="6">
                        No hay incidencias recibidas.
                    </td>
                </tr>
            `;
            actualizarBotones();
            return;
        }

        incidencias_pagina.forEach((incidencia, index) => {
            const fila = document.createElement("tr");
            fila.dataset.id_incidencia = incidencia.id;

            fila.innerHTML = `
                <td>${index + 1}</td>
                <td>${incidencia.usuario}</td>
                <td>${incidencia.turno}</td>
                <td>${incidencia.titulo}</td>
                <td>${incidencia.tipo}</td>
                <td>${incidencia.fecha_hora}</td>
            `;
            contenedor_incidencias.appendChild(fila);
        });

        actualizarBotones();
    }

    function actualizarBotones() {
        const total_paginas = Math.ceil(incidencias_recibidas.length / filas_por_pagina);

        btn_retroceder.disabled = pagina_actual === 1;

        btn_avanzar.disabled = pagina_actual >= total_paginas;
    }

    btn_retroceder.addEventListener("click", () => {
        if (pagina_actual > 1) {
            pagina_actual--;
            mostrarIncidencias();
        }
    });

    btn_avanzar.addEventListener("click", () => {
        const total_paginas = Math.ceil(incidencias_recibidas.length / filas_por_pagina);

        if (pagina_actual < total_paginas) {
            pagina_actual++;
            mostrarIncidencias();
        }
    });

    async function incidencia_recibida() {
        try {
            const formulario = new FormData();
            formulario.append("tipo_incidencia", tipo_incidencia);
            formulario.append("turno_laboral", turno_laboral);

            const respuesta = await fetch("/incidencias/incidencias_recibidos_vigilantes/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            if (!resultado.estado) {
                return;
            }

            incidencias_recibidas = resultado.incidencias;

            pagina_actual = 1;
            mostrarIncidencias();
        } catch (error) {
            console.error(error);
        }
    }
    incidencia_recibida();

    contenedor_incidencias.addEventListener("click", async (e) => {
        const fila = e.target.closest("tr");

        const incidencia = fila.dataset.id_incidencia;

        try {
            const formulario = new FormData();
            formulario.append("id_incidencia", incidencia);

            const respuesta = await fetch("/incidencias/buscar_incidencia/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            input_vigilante_incidencia.value = resultado.incidencia.usuario;
            input_ci_vigilante.value = resultado.incidencia.ci_usuario;
            input_turno_laboral.value = resultado.incidencia.turno;
            input_titulo_v.value = resultado.incidencia.titulo;
            input_tipo_incidencia_v.value = resultado.incidencia.tipo;
            textarea_descripcion_incidencia_v.value = resultado.incidencia.descripcion;
            input_fecha_incidencia_v.value = resultado.incidencia.fecha_hora;

            dialogo_incidencia.showModal();
        } catch (error) {
            console.error(error);
        }
    });

    btn_cerrar_incidencia.addEventListener("click", () => {
        dialogo_incidencia.close();
    });

    btn_lista_incidencias_pdf.addEventListener("click", async () => {
        try {
            const datos = new FormData();
            datos.append("csrfmiddlewaretoken", csrfToken);
            datos.append("tipo_incidencia", select_tipos_incidencias.value);
            datos.append("turno_laboral", select_turno_laboral.value);

            const respuesta = await fetch("/incidencias/lista_incidencias_admin_pdf/", {
                method: "POST",
                body: datos
            });
            const tipoRespuesta = respuesta.headers.get("Content-Type") || "";

            if (tipoRespuesta.includes("application/json")) {
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
            }, 10000);

        } catch (error) {
            console.error(error);
        }
    });

});