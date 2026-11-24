const $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => [...r.querySelectorAll(s)];

function toast(msg) {
  const t = $("#toast"); t.textContent = msg; t.classList.add("show");
  clearTimeout(t._h); t._h = setTimeout(() => t.classList.remove("show"), 2200);
}

// Add to cart (AJAX)
async function addToCart(id, qty = 1) {
  const r = await fetch("/api/cart/add", { method: "POST", headers: { "Content-Type": "application/json" },
                                           body: JSON.stringify({ id, qty }) });
  const d = await r.json();
  if (d.login) { toast(d.msg); setTimeout(() => location.href = "/login?next=" + location.pathname, 900); return false; }
  toast(d.msg);
  if (d.ok) { let b = $("#cartBadge"); if (!b) { b = document.createElement("span"); b.id = "cartBadge"; b.className = "badge"; $(".cart-btn").append(b); } b.textContent = d.count; }
  return d.ok;
}
document.addEventListener("click", e => {
  const a = e.target.closest("[data-add]");
  if (a) { e.preventDefault(); const q = a.dataset.qtyInput ? +$(a.dataset.qtyInput).value : 1; addToCart(+a.dataset.add, q)
    .then(ok => ok && a.dataset.go && (location.href = a.dataset.go)); }
  const m = e.target.closest("[data-step]");
  if (m) { const i = $(m.dataset.target); const max = +i.max || 9999; i.value = Math.min(max, Math.max(1, +i.value + +m.dataset.step)); }
});

// Hero carousel
(() => {
  const s = $$(".slide"); if (!s.length) return;
  const dots = $(".dots"); let n = 0, t;
  s.forEach((_, i) => { const d = document.createElement("i"); d.onclick = () => go(i); dots.append(d); });
  const go = i => { n = i; s.forEach((x, k) => x.classList.toggle("on", k === n)); $$("i", dots).forEach((x, k) => x.classList.toggle("on", k === n)); clearInterval(t); t = setInterval(() => go((n + 1) % s.length), 4000); };
  go(0);
})();

// Flash-sale countdown (to midnight)
(() => {
  const c = $("#countdown"); if (!c) return;
  const tick = () => { const now = new Date(), end = new Date(now); end.setHours(24, 0, 0, 0);
    const d = Math.floor((end - now) / 1000), p = x => String(x).padStart(2, "0");
    c.innerHTML = `<b>${p(Math.floor(d / 3600))}</b><b>${p(Math.floor(d % 3600 / 60))}</b><b>${p(d % 60)}</b>`; };
  tick(); setInterval(tick, 1000);
})();
