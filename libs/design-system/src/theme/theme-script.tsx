/**
 * Inline script rendered in <head> before first paint to apply the persisted
 * theme and avoid a flash of the wrong color scheme (13 §12).
 */
export function ThemeScript() {
  const script = [
    "(function () {",
    "  try {",
    "    var stored = window.localStorage.getItem('atoz-theme');",
    "    var dark = stored === 'dark' || (stored !== 'light' && window.matchMedia('(prefers-color-scheme: dark)').matches);",
    "    var el = document.documentElement;",
    "    if (dark) { el.classList.add('dark'); el.setAttribute('data-theme', 'dark'); }",
    "    el.style.colorScheme = dark ? 'dark' : 'light';",
    "  } catch (e) {}",
    "})();",
  ].join("");
  return <script dangerouslySetInnerHTML={{ __html: script }} />;
}
