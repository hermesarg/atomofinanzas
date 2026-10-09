# Átomo Finanzas V2

V2 visual en paralelo a la app Streamlit actual.

## Objetivo

- Desktop amplio, simple y confiable.
- Mobile primero: pocas decisiones por pantalla, navegación inferior y acciones principales claras.
- Entradas en verde y salidas en rojo, sin usar el color como única señal.
- Electro financiero animado: trazado izquierda → derecha y partículas que recorren la señal.
- Perfil de evolución comenzando en **Átomo**.
- Transiciones suaves y soporte de movimiento reducido por accesibilidad.

## Estado

Este primer corte es un **prototipo funcional de interfaz** con datos ficticios.
Los botones de ingreso/salida abren un flujo visual, pero todavía **no escriben en Turso**.
La app Streamlit actual permanece intacta.

## Ejecutar localmente

```bash
cd web-v2
npm install
npm run dev
```

Luego abrir http://localhost:3000.

## Siguiente integración

1. Autenticación privada.
2. Capa server-side para Turso (nunca exponer el token de base en el navegador).
3. Cuentas y movimientos reales.
4. Electro calculado con las mismas reglas deterministas de la versión actual.
5. PWA instalable y notificaciones opcionales.
6. Demo pública aislada.
