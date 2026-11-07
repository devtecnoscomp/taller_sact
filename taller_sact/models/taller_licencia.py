from odoo import api, fields, models


class TallerLicenciaCertificado(models.Model):
    _name = "taller.licencia.certificado"
    _description = "Certificado de licencia"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"

    name = fields.Char(string="Orden", required=True, copy=False, readonly=True,
                       default="Nuevo", tracking=True)
    sact_id = fields.Integer(string="ID SACT origen", copy=False)

    orden_id = fields.Many2one("taller.orden", string="Orden", required=True,
                               ondelete="restrict", tracking=True)
    partner_id = fields.Many2one("res.partner", string="Cliente",
                                 related="orden_id.partner_id", readonly=True, store=True)
    equipo_info = fields.Char(string="Equipo", compute="_compute_equipo",
                              readonly=True, store=False)
    tipo_licencia_id = fields.Many2one("taller.tipo.licencia", string="Tipo de licencia",
                                       required=True, tracking=True)
    clave = fields.Char(string="Clave de activación", required=True, tracking=True)
    duracion = fields.Char(string="Duración", tracking=True,
                           help="Ej: 1 año, Permanente, 6 meses (SACT licencias.duracion)")
    fecha_emision = fields.Date(string="Fecha emisión", default=fields.Date.today,
                                required=True, tracking=True)
    vigente_desde = fields.Date(string="Vigente desde", default=fields.Date.today)
    vigente_hasta = fields.Date(string="Vigente hasta")
    tecnico_id = fields.Many2one("taller.tecnico", string="Técnico responsable", tracking=True)
    observaciones = fields.Text(string="Observaciones")
    state = fields.Selection(
        [("borrador", "Borrador"),
         ("emitido", "Emitido"),
         ("anulado", "Anulado")],
        string="Estado", default="borrador", required=True, tracking=True)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "Nuevo") == "Nuevo":
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "taller.licencia.certificado") or "Nuevo"
            if not vals.get("tecnico_id") and vals.get("orden_id"):
                orden = self.env["taller.orden"].browse(vals["orden_id"])
                tec = orden.tecnico_alta_id or orden.tecnico_prealta_id or orden.tecnico_id
                if tec:
                    vals["tecnico_id"] = tec.id
        return super().create(vals_list)

    @api.depends("orden_id")
    def _compute_equipo(self):
        for rec in self:
            o = rec.orden_id
            if o:
                rec.equipo_info = " ".join(x for x in [
                    o.tipo_equipo_id.name or "", o.marca_id.name or "",
                    o.modelo or "", o.numero_serie or ""] if x)
            else:
                rec.equipo_info = False

    def action_emitir(self):
        self.write({"state": "emitido"})
        for rec in self:
            rec.message_post(body="Certificado %s emitido." % rec.name)

    def action_anular(self):
        self.write({"state": "anulado"})
        for rec in self:
            rec.message_post(body="Certificado %s anulado." % rec.name)

    def print_certificado(self):
        self.ensure_one()
        return {"type": "ir.actions.act_url",
                "url": "/taller/licencia/%s/certificado" % self.id, "target": "new"}
