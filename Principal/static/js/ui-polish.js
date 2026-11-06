/* Pre-ICFES: mejoras progresivas de interfaz, sin modificar calificación ni autenticación. */
'use strict';
(() => {
  const KEY='preicfes.ui.v2';
  const defaults={dark:false,textSize:100,reduceMotion:false};
  let options={...defaults};
  try {const stored=JSON.parse(localStorage.getItem(KEY)||'{}');if(stored&&typeof stored==='object')options={...defaults,...stored};}catch (_){}
  const apply=()=>{
    document.body.classList.toggle('theme-dark',Boolean(options.dark));
    document.body.classList.toggle('reduce-motion',Boolean(options.reduceMotion));
    const scale=Math.max(90,Math.min(120,Number(options.textSize)||100));
    document.body.style.setProperty('--pc-text-scale',String(scale/100));
  };
  apply();
  document.addEventListener('DOMContentLoaded',()=>{
    const dark=document.querySelector('[data-ui-preference="dark"]');
    const size=document.querySelector('[data-ui-preference="text-size"]');
    const motion=document.querySelector('[data-ui-preference="reduce-motion"]');
    const output=document.getElementById('pref-text-size-output');
    if(dark)dark.checked=Boolean(options.dark);
    if(motion)motion.checked=Boolean(options.reduceMotion);
    if(size)size.value=String(Math.max(90,Math.min(120,Number(options.textSize)||100)));
    if(output)output.textContent=`${Number(options.textSize)||100} %`;
    const save=()=>{apply();try{localStorage.setItem(KEY,JSON.stringify(options));}catch(_){}};
    dark?.addEventListener('change',()=>{options.dark=dark.checked;save();});
    motion?.addEventListener('change',()=>{options.reduceMotion=motion.checked;save();});
    size?.addEventListener('input',()=>{options.textSize=Number(size.value);if(output)output.textContent=`${options.textSize} %`;save();});
    // Filtrado de la tabla: solo afecta la visualización, nunca elimina ni cambia usuarios.
    const search=document.getElementById('user-search');
    const roles=document.getElementById('role-filter');
    const rows=[...document.querySelectorAll('#users-table tbody tr')].filter(row=>row.querySelector('.table-user'));
    const count=document.getElementById('table-count');
    const filter=()=>{
      const q=(search?.value||'').toLocaleLowerCase('es').trim();
      const role=(roles?.value||'').toLocaleLowerCase('es').trim();
      let visible=0;
      rows.forEach(row=>{
        const content=row.textContent.toLocaleLowerCase('es');
        const roleContent=[...row.querySelectorAll('.role-pill')].map(el=>el.textContent.toLocaleLowerCase('es')).join(' ');
        const ok=(!q||content.includes(q))&&(!role||roleContent.includes(role));
        row.hidden=!ok;if(ok)visible+=1;
      });
      if(count)count.textContent=`Mostrando ${visible} de ${rows.length} usuarios`;
    };
    search?.addEventListener('input',filter);
    roles?.addEventListener('change',filter);
    filter();
    // Mostrar el último mensaje del tutor sin interferir con su lógica.
    const history=document.getElementById('respuesta');
    if(history?.querySelector('.chat-row'))history.scrollTop=history.scrollHeight;
  });
})();
