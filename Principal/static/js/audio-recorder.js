/* Grabación del tutor: aislada, opt-in y tolerante a permisos/navegadores. */
'use strict';
document.addEventListener('DOMContentLoaded', () => {
  const record = document.getElementById('grabar');
  const stop = document.getElementById('detener');
  const input = document.getElementById('audioInput');
  if (!record || !stop || !input) return;

  const status = document.getElementById('audio-status');
  const announce = (message) => { if (status) status.textContent = message; };
  const formats = [
    ['audio/webm;codecs=opus', '.webm'],
    ['audio/webm', '.webm'],
    ['audio/ogg;codecs=opus', '.ogg'],
    ['audio/ogg', '.ogg'],
    ['audio/mp4', '.m4a']
  ];
  let stream = null;
  let recorder = null;
  let chunks = [];

  const release = () => {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      stream = null;
    }
    record.disabled = false;
    stop.disabled = true;
    recorder = null;
  };

  record.addEventListener('click', async () => {
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') {
      announce('Este navegador no admite grabación. Puedes escribir tu pregunta.');
      return;
    }
    if (recorder) return;
    record.disabled = true;
    stop.disabled = true;
    chunks = [];
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const selected = typeof MediaRecorder.isTypeSupported === 'function'
        ? formats.find(([type]) => MediaRecorder.isTypeSupported(type))
        : null;
      recorder = selected
        ? new MediaRecorder(stream, { mimeType: selected[0] })
        : new MediaRecorder(stream);
      const type = recorder.mimeType || selected?.[0] || '';
      const extension = type.includes('webm') ? '.webm'
        : type.includes('ogg') ? '.ogg'
          : type.includes('mp4') ? '.m4a' : null;
      if (!extension) {
        announce('El formato de audio del navegador no es compatible. Usa otro navegador.');
        release();
        return;
      }

      recorder.addEventListener('dataavailable', (event) => {
        if (event.data?.size) chunks.push(event.data);
      });
      recorder.addEventListener('error', () => {
        announce('La grabación se interrumpió. Intenta nuevamente.');
        release();
      });
      recorder.addEventListener('stop', () => {
        try {
          const blob = new Blob(chunks, { type });
          if (!blob.size || blob.size > 25 * 1024 * 1024) {
            announce('La grabación está vacía o supera el límite de 25 MB.');
            return;
          }
          const file = new File([blob], 'grabacion' + extension, { type });
          const transfer = new DataTransfer();
          transfer.items.add(file);
          input.files = transfer.files;
          input.dispatchEvent(new Event('change', { bubbles: true }));
          announce('Grabación lista. Puedes enviarla al tutor.');
        } catch (_) {
          announce('No se pudo adjuntar la grabación. Intenta nuevamente.');
        } finally {
          release();
        }
      });
      recorder.start();
      stop.disabled = false;
      announce('Grabando audio…');
    } catch (_) {
      announce('No se pudo acceder al micrófono. Revisa el permiso del navegador.');
      release();
    }
  });

  stop.addEventListener('click', () => {
    if (!recorder || recorder.state !== 'recording') return;
    stop.disabled = true;
    recorder.stop();
  });
});
