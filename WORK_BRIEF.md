# Átomo Finanzas — brief para ChatGPT Work

## Objetivo inmediato
Tomar este proyecto como base y hacer una **pasada completa de estabilización, refactor y QA antes de agregar funciones nuevas**.

La aplicación actual es Python + Streamlit + SQLite. Ejecutar la app, navegarla y probar flujos reales; no limitarse a leer el código.

## Principio del producto
**“Las cuentas las hago yo. Las decisiones, vos.”**

- Los cálculos matemáticos pueden ser automáticos.
- Ninguna decisión financiera debe ejecutarse automáticamente.
- Las sugerencias presentan alternativas para que la persona elija.
- La IA es complementaria, no el motor de las cuentas.
- La app debe seguir siendo útil aunque la API de IA no esté disponible.

## Identidad
- Nombre: **Átomo Finanzas**.
- Mascota oficial: Átomo, robot caricaturesco de visor negro y ojos/sonrisa naranja.
- Usar `assets/atomo_logo.png` como logo principal y `assets/atomo_favicon.png` como favicon.
- `assets/atomo_avatar.png` es la versión completa.
- El estilo aventurero/cinematográfico queda reservado para futuras animaciones/logros; no es la mascota base de UI.
- Identidad cromática aún no cerrada. Priorizar legibilidad en claro y oscuro.

## Antes de agregar funciones: estabilizar
Probar y corregir:
- navegación superior y lateral;
- botones internos que cambian de sección;
- `session_state` de Streamlit;
- modo claro y oscuro;
- responsive para celular;
- persistencia SQLite y migraciones;
- cuentas;
- movimientos;
- transferencias propias y a terceros;
- tarjetas y cuotas;
- deudas;
- inversiones;
- comparador de rendimientos;
- Electro Financiero;
- perfil/niveles de Átomo;
- validaciones y formato argentino de importes;
- errores/excepciones visibles de Streamlit.

Repetir pruebas después de cada corrección importante.

## Reglas funcionales ya definidas

### Movimientos y transferencias
- `Ingreso`, `Gasto`, `Transferencia`, `Compromiso` deben mostrar categorías/campos coherentes.
- Si es gasto, no ofrecer categorías de ingreso; viceversa.
- Transferencia distingue:
  - **Entre mis cuentas** → cambia saldos, no cuenta como gasto consolidado.
  - **A otra persona** → salida real; pedir destinatario/categoría cuando corresponda.
- En transferencias propias mostrar **Sale de** y **Entra a**.

### Números
Aceptar `100000`, `100.000`, `100.000,50`, `1.234.567,89`.
Mostrar formato argentino: punto de miles, coma decimal.

### Tarjetas
- Día de cierre opcional / “No lo sé”.
- Día de vencimiento opcional.
- Para compra con crédito, priorizar: monto total, cantidad de cuotas, primera cuota/resumen y tarjeta.
- Derivar cuotas futuras matemáticamente.
- Permitir marcar cuota/compromiso como pagado o adelantado indicando de qué cuenta salió.

### Cuentas e instituciones
- “Instituciones sugeridas” es sólo un atajo, no una obligación.
- Institución obligatoria sólo cuando estructuralmente haga falta (cuenta, tarjeta, cuenta de inversión).
- Un gasto simple no debe exigir banco/institución.

### Billeteras remuneradas — prioridad posterior a estabilización
- La persona no debería conocer TNA/TEA de Mercado Pago, Ualá, Naranja X, Personal Pay, etc.
- Si la tasa puede obtenerse de fuente confiable, debe ser automática.
- Guardar fecha, fuente, condiciones y posibles topes de saldo remunerado.
- Fallback manual sólo cuando no haya fuente confiable.
- Si sale dinero de una billetera remunerada, baja el saldo remunerado y su rendimiento futuro estimado.
- Saldo líquido sin remunerar se presenta como **oportunidad para comparar**, nunca como orden de mover dinero.

### Electro Financiero
Reemplaza al viejo “Pulso”. Separa:
- **Liquidez**: capacidad de cubrir obligaciones próximas con caja.
- **Solvencia**: activos conocidos frente a deudas/compromisos.
- **Flujo**: ingresos frente a gastos y compromisos.

La señal tipo electro se vuelve más irregular cuando hay más tensión o dispersión. Evitar lenguaje alarmista. Debe explicar por qué está en ese estado.

### Gastos flexibles y disponible libre
- Usar **Gastos flexibles** en UI: comida afuera, ocio, ropa, delivery, gasto hormiga, etc.
- **Disponible libre** es distinto: queda después de vencimientos, gastos esenciales previstos y colchón objetivo.

### Sugerencias
- Mostrar **“Qué podrías hacer ahora”** y **“Una cosa para vigilar”**.
- Preferir reglas/calculadoras transparentes.
- La IA explica, no decide.

### Inversiones
- Interfaz simple: monto invertido, especie/ticker y valor actual; no obligar a cargar cantidad/unidades si no hace falta.
- Registrar por separado: aporte al broker, compra/venta de activo, retiro de capital, renta/dividendo/interés.
- Retiro de capital no es pérdida.
- Rendimiento debe considerar aportes/retiros; más adelante fechas para rentabilidad personal.

### Comparador de rendimientos
Comparar mismo monto y horizonte entre billetera, plazo fijo, letra, bono, FCI, caución y otras.
Nombres claros: **Categoría de alternativa**, **Instrumento / nombre específico**, **Horizonte**, **Liquidez / plazo de salida**.
Resultado: capital, ganancia estimada, total, diferencias, liquidez, riesgo orientativo, fuente/fecha.
No concluir que la tasa más alta es “la mejor”.

### ON — futuro
Sección educativa con 3 ON: riesgo bajo, moderado y alto.
Mostrar bajo la par / a la par / sobre la par y explicar significado. Aclarar que bajo la par no implica automáticamente “barata”. Derivar a broker/asesor/idóneo antes de decidir.

### Gamificación
Inspiración Duolingo, pero mide **calidad de administración**, nunca riqueza absoluta.
Considerar progreso relativo en liquidez, solvencia, flujo, cumplimiento, deuda, gasto hormiga/flexible, colchón, consistencia y organización.

Electro = cómo estás hoy. Nivel = trayectoria/consistencia.

Escala temática actual:
1. Partícula
2. Átomo
3. Agua
4. Carbono
5. Cadena
6. Hidrocarburo
7. Polímero
8. Proteína
9. ADN

`Agua` funciona como nivel aproximadamente estándar/medio.
No mostrar fórmula ni umbrales exactos; sí explicar qué conductas influyen. Evitar castigos bruscos por un mes difícil.

### UX
Regla central: **si un dato puede obtenerse de forma confiable sin preguntárselo al usuario, no se lo preguntamos**.
La interfaz debe sentirse como responder pocas preguntas simples, no llenar un formulario administrativo.
- obligatorios con `*`;
- opcionales explícitos;
- ayudas contextuales cortas;
- navegación siempre accesible;
- mobile-first;
- densidad visual compacta.

## Arquitectura sugerida
Si `app.py` ya es demasiado grande, dividir en módulos (`core/`, `pages/`, `assets/`). No es obligatorio respetar una estructura exacta si hay una mejor.

## Seguridad
- No incluir, pedir ni imprimir API keys.
- `OPENAI_API_KEY` externa al código (`.env` o variable de entorno).
- No subir `.env`, base real ni backups personales.

## Entrega esperada
Antes de entregar:
1. instalar dependencias;
2. ejecutar la app;
3. recorrer todas las secciones;
4. probar formularios principales;
5. corregir errores;
6. repetir pruebas;
7. probar desktop/móvil;
8. comprobar claro/oscuro.

Entregar:
- proyecto completo funcionando;
- ZIP final;
- bugs corregidos;
- decisiones de arquitectura;
- pruebas realizadas;
- mejoras futuras deliberadamente no implementadas.
