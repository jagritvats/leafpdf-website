// Runs before the page paints: apply the theme the visitor picked last time (if any).
try {
  var t = localStorage.getItem("leaf-theme");
  if (t === "light" || t === "dark") document.documentElement.setAttribute("data-theme", t);
} catch (e) {}
