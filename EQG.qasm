// =============================================================================
// EQG.qasm — Edge Quantum Guard
// Circuitos cuánticos del stack de control (Manos / Centinela)
// OpenQASM 2.0
//
// Roles (clásicos, fuera de este archivo):
//   Ojos   — Observation Membrane (fricción / régimen)
//   Reflejos — Layout Guard / MORPH (quién trabaja)
//   Juicio — mínima acción + veredicto causal
//   Manos  — este QASM: sondeo, fase virtual, DD condicional
//
// Política:
//   layout_health >= HEALTH_THR  → workload sin DD
//   layout_health <  HEALTH_THR  → inyectar DD (adrenalina)
//
// Anclaje hardware (ibm_fez q142, v4):
//   estado bueno:      T2* ~155 µs, CPMG/libre ~1.3–1.4×
//   estado degradado:  T2* ~40 µs,  CPMG/libre ~2.1–2.2×
// =============================================================================

OPENQASM 2.0;
include "qelib1.inc";

// -----------------------------------------------------------------------------
// Parámetros lógicos (el orquestador fija n y el layout físico al transpilár)
// k = número de candidatos del sondeo / qubits del workload
// -----------------------------------------------------------------------------
qreg q[4];
creg c[4];

// =============================================================================
// BLOQUE 1 — Calibración de lectura (cal0 / cal1)
// =============================================================================

// --- cal0: medir |0...0| ---
barrier q;
measure q -> c;

// --- cal1: X en todos, medir |1...1| ---
// (en job real es un circuito separado; aquí documentado en secuencia)
x q[0]; x q[1]; x q[2]; x q[3];
barrier q;
measure q -> c;

// =============================================================================
// BLOQUE 2 — Ramsey libre (bases X e Y) → T2* + detuning
// t se materializa como delay alineado a dt en el backend
// =============================================================================

// Ramsey X, tiempo t (placeholder: sin delay explícito en QASM2 genérico)
h q;
barrier q;
// delay(t) en cada qubit — insertar en transpilation / pulse schedule
barrier q;
h q;
measure q -> c;

// Ramsey Y
h q;
barrier q;
// delay(t)
barrier q;
sdg q;
h q;
measure q -> c;

// =============================================================================
// BLOQUE 3 — CPMG (Dynamical Decoupling condicional)
// n_cpmg = 6 pulsos X típicos Centinela; solo si layout_health < HEALTH_THR
// =============================================================================

h q;
barrier q;
// secuencia CPMG en cada qubit: delay/2 - X - delay - X - ... - delay/2
// Representación esquemática (1 ciclo de eco por qubit):
x q[0]; x q[1]; x q[2]; x q[3];
// delay(gap)
x q[0]; x q[1]; x q[2]; x q[3];
// ... repetir n_cpmg veces según ProbeConfig
barrier q;
h q;
measure q -> c;

// Variante XY4 (alternativa de DD):
// X - Y - X - Y en ventanas de idle
// h q; barrier; x; y; x; y; barrier; h; measure

// =============================================================================
// BLOQUE 4 — T1 (relajación)
// =============================================================================

x q;
barrier q;
// delay(t)
barrier q;
measure q -> c;

// =============================================================================
// BLOQUE 5 — Corrección de fase (Z virtual, coste ~0)
// φ(t) = -2π · f_detuning_kHz · 1e-3 · t_µs
// Se aplica como rz en software antes del workload; no consume tiempo de idle
// =============================================================================

// Ejemplo: corrección por detuning medido en el sondeo (f en kHz, t en µs)
// rz(-2 * pi * f_kHz * 1e-3 * t_us) q[i];
rz(0) q[0];
rz(0) q[1];
rz(0) q[2];
rz(0) q[3];

// =============================================================================
// BLOQUE 6 — Workload de referencia (QAOA MaxCut p=1, grafo C4 / n=4)
// Ángulos fijos (sin optimizador clásico externo) para techo de cuenta QPU
// Layout físico: lo elige Reflejos (MORPH); DD se inserta en idles si adrenalina
// =============================================================================

// Capas de mezcla (B) y coste (C) — parámetros β, γ fijos de campaña
h q;

// Cost layer (MaxCut C4: aristas 0-1, 1-2, 2-3, 3-0)
cx q[0], q[1];
rz(0.7853981633974483) q[1];  // γ placeholder
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

// Mixer layer
rx(1.5707963267948966) q[0];  // 2β placeholder
rx(1.5707963267948966) q[1];
rx(1.5707963267948966) q[2];
rx(1.5707963267948966) q[3];

barrier q;
measure q -> c;

// =============================================================================
// Notas de integración EQG
// -----------------------------------------------------------------------------
// 1. Ojos consume T2*, detuning, T1 del análisis de BLOQUES 1–4 → fricción + régimen.
// 2. Reflejos elige initial_layout (MIS / Layout Guard) antes de transpilár.
// 3. Juicio decide: ninguna | fase_virtual | dd_condicional | remap | abortar.
// 4. Manos aplica BLOQUE 5 y, si dd_condicional, inserta BLOQUE 3 en idles del 6.
// 5. Budget típico protocolo gated: ≤15 s Arm B (EQG) + ≤15 s Arm A si favorable.
// =============================================================================
