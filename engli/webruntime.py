"""Lean web runtime for the Engli website stack — standard library only.

Two jobs Engli shouldn't do by hand: write files and serve them. HTML building
itself lives in Engli (stdlib/web.engli); this is the thin, dependency-free glue.
"""
import http.server
import os
import socketserver


def write(path, html):
    """Write one HTML file, creating parent dirs. Returns the path."""
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path


def serve(directory, port=8000):
    """Serve a built site directory on localhost (blocks). Ctrl-C to stop."""
    directory = os.path.abspath(directory)
    handler = lambda *a, **k: http.server.SimpleHTTPRequestHandler(*a, directory=directory, **k)
    with socketserver.TCPServer(("", int(port)), handler) as httpd:
        print(f"Engli Web: serving {directory} at http://localhost:{port} (Ctrl-C to stop)")
        httpd.serve_forever()


import re as _re


def inline(t):
    t = _re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = _re.sub(r"\*(.+?)\*", r"<em>\1</em>", t)
    t = _re.sub(r"`(.+?)`", r"<code>\1</code>", t)
    t = _re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', t)
    return t


def markdown(md):
    """A small but real Markdown subset -> HTML (headings, lists, bold/italic/
    code, links, paragraphs). Dependency-free, for the teaching website stack."""
    out, para = [], []
    list_open = False

    def flush_para():
        if para:
            out.append("<p>" + inline(" ".join(para).strip()) + "</p>")
            para.clear()

    for raw in md.split("\n"):
        line = raw.rstrip()
        if not line.strip():
            flush_para()
            if list_open:
                out.append("</ul>"); list_open = False
            continue
        h = _re.match(r"(#{1,6})\s+(.*)", line)
        if h:
            flush_para()
            if list_open:
                out.append("</ul>"); list_open = False
            lvl = len(h.group(1))
            out.append(f"<h{lvl}>" + inline(h.group(2)) + f"</h{lvl}>")
            continue
        if _re.match(r"[-*]\s+", line):
            flush_para()
            if not list_open:
                out.append("<ul>"); list_open = True
            out.append("<li>" + inline(_re.sub(r"^[-*]\s+", "", line)) + "</li>")
            continue
        para.append(line)
    flush_para()
    if list_open:
        out.append("</ul>")
    return "".join(out)


# ---------------------------------------------------------------------------
# Storefront: a lean e-commerce runtime — money formatting, authoritative
# pricing, a Stripe Checkout endpoint (real SDK when a key is present, an
# offline demo session otherwise), and a static server that answers POST
# /checkout. HTML, styling and the catalog all live in Engli (stdlib/shop.engli
# and the example); this is the thin, mostly-stdlib glue.
# ---------------------------------------------------------------------------
import json as _json


def money(cents, symbol="$"):
    """Format integer minor units (cents) as a price, e.g. 1299 -> ``$12.99``."""
    return f"{symbol}{int(cents) / 100:,.2f}"


def compute_totals(catalog, items, threshold=0, percent=0):
    """The one authoritative pricing function.

    Prices come *only* from the server-side catalog — the client sends ids and
    quantities, never amounts — so a tampered cart can never change what is
    charged. Discount is ``percent`` off once the subtotal reaches ``threshold``
    (both in minor units); shipping is always free.
    """
    prices = {str(p["id"]): int(p["price"]) for p in catalog}
    subtotal, lines = 0, []
    for it in items:
        pid = str(it.get("id"))
        if pid not in prices:
            continue
        qty = max(1, int(it.get("quantity", 1)))
        unit = prices[pid]
        subtotal += unit * qty
        lines.append({"id": pid, "quantity": qty, "unit": unit})
    qualifies = bool(threshold) and subtotal >= threshold
    discount = (subtotal * percent) // 100 if qualifies else 0
    return {
        "subtotal": subtotal,
        "discount": discount,
        "total": subtotal - discount,
        "qualifies": qualifies,
        "remaining": max(0, threshold - subtotal) if threshold else 0,
        "lines": lines,
    }


def checkout_session(catalog, items, secret_key=None, currency="usd",
                     threshold=0, percent=0, success_url="/success.html",
                     cancel_url="/", names=None):
    """Create a Checkout session for a cart, pricing it from the catalog.

    With a Stripe secret key (argument or ``STRIPE_SECRET_KEY``) and the stripe
    SDK installed, this creates a real Stripe Checkout Session and returns its
    URL. With neither, it returns a *demo* session carrying the same
    server-computed total, so the whole flow runs and tests offline with no
    account and no network. Any Stripe error also falls back to demo."""
    totals = compute_totals(catalog, items, threshold, percent)
    if not totals["lines"]:
        raise ValueError("empty cart")
    key = secret_key or os.environ.get("STRIPE_SECRET_KEY")
    names = names or {str(p["id"]): p.get("name", str(p["id"])) for p in catalog}
    if key:
        try:
            import stripe  # optional dependency, imported only when used
            stripe.api_key = key
            line_items = [{
                "quantity": ln["quantity"],
                "price_data": {
                    "currency": currency,
                    "unit_amount": ln["unit"],
                    "product_data": {"name": names.get(ln["id"], ln["id"])},
                },
            } for ln in totals["lines"]]
            discounts = None
            if totals["discount"]:
                coupon = stripe.Coupon.create(amount_off=totals["discount"],
                                              currency=currency, duration="once",
                                              name=f"{percent}% off")
                discounts = [{"coupon": coupon.id}]
            session = stripe.checkout.Session.create(
                mode="payment", line_items=line_items, discounts=discounts,
                success_url=success_url, cancel_url=cancel_url)
            return {"url": session.url, "mode": "stripe", "total": totals["total"]}
        except Exception as exc:  # SDK missing or API error -> demo, never crash
            return {"url": f"{success_url}?demo=1&total={totals['total']}",
                    "mode": "demo", "reason": f"stripe unavailable: {exc}",
                    "total": totals["total"]}
    return {"url": f"{success_url}?demo=1&total={totals['total']}",
            "mode": "demo", "reason": "no STRIPE_SECRET_KEY set",
            "total": totals["total"]}


def shop_script(threshold=0, percent=0, symbol="$"):
    """The client cart: localStorage, a drawer, live totals + discount progress,
    and a checkout POST. Authored without double quotes so it embeds cleanly."""
    js = r'''
(function(){
  var KEY='engli-cart', THRESHOLD=__T__, PERCENT=__P__, SYM='__S__';
  var cart=load();
  function load(){ try{return JSON.parse(localStorage.getItem(KEY))||{};}catch(e){return {};} }
  function save(){ try{localStorage.setItem(KEY, JSON.stringify(cart));}catch(e){} }
  function money(c){ return SYM + (c/100).toFixed(2); }
  function count(){ var n=0; for(var k in cart){ n+=cart[k].qty; } return n; }
  function add(id,name,price){ if(cart[id]){cart[id].qty++;} else {cart[id]={name:name,price:price,qty:1};} save(); render(); open(true); }
  function setQty(id,q){ if(q<=0){delete cart[id];} else {cart[id].qty=q;} save(); render(); }
  function open(o){ var el=document.getElementById('cart'); var b=document.getElementById('cart-backdrop'); if(!el)return; el.classList.toggle('is-open',o); if(b)b.classList.toggle('is-open',o); }
  function render(){
    var lines=document.getElementById('cart-lines'); var sub=0; var html='';
    var ids=Object.keys(cart);
    for(var i=0;i<ids.length;i++){ var id=ids[i], it=cart[id]; sub+=it.price*it.qty;
      html+='<div class=bag-line><div class=bag-info><strong>'+it.name+'</strong><span>'+money(it.price)+'</span></div>'
          +'<div class=bag-qty><button data-dec='+id+'>-</button><b>'+it.qty+'</b><button data-inc='+id+'>+</button></div></div>'; }
    if(lines) lines.innerHTML = ids.length? html : '<p class=bag-empty>Your bag is empty.</p>';
    var qualifies = THRESHOLD>0 && sub>=THRESHOLD; var disc = qualifies? Math.floor(sub*PERCENT/100):0;
    set('cart-subtotal', money(sub)); set('cart-discount', disc? '-'+money(disc):money(0)); set('cart-total', money(sub-disc));
    var bar=document.getElementById('cart-progress-bar'); if(bar){ bar.style.width = Math.min(100, THRESHOLD? sub/THRESHOLD*100:0)+'%'; }
    var note=document.getElementById('cart-note');
    if(note){ note.textContent = THRESHOLD===0? '' : (qualifies? ('You saved '+PERCENT+'% today.') : ('Spend '+money(THRESHOLD-sub)+' more for '+PERCENT+'% off.')); }
    var cc=document.getElementById('cart-count'); if(cc){ cc.textContent=count(); cc.style.display=count()? 'inline-flex':'none'; }
    var co=document.getElementById('checkout'); if(co){ co.disabled = ids.length===0; }
  }
  function set(id,v){ var el=document.getElementById(id); if(el)el.textContent=v; }
  function checkout(){
    var items=[]; for(var id in cart){ items.push({id:id, quantity:cart[id].qty}); }
    if(!items.length) return;
    var co=document.getElementById('checkout'); if(co){co.disabled=true; co.textContent='One moment...';}
    fetch('/checkout',{method:'POST', headers:{'content-type':'application/json'}, body:JSON.stringify({items:items})})
      .then(function(r){return r.json();})
      .then(function(d){ if(d.url){ location.href=d.url; } else { alert(d.error||'Checkout failed'); reset(); } })
      .catch(function(){ alert('Checkout failed'); reset(); });
    function reset(){ if(co){co.disabled=false; co.textContent='Checkout';} }
  }
  document.addEventListener('click', function(e){
    var t=e.target;
    if(t.classList && t.classList.contains('add')){ add(t.getAttribute('data-id'), t.getAttribute('data-name'), parseInt(t.getAttribute('data-price'),10)); }
    else if(t.id==='cart-toggle'){ open(true); }
    else if(t.id==='cart-close' || t.id==='cart-backdrop'){ open(false); }
    else if(t.id==='checkout'){ checkout(); }
    else if(t.hasAttribute && t.hasAttribute('data-inc')){ var i=t.getAttribute('data-inc'); setQty(i, cart[i].qty+1); }
    else if(t.hasAttribute && t.hasAttribute('data-dec')){ var j=t.getAttribute('data-dec'); setQty(j, cart[j].qty-1); }
  });
  document.addEventListener('DOMContentLoaded', render);
})();
'''
    return (js.replace("__T__", str(int(threshold)))
              .replace("__P__", str(int(percent)))
              .replace("__S__", symbol))


def storefront(directory, catalog, port=8000, currency="usd", threshold=0,
               percent=0, success_url="/success.html", cancel_url="/", names=None):
    """Serve a built shop directory and answer POST /checkout with a session
    URL. Prices are always recomputed from ``catalog`` here, server-side."""
    directory = os.path.abspath(directory)
    live = bool(os.environ.get("STRIPE_SECRET_KEY"))

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **k):
            super().__init__(*a, directory=directory, **k)

        def _json(self, code, obj):
            body = _json.dumps(obj).encode()
            self.send_response(code)
            self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            if self.path.rstrip("/") != "/checkout":
                self.send_error(404)
                return
            try:
                length = int(self.headers.get("content-length", 0))
                payload = _json.loads(self.rfile.read(length) or b"{}")
                result = checkout_session(
                    catalog, payload.get("items", []), currency=currency,
                    threshold=threshold, percent=percent,
                    success_url=success_url, cancel_url=cancel_url, names=names)
                self._json(200, result)
            except Exception as exc:
                self._json(400, {"error": str(exc)})

        def log_message(self, *a):
            pass

    with socketserver.TCPServer(("", int(port)), Handler) as httpd:
        mode = "LIVE Stripe" if live else "DEMO"
        print(f"Engli Shop: {directory} at http://localhost:{port} "
              f"(checkout: {mode} mode, Ctrl-C to stop)")
        httpd.serve_forever()
