// Front-end init: searchable selects (Tom Select) + Alpine, wired for HTMX swaps,
// plus clickable table rows.
(function () {
  "use strict";

  // Turn every `select[data-search]` into a searchable combobox.
  function initSelects(root) {
    if (!window.TomSelect || !root.querySelectorAll) return;
    root.querySelectorAll("select[data-search]:not(.tomselected)").forEach(function (el) {
      // dropdownParent: body so the menu escapes overflow-hidden cards/tables.
      new TomSelect(el, {
        allowEmptyOption: true,
        maxOptions: null,
        dropdownParent: "body",
      });
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

  // Clickable rows: <tr data-href="..."> navigates on click, except when the
  // click lands on an interactive element (link, button, form control, menu).
  document.addEventListener("click", function (e) {
    const row = e.target.closest("tr[data-href]");
    if (!row) return;
    if (e.target.closest("a, button, input, select, textarea, label, .ts-wrapper, [data-row-ignore]")) {
      return;
    }
    window.location = row.dataset.href;
  });
})();
