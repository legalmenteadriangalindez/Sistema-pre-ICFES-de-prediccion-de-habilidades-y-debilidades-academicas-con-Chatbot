// ====================================VERIFICAR RESPUESTA CORRECTA=========================================
const respuestas= document.querySelectorAll(".respuesta_correcta"); // Obtener el contenedor de respuesta correcta

const boton_verificar= document.getElementById("verificar"); // obtener el boton de verificar respuestas 



document.addEventListener("DOMContentLoaded",function(){

boton_verificar.addEventListener("click",function(){   // funcion para ocultar respuestas 
    
    respuestas.forEach(respuesta => {

        respuesta.classList.toggle("ocultar_respuesta");
        for(let i=0; i<totalDePreguntas;i++){

           const radio = document.querySelector(`input[name="opciones_${i}"]:checked`)
           correcta= respuestas[i].dataset.respuesta;
           if(radio){
               console.log(`=== pregunta ${i} == respuesta === ${radio.value}`);
               if(radio.value === correcta){
                  console.log(correcta);
                  console.log("Hacertaste");
                  respuestas[i].style.border="solid 2px green"
               }else{
                  console.log("no hacertaste");
                  console.log(correcta);
                  respuestas[i].style.border="solid 2px red"               
               }
           }else{
               console.log(`pregunta ${i} sin respuesta`);
           }
       }
    });
   
})
});
// =========================================================================================