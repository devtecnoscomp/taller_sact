from odoo import fields, models


class TallerTecnico(models.Model):
    _name = "taller.tecnico"
    _description = "Técnico del taller (empleados)"
    _order = "name"

    name = fields.Char(string="Nombre", required=True)
    telefono = fields.Char(string="Teléfono")
    active = fields.Boolean(string="Activo", default=True)
    user_id = fields.Many2one("res.users", string="Usuario Odoo vinculado",
                              help="Opcional: usuario para que el técnico entre a Odoo")
