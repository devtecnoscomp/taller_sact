{
    "name": "SACT",
    "version": "18.0.1.34.0",
    "summary": "Gestión de taller: recepción, diagnóstico, reparación y entrega",
    "description": """
Taller SACT - reemplazo del módulo Repair estándar.
Replica el flujo: ESPERA -> EN REPARACION (nota) -> LISTO (pre-alta) -> ENTREGADO (alta) / DE BAJA.
Incluye equipo, cliente, técnico, accesorios, fotos (chatter/adjuntos),
actualizaciones/timeline, garantías, precios y token de seguimiento portal.
    """,
    "author": "SACT",
    "website": "https://github.com/devtecnoscomp/taller_sact",
    "category": "Services/Repair",
    "depends": ["base", "mail", "sale", "stock"],
    "data": [
        "security/ir.model.access.csv",
        "data/sequence.xml",
        "data/tecnicos.xml",
        "views/taller_orden_views.xml",
        "views/taller_pedido_views.xml",
        "views/taller_tecnico_views.xml",
        "views/taller_catalogos_views.xml",
        "views/taller_wizards_views.xml",
        "views/taller_reportes_views.xml",
        "views/taller_insumo_views.xml",
        "views/taller_campo_views.xml",
        "views/taller_licencia_views.xml",
        "views/taller_reports.xml",
        "views/taller_menus.xml",
    ],
    "demo": [],
    "installable": True,
    "application": True,
    "images": ["static/img/logo.png", "static/description/screen1.png"],
    "license": "LGPL-3",
}
