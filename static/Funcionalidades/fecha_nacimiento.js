document.addEventListener("DOMContentLoaded", () => {
    const fechaNacimiento = document.getElementById("fecha_nacimiento_usuario");

    const añoActual = new Date().getFullYear();
    const añoMaximo = añoActual - 18;

    fechaNacimiento.max = `${añoMaximo}-12-31`;

    fechaNacimiento.addEventListener("keydown", e => e.preventDefault());
    fechaNacimiento.addEventListener("paste", e => e.preventDefault());
});