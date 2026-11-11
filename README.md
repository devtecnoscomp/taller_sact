# SACT — Sistema de Administración y Control de Taller

Módulo personalizado para **Odoo** que gestiona de forma integral el flujo de un **taller de servicio técnico de computación** (recepción, diagnóstico, reparación y entrega de equipos). Reemplaza el flujo estándar de reparación de Odoo con un ciclo de vida propio adaptado a las operaciones del taller.

- Rama `17.0`: versión 17.0.1.34.0
- Rama `18.0`: versión 18.0.1.34.0

Módulo técnico: `taller_sact`

## Descripción

El módulo **SACT** digitaliza el día a día del taller: desde la recepción del equipo del cliente hasta su entrega (o baja), pasando por el diagnóstico, la reparación, la pre-alta, el alta y el seguimiento público para el cliente. Incluye gestión de pedidos de piezas, insumos/costos internos, trabajos de campo (servicio en sitio), certificados de licencia con firmas y reportes filtrados con estadísticas por técnico.

## Características principales

- **Órdenes de servicio** con datos del equipo (tipo, marca, modelo, serie), cliente, técnico, accesorios, cargador, falla reportada y descripción del trabajo.
- **Flujo de estados**: `ESPERA → EN REPARACIÓN → LISTO → ENTREGADO / DE BAJA`.
- **Timeline / actualizaciones** por orden con notas y fotos (chatter y adjuntos).
- **Pre-altas**: diagnóstico, solución previa, precio estimado y código de 9 dígitos (con código de barras para escaneo).
- **Altas (entrega)**: solución aplicada, calidad del servicio, garantía, productos/refacciones usadas, precio final y fecha de salida.
- **Bajas**: motivo y observaciones (abandono, no reparable, cancelación, duplicada, etc.).
- **Pedidos de piezas** con control de abono/saldo y estado pendiente/entregado.
- **Insumos** (repuestos, consumibles, herramientas) con stock mínimo, costo y alerta de bajo stock.
- **Trabajos de campo** (servicio en sitio) con técnicos, montos cobrados y gastos (comida, combustible, materiales) y neto.
- **Certificados de licencia** con firmas, vigencia y estados borrador/emitido/anulado.
- **Catálogos** configurables: tipos de equipo, marcas, tipos de trabajo, tipos de licencia y técnicos.
- **Reportes filtrados** (altas por periodo, insumos, trabajos de campo) e **impresibles** con encabezado corporativo y código QR de WhatsApp.
- **Portal de seguimiento público** para el cliente mediante token (sin login), con timeline y fotos.
- **Notificaciones por WhatsApp** (recordatorio de equipo listo, saludo al cliente).
- **Estadísticas por técnico** (órdenes, altas, ingresos y porcentajes).

## Requisitos

- Odoo 17.0 / 18.0
- Dependencias: `base`, `mail`, `sale`, `stock`

## Instalación

1. Copie la carpeta `taller_sact` dentro del directorio de addons de su instancia de Odoo.
2. Reinicie el servidor de Odoo.
3. Active el modo desarrollador y actualice la lista de aplicaciones.
4. Instale el módulo **SACT** desde Aplicaciones.

## Uso

Desde el menú **SACT** del backend:

1. **Órdenes** → cree una nueva orden de trabajo (recepción del equipo).
2. Agregue **notas** (Nueva nota) para avanzar el estado a `EN REPARACIÓN` y compartirlas con el cliente mediante el link de seguimiento.
3. Genere la **pre-alta** cuando el equipo esté diagnosticado/reparado (pasa a `LISTO`).
4. Genere el **alta** al entregar el equipo (pasa a `ENTREGADO`).
5. Use **Generar baja** para cancelar/abandonar una orden.
6. Gestione **Pedidos**, **Insumos**, **Trabajos de campo** y **Licencias** desde sus menús.
7. Consulte **Reportes** y **Estadísticas por técnico**.

El cliente puede consultar el estado de su equipo en el portal público `/taller/seguimiento/<token>`.

## Estructura del proyecto

```
taller_sact/
├── README.md
├── .gitignore
└── taller_sact/                 # módulo Odoo
    ├── __init__.py
    ├── __manifest__.py
    ├── controllers/             # rutas HTTP (seguimiento público, impresión, reportes)
    ├── data/                    # secuencias y datos iniciales (técnicos)
    ├── doc/                     # documentación (index.rst)
    ├── models/                  # modelos de negocio
    ├── security/                # permisos de acceso
    ├── static/                  # icono, logo, descripción para la tienda
    └── views/                   # vistas, menús y reportes
```

## Ramas y versiones

| Rama | Versión Odoo |
|------|--------------|
| `17.0` | 17.0.1.34.0 |
| `18.0` / `main` | 18.0.1.34.0 |

## Licencia

LGPL-3

## Autor

SACT — https://github.com/devtecnoscomp/taller_sact
