# QA de la beta personal gratuita — 6 de octubre de 2026

Preparada para Streamlit Community Cloud + Turso libSQL. **No desplegada aún**: las cuentas, la URL HTTPS real y las cuotas de esos servicios se verifican al publicarla. No se contrató ningún servicio pago.

## Correcciones

- Persistencia externa de las finanzas y del propietario: sin dependencia del archivo local temporal.
- Importación inicial atómica. Las instituciones se cargan antes de las cuentas que las referencian; esto corrige un fallo por claves foráneas observado en navegador.
- Migración e importación por lotes para reducir viajes de red. Se verifica un marcador final porque libsql 0.1.11 descarta errores de executescript; un lote fallido se detecta y revierte antes del commit.
- Exportación consistente a SQLite, sin contraseñas ni tablas de acceso. Respaldos diarios en la base externa, con hasta 30 fechas de actividad.
- Conexión fallida bloquea la operación sin crear un archivo financiero local; errores de acceso, pantallas y callbacks de tasas se presentan con mensajes breves y sin secretos.
- La entrada cloud exige acceso privado y guardado remoto incluso si se omiten opciones de configuración.

## Pruebas aprobadas

- Formularios completos en SQLite local y en servidor libSQL oficial v0.24.32, driver libsql 0.1.11. Altas/modificaciones de cuentas, ingreso/gasto, transferencias propias y a terceros, tarjetas/cuotas/pagos, deudas, inversiones, comparación, instituciones, ajustes, proyección, navegación y validaciones.
- Contabilidad del historial, migraciones, rollback, formato argentino, nivel independiente de riqueza y funcionamiento sin clave de IA.
- Acceso anónimo bloqueado, activación, contraseña derivada, intentos persistentes, cierre de sesión y vencimiento/revocación.
- Chromium real: todas las secciones en claro/oscuro; móvil de 390 y 360 píxeles; pago, ingreso, cambio de tasa, carga inicial, descarga, recarga, cierre de sesión y reinicio real. 11 escenarios de la web gratuita y 45 comprobaciones adicionales del prototipo local.
- Eliminación de TODO el directorio de datos del servidor web y nuevo proceso: propietario, saldos, operaciones y tasa permanecen en la base externa.
- Importación fallida a mitad de lote revierte datos y marcador; la repetición no reemplaza datos existentes. Concurrencia, desconexión, ausencia de credenciales y respaldo financiero íntegro comprobados contra el servidor real.
- Prueba aislada del historial previo, sin publicarlo ni alterar el original: todas sus filas, columnas e identificadores se preservan al importar y exportar. El orden físico de columnas puede diferir; el contenido permanece igual.
- Inicio e importación con 120 ms añadidos por llamada al driver: completados. No sustituye medir la latencia del alojamiento real.

Las capturas y `qa_gratis/resultados.json` usan exclusivamente datos ficticios. QA simula tamaños de celular en Chromium; falta la prueba en el teléfono físico del propietario y con las cuentas reales de alojamiento. La URL debe mantenerse privada al desplegar. No se garantiza disponibilidad permanente en planes gratuitos.
