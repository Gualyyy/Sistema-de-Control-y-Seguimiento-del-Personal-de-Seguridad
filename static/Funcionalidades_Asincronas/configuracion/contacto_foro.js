document.addEventListener("DOMContentLoaded", () => {

    const contenedor_telefono = document.getElementById("telefono");
    const contenedor_correo_electronico = document.getElementById("correo_electronico");
    const contenedor_direccion = document.getElementById("direccion");

    async function datos_contacto() {
        try {
            const respuesta = await fetch("/datos_contacto_foro/");
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

            if (resultado.estado === "exito") {
                const contacto = resultado.contacto;

                contenedor_telefono.textContent = contacto.telefono?.trim() || "N/A";
                contenedor_correo_electronico.textContent = contacto.correo_electronico?.trim() || "N/A";
                contenedor_direccion.textContent = contacto.direccion?.trim() || "N/A";
            } else {
                contenedor_telefono.textContent = "N/A";
                contenedor_correo_electronico.textContent = "N/A";
                contenedor_direccion.textContent = "N/A";
            }
        } catch (error) {
            console.error(error);

            contenedor_telefono.textContent = "N/A";
            contenedor_correo_electronico.textContent = "N/A";
            contenedor_direccion.textContent = "N/A";
        }
    }
    datos_contacto();

});