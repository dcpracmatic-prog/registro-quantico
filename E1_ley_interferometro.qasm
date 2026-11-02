// =============================================================================
// E1_ley_interferometro.qasm — Propuestas alternativas E1 (Ley / ingeniería inversa)
// OpenQASM 2.0 — listo para OpenQuantum
//
// Objetivo:
//   Medir contraste de interferómetro de 1 qubit bajo dephasing controlado (mu)
//   para comparar:
//     - baseline (cúbit de índice bajo / layout ingenuo)
//     - soporte de la ley (cúbit de máxima sigma / celda tame)
//
// Diseño del circuito (mismo canal que notebooks E1 / E1-rev):
//   H → idle (proxy de dephasing ~ mu) → Rz(fase ~ mu) → H → measure
//
// Variantes incluidas (un job = un mu representativo):
//   Este archivo usa mu ≈ 0.40 (punto central de la grilla E1-rev).
//   Idle gates ≈ 16 (mu * 40). Fase Rz proporcional a mu.
//
// Uso en OpenQuantum (pantalla que compartiste):
//   1. Arrastra este .qasm
//   2. Nombre sugerido: E1-Ley-Interferometro-mu040
//   3. Categoría / Subcategoría: según tu catálogo (prueba / coherencia)
//   4. Disparos: 2048 o 4096 (recomendado; 100 es solo smoke)
//   5. Deshabilitar el recableado de cúbits: FALSO
//      (deja que el scheduler elija; o FALSO + fuerza layout en runs posteriores)
//
// Interpretación de resultados (criterio de camino E1-rev):
//   V = (n0 - n1) / shots
//   Comparar V en el mismo mu entre:
//     - job mapeado a cúbit de baja sigma (baseline)
//     - job mapeado a cúbit de alta sigma (ley)
//   CAMINO_OK si Delta = V_ley - V_baseline > 0.02
//
// Nota: OpenQuantum ejecuta un circuito por job. Para ablación baseline vs ley
//       lanza dos jobs con el mismo .qasm (o variantes) y anota el qubit físico
//       que asignó el backend. La calibración de sesión (T1/T2/RO) se usa fuera
//       para elegir cuál qubit es "ley" y cuál es baseline.
// =============================================================================

OPENQASM 2.0;
include "qelib1.inc";

qreg q[1];
creg c[1];

// --- Preparación: superposición ---
h q[0];

// --- Idle proxy de dephasing (mu ≈ 0.40 → ~16 ids) ---
// En hardware real el idle acumula desfase ambiental / TLS.
id q[0];
id q[0];
id q[0];
id q[0];
id q[0];
id q[0];
id q[0];
id q[0];
id q[0];
id q[0];
id q[0];
id q[0];
id q[0];
id q[0];
id q[0];
id q[0];

// --- Fase aleatoria / registro parcial ~ mu (fase fija reproducible) ---
// phase = (seed % 1000)/1000 * 2π * mu  → aquí mu=0.4, seed efectivo → ≈ 0.8π
rz(2.5132741228718345) q[0];   // ≈ 0.8 * π

// --- Cierre interferométrico ---
h q[0];

// --- Lectura ---
measure q[0] -> c[0];
