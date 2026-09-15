document.addEventListener("DOMContentLoaded", () => {

    const select_fecha_asignacion = document.getElementById("fecha_asignaciones");
    const select_perfiles_registrados = document.getElementById("perfiles_registrados");

    const btn_historial_pdf = document.getElementById("lista_historial_pdf");

    const contenedor_devoluciones = document.getElementById("registros_devoluciones");

    const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

    let perfil = "", fecha = "";

    async function fechas_devolucion() {
        try {
            const respuesta = await fetch("/asignaciones/fechas_historial_devolucion/");
            const resultado = await respuesta.json();
            console.log(resultado);

            select_fecha_asignacion.innerHTML = "<option value='' selected>Selecciona una Fecha</option>";

            resultado.fechas.forEach(fecha => {
                const option = document.createElement("option");
                option.value = fecha.fecha;
                option.textContent = fecha.fecha_mostrar;
                select_fecha_asignacion.append(option);
            });
        } catch (error) {
            console.error(error);
        }
    }
    fechas_devolucion();

    async function perfiles_registrados() {
        try {
            const respuesta = await fetch("/asignaciones/perfil_historial_devolucion/");
            const resultado = await respuesta.json();
            console.log(resultado);

            select_perfiles_registrados.innerHTML = "<option value='' selected>Seleccione un Perfil Laboral</option>";

            resultado.perfiles.forEach(perfil => {
                const option = document.createElement("option");
                option.value = perfil.id_perfil;
                option.textContent = perfil.perfil;
                select_perfiles_registrados.append(option);
            });
        } catch (error) {
            console.error(error);
        }
    }
    perfiles_registrados();

    select_fecha_asignacion.addEventListener("change", async () => {
        fecha = select_fecha_asignacion.value;

        await historial_devoluciones();
    });

    select_perfiles_registrados.addEventListener("change", async () => {
        perfil = select_perfiles_registrados.value;

        await historial_devoluciones();
    });

    async function historial_devoluciones() {
        try {
            const formulario = new FormData();
            formulario.append("fecha", fecha);
            formulario.append("perfil", perfil);

            const respuesta = await fetch("/asignaciones/visualizar_devoluciones/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            contenedor_devoluciones.innerHTML = "";

            resultado.forEach((devolucion, index) => {
                const fila = document.createElement("tr");
                fila.innerHTML = `
                    <td>${index + 1}</td>
                    <td>${devolucion.empleado}</td>
                    <td>${devolucion.equipo}</td>
                    <td>${devolucion.cantidad}</td>
                    <td>${devolucion.fecha_devolucion}</td>
                `;
                contenedor_devoluciones.appendChild(fila);
            });
        } catch (error) {
            console.error(error);
        }
    }
    historial_devoluciones();

    btn_historial_pdf.addEventListener("click", async () => {
        const formulario = document.createElement("form");
        formulario.method = "POST";
        formulario.action = "/asignaciones/lista_historial_devolucion_pdf/";
        formulario.target = "_blank";

        const csrf = csrfToken;
        const idfecha = document.querySelector("#fecha_asignaciones").value;
        const idperfil = document.querySelector("#perfiles_registrados").value;

        formulario.innerHTML = `
            <input type="hidden" name="csrfmiddlewaretoken" value="${csrf}">
            
            <input type="hidden" name="fecha" value="${idfecha}">

            <input type="hidden" name="perfil" value="${idperfil}">
        `;

        document.body.appendChild(formulario);
        formulario.submit();
        formulario.remove();
    });
});