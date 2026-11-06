/* Búsqueda y filtros de usuarios: solo modifica visibilidad de filas. */
'use strict';
document.addEventListener('DOMContentLoaded', () => {
  const table = document.getElementById('users-table');
  if (!table) return;

  const search = document.getElementById('user-search');
  const roles = document.getElementById('role-filter');
  const count = document.getElementById('table-count');
  const rows = Array.from(table.querySelectorAll('tbody tr')).filter(
    (row) => row.querySelector('.table-user')
  );

  const filter = () => {
    const query = (search?.value || '').toLocaleLowerCase('es').trim();
    const role = (roles?.value || '').toLocaleLowerCase('es').trim();
    let visible = 0;
    rows.forEach((row) => {
      const text = row.textContent.toLocaleLowerCase('es');
      const assigned = Array.from(row.querySelectorAll('.role-pill'))
        .map((el) => el.textContent.toLocaleLowerCase('es')).join(' ');
      const show = (!query || text.includes(query)) && (!role || assigned.includes(role));
      row.hidden = !show;
      if (show) visible += 1;
    });
    if (count) count.textContent = `Mostrando ${visible} de ${rows.length} usuarios`;
  };

  search?.addEventListener('input', filter);
  roles?.addEventListener('change', filter);
  filter();
});
