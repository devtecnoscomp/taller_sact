import secrets
from urllib.parse import quote

from odoo import api, fields, models


class TallerOrden(models.Model):
    _name = "taller.orden"
    _description = "Orden de taller SACT"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"

    name = fields.Char(string="Orden", required=True, copy=False, readonly=True,
                       default="Nuevo", tracking=True)
    # Equivalente SACT: ordenes_trabajo.codigo_orden (INT AI). Aquí usamos secuencia legible.
    sact_codigo_orden = fields.Integer(string="Código SACT origen", copy=False, help="codigo_orden original en MySQL SACT para migración")

    partner_id = fields.Many2one("res.partner", string="Cliente", required=True, tracking=True)
    # SACT clientes.identificacion -> res.partner.vat (migración)

    tecnico_id = fields.Many2one("taller.tecnico", string="Técnico recepción", tracking=True)
    # Quien recibió la orden. No lo pisan los wizards (como SACT ordenes_trabajo.coduser).
    tecnico_prealta_id = fields.Many2one("taller.tecnico", string="Técnico pre-alta", tracking=True,
                                         help="Quien diagnosticó (SACT pre_altas.coduser_tecnico)")
    tecnico_alta_id = fields.Many2one("taller.tecnico", string="Técnico que realizó el trabajo", tracking=True,
                                      help="Quien trabajó/entregó el equipo (SACT altas.coduser_alt). Puede diferir del de recepción.")

    # --- Equipo (una orden = un equipo, como en SACT; catálogos en Parámetros) ---
    tipo_equipo_id = fields.Many2one("taller.tipo.equipo", string="Tipo de equipo", tracking=True)
    marca_id = fields.Many2one("taller.marca", string="Marca", tracking=True)
    tipo_trabajo_id = fields.Many2one("taller.tipo.trabajo", string="Tipo de trabajo")

    @api.onchange("tipo_equipo_id")
    def _onchange_tipo_equipo_id(self):
        if self.marca_id and self.marca_id.tipo_equipo_id != self.tipo_equipo_id:
            self.marca_id = False
        if self.tipo_equipo_id:
            return {"domain": {"marca_id": [("tipo_equipo_id", "=", self.tipo_equipo_id.id)]}}
        return {"domain": {"marca_id": []}}
    modelo = fields.Char(string="Modelo")
    numero_serie = fields.Char(string="N° Serie", tracking=True)
    defecto_previo = fields.Text(string="Defecto previo")
    descripcion_problema = fields.Text(string="Falla reportada", required=True)
    accesorios = fields.Text(string="Accesorios")
    cargador = fields.Selection([("Si", "Sí"), ("No", "No"), ("No Aplica", "No Aplica")], string="Cargador", default="No Aplica")
    descripcion_trabajo = fields.Text(string="Descripción del trabajo")

    # Flujo: ESPERA -> EN REPARACION (al agregar nota) -> LISTO (pre-alta) -> ENTREGADO (alta). BAJA solo por baja.
    state = fields.Selection(
        [
            ("espera", "ESPERA"),
            ("en_reparacion", "EN REPARACION"),
            ("listo", "LISTO"),
            ("entregado", "ENTREGADO"),
            ("baja", "DE BAJA"),
        ],
        string="Estado",
        default="espera",
        required=True,
        tracking=True,
    )
    fecha_ingreso = fields.Datetime(string="Fecha ingreso", default=fields.Datetime.now, required=True)
    fecha_salida = fields.Datetime(string="Fecha salida", tracking=True)
    fecha_listo = fields.Datetime(string="Fecha listo (pre-alta)", copy=False,
                                  help="Cuándo quedó reparada y pendiente de entrega.")
    dias_listo = fields.Integer(string="Días esperando", compute="_compute_dias_listo",
                                help="Días desde que está lista sin entregar.")
    telefono_cliente = fields.Char(string="Teléfono cliente", related="partner_id.phone", readonly=True)
    token_seguimiento = fields.Char(string="Token seguimiento", copy=False, readonly=True)
    codigo_prealta = fields.Char(string="Código pre-alta (9 dígitos)", copy=False, tracking=True)
    link_seguimiento = fields.Char(string="Link cliente", compute="_compute_links", store=False)
    whatsapp_link = fields.Char(string="Enviar por WhatsApp", compute="_compute_links", store=False)

    # --- Pre-alta / Alta (diagnóstico y entrega) ---
    solucion_previa = fields.Text(string="Solución previa (pre-alta)")
    precio_estimado = fields.Float(string="Precio estimado")
    solucion = fields.Text(string="Solución (alta)")
    calidad = fields.Selection(
        [("Excelente", "Excelente"), ("Bueno", "Bueno"), ("Regular", "Regular"), ("Deficiente", "Deficiente")],
        string="Calidad",
    )
    garantia = fields.Selection(
        [
            ("Sin Garantía", "Sin Garantía"),
            ("Garantía Limitada", "Garantía Limitada"),
            ("1 Semana", "1 Semana"),
            ("2 Semanas", "2 Semanas"),
            ("1 Mes", "1 Mes"),
            ("3 Meses", "3 Meses"),
            ("6 Meses", "6 Meses"),
            ("1 Año", "1 Año"),
            ("2 Años", "2 Años"),
        ],
        string="Garantía",
        default="Sin Garantía",
    )
    precio = fields.Float(string="Precio final", tracking=True)
    productos_usados = fields.Text(string="Productos/refacciones usadas")
    reclama = fields.Char(string="Entregado a (reclama)")
    motivo_baja = fields.Char(string="Motivo de baja")
    observaciones_baja = fields.Text(string="Observaciones baja")

    actualizacion_ids = fields.One2many("taller.actualizacion", "orden_id", string="Actualizaciones / Timeline")
    certificado_ids = fields.One2many("taller.licencia.certificado", "orden_id", string="Certificados de licencia")
    sale_order_id = fields.Many2one("sale.order", string="Cotización/Venta", copy=False)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "Nuevo") == "Nuevo":
                vals["name"] = self.env["ir.sequence"].next_by_code("taller.orden") or "Nuevo"
            if not vals.get("token_seguimiento"):
                vals["token_seguimiento"] = secrets.token_hex(16)
        return super().create(vals_list)

    @api.depends("token_seguimiento")
    def _compute_links(self):
        base = self.env["ir.config_parameter"].sudo().get_param(
            "web.base.url", "http://localhost:8069"
        ).rstrip("/")
        for rec in self:
            if rec.token_seguimiento:
                link = "%s/taller/seguimiento/%s" % (base, rec.token_seguimiento)
                rec.link_seguimiento = link
                rec.whatsapp_link = "https://wa.me/?text=" + (
                    "Hola, le compartimos el enlace para consultar el estado de su equipo:\n" + link
                )
            else:
                rec.link_seguimiento = False
                rec.whatsapp_link = False

    def ensure_token(self):
        """Como SACT obtenerTokenSeguimiento(): genera y persiste si no existe."""
        for rec in self:
            if not rec.token_seguimiento:
                rec.token_seguimiento = secrets.token_hex(16)
        return True

    @api.depends("fecha_listo", "state")
    def _compute_dias_listo(self):
        hoy = fields.Date.today()
        for rec in self:
            if rec.fecha_listo and rec.state == "listo":
                rec.dias_listo = (hoy - rec.fecha_listo.date()).days
            else:
                rec.dias_listo = 0

    def action_recordatorio(self):
        """Abre WhatsApp recordando que el equipo ya está reparado (solo LISTO)."""
        from odoo.exceptions import UserError
        self.ensure_one()
        if self.state != "listo":
            raise UserError("Solo se envían recordatorios de equipos listos sin entregar.")
        tel = "".join(c for c in (self.partner_id.phone or self.partner_id.mobile or "") if c.isdigit())
        if not tel:
            raise UserError("El cliente %s no tiene teléfono registrado." % self.partner_id.name)
        if len(tel) == 8:
            tel = "504" + tel
        primer = (self.partner_id.name or "").split(" ")[0]
        equipo = " ".join(x for x in [self.tipo_equipo_id.name if self.tipo_equipo_id else "",
                                      self.marca_id.name if self.marca_id else "",
                                      self.modelo or ""] if x)
        msg = ("%s, le recordamos que su equipo (%s) ya está reparado y listo para entrega. "
               "Orden %s, total L. %s. ¡Lo esperamos!" % (primer, equipo, self.name, self.precio_estimado))
        return {"type": "ir.actions.act_url",
                "url": "https://wa.me/%s?text=%s" % (tel, quote(msg)), "target": "new"}

    # --- Lanzadores de pantallas separadas (wizards), con la orden preseleccionada ---
    def action_wizard_prealta(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Generar pre-alta",
            "res_model": "taller.prealta.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_orden_id": self.id},
        }

    def action_wizard_alta(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Generar alta",
            "res_model": "taller.alta.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_orden_id": self.id},
        }

    def action_wizard_baja(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Generar baja",
            "res_model": "taller.baja.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_orden_id": self.id},
        }

    def action_wizard_nota(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Nueva nota",
            "res_model": "taller.nota.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_orden_id": self.id},
        }

    def action_listo(self):
        self._check_abierta()
        self.write({"state": "listo"})

    def action_en_reparacion(self):
        self._check_abierta()
        self.write({"state": "en_reparacion"})

    def action_entregar(self):
        self._check_abierta()
        self.write({"state": "entregado", "fecha_salida": fields.Datetime.now()})

    def action_baja(self):
        self._check_abierta()
        self.write({"state": "baja", "fecha_salida": fields.Datetime.now()})

    def action_espera(self):
        self._check_abierta()
        self.write({"state": "espera"})

    def _check_abierta(self):
        from odoo.exceptions import UserError
        if any(s in ("entregado", "baja") for s in self.mapped("state")):
            raise UserError("La orden ya está cerrada (entregada o de baja). No se puede modificar su estado.")

    def print_orden(self):
        self.ensure_one()
        return {"type": "ir.actions.act_url",
                "url": "/taller/orden/%s/boleta" % self.id, "target": "new"}

    def action_whatsapp(self):
        """Abre WhatsApp saludando al cliente según la hora (como SACT)."""
        from odoo.exceptions import UserError
        self.ensure_one()
        tel = "".join(c for c in (self.partner_id.phone or self.partner_id.mobile or "") if c.isdigit())
        if not tel:
            raise UserError("El cliente %s no tiene teléfono registrado." % self.partner_id.name)
        if len(tel) == 8:
            tel = "504" + tel
        hora = fields.Datetime.context_timestamp(self, fields.Datetime.now()).hour
        saludo = "Buenos días" if 5 <= hora < 12 else ("Buenas tardes" if hora < 19 else "Buenas noches")
        primer = (self.partner_id.name or "").split(" ")[0]
        msg = "%s, %s, le saludamos de parte del área de soporte técnico de Tecnos Comp." % (saludo, primer)
        return {"type": "ir.actions.act_url",
                "url": "https://wa.me/%s?text=%s" % (tel, quote(msg)), "target": "new"}

    def print_prealta(self):
        self.ensure_one()
        return {"type": "ir.actions.act_url",
                "url": "/taller/orden/%s/prealta" % self.id, "target": "new"}

    def generar_prealta(self):
        """Abre el wizard 'Generar pre-alta' (botón Nuevo en el listado de Pre-altas)."""
        return {
            "type": "ir.actions.act_window",
            "name": "Generar pre-alta",
            "res_model": "taller.prealta.wizard",
            "views": [[False, "form"]],
            "target": "new",
        }

    def print_alta(self):
        self.ensure_one()
        return {"type": "ir.actions.act_url",
                "url": "/taller/orden/%s/alta" % self.id, "target": "new"}

    def action_generar_certificado(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Generar certificado de licencia",
            "res_model": "taller.licencia.certificado",
            "view_mode": "form",
            "target": "current",
            "context": {"default_orden_id": self.id},
        }
