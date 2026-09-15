document.addEventListener("DOMContentLoaded", function () {

    function configurarTelefono() {
        const prefijos = document.querySelectorAll(".prefijo-telefono");

        prefijos.forEach(function(select){

            const input = select.closest(".form-row").querySelector(".numero-telefono");

            if(!input){
                return;
            }

            if(select.value === ""){
                input.disabled = true;
            }

            select.addEventListener(
                "change",
                function(){
                    if(this.value === ""){
                        input.value = "";
                        input.disabled = true;
                    }else{
                        input.disabled = false;
                        input.focus();
                    }
                }
            );
        });
    }

    configurarTelefono();
});