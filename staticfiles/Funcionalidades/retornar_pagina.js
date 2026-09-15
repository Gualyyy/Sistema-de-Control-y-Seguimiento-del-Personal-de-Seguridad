document.addEventListener("DOMContentLoaded", () => {
    const btn_volver = document.getElementById("volver");

    btn_volver.addEventListener("click", () => {
        if (window.history.length > 1) {
            window.history.back();
            return;
        }

        window.location.href = "{% url 'inicio_sesion' %}";
    });

});