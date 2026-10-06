# Pruebas del prototipo móvil — 5 de octubre de 2026

- Navegador real: 45 comprobaciones aprobadas en escritorio y 390/360 px, con modos claro y oscuro. Formularios móviles, tasas, pago de pendientes y recarga de SQLite.
- Formularios y navegación: altas/modificaciones de cuentas, movimientos, transferencias, tarjetas, cuotas, deudas, inversiones, comparador, entidades, ajustes y formatos argentinos aprobados.
- Carga guiada: campos obligatorios, fechas anteriores, reinicio de formulario, pendientes y tasa editable/concurrente aprobados.
- Migraciones e historial: integridad, reversión ante errores y contabilidad de registros importados aprobadas.
- Conservación: todas las tablas de una copia del cierre permanecen idénticas al recorrer la nueva aplicación.

Capturas con datos ficticios en qa_prototipo. Las pruebas no alteraron la base del usuario. Lanzadores Windows revisados; helper de red comprobado. Falta confirmar conexión desde el teléfono físico del usuario.
