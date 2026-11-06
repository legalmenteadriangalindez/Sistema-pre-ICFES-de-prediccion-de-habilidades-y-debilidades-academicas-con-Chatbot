/* Smoke tests sin dependencias externas: node --test tests/javascript/*.test.cjs */
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const root = path.resolve(__dirname, '../..');
const jsDir = path.join(root, 'Principal/static/js');
const scripts = [
  'ui-2026.js', 'ui-polish.js', 'confirmations.js',
  'chat.js', 'audio-recorder.js', 'admin-users.js',
];

function element(extra = {}) {
  const events = {};
  const classes = new Set();
  const attributes = {};
  const node = {
    value: '', checked: false, textContent: '', hidden: false, disabled: false,
    scrollTop: 0, scrollHeight: 123, dataset: {}, files: [],
    events,
    classList: {
      toggle(name, force) {
        const add = force === undefined ? !classes.has(name) : Boolean(force);
        if (add) classes.add(name);
        else classes.delete(name);
        return add;
      },
      contains: (name) => classes.has(name),
      remove: (name) => classes.delete(name),
    },
    style: { setProperty(name, value) { attributes[name] = value; } },
    setAttribute(name, value) { attributes[name] = value; },
    getAttribute(name) { return attributes[name] || null; },
    addEventListener(name, callback) { (events[name] ||= []).push(callback); },
    async fire(name, event = {}) {
      return Promise.all((events[name] || []).map((callback) => callback(event)));
    },
    querySelector: () => null, querySelectorAll: () => [],
    closest: () => null, focus() {},
  };
  return Object.assign(node, extra);
}

function environment({ elements = {}, selectors = {}, lists = {}, storage = {} } = {}) {
  const document = element({
    body: element(),
    getElementById: (id) => elements[id] || null,
    querySelector: (selector) => selectors[selector] || null,
    querySelectorAll: (selector) => lists[selector] || [],
  });
  const values = { ...storage };
  const localStorage = {
    getItem: (key) => Object.prototype.hasOwnProperty.call(values, key) ? values[key] : null,
    setItem: (key, val) => { values[key] = val; },
  };
  const window = { confirm: () => true };
  const context = { document, window, localStorage, navigator: {} };
  const load = (file) => vm.runInNewContext(
    fs.readFileSync(path.join(jsDir, file), 'utf8'),
    context, { filename: file }
  );
  return { context, document, load, values, ready: () => document.fire('DOMContentLoaded') };
}

test('cada módulo puede cargarse en páginas sin sus controles', async () => {
  for (const file of scripts) {
    const ctx = environment();
    assert.doesNotThrow(() => ctx.load(file), file);
    await assert.doesNotReject(ctx.ready(), file);
  }
});

test('scripts heredados/vacíos no quedan enlazados desde la plantilla base', () => {
  const shell = fs.readFileSync(
    path.join(root, 'Principal/templates/app_shell.html'), 'utf8'
  );
  assert.doesNotMatch(shell, /js\/script\.js/);
  assert.match(shell, /js\/ui-2026\.js/);
  assert.match(shell, /js\/ui-polish\.js/);
  assert.match(shell, /js\/confirmations\.js/);
  assert.doesNotMatch(shell, /js\/chat\.js|js\/audio-recorder\.js|js\/admin-users\.js/);
  for (const file of ['script.js', 'configuracion.js', 'perfil.js',
    'registro.js', 'inicioDeSesion.js']) {
    assert.equal(fs.existsSync(path.join(jsDir, file)), false, file);
  }
});

test('botón de menú solo modifica su sidebar y se cierra con Escape', async () => {
  const toggle = element();
  const sidebar = element();
  const ctx = environment({
    elements: { 'app-menu-toggle': toggle, 'app-sidebar': sidebar },
  });
  ctx.load('ui-2026.js');
  await ctx.ready();
  await toggle.fire('click');
  assert.equal(sidebar.classList.contains('open'), true);
  assert.equal(toggle.getAttribute('aria-expanded'), 'true');
  await ctx.document.fire('keydown', { key: 'Escape' });
  assert.equal(sidebar.classList.contains('open'), false);
  assert.equal(toggle.getAttribute('aria-expanded'), 'false');
});

test('preferencias v2 mantienen escala, modo oscuro y persistencia', async () => {
  const dark = element();
  const font = element();
  const motion = element();
  const output = element();
  const ctx = environment({
    selectors: {
      '[data-ui-preference="dark"]': dark,
      '[data-ui-preference="text-size"]': font,
      '[data-ui-preference="reduce-motion"]': motion,
    },
    elements: { 'pref-text-size-output': output },
    storage: { 'preicfes.ui.v2': JSON.stringify({
      dark: true, textSize: 115, reduceMotion: true,
    }) },
  });
  ctx.load('ui-polish.js');
  await ctx.ready();
  assert.equal(ctx.document.body.classList.contains('theme-dark'), true);
  assert.equal(ctx.document.body.classList.contains('reduce-motion'), true);
  assert.equal(font.value, '115');
  dark.checked = false;
  await dark.fire('change');
  assert.equal(ctx.document.body.classList.contains('theme-dark'), false);
  assert.equal(JSON.parse(ctx.values['preicfes.ui.v2']).dark, false);
  font.value = '120';
  await font.fire('input');
  assert.equal(output.textContent, '120 %');
});

test('compatibilidad: migra preferencia antigua sin crear un segundo controlador', async () => {
  const ctx = environment({ storage: { modoOscuro: 'true' } });
  ctx.load('ui-polish.js');
  await ctx.ready();
  assert.equal(ctx.document.body.classList.contains('theme-dark'), true);
});

test('confirmación cancela formularios marcados y omite formularios normales', async () => {
  const form = element();
  form.getAttribute = (name) => name === 'data-confirm' ? '¿Eliminar?' : null;
  let prevented = false;
  const ctx = environment();
  ctx.context.window.confirm = () => false;
  ctx.load('confirmations.js');
  await ctx.document.fire('submit', {
    target: { closest: () => form },
    preventDefault() { prevented = true; },
  });
  assert.equal(prevented, true);
  prevented = false;
  await ctx.document.fire('submit', {
    target: { closest: () => null },
    preventDefault() { prevented = true; },
  });
  assert.equal(prevented, false);
});

test('chat no necesita audio, evita envío vacío y respeta sugerencias', async () => {
  const input = element({ scrollHeight: 80 });
  const send = element();
  const file = element();
  const audio = element();
  const attachment = element();
  const history = element({ querySelector: () => element(), scrollHeight: 220 });
  const form = element({
    querySelector: (q) => q.includes('archivo') ? file : audio,
    requestSubmit() { form.submissions = (form.submissions || 0) + 1; },
  });
  const chip = element({ dataset: { chatSuggestion: 'Revisar matemáticas' } });
  const ctx = environment({
    elements: {
      'tutor-form': form, 'chat-prompt': input, generar: send,
      'attachment-name': attachment, respuesta: history,
    },
    lists: { '[data-chat-suggestion]': [chip] },
  });
  ctx.load('chat.js');
  await ctx.ready();
  assert.equal(send.disabled, true);
  await chip.fire('click');
  assert.equal(input.value, 'Revisar matemáticas');
  assert.equal(send.disabled, false);
  await input.fire('keydown', {
    ctrlKey: true, key: 'Enter', preventDefault() {},
  });
  assert.equal(form.submissions, 1);
  input.value = '';
  file.files = [{ name: 'apuntes.pdf' }];
  await file.fire('change');
  assert.equal(send.disabled, false);
  assert.equal(attachment.textContent, 'apuntes.pdf');
  assert.equal(history.scrollTop, 220);
});

test('filtro administrativo funciona sin tocar filas de otros módulos', async () => {
  const row = element({
    textContent: 'Carlos Docente',
    querySelector: (q) => q === '.table-user' ? element() : null,
    querySelectorAll: () => [element({ textContent: 'Docente' })],
  });
  const table = element({ querySelectorAll: () => [row] });
  const search = element();
  const role = element();
  const count = element();
  const ctx = environment({
    elements: {
      'users-table': table, 'user-search': search,
      'role-filter': role, 'table-count': count,
    },
  });
  ctx.load('admin-users.js');
  await ctx.ready();
  assert.equal(row.hidden, false);
  search.value = 'Ana';
  await search.fire('input');
  assert.equal(row.hidden, true);
  search.value = '';
  await search.fire('input');
  assert.equal(row.hidden, false);
  assert.equal(count.textContent, 'Mostrando 1 de 1 usuarios');
});

test('grabación inexistente o sin permisos no rompe la página', async () => {
  const record = element(), stop = element(), input = element();
  const status = element();
  const ctx = environment({ elements: {
    grabar: record, detener: stop, audioInput: input,
    'audio-status': status,
  } });
  ctx.load('audio-recorder.js');
  await ctx.ready();
  await record.fire('click');
  assert.match(status.textContent, /no admite grabación/i);
});

test('grabación convierte WebM a adjunto y libera el micrófono', async () => {
  const record = element(), stop = element(), input = element();
  const status = element();
  const tracks = [{ stopped: false, stop() { this.stopped = true; } }];
  const stream = { getTracks: () => tracks };
  let changed = false;
  input.dispatchEvent = () => { changed = true; };
  class Recorder {
    constructor() {
      this.mimeType = 'audio/webm;codecs=opus';
      this.state = 'inactive';
      this.listeners = {};
    }
    static isTypeSupported(type) { return type === 'audio/webm;codecs=opus'; }
    addEventListener(name, cb) { this.listeners[name] = cb; }
    start() { this.state = 'recording'; }
    stop() {
      this.state = 'inactive';
      this.listeners.dataavailable({ data: { size: 123 } });
      this.listeners.stop();
    }
  }
  class BlobFake {
    constructor(parts, options) {
      this.size = parts.reduce((total, p) => total + (p.size || 0), 0);
      this.type = options.type;
    }
  }
  class FileFake extends BlobFake {
    constructor(parts, filename, options) {
      super(parts, options);
      this.name = filename;
    }
  }
  class DataTransferFake {
    constructor() {
      this.files = [];
      this.items = { add: (file) => this.files.push(file) };
    }
  }
  const ctx = environment({ elements: {
    grabar: record, detener: stop, audioInput: input,
    'audio-status': status,
  } });
  ctx.context.navigator.mediaDevices = { getUserMedia: async () => stream };
  Object.assign(ctx.context, {
    MediaRecorder: Recorder,
    Blob: BlobFake, File: FileFake, DataTransfer: DataTransferFake,
    Event: class Event { constructor(name) { this.type = name; } },
  });
  ctx.load('audio-recorder.js');
  await ctx.ready();
  await record.fire('click');
  assert.equal(stop.disabled, false);
  await stop.fire('click');
  assert.equal(record.disabled, false);
  assert.equal(stop.disabled, true);
  assert.equal(tracks[0].stopped, true);
  assert.equal(changed, true);
  assert.equal(input.files[0].name, 'grabacion.webm');
  assert.match(status.textContent, /lista/i);
});
