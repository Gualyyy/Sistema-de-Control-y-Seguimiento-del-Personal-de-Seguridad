document.addEventListener("DOMContentLoaded", () => {

    const select_perfiles_registrados = document.getElementById("perfiles_registrados");

    const select_fecha_asignaciones = document.getElementById("fecha_asignaciones");
    const contenedor_asignaciones = document.getElementById("contenedor_asignaciones");

    const btn_lista_historial_pdf = document.getElementById("lista_historial_pdf");

    const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

    let fecha = "", perfil = "";

    function perfiles_registrados() {
        const perfiles = [
            "Supervisor Encargado",
            "Personal de Limpieza",
            "Despachador",
            "Vigilante"
        ];

        select_perfiles_registrados.innerHTML = "<option value='' selected>Selecciona un Perfil</option>";

        perfiles.forEach(perfil => {
            const option = document.createElement("option");
            option.value = perfil;
            option.textContent = perfil;
            select_perfiles_registrados.append(option);
        });
    }
    perfiles_registrados();

    async function fechas_asignaciones() {
        try {
            const respuesta = await fetch("/fechas_historial_asignaciones/");
            const resultado = await respuesta.json();
            console.log(resultado);

            select_fecha_asignaciones.innerHTML = "<option value='' selected>Selecciona una fecha</option>";

            resultado.fechas.forEach(fecha => {
                const option = document.createElement("option");
                option.value = fecha.valor;
                option.textContent = fecha.texto;
                select_fecha_asignaciones.append(option);
            });
        } catch (error) {
            console.error(error);
        }
    }
    fechas_asignaciones();

    select_perfiles_registrados.addEventListener("change", async () => {
        perfil = select_perfiles_registrados.value;

        historial_perfiles()
    });

    select_fecha_asignaciones.addEventListener("change", async () => {
        fecha = select_fecha_asignaciones.value;

        await historial_perfiles();
    });

    async function historial_perfiles() {
        try {
            const formulario = new FormData();
            formulario.append("fecha", fecha);
            formulario.append("perfil", perfil);

            const respuesta = await fetch("/historial_perfiles/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            contenedor_asignaciones.innerHTML = "";

            resultado.historial.forEach((registro, index) => {
                const fila = document.createElement("tr");
                fila.innerHTML = `
                    <td>${index + 1}</td>
                    <td>${registro.usuario}</td>
                    <td>${registro.perfil}</td>
                    <td>${registro.turno}</td>
                    <td>${registro.accion}</td>
                    <td>${registro.fecha_accion}</td>
                `;
                contenedor_asignaciones.appendChild(fila);
            });
        } catch (error) {
            console.error(error);
        }
    }
    historial_perfiles();

    btn_lista_historial_pdf.addEventListener("click", () => {
        const formulario = document.createElement("form");
        formulario.method = "POST";
        formulario.action = "/lista_historial_perfiles_pdf/";
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