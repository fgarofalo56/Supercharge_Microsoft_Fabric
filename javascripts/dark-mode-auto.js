/**
 * Auto-detect browser dark mode preference and apply MkDocs Material slate theme.
 * Only activates if the user hasn't manually toggled the theme via the palette switch.
 */
(function () {
  "use strict";
  var STORAGE_KEY = "__palette";

  // If user has never manually toggled, respect OS preference
  if (!localStorage.getItem(STORAGE_KEY)) {
    if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
      // Set slate scheme
      document.body.setAttribute("data-md-color-scheme", "slate");
      document.body.setAttribute("data-md-color-primary", "indigo");
      document.body.setAttribute("data-md-color-accent", "amber");
    }
  }

  // Listen for OS theme changes in real-time
  if (window.matchMedia) {
    window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", function (e) {
      if (!localStorage.getItem(STORAGE_KEY)) {
        document.body.setAttribute("data-md-color-scheme", e.matches ? "slate" : "default");
      }
    });
  }
})();
