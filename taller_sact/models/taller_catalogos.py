from odoo import fields, models


class TallerTipoEquipo(models.Model):
    _name = "taller.tipo.equipo"
    _description = "Tipo de equipo (catálogo SACT)"
    _order = "name"

    name = fields.Char(string="Nombre", required=True)
    active = fields.Boolean(string="Activo", default=True)
    sact_id = fields.Integer(string="ID SACT", copy=False,
                             help="ID original en MySQL SACT para trazabilidad")
    marca_ids = fields.One2many("taller.marca", "tipo_equipo_id", string="Marcas")

    _sql_constraints = [("name_uniq", "unique(name)", "Ya existe este tipo de equipo.")]


class TallerMarca(models.Model):
    _name = "taller.marca"
    _description = "Marca por tipo de equipo (catálogo SACT)"
    _order = "name"

    name = fields.Char(string="Nombre", required=True)
    tipo_equipo_id = fields.Many2one("taller.tipo.equipo", string="Tipo de equipo", required=True)
    active = fields.Boolean(string="Activo", default=True)
    sact_id = fields.Integer(string="ID SACT", copy=False)

    _sql_constraints = [("name_tipo_uniq", "unique(name, tipo_equipo_id)",
                         "Ya existe esta marca para ese tipo de equipo.")]


class TallerTipoTrabajo(models.Model):
    _name = "taller.tipo.trabajo"
    _description = "Tipo de trabajo (catálogo SACT)"
    _order = "name"

    name = fields.Char(string="Nombre", required=True)
    active = fields.Boolean(string="Activo", default=True)
    sact_id = fields.Integer(string="ID SACT", copy=False)

    _sql_constraints = [("name_uniq", "unique(name)", "Ya existe este tipo de trabajo.")]


class TallerTipoLicencia(models.Model):
    _name = "taller.tipo.licencia"
    _description = "Tipo de licencia (catálogo SACT)"
    _order = "name"

    name = fields.Char(string="Nombre", required=True)
    descripcion = fields.Text(string="Descripción")
    active = fields.Boolean(string="Activo", default=True)
    sact_id = fields.Integer(string="ID SACT", copy=False)

    _sql_constraints = [("name_uniq", "unique(name)", "Ya existe este tipo de licencia.")]
