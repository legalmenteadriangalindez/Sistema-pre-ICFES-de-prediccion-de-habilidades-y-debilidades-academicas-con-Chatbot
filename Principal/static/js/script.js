// ===========================MODO OSCURO ===============================
function toggleModoOscuro(){

        const inputModoOscuro = document.getElementById("modoOscuro");
        
        const contenedorChat = document.getElementById("chatContainer");

        const contenedorRespuesta = document.getElementById("respuesta");

        const body = document.querySelector("body");

        const nav = document.querySelector("nav");

        const footer = document.querySelector("footer");



        if (inputModoOscuro.checked){

            body.classList.add("bodyModoOscuro");

            nav.classList.add("NavFooterModoOscuro");

            footer.classList.add("NavFooterModoOscuro");

            contenedorChat.classList.add("chatModoOscuro");

            contenedorRespuesta.classList.add("chatModoOscuro");

            localStorage.setItem("modoOscuro", "true"); // Guardar el estado en localStorage
            
        }else{

            body.classList.remove("bodyModoOscuro");
            
            nav.classList.remove("NavFooterModoOscuro");
            
            footer.classList.remove("NavFooterModoOscuro");

            contenedorChat.classList.remove("chatModoOscuro");

            contenedorRespuesta.classList.remove("chatModoOscuro");

            localStorage.setItem("modoOscuro", "false"); // Guardar el estado en localStorage
        }      

}

document.addEventListener("DOMContentLoaded", function(){
    const modoOscuroGuardado = localStorage.getItem("modoOscuro");
    const inputModoOscuro = document.getElementById("modoOscuro");
    if (modoOscuroGuardado === "true") {
        inputModoOscuro.checked = true;
        toggleModoOscuro();
    }
});



// ***********************************MODO OSCURO************************************************



// ========================= TAMAÑO FUENTE ==================================
function SlideTamañoFuente(valor){
    body = document.querySelector("body");
    body.style.fontSize = valor + "%";
}
// *********************************TAMAÑO FUENTE***************************************

//======================================MICROFONO=============================================================
let mediaRecorder; 

let audioChuncks=[];



const botonGrabarAudio= document.getElementById("grabar");

const botonDetenerAudio= document.getElementById("detener");

const InputAudio= document.getElementById("audioInput");


botonGrabarAudio.onclick = async ()=>{
     const stream= await navigator.mediaDevices.getUserMedia({audio: true});
     mediaRecorder = new MediaRecorder(stream)
    
     mediaRecorder.start();
     audioChuncks=[];

     mediaRecorder.ondataavailable = e => audioChuncks.push(e.data);

     mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChuncks,{type: "audio/webm"});
        const audioFile = new File([audioBlob],"grabacion.webm",{type: "audio/webm"});

        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(audioFile);
        InputAudio.files = dataTransfer.files;
     };
    
     botonGrabarAudio.disabled= true;
     botonDetenerAudio.disabled= false;

};

botonDetenerAudio.onclick =() => {
   mediaRecorder.stop();
   botonGrabarAudio.disabled= false;
   botonDetenerAudio.disabled= true;
}


//****************************************MICROFONO********************************************************************


//****************************************BOTON DE CONFIRMACION ***************************************************** */

let chatToDelete = null;

// pedir confirmación del sistema (nativo)
function openDeleteModal(chatId) {
    chatToDelete = chatId;

    const confirmacion = confirm("¿Seguro que deseas eliminar esta conversación?");

    if (confirmacion) {
        confirmDelete();
    } else {
        chatToDelete = null;
    }
}

// ejecuta eliminación
function confirmDelete() {
    if (!chatToDelete) return;

    const form = document.getElementById(`deleteForm-${chatToDelete}`);

    if (form) {
        form.submit();
    }

    chatToDelete = null;
}

// NOTIFICACIÓN SIMPLE (opcional pero recomendado)
function showToast(message) {
    const toast = document.createElement("div");

    toast.innerText = message;

    toast.style.position = "fixed";
    toast.style.bottom = "20px";
    toast.style.right = "20px";
    toast.style.background = "#28a745";
    toast.style.color = "white";
    toast.style.padding = "12px 18px";
    toast.style.borderRadius = "8px";
    toast.style.boxShadow = "0 4px 10px rgba(0,0,0,0.3)";
    toast.style.zIndex = "99999";

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 2500);
}