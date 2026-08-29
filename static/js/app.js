// Front-end init: searchable selects (Tom Select) + Alpine, wired for HTMX swaps.
(function () {
  "use strict";

  // Turn every `select[data-search]` into a searchable combobox.
  function initSelects(root) {
    if (!window.TomSelect || !root.querySelectorAll) return;
    root.querySelectorAll("select[data-search]:not(.tomselected)").forEach(function (el) {
      new TomSelect(el, { allowEmptyOption: true, maxOptions: null });
    });
  }

  // Initialize Alpine components inside a swapped-in subtree.
  function initAlpine(root) {
    if (window.Alpine && root.nodeType === 1) {
      window.Alpine.initTree(root);
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    initSelects(document);
  });

  // HTMX fires htmx:load for the initial load and each swapped-in fragment.
  document.addEventListener("htmx:load", function (e) {
    initSelects(e.target);
    initAlpine(e.target);
  });
})();
