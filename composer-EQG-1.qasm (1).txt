// =============================================================================
// EQG.qasm — Edge Quantum Guard (workload ejecutable)
// OpenQASM 2.0 — un solo circuito, una sola medicion al final
//
// Uso en IBM Quantum Composer:
//   1. Abrir / pegar este archivo
//   2. Configurar y ejecutar -> backend real (p.ej. ibm_fez)
//   3. Shots: 256
//   4. Revisar tiempo estimado de QPU antes de enviar
//
// Esto es el BRAZO de trabajo (QAOA MaxCut n=4, p=1, grafo C4).
// Ojos / Reflejos / Juicio / DD condicional viven fuera (software clasico).
// =============================================================================

OPENQASM 2.0;
include "qelib1.inc";

qreg q[4];
creg c[4];

// Preparacion
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
