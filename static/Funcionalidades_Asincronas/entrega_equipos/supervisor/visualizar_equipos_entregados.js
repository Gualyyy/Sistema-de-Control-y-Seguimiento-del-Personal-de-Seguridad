document.addEventListener("DOMContentLoaded", () => {

    const contenedor_equipos_recibido = document.getElementById("contenedor_equipos_recibido");

    const select_categoria_equipos = document.getElementById("categoria_equipos");

    const dialogo_recibido = document.getElementById("dialogo_recibido");
    const btn_cerrar = document.getElementById("btn_cerrar");

    const input_id_recibido_equipo = document.getElementById("id_recibido_equipo");
    const input_equipo_entregado = document.getElementById("equipo_entregado");
    const input_categoria_equipo = document.getElementById("categoria_equipo");
    const input_codigo_equipo = document.getElementById("codigo_equipo");
    const input_cantidad_equipo = document.getElementById("cantidad_equipo");
    const input_cantidad_disponible = document.getElementById("cantidad_disponible");
    const input_fecha_entrega = document.getElementById("fecha_entrega");
    const textarea_observacion_entrega = document.getElementById("observacion_entrega");

    const btn_lista_entrega_pdf = document.getElementById("lista_entrega_pdf");
    const btn_datos_entrega_pdf = document.getElementById("datos_entrega_pdf");

    let categoria = "";

    async function categoria_equipos() {
        try {
            const respuesta = await fetch("/asignaciones/categoria_equipo_recibido/");
            const resultado = await respuesta.json();
            console.log(resultado);

            select_categoria_equipos.innerHTML = "<option value=''>Selecciona la Categoria</option>"

            if (resultado.estado == "fallo") {
                await Swal.fire({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon
                });
                return;
            }

            resultado.categorias.forEach(categoria => {
                const option_categoria = document.createElement("option");
                option_categoria.value = categoria.id_categoria;
                option_categoria.textContent = categoria.nombre;
                select_categoria_equipos.append(option_categoria);
            });
        } catch (error) {
            console.error(error);
        }
    }
    categoria_equipos();

    select_categoria_equipos.addEventListener("change", async () => {
        categoria = select_categoria_equipos.value;

        await equipos_recibido_registrados();
    });

    async function equipos_recibido_registrados() {
        try {
            const formulario = new FormData();
            formulario.append("categoria", categoria);

            const respuesta = await fetch("/asignaciones/visualizar_equipos_supervisor/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            contenedor_equipos_recibido.innerHTML = "";

            resultado.equipos.forEach((recibido, index) => {
                contenedor_equipos_recibido.innerHTML += `
                    <tr data-id_recibido="${recibido.id_entrega}">
                        <td>${index + 1}</td>
                        <td>${recibido.equipo}</td>
                        <td>${recibido.codigo}</td>
                        <td>${recibido.cantidad_entregada}</td>
                        <td>${recibido.cantidad_disponible}</td>
                        <td>${recibido.fecha_entrega}</td>
                    </tr>
                `;
            });
        } catch (error) {
            console.error(error);
        }
    }
    equipos_recibido_registrados();

    contenedor_equipos_recibido.addEventListener("click", async (e) => {
        const fila = e.target.closest("tr")
        if (!fila) return;

        try {
            const formulario = new FormData();
            formulario.append("id_recibido", fila.dataset.id_recibido);

            const respuesta = await fetch("/asignaciones/datos_equipo_recibido/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            if (resultado.estado == "fallo") {
                await Swal.fire({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon
                });
                return;
            }

            dialogo_recibido.showModal();

            input_id_recibido_equipo.value = resultado.equipo.id_entrega;
            input_equipo_entregado.value = resultado.equipo.nombre_equipo;
            input_categoria_equipo.value = resultado.equipo.categoria;
            input_codigo_equipo.value = resultado.equipo.codigo_equipo;
            input_cantidad_equipo.value = resultado.equipo.cantidad_entregada;
            input_cantidad_disponible.value = resultado.equipo.cantidad_disponible_entrega;
            input_fecha_entrega.value = resultado.equipo.fecha_entrega;
            textarea_observacion_entrega.value = resultado.equipo.observacion_entrega;
        } catch (error) {
            console.error(error);
        }
    });

    btn_cerrar.addEventListener("click", () => {
        dialogo_recibido.close();
    });

    btn_lista_entrega_pdf.addEventListener("click", async () => {
        const formulario = new FormData();
        formulario.append("categoria", select_categoria_equipos.value);
        formulario.append("csrfmiddlewaretoken", document.querySelector("[name=csrfmiddlewaretoken]").value);

        try {
            const respuesta = await fetch("/asignaciones/lista_equipos_recibido_pdf/", {
                method: "POST",
                body: formulario
            });

            const contentType = respuesta.headers.get("content-type") || "";

            if (!respuesta.ok || !contentType.includes("application/pdf")) {
                const resultado = await respuesta.json();
                Swal.fire({
                    title: resultado.title || "Error",
                    text: resultado.descripcion || "No se pudo generar el reporte.",
                    icon: resultado.icon || "error"
                });
                return;
            }

            const blob = await respuesta.blob();
            const url = URL.createObjectURL(blob);

            window.open(url, "_blank");

            setTimeout(() => URL.revokeObjectURL(url), 60000);

        } catch (error) {
            console.error(error);
        }
    });

    btn_datos_entrega_pdf.addEventListener("click", async () => {
        const formulario = new FormData();
        formulario.append("id_entrega", input_id_recibido_equipo.value);
        formulario.append("csrfmiddlewaretoken", document.querySelector("[name=csrfmiddlewaretoken]").value);

        try {
            const respuesta = await fetch("/asignaciones/datos_equipo_recibido_pdf/", {
                method: "POST",
                body: formulario
            });
            const contentType = respuesta.headers.get("content-type") || "";

            if (!respuesta.ok || !contentType.includes("application/pdf")) {
                const resultado = await respuesta.json();
                Swal.fire({
                    title: resultado.title || "Error",
                    text: resultado.descripcion || "No se pudo generar el reporte PDF.",
                    icon: resultado.icon || "error"
                });
                return;
            }

            const archivo = await respuesta.blob();
            const url = URL.createObjectURL(archivo);

            window.open(url, "_blank");

            setTimeout(() => URL.revokeObjectURL(url), 60000);

        } catch (error) {
            console.error(error);
        }
    });
});