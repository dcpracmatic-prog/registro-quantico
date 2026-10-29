# Verifiable Quantum Circuit Compilation

Repositorio de trabajo y documentación para la competencia **Google Verifiable Quantum Circuit Compilation**, enfocada en la optimización de circuitos cuánticos mediante agentes de IA, compilación automática y verificación clásica eficiente.

## Competencia

Dirección oficial de la competencia:

https://www.kaggle.com/competitions/google-verifiable-quantum-circuit-compilation

---

# Introducción

La compilación de algoritmos cuánticos tolerantes a fallos sigue siendo uno de los mayores desafíos de la computación cuántica. Un mismo algoritmo puede implementarse mediante numerosas estrategias de aritmética reversible, administración de ancillas, aproximaciones numéricas y esquemas de uncomputación, generando espacios de búsqueda extremadamente grandes.

Tradicionalmente, la optimización de estos circuitos requería meses de trabajo manual por parte de investigadores especializados. Este proyecto propone un enfoque diferente: utilizar agentes de IA para explorar automáticamente miles de variantes y evaluar cada una mediante mecanismos de verificación clásica rápidos y reproducibles.

La competencia se centra en encontrar compilaciones más eficientes para tres problemas científicos reales que actualmente representan algunos de los mayores costos de los algoritmos cuánticos modernos.

---

# Idea Principal

La propuesta parte de una observación importante:

Muchos de los subcircuitos más costosos de los algoritmos cuánticos prácticos no generan superposiciones arbitrarias internamente.

En su lugar utilizan principalmente:

- Lógica reversible clásica.
- Operaciones de fase.
- Measurement-Based Uncomputation.
- Tablas de consulta cuánticas.
- Aritmética reversible.

Cuando se restringen los circuitos a estas características es posible:

- Simularlos eficientemente de forma clásica.
- Verificar automáticamente millones de casos.
- Permitir optimización iterativa mediante IA.
- Explorar espacios de diseño mucho más grandes que los abordables manualmente.

---

# Kickmix

La base de toda la competencia es el modelo de circuitos **Kickmix**.

Un circuito Kickmix restringe las operaciones permitidas a un conjunto de puertas que mantiene verificabilidad clásica.

## Tipos de operaciones permitidas

### Lógica reversible

- X
- CX (CNOT)
- CCX (Toffoli)
- SWAP

### Operaciones de fase

- Z
- CZ
- CCZ
- Z_POW
- NEG

### Operaciones de medición y limpieza

- HMR (Hadamard Measurement Reset)
- R (Reset)

### Operaciones clásicas auxiliares

- BIT_STORE0
- BIT_STORE1
- BIT_INVERT

---

## Ventajas de Kickmix

Con estas restricciones:

- Los estados base se transforman en otros estados base.
- No es necesario almacenar vectores de estado completos.
- La simulación escala linealmente con el número de puertas.
- Los circuitos pueden verificarse mediante fuzz testing clásico.

Esto permite ejecutar procesos de evaluación extremadamente rápidos incluso sobre circuitos con cientos de millones de operaciones.

---

# Sistema de Verificación

La competencia utiliza un mecanismo de evaluación totalmente automático.

## Fuzz Testing

Cada circuito es probado contra grandes cantidades de entradas generadas automáticamente.

El objetivo no es demostrar equivalencia formal perfecta, sino estimar la probabilidad real de fallo del circuito.

Esto permite aceptar:

- Aproximaciones numéricas.
- Truncamientos controlados.
- Optimizaciones agresivas.

siempre que mantengan tasas de error aceptables.

---

## Fiat-Shamir Heuristic

Para evitar que los participantes optimicen sus soluciones exclusivamente para un conjunto fijo de pruebas:

1. Se calcula el SHA-256 del circuito enviado.
2. Ese hash genera la semilla de los casos de prueba.
3. Cualquier cambio en el circuito produce automáticamente nuevos desafíos.

Beneficios:

- Evaluación reproducible.
- No existen test cases secretos masivos.
- Verificación determinista.
- Difícil sobreajustar una solución.

---

## Qué se verifica

Cada ejecución valida:

- Registros de entrada y salida.
- Correctitud lógica.
- Correctitud de fase.
- Limpieza de ancillas.
- Uncomputación adecuada.
- Tolerancias numéricas definidas para cada benchmark.

---

# Infraestructura de Software

## Qualtran

Framework de Google Quantum AI utilizado para:

- Construcción de circuitos.
- Modelado de algoritmos.
- Generación de implementaciones de referencia.

---

## Kickmix Simulator

Implementación en:

- C++20
- Python

Proporciona:

- Construcción rápida de circuitos.
- Serialización eficiente.
- Simulación SIMD.
- Visualización de costos.
- Flamecharts de Toffolis y qubits.

---

# Benchmark 1
# Inverse Square Root for Coulomb Simulation

## Problema

La simulación cuántica de sistemas físicos requiere calcular repetidamente:

$$
\frac{1}{\sqrt{x}}
$$

donde:

$$
x=(x_i-x_j)^2+(y_i-y_j)^2+(z_i-z_j)^2
$$

Este cálculo aparece directamente en:

- Simulación de interacciones Coulombianas.
- Física de plasmas.
- Materia densa caliente.
- Diseño de reactores de fusión.

---

## Importancia

La evolución temporal de los electrones bajo el Hamiltoniano Coulombiano depende de este cálculo.

El costo total de estas simulaciones está dominado por la evaluación repetida de distancias entre partículas.

Reducir el costo de este subcircuito impacta directamente en:

- Recursos requeridos.
- Tiempo de ejecución.
- Escalabilidad futura.

---

## Implementación de Referencia

La solución base sigue una estrategia inspirada en el famoso algoritmo:

**Fast Inverse Square Root (Quake III Arena)**

El procedimiento incluye:

### 1. Normalización

El valor de entrada se reescala al intervalo:

$$
[1,4)
$$

para reducir costos aritméticos.

### 2. Aproximación Inicial

Se utiliza interpolación cúbica por segmentos.

### 3. Newton-Raphson

Se aplica una iteración para alcanzar precisión de aproximadamente 24 bits.

### 4. Phase Kickback

El resultado se convierte en una fase cuántica.

### 5. Uncomputation

Se limpian todos los registros auxiliares.

---

## Objetivo de Optimización

Los participantes pueden mejorar:

- Aproximación polinomial.
- Estrategias de normalización.
- Newton-Raphson.
- Tablas QROM.
- Gestión de ancillas.
- Costos de multiplicación.

---

## Métrica

Minimizar:

$$
Score = Q \times C
$$

donde:

- Q = qubits utilizados.
- C = costo Toffoli equivalente.

---

# Benchmark 2
# Reed-Solomon Decoding for DQI

## Contexto

El benchmark surge del algoritmo:

**Decoded Quantum Interferometry (DQI)**

DQI transforma ciertos problemas de optimización en problemas de decodificación de códigos correctores de errores.

---

## Problema Subyacente

Optimal Polynomial Intersection (OPI)

Se busca encontrar polinomios de bajo grado que satisfagan la mayor cantidad posible de restricciones definidas sobre campos finitos.

Este problema es atractivo porque:

- Las soluciones pueden verificarse eficientemente de forma clásica.
- Encontrarlas es extremadamente costoso.

---

## Rol de Reed-Solomon

DQI utiliza:

- Reed-Solomon Codes.
- Dual Reed-Solomon Codes.
- Syndrome Decoding.

La preparación cuántica de los estados depende críticamente de recuperar errores a partir de síndromes.

La decodificación se convierte entonces en el principal cuello de botella.

---

## Implementación Base

El decoder de referencia utiliza:

### Solución de la Ecuación Clave

Mediante:

- Extended Euclidean Algorithm (EEA)

### Localización de Errores

Mediante:

- Chien Search

### Recuperación de Símbolos

Mediante:

- Fórmula de Forney

### Limpieza

Mediante:

- Measurement-Based Uncomputation

---

## Espacio de Optimización

Los agentes pueden explorar:

- Nuevas estrategias de decodificación.
- Reordenamiento de operaciones.
- Gestión de workspace.
- Simplificaciones algebraicas.
- Implementaciones más eficientes de aritmética finita.

---

## Métrica

La métrica considera simultáneamente:

- Número de qubits.
- Número de Toffolis.
- Probabilidad certificada de error.

La penalización crece cuando aumenta la tasa de fallo.

---

# Benchmark 3
# Quantum Chemistry Block Encoding

## Contexto

Las simulaciones modernas de química cuántica utilizan representaciones comprimidas de Hamiltonianos electrónicos.

El principal costo computacional suele encontrarse en:

- Quantum Lookup Tables.
- Block-Encoding.
- State Preparation.
- Rotaciones de Majorana.

---

## Objetivo General

Construir una representación eficiente del Hamiltoniano minimizando el volumen espacio-tiempo requerido para ejecutar el algoritmo completo.

---

## Parte 1:
### DFTHC Factorization

Los participantes deben construir una factorización comprimida del tensor electrónico.

Se optimiza:

- Número de componentes.
- Factores tensoriales.
- Pesos.
- Compresión matemática.

Manteniendo una precisión química mínima obligatoria.

---

## Parte 2:
### Boolean Angle Oracles

Los participantes diseñan circuitos que generan ángulos requeridos por las rotaciones del bloque de simulación.

Se optimiza:

- Organización de QROMs.
- Streaming de parámetros.
- Precisión binaria.
- Costos de consulta.

---

## Parte 3:
### Majorana Rotations

Los participantes controlan:

- Árboles de Givens Rotations.
- Conectividad.
- Estructuras de propagación.
- Transformaciones Majorana.

---

## Restricciones

Las soluciones deben:

- Respetar límites de precisión química.
- Cumplir verificaciones tensoriales.
- Mantener coherencia algebraica.
- Cumplir límites de recursos definidos por el benchmark.

---

## Métrica

$$
Score=
\lambda_{eff}
\times T_{tot}
\times Q_{tot}
$$

La puntuación depende simultáneamente de:

- Calidad física de la aproximación.
- Coste computacional.
- Recursos cuánticos requeridos.

---

# Estrategias Recomendadas

Los participantes pueden abordar la competencia desde distintas perspectivas:

## Optimización Algorítmica

- Cambiar algoritmos aritméticos.
- Reducir complejidad.
- Eliminar trabajo redundante.

## Optimización de Compilación

- Reducir Toffolis.
- Reducir ancillas.
- Mejorar scheduling.

## Optimización Numérica

- Aproximaciones mejores.
- Truncamientos controlados.
- Reescalado inteligente.

## Optimización Mediante IA

- Agentes autónomos.
- Búsqueda iterativa.
- Evolución de soluciones.
- Síntesis automática de programas.

---

# Temas Avanzados y Detalles Técnicos

Para evitar sobrecargar este README, los siguientes temas se documentan de forma independiente:

📚 https://github.com/dcpracmatic-prog/registro-quantico/tree/main/verifiable_quantum_circuit_compilation

### Kickmix

- Especificación completa del formato `.kmb`
- Internals del simulador
- SIMD execution
- Condition stacks
- Binary serialization

### Verificación

- Derivación matemática de las cotas de fidelidad
- Clopper-Pearson bounds
- Probabilidades de falso positivo
- Fiat-Shamir formal

### Benchmark 1

- Polinomios cúbicos completos
- Reescalamiento de coeficientes
- Newton-Raphson detallado
- Costos bitwise
- Implementación de QROM

### Benchmark 2

- Construcción matemática de DQI
- Optimal Polynomial Intersection
- Reed-Solomon Dual Codes
- Key Equation Solver
- Chien Search
- Forney Recovery

### Benchmark 3

- DFTHC completo
- Block-Encoding matemático
- Spectrum Amplification
- SOSSA
- Majorana Operators
- Givens Trees
- Boolean Oracle Verification

### Futuro de la Plataforma

- Compilación orientada a QEC
- Arquitecturas físicas
- Resource estimation
- Lean theorem proving
- Formal verification

---

# Referencias

**Competencia Oficial**

https://www.kaggle.com/competitions/google-verifiable-quantum-circuit-compilation

**Repositorio de Documentación**

https://github.com/dcpracmatic-prog/registro-quantico/tree/main/verifiable_quantum_circuit_compilation/verification

**Fuente**

Khattar, Rubin, Gidney, Broughton, Low, Babbush.  
*Leveraging Verifiable Structure in Quantum Circuits to Find More Efficient Compilations with Agentic AI* (Google Quantum AI, 2026).
