OPENQASM 2.0;
include "qelib1.inc";
// ============================================================
// LEY DE ESTABILIZACION — sonda interferometrica (un archivo)
// ============================================================
// Formalismo operativo:
//   sigma_i = c_i * p_i * r_i
//   s_eff   = media de sigma en el soporte de ejecucion
//   lambda_ley = 0.28   (fijo; 1 - s_atractor_ref, s_atractor~0.72)
//   V(mu) = 1 - mu * (1 - lambda_ley * s_eff)
//
// Este circuito fija mu=0.5 (punto central).
// n_id = round(mu*40) = 20  (fuerza de dephasing / registro parcial)
// Rz phase = 0.02199115 rad (fase de sonda determinista)
//
// PREDICCION (no se ajusta tras medir):
//   V_std (sin ley)     = 0.5000
//   V_ley (s_eff=0.72) = 0.6008
//
// COMO USAR EN OPEN QUANTUM / IBM:
//   1. Cargar este .qasm
//   2. Mapear el qubit logico al fisico de MAYOR s_eff
//      (s_eff desde T1,T2,readout de la sesion: sigma=c*p*r)
//   3. Ejecutar; contraste V_obs = (n0-n1)/(n0+n1)
//   4. Si V_obs se acerca a V_ley (no a V_std) en qubits de alto s:
//        la configuracion de la ley se refleja en el aparato.
//      Si V_obs ~ V_std independientemente de s:
//        en este canal la ley no aporta; el camino no se sostiene.
//
// No demuestra la ontologia completa. Solo confronta la prediccion
// operativa de la ley con un contraste medible.
// ============================================================

qreg q[1];
creg c[1];

// Superposicion (dos caminos logicos en un qubit)
h q[0];

// Registro / dephasing de fuerza mu=0.5  (idle calibrado)
id q[0];  // idle 1/20
id q[0];  // idle 2/20
id q[0];  // idle 3/20
id q[0];  // idle 4/20
id q[0];  // idle 5/20
id q[0];  // idle 6/20
id q[0];  // idle 7/20
id q[0];  // idle 8/20
id q[0];  // idle 9/20
id q[0];  // idle 10/20
id q[0];  // idle 11/20
id q[0];  // idle 12/20
id q[0];  // idle 13/20
id q[0];  // idle 14/20
id q[0];  // idle 15/20
id q[0];  // idle 16/20
id q[0];  // idle 17/20
id q[0];  // idle 18/20
id q[0];  // idle 19/20
id q[0];  // idle 20/20

// Fase de sonda (phi = 2*pi*mu*seed_frac)
rz(0.02199115) q[0];

// Interferencia y medida
h q[0];
measure q[0] -> c[0];

