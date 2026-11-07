from odoo import api, fields, models


class TallerInsumo(models.Model):
    _name = "taller.insumo"
    _description = "Insumo de taller"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "fecha desc, id desc"

    name = fields.Char(string="Insumo", required=True, tracking=True)
    sact_id = fields.Integer(string="ID SACT origen", copy=False,
                             help="id original en MySQL SACT para futura migración")
    categoria = fields.Selection(
        [("repuesto", "Repuesto"),
         ("consumible", "Consumible"),
         ("herramienta", "Herramienta"),
         ("otro", "Otro")],
        string="Categoría", required=True, default="repuesto", tracking=True)
    cantidad = fields.Float(string="Cantidad / Existencia", default=0.0, required=True, tracking=True)
    stock_minimo = fields.Float(string="Stock mínimo", default=0.0)
    costo = fields.Float(string="Costo unit. (L.)", required=True, default=0.0)
    valor_total = fields.Float(string="Gasto total (L.)", compute="_compute_valores",
                               store=True, readonly=True)
    bajo_minimo = fields.Boolean(string="Bajo stock", compute="_compute_valores",
                                 store=True)
    proveedor_id = fields.Many2one("res.partner", string="Proveedor", tracking=True)
    fecha = fields.Date(string="Fecha registro", default=fields.Date.today, required=True, tracking=True)
    active = fields.Boolean(string="Activo", default=True)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)

    @api.depends("cantidad", "costo", "stock_minimo")
    def _compute_valores(self):
        for rec in self:
            rec.valor_total = (rec.cantidad or 0.0) * (rec.costo or 0.0)
            rec.bajo_minimo = (rec.cantidad or 0.0) <= (rec.stock_minimo or 0.0)


class TallerReporteInsumosWizard(models.TransientModel):
    _name = "taller.reporte.insumos.wizard"
    _description = "Reporte de insumos filtrado"

    fecha_desde = fields.Date(string="Fecha inicial")
    fecha_hasta = fields.Date(string="Fecha final")
    categoria = fields.Selection(
        [("repuesto", "Repuesto"),
         ("consumible", "Consumible"),
         ("herramienta", "Herramienta"),
         ("otro", "Otro")],
        string="Categoría")
    proveedor_id = fields.Many2one("res.partner", string="Proveedor")
    solo_bajo_stock = fields.Boolean(string="Solo bajo stock", default=False)

    def _domain(self):
        dom = []
        if self.fecha_desde:
            dom.append(("fecha", ">=", self.fecha_desde))
        if self.fecha_hasta:
            dom.append(("fecha", "<=", self.fecha_hasta))
        if self.categoria:
            dom.append(("categoria", "=", self.categoria))
        if self.proveedor_id:
            dom.append(("proveedor_id", "=", self.proveedor_id.id))
        if self.solo_bajo_stock:
            dom.append(("bajo_minimo", "=", True))
        return dom

    def action_ver_lista(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Insumos (filtrado)",
            "res_model": "taller.insumo",
            "view_mode": "list,form",
            "domain": self._domain(),
            "target": "current",
        }

    def action_imprimir(self):
        self.ensure_one()
        url = "/taller/reporte/insumos?desde=%s&hasta=%s&categoria=%s&proveedor=%s&bajo=%s" % (
            self.fecha_desde or "", self.fecha_hasta or "",
            self.categoria or "", self.proveedor_id.id or "",
            "1" if self.solo_bajo_stock else "")
        return {"type": "ir.actions.act_url", "url": url, "target": "new"}
