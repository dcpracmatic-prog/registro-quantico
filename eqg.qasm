// =============================================================================
// EQG.qasm — Edge Quantum Guard (workload ejecutable)
// OpenQASM 2.0 — un solo circuito, una sola medicion al final
//
// Origen: registro-quantico (composer-EQG-1) — brazo de trabajo QAOA MaxCut
// Mejor resultado documentado en registro: pilots EQG_MEJORA_QAOA en ibm_fez
// (N=8 p=2, ΔAR +0.022–0.038, z≥5.7). Este circuito es la version compacta
// lista para OpenQuantum / IBM Composer (n=4, p=1, grafo C4).
//
// Uso en OpenQuantum:
//   1. Sube este archivo .qasm
//   2. Nombre descriptivo: EQG-Centinela-QAOA-MaxCut-C4
//   3. Disparos (shots): 100–256 (o 1024 si el backend lo permite)
//   4. Deshabilitar re cableado de cubits: FALSO (permitir mapping)
//
// EQG ciclo: Observe → MORPH layout → Decide (hold/remap/DD) → Actuate Centinela
// Este archivo es el BRAZO de trabajo. Ojos/Reflejos/Juicio viven fuera.
// =============================================================================

OPENQASM 2.0;
include "qelib1.inc";

qreg q[4];
creg c[4];

// Preparacion (superposicion inicial)
h q[0];
h q[1];
h q[2];
h q[3];

// Capa de coste MaxCut C4 (aristas 0-1, 1-2, 2-3, 3-0), gamma = pi/4
cx q[0], q[1];
rz(0.7853981633974483) q[1];
cx q[0], q[1];

cx q[1], q[2];
rz(0.7853981633974483) q[2];
cx q[1], q[2];

cx q[2], q[3];
rz(0.7853981633974483) q[3];
cx q[2], q[3];

cx q[3], q[0];
rz(0.7853981633974483) q[0];
cx q[3], q[0];

// Capa mezcladora, 2*beta = pi/2
rx(1.5707963267948966) q[0];
rx(1.5707963267948966) q[1];
rx(1.5707963267948966) q[2];
rx(1.5707963267948966) q[3];

// Una sola medicion al final
measure q[0] -> c[0];
measure q[1] -> c[1];
measure q[2] -> c[2];
measure q[3] -> c[3];
