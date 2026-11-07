import base64
import html

from odoo import http


ESTADO_LABEL = {
    "espera": "ESPERA",
    "en_reparacion": "EN REPARACION",
    "listo": "LISTO",
    "entregado": "ENTREGADO",
    "baja": "DE BAJA",
}

ESTADO_CLASS = {
    "espera": "st-espera",
    "en_reparacion": "st-info",
    "listo": "st-ok",
    "entregado": "st-ok",
    "baja": "st-baja",
}


class TallerSeguimiento(http.Controller):
    @http.route(
        "/taller/seguimiento/<string:token>",
        type="http", auth="public", website=False, csrf=False, methods=["GET"],
    )
    def seguimiento(self, token):
        token = "".join(c for c in (token or "") if c.isalnum()).lower()
        orden = None
        acts = []
        if len(token) == 32:
            orden = http.request.env["taller.orden"].sudo().search(
                [("token_seguimiento", "=", token)], limit=1)
            if orden:
                acts = http.request.env["taller.actualizacion"].sudo().search(
                    [("orden_id", "=", orden.id)], order="fecha asc, id asc")
        body = self._render(orden, acts)
        return http.request.make_response(body, headers=[
            ("Content-Type", "text/html; charset=utf-8"),
            ("X-Robots-Tag", "noindex, nofollow"),
        ])

    @http.route(
        "/taller/imagen/<int:aid>",
        type="http", auth="public", website=False, methods=["GET"],
    )
    def imagen(self, aid, token=None):
        """Sirve una foto de avance solo con el token de su orden (como SACT uploads/)."""
        token = "".join(c for c in (token or "") if c.isalnum()).lower()
        att = http.request.env["ir.attachment"].sudo().browse(aid)
        if not att.exists() or att.res_model != "taller.actualizacion":
            return http.request.not_found()
        act = http.request.env["taller.actualizacion"].sudo().browse(att.res_id)
        if not act.exists() or act.orden_id.token_seguimiento != token:
            return http.request.not_found()
        return http.request.make_response(
            base64.b64decode(att.datas) if att.datas else b"",
            headers=[("Content-Type", att.mimetype or "application/octet-stream"),
                     ("X-Robots-Tag", "noindex, nofollow")])

    def _render(self, orden, acts):
        if not orden:
            tarjeta = (
                '<div class="card vacio"><h2>Orden no encontrada</h2>'
                "<p>El enlace de seguimiento no es válido o la orden ya no está disponible. "
                "Verifique el enlace con el taller.</p></div>"
            )
            titulo = "Seguimiento de Orden"
        else:
            e = html.escape
            estado = ESTADO_LABEL.get(orden.state, orden.state.upper())
            clase = ESTADO_CLASS.get(orden.state, "st-info")
            equipo = " ".join(x for x in [
                orden.tipo_equipo_id.name or "", orden.marca_id.name or "", orden.modelo or ""] if x)
            fecha = orden.fecha_ingreso.strftime("%d/%m/%Y") if orden.fecha_ingreso else "-"
            tarjeta = (
                '<div class="card"><div class="card-head"><h2>Orden de Trabajo %s</h2>'
                '<span class="estado-actual %s"><span class="punto"></span> %s</span></div>'
                '<div class="datos">'
                '<div class="dato"><label>Cliente</label><span>%s</span></div>'
                '<div class="dato"><label>Equipo</label><span>%s</span></div>'
                '<div class="dato"><label>F. Ingreso</label><span>%s</span></div>'
                "</div></div>"
                % (e(orden.name), clase, e(estado), e(orden.partner_id.name),
                   e(equipo), e(fecha))
            )
            if not acts:
                tarjeta += ('<div class="card"><div class="card-head"><h2>Avances y Actualizaciones</h2></div>'
                            '<div class="sin-historial">Aún no hay actualizaciones registradas. '
                            "Vuelva a consultar más tarde.</div></div>")
            else:
                items = []
                for a in acts:
                    f = a.fecha.strftime("%d/%m/%Y %I:%M %p") if a.fecha else ""
                    nota = "<div class='tl-nota'>%s</div>" % e(a.nota).replace("\n", "<br/>") if a.nota else ""
                    fotos = "".join(
                        "<img src='/taller/imagen/%s?token=%s' loading='lazy'/>" % (att.id, orden.token_seguimiento)
                        for att in a.imagen_ids
                        if (att.mimetype or "").startswith("image/"))
                    if fotos:
                        fotos = "<div class='tl-fotos'>%s</div>" % fotos
                    items.append(
                        "<div class='tl-item'><div class='tl-dot'></div><div class='tl-card'>"
                        "<div class='tl-head'><span class='tl-estado %s'>%s</span>"
                        "<span class='tl-fecha'>%s</span></div>%s%s"
                        "</div></div>"
                        % ("st-info", e(a.estado or ""), e(f), nota, fotos))
                tarjeta += ('<div class="card"><div class="card-head"><h2>Avances y Actualizaciones</h2></div>'
                            "<div class='timeline'>%s</div></div>" % "".join(items))
            titulo = "Estado de su Orden %s" % orden.name
        return """<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex, nofollow">
<title>%s - Taller</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',system-ui,sans-serif;background:#eef2f6;color:#1e293b;min-height:100vh;display:flex;flex-direction:column}
.topbar{background:#00144a;color:#fff;padding:.9rem 1.25rem}
.topbar .ttl{font-size:1.05rem;font-weight:700}
.topbar .sub{font-size:.78rem;color:#aab4c8}
.wrap{flex:1;width:100%%;max-width:760px;margin:1.75rem auto;padding:0 1rem}
.card{background:#fff;border-radius:16px;box-shadow:0 1px 3px rgba(15,23,42,.08);padding:1.5rem;margin-bottom:1.25rem}
.card-head{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;gap:.5rem;border-bottom:1px solid #eef2f6;padding-bottom:.85rem;margin-bottom:1rem}
.card-head h2{font-size:1.15rem}
.estado-actual{display:inline-flex;align-items:center;gap:.5rem;font-weight:700;color:#fff;padding:.4rem 1rem;border-radius:999px;font-size:.85rem}
.st-ok{background:#1b7f3b}.st-baja{background:#c0392b}.st-espera{background:#b7791f}.st-info{background:#3498db}
.estado-actual .punto{width:8px;height:8px;border-radius:50%%;background:#fff}
.datos{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:.9rem 1.2rem}
.dato label{display:block;font-size:.7rem;text-transform:uppercase;letter-spacing:.05em;color:#64748b;margin-bottom:.15rem}
.dato span{font-weight:600;word-break:break-word}
.timeline{position:relative;padding-left:1.7rem}
.timeline::before{content:"";position:absolute;left:.45rem;top:.5rem;bottom:.5rem;width:2px;background:#dbe3ec}
.tl-item{position:relative;margin-bottom:1.2rem}
.tl-dot{position:absolute;left:-1.7rem;top:.3rem;width:.95rem;height:.95rem;border-radius:50%%;background:#fff;border:3px solid #3498db}
.tl-card{border:1px solid #e6ebf1;border-radius:12px;padding:.85rem 1rem;background:#fafbfd}
.tl-head{display:flex;flex-wrap:wrap;gap:.5rem;align-items:center;margin-bottom:.35rem}
.tl-estado{font-weight:700;font-size:.78rem;color:#fff;padding:.15rem .7rem;border-radius:999px;background:#3498db}
.tl-fecha{font-size:.78rem;color:#64748b}
.tl-nota{margin-top:.45rem;font-size:.9rem;color:#334155}
.tl-fotos{display:grid;grid-template-columns:repeat(auto-fill,minmax(110px,1fr));gap:.5rem;margin-top:.6rem}
.tl-fotos img{width:100%%;height:110px;object-fit:cover;border-radius:8px;border:1px solid #e6ebf1}
.sin-historial{text-align:center;color:#64748b;padding:1.5rem 0;font-size:.92rem}
.vacio{text-align:center;padding:2.5rem 1rem}
.vacio h2{font-size:1.3rem;margin-bottom:.5rem}
.vacio p{color:#64748b;font-size:.95rem;max-width:380px;margin:0 auto}
.foot{text-align:center;color:#94a3b8;font-size:.78rem;padding:1rem;margin-top:auto}
</style></head><body>
<div class="topbar"><div class="ttl">Seguimiento de Orden</div><div class="sub">Taller - consulta pública del estado de su equipo</div></div>
<div class="wrap">%s</div>
<div class="foot">Taller SACT - Odoo</div>
</body></html>""" % (html.escape(titulo), tarjeta)  # noqa: UP031


class TallerPrint(http.Controller):
    """Boletas para impresión en pestaña limpia (sin el chrome del backend)."""

    def _boleta(self, orden_id, template_xmlid):
        orden = http.request.env["taller.orden"].browse(orden_id)
        if not orden.exists():
            return http.request.not_found()
        html = http.request.env["ir.ui.view"]._render_template(
            template_xmlid, {"docs": orden})
        return http.request.make_response(html, headers=[
            ("Content-Type", "text/html; charset=utf-8"),
        ])

    @http.route("/taller/orden/<int:orden_id>/boleta", type="http",
                auth="user", website=False, methods=["GET"])
    def boleta(self, orden_id):
        return self._boleta(orden_id, "taller_sact.report_taller_orden")

    @http.route("/taller/orden/<int:orden_id>/prealta", type="http",
                auth="user", website=False, methods=["GET"])
    def prealta(self, orden_id):
        return self._boleta(orden_id, "taller_sact.report_taller_prealta")

    @http.route("/taller/orden/<int:orden_id>/alta", type="http",
                auth="user", website=False, methods=["GET"])
    def alta(self, orden_id):
        return self._boleta(orden_id, "taller_sact.report_taller_alta")

    @http.route("/taller/pedido/<int:pedido_id>/boleta", type="http",
                auth="user", website=False, methods=["GET"])
    def boleta_pedido(self, pedido_id):
        pedido = http.request.env["taller.pedido"].browse(pedido_id)
        if not pedido.exists():
            return http.request.not_found()
        html = http.request.env["ir.ui.view"]._render_template(
            "taller_sact.report_taller_pedido", {"docs": pedido})
        return http.request.make_response(html, headers=[
            ("Content-Type", "text/html; charset=utf-8"),
        ])

    @http.route("/taller/licencia/<int:cert_id>/certificado", type="http",
                auth="user", website=False, methods=["GET"])
    def certificado_licencia(self, cert_id):
        cert = http.request.env["taller.licencia.certificado"].browse(cert_id)
        if not cert.exists():
            return http.request.not_found()
        html = http.request.env["ir.ui.view"]._render_template(
            "taller_sact.report_taller_licencia", {"docs": cert})
        return http.request.make_response(html, headers=[
            ("Content-Type", "text/html; charset=utf-8"),
        ])

    @http.route("/taller/pedidos/financiero", type="http",
                auth="user", website=False, methods=["GET"])
    def financiero_pedidos(self):
        """Reporte financiero de pedidos (como SACT reporte_financiero)."""
        from odoo import fields
        Ped = http.request.env["taller.pedido"]
        todos = Ped.search([])
        entregados = todos.filtered(lambda p: p.state == "entregado")
        pendientes = todos.filtered(lambda p: p.state == "pendiente")
        por_mes = {}
        for p in todos:
            clave = p.fecha.strftime("%Y-%m") if p.fecha else "s/f"
            m = por_mes.setdefault(clave, {"mes": clave, "total": 0, "ingresos": 0.0})
            m["total"] += 1
            m["ingresos"] += p.precio_pieza or 0.0
        html = http.request.env["ir.ui.view"]._render_template(
            "taller_sact.reporte_financiero_pedidos", {
                "total_pedidos": len(todos),
                "ingresos_brutos": sum(todos.mapped("precio_pieza")),
                "total_abonos": sum(todos.mapped("abono")),
                "saldo_pendiente": sum(todos.mapped("saldo")),
                "pedidos_entregados": len(entregados),
                "pedidos_pendientes": len(pendientes),
                "por_mes": sorted(por_mes.values(), key=lambda m: m["mes"], reverse=True)[:12],
                "hoy": fields.Datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            })
        return http.request.make_response(html, headers=[
            ("Content-Type", "text/html; charset=utf-8"),
        ])

    @http.route("/taller/reporte/altas", type="http",
                auth="user", website=False, methods=["GET"])
    def reporte_altas(self, tipo="hoy", desde=None, hasta=None, mes=None, ano=None):
        """Reporte de altas por periodo (como SACT imprimir-reporte-altas)."""
        import calendar
        from datetime import date
        from odoo import fields
        hoy = fields.Date.today()
        if tipo == "mes" and mes and ano:
            d1 = date(int(ano), int(mes), 1)
            d2 = date(int(ano), int(mes), calendar.monthrange(int(ano), int(mes))[1])
            etiqueta = "Mes de %02d/%s" % (int(mes), ano)
        elif tipo == "ano" and ano:
            d1, d2 = date(int(ano), 1, 1), date(int(ano), 12, 31)
            etiqueta = "Año %s" % ano
        elif tipo == "rango" and desde and hasta:
            d1 = fields.Date.from_string(desde)
            d2 = fields.Date.from_string(hasta)
            etiqueta = "Del %s al %s" % (d1.strftime("%d/%m/%Y"), d2.strftime("%d/%m/%Y"))
        else:
            d1 = d2 = hoy
            etiqueta = "Hoy, %s" % hoy.strftime("%d/%m/%Y")
        Orden = http.request.env["taller.orden"]
        ini = fields.Datetime.to_datetime(d1)
        fin = fields.Datetime.to_datetime(fields.Date.add(d2, days=1))
        ordenes = Orden.search(
            [("state", "=", "entregado"),
             ("fecha_salida", ">=", ini), ("fecha_salida", "<", fin)],
            order="fecha_salida desc")
        html = http.request.env["ir.ui.view"]._render_template(
            "taller_sact.reporte_altas", {
                "docs": ordenes, "total": sum(ordenes.mapped("precio")),
                "etiqueta": etiqueta})
        return http.request.make_response(html, headers=[
            ("Content-Type", "text/html; charset=utf-8"),
        ])

    @http.route("/taller/estadisticas", type="http",
                auth="user", website=False, methods=["GET"])
    def estadisticas(self, tecnico=None, desde=None, hasta=None):
        """Dashboard por técnico como SACT estadisticas.php."""
        from odoo import fields
        env = http.request.env
        Tec, Ord = env["taller.tecnico"], env["taller.orden"]
        if tecnico:
            tecs = Tec.search([("id", "=", int(tecnico))])
        else:
            tecs = Tec.search([("active", "=", True)], order="name")
        d1 = fields.Date.from_string(desde) if desde else None
        d2 = fields.Date.from_string(hasta) if hasta else None
        dom_rec, dom_alt = [], [("state", "=", "entregado")]
        if d1:
            ini = fields.Datetime.to_datetime(d1)
            dom_rec.append(("fecha_ingreso", ">=", ini))
            dom_alt.append(("fecha_salida", ">=", ini))
        if d2:
            fin = fields.Datetime.to_datetime(fields.Date.add(d2, days=1))
            dom_rec.append(("fecha_ingreso", "<", fin))
            dom_alt.append(("fecha_salida", "<", fin))
        stats = []
        for t in tecs:
            altas = Ord.search(dom_alt + [("tecnico_alta_id", "=", t.id)])
            stats.append({
                "name": t.name,
                "ordenes": Ord.search_count(dom_rec + [("tecnico_id", "=", t.id)]),
                "altas": len(altas),
                "ingresos": sum(altas.mapped("precio")),
            })
        tot_o = sum(s["ordenes"] for s in stats)
        tot_a = sum(s["altas"] for s in stats)
        tot_i = sum(s["ingresos"] for s in stats)
        for s in stats:
            s["pct_altas"] = (s["altas"] / tot_a * 100) if tot_a else 0
            s["pct_ing"] = (s["ingresos"] / tot_i * 100) if tot_i else 0
        html = env["ir.ui.view"]._render_template("taller_sact.estadisticas", {
            "stats": stats, "tot_ordenes": tot_o, "tot_altas": tot_a, "tot_ingresos": tot_i,
            "tecnicos": Tec.search([("active", "=", True)], order="name"),
            "sel_tecnico": int(tecnico) if tecnico else False,
            "desde": desde or "", "hasta": hasta or ""})
        return http.request.make_response(html, headers=[
            ("Content-Type", "text/html; charset=utf-8"),
        ])

    @http.route("/taller/reporte/insumos", type="http",
                auth="user", website=False, methods=["GET"])
    def reporte_insumos(self, desde=None, hasta=None, categoria=None,
                        proveedor=None, bajo=None):
        """Reporte de insumos filtrado (como SACT insumos.php)."""
        from odoo import fields
        dom, partes = [], []
        if desde:
            dom.append(("fecha", ">=", fields.Date.from_string(desde)))
            partes.append("desde %s" % desde)
        if hasta:
            dom.append(("fecha", "<=", fields.Date.from_string(hasta)))
            partes.append("hasta %s" % hasta)
        if categoria:
            dom.append(("categoria", "=", categoria))
            partes.append("cat=%s" % categoria)
        if proveedor:
            dom.append(("proveedor_id", "=", int(proveedor)))
            partes.append("prov=%s" % proveedor)
        if bajo == "1":
            dom.append(("bajo_minimo", "=", True))
            partes.append("bajo stock")
        docs = http.request.env["taller.insumo"].search(dom, order="fecha desc, id desc")
        html = http.request.env["ir.ui.view"]._render_template(
            "taller_sact.reporte_insumos", {
                "docs": docs, "total": sum(docs.mapped("valor_total")),
                "etiqueta": ", ".join(partes) or "todos"})
        return http.request.make_response(html, headers=[
            ("Content-Type", "text/html; charset=utf-8"),
        ])

    @http.route("/taller/reporte/campo", type="http",
                auth="user", website=False, methods=["GET"])
    def reporte_campo(self, desde=None, hasta=None, tecnico=None):
        """Reporte de trabajos de campo filtrado."""
        from odoo import fields
        dom, partes = [], []
        if desde:
            dom.append(("fecha", ">=", fields.Date.from_string(desde)))
            partes.append("desde %s" % desde)
        if hasta:
            dom.append(("fecha", "<=", fields.Date.from_string(hasta)))
            partes.append("hasta %s" % hasta)
        if tecnico:
            dom.append(("tecnico_ids", "in", int(tecnico)))
            partes.append("tecnico=%s" % tecnico)
        docs = http.request.env["taller.campo"].search(dom, order="fecha desc, id desc")
        html = http.request.env["ir.ui.view"]._render_template(
            "taller_sact.reporte_campo", {
                "docs": docs,
                "total_cobrado": sum(docs.mapped("monto_cobrado")),
                "total_gasto": sum(docs.mapped("gasto_operativo")),
                "total_neto": sum(docs.mapped("neto")),
                "total_registros": len(docs),
                "etiqueta": ", ".join(partes) or "todos"})
        return http.request.make_response(html, headers=[
            ("Content-Type", "text/html; charset=utf-8"),
        ])
