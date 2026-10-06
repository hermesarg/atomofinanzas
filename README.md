# Átomo Finanzas — beta personal gratuita

**Las cuentas las hago yo. Las decisiones, vos.**

Proyecto preparado para Streamlit Community Cloud privado y una base Turso de motor **libSQL**, en sus planes gratuitos. No se creó ningún servicio pago. Código alojado en el repositorio privado `hermesarg/atomofinanzas`. La entrada personal es `app_cloud.py`; `app_demo.py` permite levantar una demostración pública separada con datos ficticios y una base temporal por sesión.

La entrada para la web es `app_cloud.py`: obliga a acceso privado, guardado externo y horario argentino. `app.py` conserva el funcionamiento local con SQLite. No hay registro público de usuarios ni decisiones financieras automáticas. La IA es opcional; `OPENAI_API_KEY` permanece externa y no es necesaria para usar la beta.

## Puesta en línea

1. Repositorio privado: https://github.com/hermesarg/atomofinanzas. El proyecto se carga en su raíz, rama `main`. Nunca subir la base personal, respaldos ni secretos.
2. Crear una cuenta gratuita en https://turso.tech y una base vacía de motor **libSQL** (no el motor nuevo Turso). Copiar su URL y el token de acceso directamente al panel privado del alojamiento. No pegarlos en el chat. No activar planes pagos ni facturación por excedentes.
3. En https://share.streamlit.io conectar GitHub y desplegar ese repositorio, rama `main`, archivo **`app_cloud.py`**, Python **3.12**. En Advanced settings → Secrets completar las tres variables del ejemplo con valores reales. El código de activación debe ser aleatorio y de al menos 32 caracteres; se usa una sola vez para crear el propietario.
4. Verificar App settings → Sharing → **Only specific people**. Mantener exclusivamente al propietario; no compartir invitaciones. La app tiene además su usuario y contraseña internos.
5. Abrir la URL privada y crear el acceso. Contraseña de 12 a 256 caracteres. Cerrar la app local y, desde Inicio → Traer mis datos de la PC, elegir la **última** copia de `datos/finanzas.db`. Revisar el resumen antes de confirmar. Hacerlo antes de cargar nuevas operaciones en la web.
6. Comprobar desde el celular un ingreso y un gasto, el historial y el saldo, cerrar sesión, volver a entrar y descargar un respaldo. Solo después usar la URL como registro diario.

Los planes gratuitos tienen límites y la app puede dormir sin uso. Hay que verificar esos límites al crear las cuentas. Guardar en Turso evita depender del disco temporal de Streamlit; no convierte los dos proveedores en un servicio sin límites. Las condiciones vigentes se consultan en https://docs.streamlit.io/deploy/streamlit-community-cloud y https://turso.tech/pricing.

## Datos y respaldos

Cada formulario confirmado guarda en la base externa. Si la conexión falla no se escribe en una base local de emergencia. Ante un error de confirmación, revisar el historial antes de repetir: una caída de red durante el commit puede impedir recibir la confirmación aunque la operación se haya guardado.

La importación inicial es una transacción: conserva identificadores, entidades, bancos, cuentas, movimientos, tarjetas, deudas, inversiones y configuración. Se bloquea después de importar o cuando ya existen registros. No reemplaza cargas posteriores. Los datos de acceso no se importan ni salen en los respaldos financieros.

Más → Ajustes → Mis respaldos permite descargar una base SQLite completa, compatible con la versión local. También se guarda una copia diaria en la base externa cuando hay actividad, hasta 30 fechas. Estos respaldos dependen del mismo proveedor: conservar una copia descargada fuera del alojamiento.

PC y web son registros independientes; no hay sincronización automática entre ambos. Después de importar, elegir la web para las cargas cotidianas. Los dispositivos conectados a la misma web consultan la misma base externa.

Si se pierde la contraseña, la pantalla de ingreso ofrece **Olvidé mi contraseña**. Pide el usuario y el código privado `ATOMO_SETUP_TOKEN` del alojamiento, y genera una contraseña nueva sin tocar cuentas, movimientos, tarjetas ni inversiones. `recuperar_acceso.py` y el panel de Turso quedan como vías administrativas de emergencia.

## Períodos financieros

La web separa **fecha real** y **período financiero**. Al comenzar, el propietario puede elegir mes calendario, día fijo de cobro, número de día hábil, confirmación manual al cobrar el sueldo o inicio totalmente manual. Cada período guarda su propio inicio, fin y criterio; cambiar la preferencia sólo afecta ciclos futuros y no reescribe períodos ya cerrados. El encabezado muestra siempre cómo se está computando el período activo.

## Demo pública

Para pruebas de terceros, crear una **segunda app** en Streamlit desde el mismo repositorio y elegir `app_demo.py` como Main file path. No cargar los Secrets de Turso ni el token del propietario en esa app. Cada sesión recibe una SQLite temporal con datos ficticios; puede registrar, editar y navegar sin tocar la base personal. Un botón **Reiniciar demo** restaura los datos de prueba de esa sesión.

## Ejecución local y pruebas

Python 3.12. Instalar `python -m pip install -r requirements-lock.txt`. Ejecutar `python -m streamlit run app.py` para SQLite local. Para simular el alojamiento con credenciales externas: `python -m streamlit run app_cloud.py`. Los secretos se configuran mediante variables de entorno o `.streamlit/secrets.toml`, siempre fuera del repositorio.

`requirements.txt` contiene las dependencias directas; `requirements-lock.txt` fija las versiones de producción probadas. `requirements-dev.txt` añade Playwright para pruebas de navegador.

Pruebas locales: `python tests/check_flows.py`, `check_quick.py`, `check_history_accounting.py`, `check_migration_and_ai.py` y `check_web_private.py`. Navegador: `python tests/check_browser_prototype.py`.

Pruebas remotas reales: indicar `SQLD_QA_BINARY` con un ejecutable oficial `sqld` y ejecutar `tests/check_remote_storage.py`, `tests/check_remote_flows.py` y `tests/check_browser_free.py`. Crean un servidor aislado con datos ficticios y usan el driver libsql por HTTP local. No requieren ni consultan la base personal. El HTTP de pruebas está limitado a localhost y una opción explícita; la web exige TLS.

Resultados y límites de QA: `docs/QA_Web_Gratis.md`.

## Mejoras futuras deliberadamente pendientes

- Registro de varias personas y separación de bases por usuario.
- Rediseño visual del Electro Financiero.
- Tasas automáticas con fuente, fecha y condiciones verificadas.
- Sincronización PC/web e importación recurrente de extractos.
- Publicación para terceros, dominio propio y planes pagos.

Esta entrega adapta el alojamiento y corrige el guardado, la importación y el manejo de errores. Conserva los cinco menús y los formularios simples ya probados; no agrega productos financieros.
