document.addEventListener("DOMContentLoaded", () => {

    const control_imagen_perfil = document.getElementById("imagen_perfil");

    const btn_retirar_cargo = document.getElementById("btn_retirar_cargo");
    const btn_reporte = document.getElementById("btn_reporte");

    const input_id_administrador = document.getElementById("id_administrador");

    const input_nombres_usuario = document.getElementById("nombres_usuario");
    const input_apellidos_usuario = document.getElementById("apellidos_usuario");
    const input_ci_usuario = document.getElementById("ci_usuario");
    const input_genero_usuario = document.getElementById("genero_usuario");
    const input_estado_civil_usuario = document.getElementById("estado_civil_usuario");

    const input_telefono_principal = document.getElementById("telefono_principal");
    const input_correo_principal = document.getElementById("correo_principal");

    const input_telefono_secundaria = document.getElementById("telefono_secundaria");
    const input_correo_secundaria = document.getElementById("correo_secundaria");

    const input_condicion_residencia = document.getElementById("condicion_residencia");
    const input_municipio_residencia = document.getElementById("municipio_residencia");
    const input_parroquia_residencia = document.getElementById("parroquia_residencia");
    const textarea_direccion_domicilio = document.getElementById("direccion_domicilio");

    const input_pais_nacimento = document.getElementById("pais_nacimento");
    const input_estado_nacimiento = document.getElementById("estado_nacimiento");
    const input_municipio_nacimiento = document.getElementById("municipio_nacimiento");
    const input_parroquia_nacimiento = document.getElementById("parroquia_nacimiento");
    const textarea_direccion_nacimiento = document.getElementById("direccion_nacimiento");
    const input_fecha_nacimiento = document.getElementById("fecha_nacimiento");

    const texto_retirar_cargo = btn_retirar_cargo.querySelector("span");

    async function datos_administrador() {
        try {
            const respuesta = await fetch("/administrador_registrado/");
            const resultado = await respuesta.json();
            console.log(resultado);

            if (resultado.estado != "exito" && !resultado.tiene_credenciales) {
                await Swal.fire({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon
                });
                return;
            }

            input_id_administrador.value = resultado.usuario.id;

            if (resultado.foto_perfil) {
                control_imagen_perfil.src = resultado.foto_perfil;
            } else {
                control_imagen_perfil.src = control_imagen_perfil.dataset.foto_predeterminada;
            }

            // ACTUALIZAR TEXTO Y ACCIÓN DEL BOTÓN
            if (resultado.laboral.vigencia) {
                texto_retirar_cargo.textContent = "Retirar cargo";
                btn_retirar_cargo.dataset.accion = "retirar_cargo";
            } else {
                texto_retirar_cargo.textContent = "Asignar cargo";
                btn_retirar_cargo.dataset.accion = "asignar_cargo";
            }

            input_nombres_usuario.value = resultado.usuario.nombres;
            input_apellidos_usuario.value = resultado.usuario.apellidos;
            input_ci_usuario.value = resultado.usuario.cedula_identidad;
            input_genero_usuario.value = resultado.usuario.genero;
            input_estado_civil_usuario.value = resultado.usuario.estado_civil;

            input_telefono_principal.value = resultado.contacto.telefono_principal;
            input_correo_principal.value = resultado.contacto.correo_principal;

            input_telefono_secundaria.value = resultado.contacto.telefono_secundario;
            input_correo_secundaria.value = resultado.contacto.correo_secundario;

            input_pais_nacimento.value = resultado.nacimiento.pais;
            input_estado_nacimiento.value = resultado.nacimiento.estado;
            input_municipio_nacimiento.value = resultado.nacimiento.municipio;
            input_parroquia_nacimiento.value = resultado.nacimiento.parroquia;
            input_fecha_nacimiento.value = resultado.nacimiento.fecha_nacimiento;
            textarea_direccion_nacimiento.value = resultado.nacimiento.direccion;

            input_condicion_residencia.value = resultado.residencia.condicion_residencia;
            input_municipio_residencia.value = resultado.residencia.municipio;
            input_parroquia_residencia.value = resultado.residencia.parroquia;
            textarea_direccion_domicilio.value = resultado.residencia.direccion;
        } catch (error) {
            console.error(error);
        }
    }
    datos_administrador();

    btn_retirar_cargo.addEventListener("click", async () => {
        const accion = btn_retirar_cargo.dataset.accion;
        const id = input_id_administrador.value;

        try {
            const formulario = new FormData();
            formulario.append("id_administrador", id);
            formulario.append("accion", accion);

            const respuesta = await fetch("/gestionar_administrador/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector(
                        "[name=csrfmiddlewaretoken]"
                    ).value
                },
                body: formulario
            });

            const resultado = await respuesta.json();

            await Swal.fire({
                title: resultado.title,
                text: resultado.descripcion,
                icon: resultado.icon
            });

            datos_administrador();
        } catch (error) {
            console.error(error);
        }
    });

});