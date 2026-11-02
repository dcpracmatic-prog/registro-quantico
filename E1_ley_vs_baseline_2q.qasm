// =============================================================================
// E1_ley_vs_baseline_2q.qasm — Comparación en un solo job
// OpenQASM 2.0 — OpenQuantum
//
// Dos interferómetros independientes en paralelo (mismo mu ≈ 0.40):
//   q[0]  →  brazo "baseline" (se espera mapear a cúbit de menor sigma)
//   q[1]  →  brazo "ley"      (se espera mapear a cúbit de mayor sigma)
//
// Métrica:
//   V0 = (n0_0 - n1_0) / shots_en_c0
//   V1 = (n0_1 - n1_1) / shots_en_c1
//   Delta = V1 - V0
//   CAMINO_OK si Delta > 0.02 (criterio E1-rev)
//
// Uso OpenQuantum:
//   Nombre: E1-Ley-vs-Baseline-2q-mu040
//   Disparos: 2048 o 4096
//   Deshabilitar el recableado de cúbits: FALSO
//     (recomendado: dejar que el scheduler asigne; luego anotar qué físicos
//      recibieron q[0] y q[1] y correlacionar con calibración T2/T1/RO)
//
// Si el backend permite layout fijo, fuerza q[0]→cúbit débil y q[1]→cúbit fuerte
// para maximizar la señal de la ingeniería inversa.
// =============================================================================

OPENQASM 2.0;
include "qelib1.inc";

qreg q[2];
creg c[2];

// ========== Brazo 0 — baseline (misma secuencia) ==========
h q[0];
id q[0]; id q[0]; id q[0]; id q[0];
id q[0]; id q[0]; id q[0]; id q[0];
id q[0]; id q[0]; id q[0]; id q[0];
id q[0]; id q[0]; id q[0]; id q[0];
rz(2.5132741228718345) q[0];
h q[0];

// ========== Brazo 1 — ley (idéntica secuencia; solo cambia el qubit físico) ==========
h q[1];
id q[1]; id q[1]; id q[1]; id q[1];
id q[1]; id q[1]; id q[1]; id q[1];
id q[1]; id q[1]; id q[1]; id q[1];
id q[1]; id q[1]; id q[1]; id q[1];
rz(2.5132741228718345) q[1];
h q[1];

// Lectura independiente
measure q[0] -> c[0];
measure q[1] -> c[1];
