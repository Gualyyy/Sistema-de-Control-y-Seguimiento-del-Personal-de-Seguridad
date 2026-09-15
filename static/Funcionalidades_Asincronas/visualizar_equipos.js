document.addEventListener("DOMContentLoaded", () => {

    const contenedor_equipos = document.getElementById("contenedor_equipos");
    const input_codigo_equipo = document.getElementById("codigo_equipo");
    const select_categorias_registradas = document.getElementById("categorias_registradas");
    const dialogo_equipo = document.getElementById("dialogo_equipo");
    const btn_cerrar = document.getElementById("btn_cerrar");

    const input_id_equipo = document.getElementById("id_equipo");
    const nombre_equipo = document.getElementById("nombre_equipo");
    const codigo_equipo = document.getElementById("codigo_equipo_visualizar");
    const observacion_equipo = document.getElementById("observacion_equipo");
    const cantidad_total_equipo = document.getElementById("cantidad_total_equipo");
    const cantidad_disponible_equipo = document.getElementById("cantidad_disponible_equipo");
    const categoria_equipo = document.getElementById("categoria_equipo");

    const btn_lista_equipos_pdf = document.getElementById("lista_equipos_pdf");
    const btn_datos_equipo_pdf = document.getElementById("datos_equipo_pdf");

    const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

    async function categoria_equipo_registrados() {
        try {
            const respuesta = await fetch("/categoria_registrados/");
            const resultado = await respuesta.json();
            console.log(resultado);

            select_categorias_registradas.innerHTML = "<option selected>Seleccione la categoria</option>";

            resultado.forEach(categoria => {
                const option_categoria = document.createElement("option");
                option_categoria.value = categoria.id_categoria;
                option_categoria.textContent = categoria.nombre;
                select_categorias_registradas.append(option_categoria);
            });

        } catch (error) {
            console.error(error);
        }
    }
    categoria_equipo_registrados();

    async function equipos_registrados() {
        try {
            const formulario = new FormData();
            formulario.append("codigo", input_codigo_equipo.value);
            formulario.append("categoria", select_categorias_registradas.value);

            const respuesta = await fetch("/visualizacion_equipos/", {
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
                    icon: resultado.icon
                });
                return;
            }

            contenedor_equipos.innerHTML = "";
            resultado.forEach((equipo, index) => {
                contenedor_equipos.innerHTML += `
                    <tr data-codigo="${equipo.codigo}">
                        <td>${index + 1}</td>
                        <td>${equipo.nombre}</td>
                        <td>${equipo.codigo}</td>
                        <td>${equipo.cantidad_total}</td>
                        <td>${equipo.cantidad_disponible}</td>
                    </tr>
                `;

            });
        } catch (error) {
            console.error(error);
        }
    }
    equipos_registrados();

    input_codigo_equipo.addEventListener("input", equipos_registrados);
    select_categorias_registradas.addEventListener("change", equipos_registrados);

    contenedor_equipos.addEventListener("click", async (e) => {
        const fila = e.target.closest("tr");
        if (!fila) return;

        const equipo = fila.dataset.codigo;
        try {
            const formulario = new FormData();
            formulario.append("codigo_equipo", equipo);

            const respuesta = await fetch("/buscar_equipos/", {
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
                    icon: resultado.icon
                });
                return;
            }

            dialogo_equipo.showModal();

            input_id_equipo.value = resultado.equipo.id_equipo;
            nombre_equipo.value = resultado.equipo.nombre;
            codigo_equipo.value = resultado.equipo.codigo;
            observacion_equipo.value = resultado.equipo.observacion;
            cantidad_total_equipo.value = resultado.equipo.cantidad_total;
            cantidad_disponible_equipo.value = resultado.equipo.cantidad_disponible;
            categoria_equipo.value = resultado.equipo.categoria;
        } catch (error) {
            console.error(error);
        }
    });

    btn_cerrar.addEventListener("click", () => {
        dialogo_equipo.close();
    });


    btn_lista_equipos_pdf.addEventListener("click", () => {
        const formulario = document.createElement("form");
        formulario.method = "POST";
        formulario.action = "/lista_equipos_pdf/";
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

    btn_datos_equipo_pdf.addEventListener("click", () => {
        const formulario = document.createElement("form");
        formulario.method = "POST";
        formulario.action = "/datos_equipos_pnf/";
        formulario.target = "_blank";

        const csrf = document.querySelector('[name=csrfmiddlewaretoken]').value;
        const idEquipo = document.querySelector("#id_equipo").value;

        formulario.innerHTML = `
            <input type="hidden" name="csrfmiddlewaretoken" value="${csrf}">
            
            <input type="hidden" name="id_equipo" value="${idEquipo}">
        `;

        document.body.appendChild(formulario);
        formulario.submit();
        formulario.remove();
    });
});