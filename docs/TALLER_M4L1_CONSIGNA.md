# 🏦 Taller Práctico M4L1: Diseñando un Mini Pipeline Visión → JSON

## 1. Contexto y Escenario

Formas parte de un equipo de Ingeniería de IA contratado por un banco mediano para automatizar la lectura de **formularios escaneados de solicitud de crédito**.
Actualmente el banco opera con carga manual (lenta y con alta tasa de error). Tu objetivo es diseñar la arquitectura de la **versión 1.0 del pipeline Visión → Salida Estructurada** utilizando un VLM (Vision Language Model) y validación estricta con **Pydantic v2**.

El banco les entrega tres casos representativos de lo que llega por sucursal:

1. **Formulario A (`form_01_limpio.png`):** Escaneo digital limpio y legible.
2. **Formulario B (`form_02_manuscrito.png`):** Llenado a mano alzada (riesgo de confundir comas decimales o dígitos como `1` y `7`).
3. **Formulario C (`form_03_borroso.png`):** Mancha oscura/desenfoque sobre el campo de _Ingreso Mensual_ y sin firma visible.

---

## 2. Entregable por Equipo (20 minutos en Salas de Trabajo)

Designen a **1 portavoz** para compartir pantalla al regresar (tendrán **2 minutos** para presentar). Preparen un documento breve o 1-2 diapositivas que responda estos **3 bloques**:

### Bloque `<1>`: Instrucciones de Extracción y Prevención de Alucinaciones

- ¿Cómo estructuran el prompt y el esquema para obligar al modelo a **no inventar datos** cuando un campo está borroso o vacío (Abstención Visual)?
- ¿Cómo le piden al modelo que separe lo que "ve literalmente" de la conversión numérica?

### Bloque `<2>`: Reglas de Validación Determinista y Manejo de Errores

- Escriban al menos **2 reglas de negocio cruzadas** que un prompt no puede garantizar pero que su validador `Pydantic` (`@field_validator` / `@model_validator`) sí atrapará (ej. relación entre sueldo mensual y monto solicitado, o coherencia entre calidad de imagen y score de confianza).
- Definan la **Matriz de Ruteo**: ¿Bajo qué condiciones exactas un formulario va a _Aprobación Automática (STP)_, a _Bandeja Humana (HITL / Interrupt)_ o a _Rechazo por Imagen Ilegible_?

### Bloque `<3>`: El Golden Case JSON

- Redacten el **JSON esperado ideal** para el **Formulario C (el que tiene el ingreso borroso y no tiene firma)**, demostrando cómo su esquema representa la incertidumbre sin romper el tipado del sistema.
