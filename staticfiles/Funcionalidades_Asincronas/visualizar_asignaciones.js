document.addEventListener("DOMContentLoaded", () => {

    const select_nacionalidad_busqueda = document.getElementById("nacionalidad");
    const input_cedula_busqueda = document.getElementById("cedula_identidad");
    const select_categoria_equipo = document.getElementById("categorias_registradas");

    const btn_lista_asignacion_pdf = document.getElementById("lista_asignacion_pdf");
    const btn_equipo_asignado_pdf = document.getElementById("equipo_asignado_pdf");

    const contenedor_asignaciones = document.getElementById("registros_asignaciones");

    const dialogo_asignacion = document.getElementById("dialogo_asignacion");
    const btn_cerrar_asignacion = document.getElementById("btn_cerrar_asignacion");

    const dialogo_devolucion = document.getElementById("dialogo_devolucion");
    const btn_cerrar_devolucion = document.getElementById("btn_cerrar_devolucion");

    const input_id_asignacion_v = document.getElementById("id_asignacion_visualizar");
    const empleado_asignado_v = document.getElementById("empleado_asignado_visualizar");
    const cedula_empleado_v = document.getElementById("cedula_empleado_visualizar");
    const nombre_equipo_v = document.getElementById("nombre_equipo_visualizar");
    const codigo_equipo_v = document.getElementById("codigo_equipo_visualizar");
    const categoria_equipo_v = document.getElementById("categoria_equipo_visualizar");
    const fecha_entrega_v = document.getElementById("fecha_entrega_visualizar");
    const fecha_devolucion_v = document.getElementById("fecha_devolucion_visualizar");
    const cantidad_devuelto_v = document.getElementById("cantidad_devuelto_visualizar");
    const cantidad_equipo_v = document.getElementById("cantidad_equipo_visualizar");
    const estado_equipo_v = document.getElementById("estado_equipo_visualizar");

    const formulario_devolucion = document.getElementById("formulario_devolucion");

    const input_id_asignacion_d = document.getElementById("id_asignacion_devolucion");
    const input_ci_usuario_d = document.getElementById("ci_usuario_devolucion");

    const input_empleado_asignado_d = document.getElementById("empleado_asignado_devolucion");
    const input_equipo_asignado_d = document.getElementById("equipo_asignado_devolucion");
    const input_cantidad_asignada_d = document.getElementById("cantidad_asignada_devolucion");
    const select_tipos_d = document.getElementById("tipos_devolucion");
    const select_estados_d = document.getElementById("estados_devolucion");
    const input_cantidad_d = document.getElementById("cantidad_devolver");
    const input_cantidad_devuelto_d = document.getElementById("cantidad_equipo_devuelto");
    const input_cantidad_posee_d = document.getElementById("cantidad_posee");

    const contenedor_msg_cantidad = document.getElementById("contenedor_msg_cantidad");

    const contenedor_estado_devolucion = document.getElementById("contenedor_estado_devolucion");
    const contenedor_estado_correccion = document.getElementById("contenedor_estado_correccion");
    const input_estado_correccion = document.getElementById("estado_correccion");

    const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

    let cedula = "", nacionalidad = "", categoria = "", asignacion = "", tipo = "", estado = "";
    let descripcion_cantidad_devuelto = "";

    configurarCedula(input_cedula_busqueda, select_nacionalidad_busqueda);

    async function categoria_equipo_registrados() {
        try {
            const respuesta = await fetch("/categoria_registrados/");
            const resultado = await respuesta.json();
            console.log(resultado);

            select_categoria_equipo.innerHTML = "<option value='' selected>Seleccione la categoria</option>";

            resultado.forEach(categoria => {
                const option_categoria = document.createElement("option");
                option_categoria.value = categoria.id_categoria;
                option_categoria.textContent = categoria.nombre;
                select_categoria_equipo.append(option_categoria);
            });
        } catch (error) {
            console.error(error);
        }
    }
    categoria_equipo_registrados();

    select_nacionalidad_busqueda.addEventListener("change", async () => {
        nacionalidad = select_nacionalidad_busqueda.value;

        await datos_asignados();
    });

    input_cedula_busqueda.addEventListener("input", async () => {
        cedula = input_cedula_busqueda.value;

        await datos_asignados();
    });

    select_categoria_equipo.addEventListener("change", async () => {
        categoria = select_categoria_equipo.value;

        await datos_asignados();
    });

    async function datos_asignados() {
        try {
            const formulario = new FormData();
            formulario.append("nacionalidad", nacionalidad);
            formulario.append("cedula", cedula);
            formulario.append("categoria", categoria);

            const respuesta = await fetch("/asignaciones/visualizar_asignacion_equipo/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            if (resultado.estado == "fallo") {
                await Swal.fire({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon,
                });
                return;
            }

            contenedor_asignaciones.innerHTML = "";
            resultado.forEach((asignacion, index) => {
                let accion;

                if (asignacion.estado === "Asignado" || asignacion.estado === "Parcial") {
                    accion = `
                        <button 
                            type="button"
                            class="btn_bloquear_tabla"
                            data-id="${asignacion.id}">
                            Devolución
                        </button>
                    `;
                } else {
                    accion = `
                        <span class="estado_asignacion estado_${asignacion.estado.toLowerCase()}">
                            ${asignacion.estado.replace("_", " ")}
                        </span>
                    `;
                }

                contenedor_asignaciones.innerHTML += `
                    <tr data-id_asignacion="${asignacion.id}">
                        <td>${index + 1}</td>
                        <td>${asignacion.empleado}</td>
                        <td>${asignacion.equipo}</td>
                        <td>${accion}</td>
                    </tr>
                `;
            });
        } catch (error) {
            console.error(error);
        }
    }
    datos_asignados();

    contenedor_asignaciones.addEventListener("click", async (e) => {
        const button = e.target.closest("button");
        if (button) {
            const fila = button.closest("tr");
            asignacion = fila.dataset.id_asignacion;

            await devolucion_equipo();
            return;
        }

        const fila = e.target.closest("tr");
        if (fila) {
            asignacion = fila.dataset.id_asignacion;

            await datos_asignacion();
        }
    });

    async function datos_asignacion() {
        try {
            const formulario = new FormData();
            formulario.append("id_asignacion", asignacion);

            const respuesta = await fetch("/asignaciones/buscar_datos_asignacion_equipo/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            dialogo_asignacion.showModal();

            input_id_asignacion_v.value = resultado.id;
            empleado_asignado_v.value = resultado.empleado;
            cedula_empleado_v.value = resultado.cedula;
            nombre_equipo_v.value = resultado.equipo;
            codigo_equipo_v.value = resultado.codigo;
            fecha_entrega_v.value = resultado.fecha_entrega;

            if (resultado.fecha_devolucion != "") {
                fecha_devolucion_v.value = resultado.fecha_devolucion;
            } else {
                fecha_devolucion_v.value = "N/A";
            }

            if (resultado.cantidad_devuelta > 0) {
                const cantidad = resultado.cantidad_devuelta;

                descripcion_cantidad_devuelto = `Devuelto: ${cantidad} ${cantidad === 1 ? "unidad" : "unidades"}.`;
            } else {
                descripcion_cantidad_devuelto = "No ha devuelto ninguna unidad.";
            }

            cantidad_devuelto_v.value = descripcion_cantidad_devuelto;

            const cantidad = resultado.cantidad_asignada;

            input_cantidad_asignada_d.value = `${cantidad} ${cantidad === 1 ? "unidad" : "unidades"}`;

            cantidad_equipo_v.value = resultado.estado === "Error Humano" ? "Se devolvió la cantidad asignada"
                : `${resultado.cantidad_asignada} ${resultado.cantidad_asignada === 1 ? "unidad" : "unidades"}`;
            estado_equipo_v.value = resultado.estado;
            categoria_equipo_v.value = resultado.categoria;
        } catch (error) {
            console.error(error);
        }
    }

    async function devolucion_equipo() {
        try {
            const formulario = new FormData();
            formulario.append("id_asignacion", asignacion);

            const respuesta = await fetch("/asignaciones/buscar_equipo_devolver/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            dialogo_devolucion.showModal();

            input_id_asignacion_d.value = resultado.asignacion.id;
            input_ci_usuario_d.value = resultado.asignacion.cedula;
            input_empleado_asignado_d.value = resultado.asignacion.nombres + " " + resultado.asignacion.apellidos;
            input_equipo_asignado_d.value = resultado.asignacion.equipo;

            const cantidad = resultado.asignacion.cantidad_asignada;

            input_cantidad_asignada_d.value =
                `${cantidad} ${cantidad === 1 ? "unidad" : "unidades"}`;

            if (resultado.asignacion.cantidad_devuelta > 0) {
                const cantidad_devuelta =
                    resultado.asignacion.cantidad_devuelta;

                descripcion_cantidad_devuelto =
                    `Devuelto: ${cantidad_devuelta} ${cantidad_devuelta === 1 ? "unidad" : "unidades"
                    }.`;
            } else {
                descripcion_cantidad_devuelto =
                    "No ha devuelto ninguna unidad.";
            }

            const cantidad_posee =
                cantidad - resultado.asignacion.cantidad_devuelta;

            input_cantidad_posee_d.value =
                `${cantidad_posee} ${cantidad_posee === 1 ? "unidad" : "unidades"
                }`;

            input_cantidad_asignada_d.dataset.cantidad = cantidad_posee;

            input_cantidad_devuelto_d.value =
                descripcion_cantidad_devuelto;
        } catch (error) {
            console.error(error);
        }
    }

    formulario_devolucion.addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
            const formulario = new FormData(formulario_devolucion);

            const respuesta = await fetch("/asignaciones/devolucion_equipos_asignado/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            dialogo_devolucion.close();

            await Swal.fire({
                title: resultado.title,
                text: resultado.descripcion,
                icon: resultado.icon,
            });

            await datos_asignados();
            formulario_devolucion.reset();
        } catch (error) {
            console.error(error);
        }
    });

    function restablecer_estados() {
        select_estados_d.innerHTML = `
            <option value="" selected>Seleccione el Estado de la Devolución</option>
            <option value="DEVUELTO">Devolución</option>
            <option value="DAÑADO">Dañado</option>
            <option value="HURTADO">Hurtado</option>
            <option value="EXTRAVIADO">Extraviado</option>
        `;

        select_estados_d.disabled = false;
    }

    select_tipos_d.addEventListener("change", async () => {

        tipo = select_tipos_d.value;

        if (tipo === "DEVOLUCION") {

            contenedor_estado_devolucion.hidden = false;
            contenedor_estado_correccion.hidden = true;

            estados_devolucion.required = true;

            restablecer_estados();

            input_cantidad_d.value = "";
            input_cantidad_d.readOnly = false;

            return;
        }

        if (tipo === "CORRECCION") {

            contenedor_estado_devolucion.hidden = true;
            contenedor_estado_correccion.hidden = false;

            estados_devolucion.required = false;
            estados_devolucion.value = "";

            input_estado_correccion.value = "Error Humano";

            const cantidad_pendiente =
                Number(input_cantidad_asignada_d.dataset.cantidad);

            input_cantidad_d.value = cantidad_pendiente;
            input_cantidad_d.readOnly = true;

            return;
        }

        contenedor_estado_devolucion.hidden = false;
        contenedor_estado_correccion.hidden = true;

        estados_devolucion.required = true;

        restablecer_estados();

        input_cantidad_d.value = "";
        input_cantidad_d.readOnly = false;
    });

    input_cantidad_d.addEventListener("input", () => {

        input_cantidad_d.value =
            input_cantidad_d.value.replace(/\D/g, "");

        if (input_cantidad_d.value === "") {
            contenedor_msg_cantidad.textContent = "";
            contenedor_msg_cantidad.className = "mensaje-feedback";

            input_cantidad_d.classList.remove(
                "is-invalid",
                "is-valid"
            );

            return;
        }

        if (
            input_cantidad_d.value === "0" ||
            /^0/.test(input_cantidad_d.value)
        ) {
            contenedor_msg_cantidad.textContent =
                "La cantidad debe ser un número entero mayor a 0 y no puede comenzar con 0.";

            contenedor_msg_cantidad.className =
                "mensaje-feedback error";

            input_cantidad_d.classList.add("is-invalid");
            input_cantidad_d.classList.remove("is-valid");

            input_cantidad_d.value = "";

            return;
        }

        if (input_cantidad_d.value.length > 3) {
            input_cantidad_d.value =
                input_cantidad_d.value.slice(0, 3);
        }

        const cantidad_asignada =
            Number(input_cantidad_asignada_d.dataset.cantidad);

        if (!Number.isFinite(cantidad_asignada)) {
            contenedor_msg_cantidad.textContent =
                "No se pudo determinar la cantidad disponible del equipo.";

            contenedor_msg_cantidad.className =
                "mensaje-feedback error";

            input_cantidad_d.classList.add("is-invalid");
            input_cantidad_d.classList.remove("is-valid");

            return;
        }

        const cantidad_movimiento =
            Number(input_cantidad_d.value);

        if (cantidad_movimiento > cantidad_asignada) {

            contenedor_msg_cantidad.textContent =
                `La cantidad no puede ser mayor a la cantidad que posee el empleado (${cantidad_asignada}).`;

            contenedor_msg_cantidad.className =
                "mensaje-feedback error";

            input_cantidad_d.classList.add("is-invalid");
            input_cantidad_d.classList.remove("is-valid");

            input_cantidad_d.value = "";

            return;
        }

        contenedor_msg_cantidad.textContent = "";
        contenedor_msg_cantidad.className =
            "mensaje-feedback";

        input_cantidad_d.classList.remove("is-invalid");
        input_cantidad_d.classList.add("is-valid");
    });

    btn_cerrar_devolucion.addEventListener("click", () => {
        dialogo_devolucion.close();
    });

    btn_cerrar_asignacion.addEventListener("click", () => {
        dialogo_asignacion.close();
    });

    btn_lista_asignacion_pdf.addEventListener("click", () => {
        const formulario = document.createElement("form");
        formulario.method = "POST";
        formulario.action = "/asignaciones/lista_asignaciones_pdf/";
        formulario.target = "_blank";

        const csrf = document.querySelector('[name=csrfmiddlewaretoken]').value;
        const categoria = document.querySelector("#categorias_registradas").value;

        formulario.innerHTML = `
            <input type="hidden" name="csrfmiddlewaretoken" value="${csrf}">
            
            <input type="hidden" name="categoria" value="${categoria}">
        `;

        document.body.appendChild(formulario);
        formulario.submit();
        formulario.remove();
    });

    btn_equipo_asignado_pdf.addEventListener("click", () => {
        const formulario = document.createElement("form");
        formulario.method = "POST";
        formulario.action = "/asignaciones/datos_asignacion_pdf/";
        formulario.target = "_blank";

        const csrf = document.querySelector('[name=csrfmiddlewaretoken]').value;
        const id_asignacion = document.querySelector("#id_asignacion_visualizar").value;

        formulario.innerHTML = `
            <input type="hidden" name="csrfmiddlewaretoken" value="${csrf}">
            
            <input type="hidden" name="id_asignacion" value="${id_asignacion}">
        `;

        document.body.appendChild(formulario);
        formulario.submit();
        formulario.remove();
    });
});