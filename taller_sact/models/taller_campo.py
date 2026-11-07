from odoo import api, fields, models


class TallerCampo(models.Model):
    _name = "taller.campo"
    _description = "Trabajo de campo (servicio en sitio)"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "fecha desc, id desc"

    name = fields.Char(string="Referencia", required=True, tracking=True,
                       help="Código de cotización o factura asociada")
    sact_id = fields.Integer(string="ID SACT origen", copy=False)
    fecha = fields.Date(string="Fecha de realización", default=fields.Date.today,
                        required=True, tracking=True)
    tecnico_ids = fields.Many2many("taller.tecnico", string="Técnicos",
                                   required=True, tracking=True)
    monto_cobrado = fields.Float(string="Monto cobrado (L.)", required=True,
                                 default=0.0, tracking=True)
    gasto_comida = fields.Float(string="Gasto - Comida (L.)", default=0.0)
    gasto_combustible = fields.Float(string="Gasto - Combustible (L.)", default=0.0)
    gasto_materiales = fields.Float(string="Gasto - Materiales (L.)", default=0.0)
    gasto_operativo = fields.Float(string="Gasto operativo (L.)",
                                  compute="_compute_totales", store=True, readonly=True)
    neto = fields.Float(string="Neto (L.)", compute="_compute_totales",
                        store=True, readonly=True)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)

    @api.depends("monto_cobrado", "gasto_comida", "gasto_combustible",
                 "gasto_materiales")
    def _compute_totales(self):
        for rec in self:
            gasto = (rec.gasto_comida or 0.0) + (rec.gasto_combustible or 0.0) + (rec.gasto_materiales or 0.0)
            rec.gasto_operativo = gasto
            rec.neto = (rec.monto_cobrado or 0.0) - gasto


class TallerReporteCampoWizard(models.TransientModel):
    _name = "taller.reporte.campo.wizard"
    _description = "Reporte de trabajos de campo filtrado"

    fecha_desde = fields.Date(string="Fecha inicial")
    fecha_hasta = fields.Date(string="Fecha final")
    tecnico_id = fields.Many2one("taller.tecnico", string="Técnico")

    def _domain(self):
        dom = []
        if self.fecha_desde:
            dom.append(("fecha", ">=", self.fecha_desde))
        if self.fecha_hasta:
            dom.append(("fecha", "<=", self.fecha_hasta))
        if self.tecnico_id:
            dom.append(("tecnico_ids", "in", self.tecnico_id.id))
        return dom

    def action_ver_lista(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Trabajos de campo (filtrado)",
            "res_model": "taller.campo",
            "view_mode": "list,form",
            "domain": self._domain(),
            "target": "current",
        }

    def action_imprimir(self):
        self.ensure_one()
        url = "/taller/reporte/campo?desde=%s&hasta=%s&tecnico=%s" % (
            self.fecha_desde or "", self.fecha_hasta or "",
            self.tecnico_id.id or "")
        return {"type": "ir.actions.act_url", "url": url, "target": "new"}
