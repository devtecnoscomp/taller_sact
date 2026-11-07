{
    "name": "SACT",
    "version": "17.0.1.34.0",
    "summary": "Workshop management: reception, diagnosis, repair and delivery",
    "description": """
SACT Workshop - replacement for the standard Repair module.
Replicates the flow: WAITING -> IN REPAIR (note) -> READY (pre-delivery) -> DELIVERED (delivery) / WRITTEN OFF.
Includes equipment, customer, technician, accessories, photos (chatter/attachments),
updates/timeline, warranties, prices and portal tracking token.
    """,
    "author": "SACT",
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
        "views/taller_reports.xml",
        "views/taller_campo_views.xml",
        "views/taller_licencia_views.xml",
        "views/taller_menus.xml",
    ],
    "demo": [],
    "installable": True,
    "application": True,
    "images": ["static/img/logo.png"],
    "license": "LGPL-3",
}
