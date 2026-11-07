from odoo import api, fields, models


class TallerPedido(models.Model):
    _name = "taller.pedido"
    _description = "Pedido de pieza (control independiente de órdenes, SACT)"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"

    name = fields.Char(string="Código", required=True, copy=False, readonly=True,
                       default="Nuevo", tracking=True)
    # Equivalente SACT: CONCAT('PED', LPAD(id,4,'0')). Aquí secuencia PED-0001.
    sact_id = fields.Integer(string="ID SACT origen", copy=False,
                             help="id original en MySQL SACT para migración")

    # --- Cliente (enlazado a contactos de Odoo, como en órdenes) ---
    # SACT pedidos guarda texto libre; aquí partner_id + migración por identidad->vat.
    partner_id = fields.Many2one("res.partner", string="Cliente", required=True, tracking=True)
    telefono = fields.Char(string="Teléfono", related="partner_id.phone", readonly=True)
    identidad = fields.Char(string="Identidad", related="partner_id.vat", readonly=True)

    # --- Pieza / equipo ---
    tipo_pieza = fields.Char(string="Tipo de pieza", required=True)
    marca_equipo = fields.Char(string="Marca", required=True)
    modelo_equipo = fields.Char(string="Modelo", required=True)
    serie = fields.Char(string="Número de serie")
    numero_parte = fields.Char(string="Número de parte", required=True)

    # --- Dinero ---
    precio_pieza = fields.Float(string="Precio (L.)", required=True)
    abono = fields.Float(string="Abono (L.)", default=0.0)
    saldo = fields.Float(string="Saldo (L.)", compute="_compute_saldo",
                         store=True, readonly=True)

    state = fields.Selection(
        [
            ("pendiente", "Pendiente"),
            ("entregado", "Entregado"),
        ],
        string="Estado",
        default="pendiente",
        required=True,
        tracking=True,
    )
    fecha = fields.Datetime(string="Fecha", default=fields.Datetime.now, required=True)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "Nuevo") == "Nuevo":
                vals["name"] = self.env["ir.sequence"].next_by_code("taller.pedido") or "Nuevo"
        return super().create(vals_list)

    @api.depends("precio_pieza", "abono")
    def _compute_saldo(self):
        for rec in self:
            rec.saldo = (rec.precio_pieza or 0.0) - (rec.abono or 0.0)

    def action_entregar(self):
        self.write({"state": "entregado"})

    def action_pendiente(self):
        self.write({"state": "pendiente"})

    def print_pedido(self):
        self.ensure_one()
        return {"type": "ir.actions.act_url",
                "url": "/taller/pedido/%s/boleta" % self.id, "target": "new"}
