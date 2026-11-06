/* Pruebas de notificaciones sin navegador ni dependencias npm. */
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const js = fs.readFileSync(path.resolve(
  __dirname, '../../Principal/static/js/notifications.js'
), 'utf8');

function makeNode(tag) {
  const attrs = {};
  return {
    tagName: tag.toUpperCase(), attrs, children: [], hidden: false,
    setAttribute(key, value) { attrs[key] = value; },
    getAttribute(key) { return attrs[key] || null; },
    append(...nodes) {
      for (const node of nodes) {
        node.parentNode = this;
        this.children.push(node);
      }
    },
    appendChild(node) { this.append(node); },
    remove() {
      if (this.parentNode) {
        this.parentNode.children = this.parentNode.children.filter(x => x !== this);
      }
    },
    closest(selector) {
      if (selector === '[data-notice]' && Object.hasOwn(attrs, 'data-notice')) return this;
      if (selector === '[data-notice-dismiss]' && Object.hasOwn(attrs, 'data-notice-dismiss')) return this;
      return this.parentNode?.closest(selector) || null;
    },
    querySelector(selector) {
      if (selector === '[data-notice]') {
        return this.children.find(x => Object.hasOwn(x.attrs, 'data-notice')) || null;
      }
      return null;
    },
  };
}

function setup(withHost = true) {
  const host = withHost ? makeNode('div') : null;
  if (host) host.hidden = true;
  const handlers = {};
  const document = {
    getElementById: id => id === 'app-notifications' ? host : null,
    createElement: makeNode,
    addEventListener: (type, handler) => { handlers[type] = handler; },
  };
  const window = {};
  vm.runInNewContext(js, { window, document, Set, String }, { filename: 'notifications.js' });
  return { host, window, handlers };
}

test('módulo seguro en una página que no tiene contenedor de avisos', () => {
  const { window } = setup(false);
  assert.equal(window.PreICFES.notify('Texto'), null);
});

test('la notificación usa textContent, no interpreta HTML y valida su tipo', () => {
  const { window, host } = setup();
  const malicious = '<img src=x onerror=alert(1)>';
  const notice = window.PreICFES.notify(malicious, 'tipo-inventado');
  assert.equal(host.hidden, false);
  assert.equal(notice.getAttribute('role'), 'status');
  assert.equal(notice.className, 'app-notice app-notice--info');
  assert.equal(notice.children[0].textContent, malicious);
  assert.equal(notice.children.length, 2);
  assert.equal(notice.children[1].getAttribute('aria-label'), 'Cerrar notificación');
});

test('advertencia usa role alert y se puede cerrar mediante delegación', () => {
  const { window, host, handlers } = setup();
  const notice = window.PreICFES.notify('Verifica tus datos', 'warning');
  assert.equal(notice.getAttribute('role'), 'alert');
  assert.equal(host.children.length, 1);
  handlers.click({ target: notice.children[1] });
  assert.equal(host.children.length, 0);
  assert.equal(host.hidden, true);
});

test('cerrar un aviso no elimina los demás', () => {
  const { window, host, handlers } = setup();
  const first = window.PreICFES.notify('Uno');
  const second = window.PreICFES.notify('Dos', 'success');
  handlers.click({ target: first.children[1] });
  assert.equal(host.children.length, 1);
  assert.equal(host.children[0], second);
  assert.equal(host.hidden, false);
});
