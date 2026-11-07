import random

from odoo import api, fields, models
from odoo.exceptions import UserError


class TallerPrealtaWizard(models.TransientModel):
    _name = "taller.prealta.wizard"
    _description = "Generar pre-alta (pantalla separada SACT)"

    orden_id = fields.Many2one("taller.orden", string="Orden", required=True)
    tecnico_id = fields.Many2one("taller.tecnico", string="Técnico asignado", required=True)
    solucion_previa = fields.Text(string="Descripción de la solución/trabajo", required=True)
    precio_estimado = fields.Float(string="Precio estimado", required=True)
    codigo_prealta = fields.Char(string="Código pre-alta (9 dígitos)", readonly=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        # Código 9 dígitos único como SACT generarCodigo9Digitos() (solo si la orden no tiene)
        if not res.get("codigo_prealta"):
            res["codigo_prealta"] = self._nuevo_codigo_prealta()
        if res.get("orden_id"):
            orden = self.env["taller.orden"].browse(res["orden_id"])
            res.update(self._valores_desde_orden(orden))
        return res

    @api.onchange("orden_id")
    def _onchange_orden_id(self):
        if self.orden_id:
            for campo, valor in self._valores_desde_orden(self.orden_id).items():
                if campo in self._fields:
                    self[campo] = valor

    @api.model
    def _nuevo_codigo_prealta(self):
        Orden = self.env["taller.orden"]
        for _ in range(50):
            codigo = str(random.randint(1, 999999999)).zfill(9)
            if not Orden.search_count([("codigo_prealta", "=", codigo)]):
                return codigo
        return False

    @api.model
    def _valores_desde_orden(self, orden):
        """Si la orden ya tiene pre-alta, la carga para editar (como SACT generar-prealta.php);
        si no, prepara una nueva."""
        vals = {}
        tec = orden.tecnico_prealta_id or orden.tecnico_id
        if tec:
            vals["tecnico_id"] = tec.id
        if orden.solucion_previa:
            vals["solucion_previa"] = orden.solucion_previa
        if orden.precio_estimado:
            vals["precio_estimado"] = orden.precio_estimado
        vals["codigo_prealta"] = orden.codigo_prealta or self._nuevo_codigo_prealta()
        return vals

    def action_confirm(self):
        self.ensure_one()
        if self.orden_id.state == "entregado":
            raise UserError("Esta orden ya fue entregada. No se puede generar una pre-alta.")
        if self.orden_id.state == "baja":
            raise UserError("Esta orden está de baja. No se puede generar una pre-alta.")
        primera = not self.orden_id.codigo_prealta
        self.orden_id.write({
            "tecnico_prealta_id": self.tecnico_id.id,
            "solucion_previa": self.solucion_previa,
            "precio_estimado": self.precio_estimado,
            "codigo_prealta": self.codigo_prealta,
            "state": "listo",
            "fecha_listo": fields.Datetime.now(),
        })
        self.orden_id.message_post(body="Pre-alta %s %s: %s (estimado %s)" % (
            self.codigo_prealta, "generada" if primera else "actualizada",
            self.solucion_previa, self.precio_estimado))
        return {"type": "ir.actions.act_window_close"}


class TallerAltaWizard(models.TransientModel):
    _name = "taller.alta.wizard"
    _description = "Generar alta / entrega (pantalla separada SACT)"

    orden_id = fields.Many2one("taller.orden", string="Orden", required=True)
    codigo_scan = fields.Char(string="Escanear código de pre-alta",
                              help="Pistola lectora: enfoque aquí y escanee el código de barras de la pre-alta para cargar la orden")
    tecnico_id = fields.Many2one("taller.tecnico", string="Técnico responsable", required=True)
    reclama = fields.Char(string="Equipo entregado a")
    solucion = fields.Text(string="Solución aplicada", required=True)
    calidad = fields.Selection(
        [("Excelente", "Excelente"), ("Bueno", "Bueno"),
         ("Regular", "Regular"), ("Deficiente", "Deficiente")],
        string="Calidad del servicio", default="Excelente", required=True)
    garantia = fields.Selection(
        [("Sin Garantía", "Sin Garantía"), ("Garantía Limitada", "Garantía Limitada"),
         ("1 Semana", "1 Semana"), ("2 Semanas", "2 Semanas"), ("1 Mes", "1 Mes"),
         ("3 Meses", "3 Meses"), ("6 Meses", "6 Meses"),
         ("1 Año", "1 Año"), ("2 Años", "2 Años")],
        string="Garantía", default="1 Mes", required=True)
    productos_usados = fields.Text(string="Productos/refacciones usadas")
    precio = fields.Float(string="Precio total de reparación", required=True)
    fecha_salida = fields.Datetime(string="Fecha de alta", default=fields.Datetime.now, required=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if res.get("orden_id"):
            orden = self.env["taller.orden"].browse(res["orden_id"])
            res.update(self._valores_desde_orden(orden))
        return res

    @api.onchange("orden_id")
    def _onchange_orden_id(self):
        if self.orden_id:
            for campo, valor in self._valores_desde_orden(self.orden_id).items():
                if campo in self._fields:
                    self[campo] = valor

    @api.onchange("codigo_scan")
    def _onchange_codigo_scan(self):
        if not (self.codigo_scan or "").strip():
            return
        code = self.codigo_scan.strip()
        orden = self.env["taller.orden"].search([("codigo_prealta", "=", code)], limit=1)
        if not orden:
            self.orden_id = False
            return {"warning": {
                "title": "Pre-alta no encontrada",
                "message": "Ninguna orden tiene la pre-alta %s." % code,
                "type": "notification",
            }}
        if orden.state in ("entregado", "baja"):
            self.orden_id = False
            return {"warning": {
                "title": "Orden cerrada",
                "message": "La orden %s ya está %s." % (orden.name, orden.state.upper()),
                "type": "notification",
            }}
        self.orden_id = orden
        for campo, valor in self._valores_desde_orden(orden).items():
            if campo in self._fields:
                self[campo] = valor

    @api.model
    def _valores_desde_orden(self, orden):
        """Prellena el alta con los datos de la pre-alta existente (técnico, solución, precio)."""
        vals = {}
        tec = orden.tecnico_alta_id or orden.tecnico_prealta_id or orden.tecnico_id
        if tec:
            vals["tecnico_id"] = tec.id
        if orden.solucion_previa:
            vals["solucion"] = orden.solucion_previa
        if orden.precio_estimado:
            vals["precio"] = orden.precio_estimado
        if orden.partner_id:
            vals["reclama"] = orden.partner_id.name
        return vals

    def action_confirm(self):
        self.ensure_one()
        if self.orden_id.state in ("entregado", "baja"):
            raise UserError("La orden ya está cerrada (entregada o de baja).")
        self.orden_id.write({
            "tecnico_alta_id": self.tecnico_id.id,
            "reclama": self.reclama,
            "solucion": self.solucion,
            "calidad": self.calidad,
            "garantia": self.garantia,
            "productos_usados": self.productos_usados or "Ninguno",
            "precio": self.precio,
            "fecha_salida": self.fecha_salida,
            "state": "entregado",
        })
        self.orden_id.message_post(body="Alta generada por %s: entregado a %s por %s" % (
            self.tecnico_id.name, self.reclama or self.orden_id.partner_id.name, self.precio))
        return {"type": "ir.actions.act_window_close"}


class TallerBajaWizard(models.TransientModel):
    _name = "taller.baja.wizard"
    _description = "Generar baja (pantalla separada SACT)"

    orden_id = fields.Many2one("taller.orden", string="Orden", required=True)
    motivo_baja = fields.Selection(
        [("Abandono del equipo", "Abandono del equipo"),
         ("No se realizó el trabajo", "No se realizó el trabajo"),
         ("Cancelación del cliente", "Cancelación del cliente"),
         ("No reparable / costo elevado", "No reparable / costo elevado"),
         ("Duplicada / errónea", "Duplicada / errónea"),
         ("Otro", "Otro")],
        string="Motivo", required=True)
    observaciones_baja = fields.Text(string="Observaciones (máx 500)")

    def action_confirm(self):
        self.ensure_one()
        if self.orden_id.state == "entregado":
            raise UserError("La orden ya fue entregada. No se puede dar de baja.")
        if self.orden_id.state == "baja":
            raise UserError("La orden ya está de baja.")
        self.orden_id.write({
            "motivo_baja": self.motivo_baja,
            "observaciones_baja": (self.observaciones_baja or "")[:500],
            "state": "baja",
            "fecha_salida": fields.Datetime.now(),
        })
        self.orden_id.message_post(body="Baja: %s — %s" % (
            self.motivo_baja, self.observaciones_baja or ""))
        return {"type": "ir.actions.act_window_close"}


class TallerNotaWizard(models.TransientModel):
    _name = "taller.nota.wizard"
    _description = "Nueva nota + link de seguimiento para el cliente"

    orden_id = fields.Many2one("taller.orden", string="Orden", required=True)
    estado = fields.Char(string="Estado de la orden", required=True,
                         help="Igual que SACT: ESPERA, LISTO, EN REPARACION, E.P.A.S, ENTREGADO, DE BAJA u otro personalizado (25 car.)")
    nota = fields.Text(string="Nota del avance / estado",
                       help="Describa el avance, diagnóstico, pieza requerida, etc. (máx 4000)")
    imagen = fields.Binary(string="Foto del avance",
                           help="JPG/PNG/WEBP. Se muestra en el timeline y en el link del cliente.")
    link_result = fields.Char(string="Link generado", readonly=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if res.get("orden_id"):
            orden = self.env["taller.orden"].browse(res["orden_id"])
            res.setdefault("estado", dict(orden._fields["state"].selection).get(orden.state, "ESPERA"))
        return res

    def action_confirm(self):
        """Crea la actualización como texto libre en el timeline.
        Flujo: si la orden está en ESPERA, pasa a EN REPARACION."""
        self.ensure_one()
        if self.orden_id.state in ("entregado", "baja"):
            raise UserError("La orden ya está cerrada (entregada o de baja). No se pueden añadir notas nuevas.")
        estado = (self.estado or "").strip().upper()[:25]
        if not estado:
            raise UserError("Debe indicar el nuevo estado de la orden.")
        nota = (self.nota or "").strip()[:4000] or False
        self.orden_id.ensure_token()
        act = self.env["taller.actualizacion"].create({
            "orden_id": self.orden_id.id,
            "estado": estado,
            "nota": nota,
        })
        if self.imagen:
            self.env["ir.attachment"].create({
                "name": "avance-%s.png" % act.id,
                "datas": self.imagen,
                "res_model": "taller.actualizacion",
                "res_id": act.id,
            })
        if self.orden_id.state == "espera":
            self.orden_id.write({"state": "en_reparacion"})
        self.orden_id._compute_links()
        link = self.orden_id.link_seguimiento
        self.orden_id.message_post(
            body="Nota [%s]: %s<br/>Link cliente: %s" % (estado, nota or "-", link),
            attachment_ids=act.imagen_ids.ids)
        self.link_result = link
        return {"type": "ir.actions.act_window_close"}


class TallerReporteAltasWizard(models.TransientModel):
    _name = "taller.reporte.altas.wizard"
    _description = "Reporte de altas por periodo"

    periodo_tipo = fields.Selection(
        [("hoy", "Hoy"), ("mes", "Mes"), ("ano", "Año"), ("rango", "Rango personalizado")],
        string="Periodo", default="hoy", required=True)
    fecha_desde = fields.Date(string="Fecha inicial")
    fecha_hasta = fields.Date(string="Fecha final")
    mes = fields.Selection(
        [(str(i), nombre) for i, nombre in [
            ("1", "Enero"), ("2", "Febrero"), ("3", "Marzo"), ("4", "Abril"),
            ("5", "Mayo"), ("6", "Junio"), ("7", "Julio"), ("8", "Agosto"),
            ("9", "Septiembre"), ("10", "Octubre"), ("11", "Noviembre"), ("12", "Diciembre")]],
        string="Mes", default=lambda self: str(fields.Date.today().month))
    ano = fields.Integer(string="Año", default=lambda self: fields.Date.today().year)

    def action_confirm(self):
        self.ensure_one()
        if self.periodo_tipo == "rango" and (
                not self.fecha_desde or not self.fecha_hasta or self.fecha_desde > self.fecha_hasta):
            from odoo.exceptions import UserError
            raise UserError("Indique un rango válido (inicial <= final).")
        url = "/taller/reporte/altas?tipo=%s&desde=%s&hasta=%s&mes=%s&ano=%s" % (
            self.periodo_tipo, self.fecha_desde or "", self.fecha_hasta or "",
            self.mes or "", self.ano or "")
        return {"type": "ir.actions.act_url", "url": url, "target": "new"}
