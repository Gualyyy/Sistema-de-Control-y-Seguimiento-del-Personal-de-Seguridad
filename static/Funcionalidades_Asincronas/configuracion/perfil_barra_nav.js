document.addEventListener("DOMContentLoaded", () => {
    const imagen = document.getElementById("foto_usuario_menu");
    if (!imagen) return;

    async function img_perfil() {
        const foto_predeterminada = imagen.dataset.fotoPredeterminada;

        try {
            const respuesta = await fetch("/img_perfil_almacenado/", {
                cache: "no-store"
            });
            const resultado = await respuesta.json();

            if (resultado.estado === "exito" && resultado.foto_perfil) {
                const url_foto = new URL(resultado.foto_perfil, window.location.origin);
                url_foto.searchParams.set("v", Date.now().toString());
                imagen.src = url_foto.toString();
            } else {
                imagen.src = foto_predeterminada;
            }
        } catch (error) {
            console.error(error);
            imagen.src = foto_predeterminada;
        }
    }
    img_perfil();

});