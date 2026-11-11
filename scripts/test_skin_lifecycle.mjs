// Exercise the shipped plugin's stylesheet ordering and disposal without DSH.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

const observers = new Set();
class Observer {
  constructor(callback) { this.callback = callback; this.target = null; observers.add(this); }
  observe(target) { this.target = target; }
  disconnect() { this.target = null; observers.delete(this); }
}
const head = {
  children: [],
  appendChild(node) {
    const previous = this.children.indexOf(node);
    if (previous !== -1) this.children.splice(previous, 1);
    this.children.push(node);
    node.isConnected = true;
    for (const observer of [...observers]) {
      if (observer.target === this) observer.callback([{addedNodes: [node]}]);
    }
    return node;
  },
};
const document = {
  head,
  documentElement: {},
  querySelectorAll() { return []; },
  createElement(tag) {
    return {
      nodeType: 1, tagName: tag.toUpperCase(), dataset: {}, isConnected: false,
      remove() {
        const index = head.children.indexOf(this);
        if (index !== -1) head.children.splice(index, 1);
        this.isConnected = false;
      },
    };
  },
};
let loaded;
const window = {__ModuleLoader__: {load(value) { loaded = value; }}};
vm.runInNewContext(readFileSync('client.js', 'utf8'), {
  window, document, MutationObserver: Observer, console,
});
let tokenLayers = 0;
function applyPlugin() {
  const cleanups = [];
  loaded.factory(() => {}).apply({
    effect(callback) { cleanups.push(callback()); },
    theme: {
      register() { return () => {}; },
      overrideTokens() { tokenLayers++; return () => { tokenLayers--; }; },
    },
  });
  return () => { for (const cleanup of cleanups.reverse()) if (typeof cleanup === 'function') cleanup(); };
}
const disposeFirst = applyPlugin();
const skin = head.children.find(node => node.dataset?.pluginCss === 'dsh-mc-valley');
assert.ok(skin, 'the plugin installs its stylesheet');
assert.equal(tokenLayers, 1, 'the plugin installs its token layer');

const hostStyle = {nodeType: 1, tagName: 'STYLE'};
head.appendChild(hostStyle);
assert.equal(head.children.at(-1), skin, 'skin follows a late host stylesheet');
const hostLink = {nodeType: 1, tagName: 'LINK', rel: 'stylesheet'};
head.appendChild(hostLink);
assert.equal(head.children.at(-1), skin, 'skin follows a late host stylesheet link');
assert.equal(head.children.filter(node => node === skin).length, 1, 'moving the skin does not duplicate it');

// HMR may briefly mount two instances before the older one is disposed. Their
// observers must not keep moving each other's stylesheet forever.
const disposeSecond = applyPlugin();
const skins = head.children.filter(node => node.dataset?.pluginCss === 'dsh-mc-valley');
assert.equal(skins.length, 2, 'two instances can coexist during an update');
const laterHostStyle = {nodeType: 1, tagName: 'STYLE'};
head.appendChild(laterHostStyle);
assert.ok(skins.every(node => head.children.indexOf(node) > head.children.indexOf(laterHostStyle)),
  'both instances follow late host styles without triggering one another');
disposeSecond();
assert.equal(tokenLayers, 1, 'disposing one instance preserves the other token layer');
disposeFirst();
assert.equal(head.children.includes(skin), false, 'disposal removes the skin');
assert.equal(tokenLayers, 0, 'disposal removes the token layer');
assert.equal(observers.size, 0, 'disposal disconnects all observers');
head.appendChild({nodeType: 1, tagName: 'STYLE'});
assert.equal(head.children.includes(skin), false, 'late host styles cannot revive a disposed skin');
console.log('Skin stylesheet ordering and lifecycle checks passed.');
