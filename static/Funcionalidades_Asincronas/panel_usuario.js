document.addEventListener("DOMContentLoaded", () => {

    const dialogo_empleado = document.getElementById("dialogo_empleado");
    const btn_cerrar = document.getElementById("btn_cerrar");
    const btn_empleados_pdf = document.getElementById("lista_empleado_pdf");
    const contenedor_empleados_perfil = document.getElementById("contenedor_empleados_perfil");

    let id_perfil_seleccionado = "";

    function obtener_csrf_token() {
        const nombre = "csrftoken=";
        const cookies = document.cookie.split(";");

        for (let cookie of cookies) {
            cookie = cookie.trim();

            if (cookie.startsWith(nombre)) {
                return decodeURIComponent(cookie.substring(nombre.length));
            }
        }
        return null;
    }

    async function ultimo_inicio_sesion() {
        const contenedor = document.getElementById("contenedor_ultimo_acceso");
        const mensaje = document.getElementById("sin_ultimo_acceso");
        const fecha = document.getElementById("fecha_ultimo_acceso");
        const ip = document.getElementById("ip_ultimo_acceso");
        const dispositivo = document.getElementById("dispositivo_ultimo_acceso");
        const estado = document.getElementById("estado_ultimo_acceso");

        try {
            const respuesta = await fetch("/ultimo_inicio_sesion/");
            const resultado = await respuesta.json();

            if (!resultado.sesion) {
                contenedor.hidden = true;
                mensaje.hidden = false;
                return;
            }

            const sesion = resultado.sesion;
            fecha.textContent = formatear_fecha(sesion.fecha_inicio);
            ip.textContent = sesion.direccion_ip;
            const datos_dispositivo = sesion.dispositivo;
            dispositivo.textContent =
                `${datos_dispositivo.navegador} ` +
                `${datos_dispositivo.version} · ` +
                `${datos_dispositivo.sistema} · ` +
                `${datos_dispositivo.dispositivo}`;

            estado.textContent = sesion.activa ? "Sesión activa" : "Sesión finalizada";

        } catch (error) {
            console.error(error);
            contenedor.hidden = true;
            mensaje.textContent = "No fue posible obtener la información del último inicio de sesión.";
            mensaje.hidden = false;
        }
    }
    ultimo_inicio_sesion();

    function formatear_fecha(fecha) {
        if (!fecha) {
            return "No disponible";
        }

        return new Date(fecha).toLocaleString(
            "es-VE",
            {
                day: "2-digit",
                month: "2-digit",
                year: "numeric",
                hour: "2-digit",
                minute: "2-digit",
                hour12: true
            }
        );
    }

    const contenedor_principal_empleados = document.querySelector(".contenedor_empleados");
    if (!contenedor_principal_empleados) {
        return;
    }

    const imagenes_personal = {
        "Supervisor Encargado": "supervisor_encargado.png",
        "Personal de Limpieza": "personal_limpieza.png",
        "Vigilante": "vigilante.png",
        "Despachador": "despachador.png"
    };

    async function empleados_registrados() {
        try {
            const respuesta = await fetch("/empleados_registrados/");
            const resultado = await respuesta.json();

            contenedor_principal_empleados.innerHTML = "";

            resultado.forEach(perfil => {
                const tarjeta = document.createElement("article");
                tarjeta.className = "tarjeta_perfil";

                const imagen = imagenes_personal[perfil.perfil];

                tarjeta.innerHTML = `
                    <div class="imagen_perfil">
                        <img src="/static/Imagenes/${imagen}" alt="${perfil.perfil}">
                    </div>

                    <div class="datos_perfil">
                        <span class="cantidad_empleados">
                            ${perfil.cantidad}
                        </span>
                        <h2 class="nombre_perfil">
                            ${perfil.perfil}
                        </h2>
                    </div>
                `;

                tarjeta.addEventListener("click", async () => {
                    id_perfil_seleccionado = perfil.id_perfil;

                    await cargar_empleados_perfil(perfil.id_perfil);
                });

                btn_cerrar.addEventListener("click", () => {
                    dialogo_empleado.close();
                });

                contenedor_principal_empleados.appendChild(tarjeta);
            });
        } catch (error) {
            console.error(error);
        }
    }
    empleados_registrados();

    async function cargar_empleados_perfil(idPerfil) {
        try {
            console.log(idPerfil)

            const formulario = new FormData();
            formulario.append("id_perfil", idPerfil);

            const respuesta = await fetch("/empleado_perfil/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": obtener_csrf_token()
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            contenedor_empleados_perfil.innerHTML = "";

            if (resultado.empleados.length === 0) {
                const fila = document.createElement("tr");

                fila.innerHTML = `
                    <td colspan="7" class="tabla_sin_registros">
                        No hay empleados registrados para este perfil.
                    </td>
                `;
                contenedor_empleados_perfil.appendChild(fila);
            } else {
                resultado.empleados.forEach((empleado, index) => {
                    const fila = document.createElement("tr");

                    fila.innerHTML = `
                        <td>${index + 1}</td>
                        <td>${empleado.nombres}</td>
                        <td>${empleado.apellidos}</td>
                        <td>${empleado.cedula}</td>
                        <td>${empleado.telefono}</td>
                        <td>${empleado.correo}</td>
                        <td>${empleado.turno}</td>
                    `;
                    contenedor_empleados_perfil.appendChild(fila);
                });
            }

            dialogo_empleado.showModal();
        } catch (error) {
            console.error(error);
        }
    }

    btn_empleados_pdf.addEventListener("click", async () => {
        try {
            const formulario = new FormData();
            formulario.append("csrfmiddlewaretoken", obtener_csrf_token());
            formulario.append("id_perfil", id_perfil_seleccionado);

            const respuesta = await fetch("/empleado_perfil_pdf/", {
                method: "POST",
                body: formulario
            });
            const tipo = respuesta.headers.get("content-type");

            // RESPUESTA JSON
            if (tipo && tipo.includes("application/json")) {
                const resultado = await respuesta.json();
                dialogo_empleado.close();

                if (resultado.estado === "fallo") {
                    Swal.fire({
                        title: resultado.title,
                        text: resultado.descripcion,
                        icon: resultado.icon
                    });
                    return;
                }
            }

            // RESPUESTA PDF
            const archivo = await respuesta.blob();
            const url = URL.createObjectURL(archivo);
            window.open(url, "_blank");

        } catch (error) {
            console.error(error);
        }
    });
});