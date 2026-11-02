// =============================================================================
// E1_ley_interferometro_mu070.qasm — Variante mu ≈ 0.70 (dephasing más fuerte)
// OpenQASM 2.0 — OpenQuantum
//
// Misma estructura que E1_ley_interferometro.qasm pero con mayor carga de idle
// y fase. Útil para ver si el soporte de alta sigma conserva contraste cuando
// el canal se degrada más.
//
// Uso OpenQuantum:
//   Nombre: E1-Ley-Interferometro-mu070
//   Disparos: 2048–4096
//   Deshabilitar recableado: FALSO
// =============================================================================

OPENQASM 2.0;
include "qelib1.inc";

qreg q[1];
creg c[1];

h q[0];

// Idle ~ mu*40 ≈ 28
id q[0]; id q[0]; id q[0]; id q[0]; id q[0]; id q[0]; id q[0];
id q[0]; id q[0]; id q[0]; id q[0]; id q[0]; id q[0]; id q[0];
id q[0]; id q[0]; id q[0]; id q[0]; id q[0]; id q[0]; id q[0];
id q[0]; id q[0]; id q[0]; id q[0]; id q[0]; id q[0]; id q[0];

// fase ≈ (0.7) * 1.0 * 2π  (proxy fijo)
rz(4.39822971502571) q[0];

h q[0];
measure q[0] -> c[0];
