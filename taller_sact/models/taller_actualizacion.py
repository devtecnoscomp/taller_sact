from odoo import fields, models


class TallerActualizacion(models.Model):
    _name = "taller.actualizacion"
    _description = "Actualización de orden (timeline SACT)"
    _order = "fecha desc, id desc"

    orden_id = fields.Many2one("taller.orden", string="Orden", required=True, ondelete="cascade")
    estado = fields.Char(string="Estado reportado")
    nota = fields.Text(string="Nota", required=True)
    user_id = fields.Many2one("res.users", string="Usuario", default=lambda self: self.env.user)
    fecha = fields.Datetime(string="Fecha", default=fields.Datetime.now)
    imagen_ids = fields.One2many("ir.attachment", "res_id", string="Fotos",
                                 domain=[("res_model", "=", "taller.actualizacion")],
                                 help="Fotos del avance")
