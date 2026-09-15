document.addEventListener("DOMContentLoaded", () => {

    const contenedor_reloj = document.getElementById("reloj_asistencia");
    const fecha_asistencia = document.getElementById("fecha_asistencia");

    const reloj = FlipClock.flipClock({
        parent: contenedor_reloj,
        face: FlipClock.clock(),
        theme: FlipClock.theme({
            dividers: ":",
            css: FlipClock.css({
                fontSize: "5rem"
            })
        })
    });

    function actualizar_fecha() {
        const fecha = new Date();
        let fecha_formateada = fecha.toLocaleDateString("es-VE", {
            weekday: "long",
            day: "numeric",
            month: "long",
            year: "numeric"
        });

        fecha_formateada = fecha_formateada.charAt(0).toUpperCase() + fecha_formateada.slice(1);

        fecha_asistencia.innerHTML = `
            <i class="icon-calendar"></i>
            ${fecha_formateada}
        `;
    }

    actualizar_fecha();
});