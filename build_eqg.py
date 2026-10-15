import nbformat as nbf

nb = nbf.v4.new_notebook()
C = []
def md(s): C.append(nbf.v4.new_markdown_cell(s.strip("\n")))
def code(s): C.append(nbf.v4.new_code_cell(s.strip("\n")))

md(r'''
# EQG ON vs OFF — régimen de estrés calibrado (HIS_span)

**Problema del notebook anterior:** el baseline (OFF) daba HIS_span ≈ 0.98 → efecto techo; además el simulador no tenía ningún ruido que el DD pudiera corregir (la espera `delay` no producía error en Aer), así que EQG solo pagaba el costo de sus pulsos X (Δ = −0.006, z = −4.8) y Reflejos devolvía el mismo layout que el baseline.

## Qué cambia

| # | Cambio | Por qué |
|---|--------|---------|
| 1 | **Ruido de espera real en el simulador**: desfase coherente cuasi-estático por qubit (qubits "TLS" con θ grande) + depolarizing por ranura idle, inyectados sobre cada `delay` | Sin esto el DD no puede ayudar ni dañar de forma realista. El desfase coherente **sí** se refocaliza con X–X; el depolarizing de espera **no**, y las X cuestan error de compuerta |
| 2 | **Calibración automática del estrés usando SOLO el brazo OFF**: se busca el multiplicador de estrés para que el baseline caiga en **[0.60, 0.75]** de HIS_span | Evita ajustar el estrés mirando si EQG gana; se congela antes de medir ON |
| 3 | **Umbrales de fricción más agresivos** (`DD_FRICTION_THR=0.25`, Reflejos re-mapea siempre al mejor camino) con fricción que incluye el desfase observable | La fricción antigua ignoraba el desfase, que es lo que daña |
| 4 | **Control nulo** (`baseline2` idéntico a `baseline`) + **ablación** (`eqg_remap`, `eqg_dd`) | Calibra el falso positivo de z y separa qué pieza aporta |
| 5 | **Compuerta estricta** `PRODUCTO_OK / PRODUCTO_NO / PRUEBA_INVALIDA` | Δ>0 y z≥2 en **T1 y T5**, nulo válido, OFF dentro de banda, Manos activo |
| 6 | **Corrección de medida:** los términos Pauli mixtos (p. ej. `Z⊗Y`) se metían en el grupo Z y se estimaban mal; ahora se agrupan con `group_commuting` | Sesgaba HIS de T5 |

> `MODE="cpu"`: el simulador está construido con desfase coherente, que el DD refocaliza por diseño. Un ON>OFF en CPU demuestra que la **lógica del producto funciona cuando el ruido es de ese tipo**; solo `MODE="qpu"` dice si el hardware tiene ese ruido.
''')

md("## 0. Config")
code(r'''
# ============================================================
# CONFIG — se congela antes de mirar el brazo ON / el QPU
# ============================================================
MODE = "cpu"                 # "cpu" | "qpu"
BACKEND_NAME = "ibm_fez"
QPU_CONFIRM = False
MAX_QPU_SECONDS = 300.0

SEED = 42
EQG_VERSION = "EQG-1.1.0-stress"

# --- Régimen de estrés: el OFF debe "sangrar" ---
STRESS_BAND = (0.60, 0.75)       # banda objetivo de HIS_span del baseline
STRESS_TARGET = 0.675

if MODE == "cpu":
    N_LOGICAL = 8
    QAOA_P = 4
    HEA_LAYERS = 5
    IDLE_US = 8.0
    SHOTS = 4096
    N_CYCLES = 3                 # cada ciclo = palíndromo de brazos (ABBA generalizado)
    ABLATION = True
    STRESS_SWEEP = (1.0, 1.35)   # multiplicadores sobre el estrés calibrado (1.0 = nominal)
    SIM = dict(M=24, tls_frac=0.30, time_drift=0.30, theta_good=0.03, theta_bad=0.30)
else:
    N_LOGICAL = 8
    QAOA_P = 3
    HEA_LAYERS = 4
    IDLE_US = 10.0               # sube IDLE_US / capas si el OFF sale > 0.75
    SHOTS = 1024
    N_CYCLES = 2
    ABLATION = False
    STRESS_SWEEP = (1.0,)
    SIM = {}

# --- Política Reflejos / Manos (agresiva) ---
DD_FRICTION_THR = 0.25           # Manos: DD en todo qubit del layout con fricción >= umbral
REMAP_FRICTION_THR = 0.20        # Juicio: intervenir si la fricción media del layout base >= umbral
ABORT_FR_MEAN = 0.90
GATE_Z = 2.0

OUT_DIR = f"eqg_stress_{MODE}"
print("EQG_VERSION", EQG_VERSION, "| MODE", MODE, "| N", N_LOGICAL, "| QAOA p", QAOA_P, "| HEA", HEA_LAYERS)
print("IDLE_US", IDLE_US, "| shots", SHOTS, "| cycles", N_CYCLES, "| banda OFF", STRESS_BAND)
''')

md("## 1. Install & imports")
code(r'''
%pip install -q "qiskit>=1.3" "qiskit-aer>=0.14" "qiskit-ibm-runtime>=0.30" numpy pandas matplotlib

import json, math, time, gc, hashlib
from pathlib import Path
from collections import defaultdict
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import SparsePauliOp, Statevector
from qiskit.transpiler import CouplingMap
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error, ReadoutError

OUT = Path(OUT_DIR); OUT.mkdir(parents=True, exist_ok=True)
RNG = np.random.default_rng(SEED)
EPS = 1e-8
N = N_LOGICAL

def mem_mb():
    try:
        import resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    except Exception:
        return float("nan")

MOTOR = {r: {"active": False, "detail": None} for r in ("ojos", "reflejos", "juicio", "manos")}

def require_eqg():
    miss = [r for r, v in MOTOR.items() if not v["active"]]
    if miss:
        raise RuntimeError("EQG incompleto — roles faltantes: %s" % miss)
    print("[EQG] completo")
    for r, v in MOTOR.items():
        print(" ", r, "→", v["detail"])

FP = hashlib.sha256(json.dumps(dict(
    v=EQG_VERSION, mode=MODE, N=N, p=QAOA_P, hea=HEA_LAYERS, idle=IDLE_US, shots=SHOTS,
    cycles=N_CYCLES, thr=DD_FRICTION_THR, band=STRESS_BAND, sim=SIM), sort_keys=True, default=str).encode()).hexdigest()[:16]
print("OK | RSS≈%.0f MB | fp=%s" % (mem_mb(), FP))
''')

md("## 2. HIS_span + Hamiltonianos (con agrupación de medida corregida)")
code(r'''
def his_span(h_id, h_re, span):
    return 1.0 - abs(h_id - h_re) / max(span, EPS)

def z_diff(a, sa, b, sb):
    s = math.sqrt(sa**2 + sb**2)
    return float("nan") if s < EPS else (a - b) / s

def plabel(n, ops):
    s = ["I"] * n
    for q, l in ops.items():
        s[n - 1 - q] = l
    return "".join(s)

def maxcut_path_H(n):
    t = [("I" * n, 0.5 * (n - 1))]
    t += [(plabel(n, {i: "Z", i + 1: "Z"}), -0.5) for i in range(n - 1)]
    return SparsePauliOp.from_list(t)

def hard_pauli_H(n, seed):
    rng = np.random.default_rng(seed)
    t = []
    for L in "XYZ":
        for i in range(n - 1):
            t.append((plabel(n, {i: L, i + 1: L}), float(rng.normal(0, 0.55))))
        for i in range(n):
            t.append((plabel(n, {i: L}), float(rng.normal(0, 0.45))))
    for i in range(0, n - 2, 2):
        t.append((plabel(n, {i: "X", i + 2: "X"}), float(rng.normal(0, 0.3))))
        t.append((plabel(n, {i: "Z", i + 1: "Y"}), float(rng.normal(0, 0.25))))
    return SparsePauliOp.from_list(t).simplify()

def idle_slot(qc, idle_fn):
    if idle_fn:
        idle_fn(qc)

def qaoa_prep(n, p, gammas, betas, idle_fn=None):
    qc = QuantumCircuit(n)
    qc.h(range(n))
    for layer in range(p):
        for i in range(n - 1):
            qc.cx(i, i + 1); qc.rz(-2 * gammas[layer], i + 1); qc.cx(i, i + 1)
        idle_slot(qc, idle_fn)
        qc.rx(2 * betas[layer], range(n))
        idle_slot(qc, idle_fn)
    return qc

def hea_prep(n, layers, params, idle_fn=None):
    qc = QuantumCircuit(n)
    for L in range(layers):
        for q in range(n):
            qc.ry(float(params[L, q, 0]), q); qc.rz(float(params[L, q, 1]), q); qc.rx(float(params[L, q, 2]), q)
        for i in range(n - 1):
            qc.cx(i, i + 1)
        idle_slot(qc, idle_fn)
        for i in range(n - 2, -1, -1):
            qc.cx(i + 1, i)
        idle_slot(qc, idle_fn)
    return qc

def h_ideal(prep, H):
    return float(np.real(Statevector.from_instruction(prep).expectation_value(H)))

def spectrum_span(H):
    ev = np.linalg.eigvalsh(H.to_matrix())
    return float(ev[-1] - ev[0])

def meas_groups(H):
    groups = []
    for g in H.group_commuting(qubit_wise=True):
        labs = g.paulis.to_labels()
        basis = []
        for q in range(N):
            letters = {lab[N - 1 - q] for lab in labs} - {"I"}
            basis.append(letters.pop() if letters else "Z")
        groups.append(dict(op=g, basis=basis))
    return groups

def group_stats(counts, op, n):
    labels = op.paulis.to_labels(); coeffs = np.real(op.coeffs)
    vals, cnt = [], []
    for bs, c in counts.items():
        s = bs.replace(" ", "")[-n:].zfill(n)
        e = 0.0
        for lab, w in zip(labels, coeffs):
            par = 0
            for i, ch in enumerate(lab):
                if ch != "I" and s[i] == "1":
                    par ^= 1
            e += w * (1 - 2 * par)
        vals.append(e); cnt.append(c)
    cnt = np.asarray(cnt, float); shots = max(cnt.sum(), 1.0)
    return np.asarray(vals), cnt / shots, int(shots)

def estimate_energy(gcounts, gops, n):
    h, var = 0.0, 0.0
    for counts, op in zip(gcounts, gops):
        v, p, shots = group_stats(counts, op, n)
        m = float(p @ v); h += m
        var += float(p @ (v ** 2) - m ** 2) / max(shots, 1)
    return h, math.sqrt(max(var, 0.0))

# --- T1: QAOA p capas ---
H1 = maxcut_path_H(N)
best, GAMMAS, BETAS = None, None, None
for trial in range(24):
    g = RNG.uniform(0.15, 1.1, size=QAOA_P); b = RNG.uniform(0.08, 0.55, size=QAOA_P)
    e = h_ideal(qaoa_prep(N, QAOA_P, g, b), H1)
    if best is None or e > best:
        best, GAMMAS, BETAS = e, g.copy(), b.copy()
span1 = spectrum_span(H1); hid1 = h_ideal(qaoa_prep(N, QAOA_P, GAMMAS, BETAS), H1)

# --- T5: HEA profundo + Pauli duro ---
T5_H, T5_P, t5_best = None, None, -1.0
for s in range(60):
    H = hard_pauli_H(N, s); span = spectrum_span(H)
    params = RNG.uniform(0, 2 * np.pi, size=(HEA_LAYERS, N, 3))
    cond = abs(h_ideal(hea_prep(N, HEA_LAYERS, params), H)) / span
    if cond > t5_best:
        t5_best, T5_H, T5_P = cond, H, params.copy()
span5 = spectrum_span(T5_H); hid5 = h_ideal(hea_prep(N, HEA_LAYERS, T5_P), T5_H)

HAM = {
    "T1_QAOA": dict(H=H1, h_id=hid1, span=span1, groups=meas_groups(H1), kind="qaoa"),
    "T5_HEA": dict(H=T5_H, h_id=hid5, span=span5, groups=meas_groups(T5_H), kind="hea"),
}
print("T1 QAOA p=%d  h_id=%.3f span=%.3f grupos=%d" % (QAOA_P, hid1, span1, len(HAM["T1_QAOA"]["groups"])))
print("T5 HEA L=%d   h_id=%.3f span=%.3f grupos=%d |h_id|/span=%.3f" % (
    HEA_LAYERS, hid5, span5, len(HAM["T5_HEA"]["groups"]), t5_best))
''')

md(r'''
## 3. Dispositivo

**CPU — `SimDevice`:** cadena lineal con errores heterogéneos. Cada qubit tiene un **ángulo de desfase por ranura de espera** `θ_q` (grande en los qubits TLS "malos"), que crece/decrece con el tiempo y se escala con el multiplicador de `stress`. Además: depolarizing 1q/2q, lectura y depolarizing por ranura idle (**no refocalizable**).

**Ojos** observa señales públicas (lectura, error de X y desfase observado con ruido de medida). La fricción ahora **incluye el desfase**.
''')
code(r'''
def friction_obs(ro, xe, theta_abs):
    return float(min(1.0, 6.0 * ro + 60.0 * xe + 0.5 * min(1.0, theta_abs / 0.6)))

class SimDevice:
    P_ID = 0.0012      # depolarizing por 'id' (4 por ranura idle)
    def __init__(self, M, tls_frac, time_drift, theta_good, theta_bad, seed=SEED):
        r = np.random.default_rng(seed)
        self.M, self.rng, self.time_drift = M, r, time_drift
        self.bad = set(r.choice(M, size=max(2, int(round(tls_frac * M))), replace=False).tolist())
        isb = np.array([q in self.bad for q in range(M)])
        self.isb = isb
        self.sign = r.choice([-1.0, 1.0], M)
        self.theta0 = self.sign * np.where(isb, theta_bad, theta_good) * r.lognormal(0, 0.15, M)
        self.ro = 0.012 * r.lognormal(0, 0.15, M) * np.where(isb, 2.2, 1.0)
        self.xerr = 0.0006 * r.lognormal(0, 0.15, M) * np.where(isb, 2.0, 1.0)
        self.stress = 1.0
        self.frac = 0.5          # tiempo normalizado del experimento (0..1)

    def theta(self, q):
        scale = 1.0 + self.time_drift * (self.frac - 0.5)
        return float(self.theta0[q]) * self.stress * scale

    def observe(self, noise=0.05):
        r = self.rng
        out = {}
        for q in range(self.M):
            out[q] = dict(ro=self.ro[q] * (1 + noise * r.normal()), xerr=self.xerr[q] * (1 + noise * r.normal()),
                          theta=abs(float(self.theta0[q]) * self.stress) * (1 + noise * r.normal()))
        return out

    def noise_model(self):
        nm = NoiseModel(basis_gates=["rz", "sx", "x", "cx", "id"])
        for q in range(self.M):
            p = float(min(0.4, self.ro[q]))
            nm.add_readout_error(ReadoutError([[1 - p, p], [p, 1 - p]]), [q])
            nm.add_quantum_error(depolarizing_error(min(0.5, 3 * float(self.xerr[q])), 1), ["x", "sx"], [q])
            nm.add_quantum_error(depolarizing_error(self.P_ID * (2.0 if self.isb[q] else 1.0), 1), ["id"], [q])
        for a in range(self.M - 1):
            base = 0.018 if (self.isb[a] or self.isb[a + 1]) else 0.010
            e = depolarizing_error(base, 2)
            nm.add_quantum_error(e, ["cx"], [a, a + 1]); nm.add_quantum_error(e, ["cx"], [a + 1, a])
        return nm

def friction_from_obs(obs, n_phys):
    return np.array([friction_obs(obs[q]["ro"], obs[q]["xerr"], obs[q].get("theta", 0.0)) for q in range(n_phys)])

device = sim_backend = backend = None
if MODE == "cpu":
    device = SimDevice(**SIM)
    n_phys = device.M
    cm = CouplingMap([[i, i + 1] for i in range(n_phys - 1)] + [[i + 1, i] for i in range(n_phys - 1)])
    sim_backend = AerSimulator(method="density_matrix", noise_model=device.noise_model(), coupling_map=cm,
                               basis_gates=["rz", "sx", "x", "cx", "id", "measure", "delay", "barrier"])
    edges = [[i, i + 1] for i in range(n_phys - 1)]
    print("qubits TLS malos (%d de %d): %s" % (len(device.bad), n_phys, sorted(device.bad)))
else:
    from qiskit_ibm_runtime import QiskitRuntimeService
    service = QiskitRuntimeService()
    backend = service.backend(BACKEND_NAME)
    n_phys = backend.num_qubits
    props = backend.properties()
    edges = [list(e) for e in backend.coupling_map.get_edges()]
    print("[qpu]", backend.name, "qubits =", n_phys)

adj = defaultdict(list)
for a, b in edges:
    adj[int(a)].append(int(b)); adj[int(b)].append(int(a))

def observe_fr():
    if MODE == "cpu":
        return friction_from_obs(device.observe(), device.M)
    cal = {}
    for q in range(n_phys):
        try: ro = float(props.readout_error(q))
        except Exception: ro = 0.02
        try: xe = float(props.gate_error("x", [q]))
        except Exception: xe = 0.001
        cal[q] = dict(ro=ro, xerr=xe, theta=0.0)
    return friction_from_obs(cal, n_phys)

def path_layouts(n_logical, fr, blacklist, max_paths=300):
    bl = set(int(x) for x in blacklist); found = []
    def dfs(path):
        if len(found) >= max_paths: return
        if len(path) == n_logical:
            found.append(list(path)); return
        for nxt in sorted(adj[path[-1]], key=lambda q: fr[q]):
            if nxt in path or nxt in bl: continue
            dfs(path + [nxt])
    for s in sorted(range(n_phys), key=lambda q: fr[q]):
        if s in bl: continue
        dfs([s])
        if len(found) >= max_paths: break
    return found

def layout_score(layout, fr):
    return float(np.mean([fr[q] for q in layout]))
print("dispositivo OK")
''')

md(r'''
## 4. Circuitos, Manos (DD) y ruido de espera

- `idle_fn`: ranura de espera (`delay` IDLE_US) tras cada capa.
- **DD (Manos):** CPU → CPMG manual (X–delay/2–X–delay/2); QPU → `PadDynamicalDecoupling` con respaldo manual.
- **CPU:** cada `delay` se sustituye por `rz(θ_q·dur/IDLE)` (desfase coherente) + `id`×k (depolarizing de espera). Si el delay fue partido por DD, el desfase se refocaliza solo porque las X invierten el signo.
''')
code(r'''
from qiskit.circuit.library import XGate
from qiskit.transpiler import PassManager, InstructionDurations
from qiskit.transpiler.passes import ALAPScheduleAnalysis, PadDynamicalDecoupling

def idle_fn(qc):
    qc.barrier()
    for q in range(qc.num_qubits):
        qc.delay(IDLE_US, q, unit="us")
    qc.barrier()

UNIT_US = {"us": 1.0, "ns": 1e-3, "ms": 1e3, "s": 1e6, "dt": 1e-3}

def _manual_cpmg(tc, qubits):
    qs = set(int(q) for q in qubits)
    new = QuantumCircuit(tc.num_qubits, tc.num_clbits)
    qi = {b: i for i, b in enumerate(tc.qubits)}; ci = {b: i for i, b in enumerate(tc.clbits)}
    added = 0
    for inst in tc.data:
        op = inst.operation; qa = [qi[q] for q in inst.qubits]; ca = [ci[c] for c in inst.clbits]
        if op.name == "delay" and len(qa) == 1 and qa[0] in qs:
            dur = float(getattr(op, "duration", 0) or 0); unit = getattr(op, "unit", "dt"); half = dur / 2.0
            if half > 0:
                new.x(qa[0]); new.delay(half, qa[0], unit=unit)
                new.x(qa[0]); new.delay(half, qa[0], unit=unit)
                added += 2; continue
        new.append(op, qa, ca)
    return new, added

def _durs(n, dt=1e-9):
    rows = []
    for q in range(n):
        rows += [("rz", q, 0), ("sx", q, 50), ("x", q, 100), ("measure", q, 1000), ("delay", q, 1)]
    for a in range(max(n - 1, 0)):
        rows += [("cx", [a, a + 1], 300), ("cx", [a + 1, a], 300)]
    return InstructionDurations(rows, dt=dt)

def apply_dd(tc, qubits):
    if not qubits:
        return tc, 0
    qs = [int(q) for q in qubits]
    if MODE == "cpu":
        return _manual_cpmg(tc, qs)
    before = int(tc.count_ops().get("x", 0))
    target = getattr(backend, "target", None)
    if target is not None:
        try:
            pm = PassManager([ALAPScheduleAnalysis(target=target),
                              PadDynamicalDecoupling(target=target, dd_sequence=[XGate(), XGate()], qubits=qs,
                                                     pulse_alignment=getattr(target, "pulse_alignment", 1), skip_reset_qubits=False)])
            tc2 = pm.run(tc); a = int(tc2.count_ops().get("x", 0)) - before
            if a > 0: return tc2, a
        except Exception:
            pass
    try:
        durs = _durs(tc.num_qubits)
        pm = PassManager([ALAPScheduleAnalysis(instruction_durations=durs),
                          PadDynamicalDecoupling(durations=durs, dd_sequence=[XGate(), XGate()], qubits=qs,
                                                 pulse_alignment=1, skip_reset_qubits=False)])
        tc2 = pm.run(tc); a = int(tc2.count_ops().get("x", 0)) - before
        if a > 0: return tc2, a
    except Exception:
        pass
    return _manual_cpmg(tc, qs)

def inject_idle_noise(tc):
    """CPU: delay -> rz(theta*dur/IDLE) + id*k. Usa device.stress y device.frac vigentes."""
    new = QuantumCircuit(tc.num_qubits, tc.num_clbits)
    qi = {b: i for i, b in enumerate(tc.qubits)}; ci = {b: i for i, b in enumerate(tc.clbits)}
    for inst in tc.data:
        op = inst.operation; qa = [qi[q] for q in inst.qubits]; ca = [ci[c] for c in inst.clbits]
        if op.name == "delay" and len(qa) == 1:
            q = qa[0]
            dur_us = float(getattr(op, "duration", 0) or 0) * UNIT_US.get(getattr(op, "unit", "us"), 1.0)
            new.rz(device.theta(q) * dur_us / IDLE_US, q)
            for _ in range(max(1, int(round(4 * dur_us / IDLE_US)))):
                new.id(q)
        else:
            new.append(op, qa, ca)
    return new

def basis_change(qc, basis):
    for q, l in enumerate(basis):
        if l == "X": qc.h(q)
        elif l == "Y": qc.sdg(q); qc.h(q)
    qc.measure_all()
    return qc

def build_prep(kind):
    if kind == "qaoa":
        return qaoa_prep(N, QAOA_P, GAMMAS, BETAS, idle_fn)
    return hea_prep(N, HEA_LAYERS, T5_P, idle_fn)

def dd_qubits_for(layout, fr):
    """Manos: DD agresivo en todo qubit con fricción >= umbral; si ninguno, los peores N//3."""
    qs = [q for q in layout if fr[q] >= DD_FRICTION_THR]
    if not qs:
        qs = sorted(layout, key=lambda q: fr[q], reverse=True)[: max(2, len(layout) // 3)]
    return qs

_dd = defaultdict(int)
_base_cache = {}

def base_circuit(hname, arm, g):
    """Transpilado + DD, sin ruido de espera inyectado (cacheado)."""
    key = (hname, arm, g, tuple(ARM_CFG[arm]["layout"]), tuple(ARM_CFG[arm]["dd"]))
    if key not in _base_cache:
        d = HAM[hname]; cfg = ARM_CFG[arm]
        qc = build_prep(d["kind"]).copy()
        basis_change(qc, d["groups"][g]["basis"])
        tgt = sim_backend if MODE == "cpu" else backend
        tc = transpile(qc, tgt, initial_layout=list(cfg["layout"]), optimization_level=1, seed_transpiler=SEED + g)
        if cfg["dd"]:
            tc, nadd = apply_dd(tc, cfg["dd"])
            _dd[arm] += nadd
        _base_cache[key] = tc
    return _base_cache[key]

def final_circuit(hname, arm, g):
    tc = base_circuit(hname, arm, g)
    return inject_idle_noise(tc) if MODE == "cpu" else tc

def est_cost(n_circ, shots, per=350e-6):
    return n_circ * shots * per + 3.0 * max(1, n_circ // 40)

def execute(tcs, shots):
    if MODE == "cpu":
        out = []
        for i in range(0, len(tcs), 16):
            part = tcs[i:i + 16]
            res = sim_backend.run(part, shots=shots).result()
            out += [res.get_counts(j) for j in range(len(part))]
            gc.collect()
        return out
    from qiskit_ibm_runtime import SamplerV2
    sampler = SamplerV2(mode=backend)
    job = sampler.run([(tc, None, shots) for tc in tcs])
    jid = job.job_id(); print("Job", jid, flush=True)
    t0 = time.time(); last = t0
    while True:
        st = job.status(); nm = st if isinstance(st, str) else getattr(st, "name", str(st))
        if nm in ("DONE", "CANCELLED", "ERROR"): break
        if time.time() - t0 > 1800:
            try: job.cancel()
            except Exception: pass
            raise TimeoutError(jid)
        if time.time() - last >= 30:
            print("  status=%s waited=%.0fs" % (nm, time.time() - t0), flush=True); last = time.time()
        time.sleep(2)
    if nm != "DONE":
        raise RuntimeError("job %s %s" % (jid, nm))
    res = job.result(); counts = []
    for i in range(len(tcs)):
        data = res[i].data; c = None
        for key in ("meas", "c"):
            if hasattr(data, key):
                try: c = getattr(data, key).get_counts(); break
                except Exception: pass
        if c is None:
            for key in data:
                try: c = data[key].get_counts(); break
                except Exception: continue
        counts.append(c or {})
    return counts

def his_from_counts(hname, gcounts):
    d = HAM[hname]
    h_re, se = estimate_energy(gcounts, [x["op"] for x in d["groups"]], N)
    return his_span(d["h_id"], h_re, d["span"]), se / d["span"], h_re

ARM_CFG = {}
print("builders OK")
''')

md(r'''
## 5. Calibración del régimen de estrés (solo brazo OFF)

Se busca el multiplicador `stress` para que el **promedio de HIS_span del baseline (T1 y T5)** quede en el objetivo (0.675) y se verifica que **cada** Hamiltoniano caiga en la banda [0.60, 0.75]. **No se mira el brazo ON.** El multiplicador se congela antes del experimento.

En `qpu` no hay perilla de estrés: el notebook mide el OFF y, si queda fuera de banda, el veredicto será `PRUEBA_INVALIDA` (sube `IDLE_US` o las capas).
''')
code(r'''
LAYOUT_BASE = list(range(N))
ARM_CFG["baseline"] = dict(layout=LAYOUT_BASE, dd=[])

def pilot_off(stress=None, shots=2048):
    if stress is not None:
        device.stress = stress
    out = {}
    for h in HAM:
        ng = len(HAM[h]["groups"])
        tcs = [final_circuit(h, "baseline", g) for g in range(ng)]
        out[h] = his_from_counts(h, execute(tcs, shots))[0]
    return out

STRESS_NOM = 1.0
CALIB = {}
if MODE == "cpu":
    t0 = time.time()
    grid = [0.3, 0.6, 1.0, 1.6, 2.5, 4.0]
    pts = []
    for s in grid:
        r = pilot_off(s); pts.append((s, 0.5 * (r["T1_QAOA"] + r["T5_HEA"]), r))
        print("stress=%.2f  HIS_off T1=%.3f T5=%.3f  media=%.3f" % (s, r["T1_QAOA"], r["T5_HEA"], pts[-1][1]))
    lo = hi = None
    for (s0, m0, _), (s1, m1, _) in zip(pts[:-1], pts[1:]):
        if m0 >= STRESS_TARGET >= m1:
            lo, hi = s0, s1; break
    if lo is None:                       # sin cruce: usar el más cercano
        STRESS_NOM = min(pts, key=lambda p: abs(p[1] - STRESS_TARGET))[0]
    else:
        for _ in range(6):
            mid = math.sqrt(lo * hi); r = pilot_off(mid); m = 0.5 * (r["T1_QAOA"] + r["T5_HEA"])
            print("  bisección stress=%.3f media=%.3f" % (mid, m))
            if m >= STRESS_TARGET: lo = mid
            else: hi = mid
            if abs(m - STRESS_TARGET) < 0.01: break
        STRESS_NOM = mid
    device.stress = STRESS_NOM
    final = pilot_off(STRESS_NOM, shots=SHOTS)
    in_band = {h: STRESS_BAND[0] <= v <= STRESS_BAND[1] for h, v in final.items()}
    CALIB = dict(stress=STRESS_NOM, off_T1=final["T1_QAOA"], off_T5=final["T5_HEA"], in_band=in_band)
    print("\nSTRESS_NOM = %.3f | OFF: T1=%.3f T5=%.3f | en banda %s | %.0fs" % (
        STRESS_NOM, final["T1_QAOA"], final["T5_HEA"], in_band, time.time() - t0))
    if not all(in_band.values()):
        print("AVISO: algún Hamiltoniano del OFF queda fuera de [%.2f, %.2f]. Ajusta QAOA_P / HEA_LAYERS para igualar sensibilidades." % STRESS_BAND)
else:
    print("qpu: sin calibración de estrés (se valida la banda tras medir el OFF)")
''')

md("## 6. Motor EQG: Ojos → Juicio → Reflejos → Manos")
code(r'''
def setup_eqg():
    """Reconstruye el motor con la fricción observada al estrés vigente."""
    fr = observe_fr()
    MOTOR["ojos"] = {"active": True, "detail": "mean_fr=%.3f max=%.3f (n_hot>=thr: %d)" % (
        fr.mean(), fr.max(), int((fr >= DD_FRICTION_THR).sum()))}
    mean_fr = float(fr.mean())
    if mean_fr >= ABORT_FR_MEAN:
        raise RuntimeError("Juicio ABORT mean_fr=%.3f" % mean_fr)
    base_mean = layout_score(LAYOUT_BASE, fr)
    base_hot = [q for q in LAYOUT_BASE if fr[q] >= DD_FRICTION_THR]
    intervene = (base_mean >= REMAP_FRICTION_THR) or len(base_hot) > 0
    MOTOR["juicio"] = {"active": True, "detail": "%s fr_base=%.3f hot_en_base=%s" % (
        "INTERVENIR" if intervene else "HOLD", base_mean, base_hot)}
    blacklist = [q for q in range(n_phys) if fr[q] >= DD_FRICTION_THR]
    paths = path_layouts(N, fr, blacklist) or path_layouts(N, fr, [])
    layout_eqg = min(paths, key=lambda p: layout_score(p, fr)) if intervene else list(LAYOUT_BASE)
    MOTOR["reflejos"] = {"active": True, "detail": "base=%s eqg=%s score_base=%.3f score_eqg=%.3f" % (
        LAYOUT_BASE, layout_eqg, base_mean, layout_score(layout_eqg, fr))}
    dd_eqg = dd_qubits_for(layout_eqg, fr) if intervene else []
    dd_on_base = dd_qubits_for(LAYOUT_BASE, fr) if intervene else []
    ARM_CFG.clear()
    ARM_CFG["baseline"] = dict(layout=LAYOUT_BASE, dd=[])
    ARM_CFG["baseline2"] = dict(layout=LAYOUT_BASE, dd=[])
    ARM_CFG["eqg"] = dict(layout=layout_eqg, dd=dd_eqg)
    if ABLATION:
        ARM_CFG["eqg_remap"] = dict(layout=layout_eqg, dd=[])
        ARM_CFG["eqg_dd"] = dict(layout=LAYOUT_BASE, dd=dd_on_base)
    _dd.clear(); _base_cache.clear()
    if intervene:
        _ = base_circuit("T1_QAOA", "eqg", 0)
        n_dd = _dd.get("eqg", 0)
        if n_dd <= 0:
            raise RuntimeError("Manos no insertó DD en el probe")
    else:
        n_dd = 0
    MOTOR["manos"] = {"active": True, "detail": "dd_qubits=%s probe_pulses=%d" % (dd_eqg, n_dd)}
    _dd.clear()
    return fr

fr_now = setup_eqg()
require_eqg()
''')

md(r'''
## 7. Experimento: ABBA generalizado

Orden por ciclo: `arms + arms[::-1]`. Brazos: `baseline`, `baseline2` (**control nulo**), `eqg` y, en CPU, la ablación `eqg_remap` (solo Reflejos) y `eqg_dd` (solo Manos sobre el layout base). El tiempo normalizado `frac` recorre 0→1 y gobierna la deriva.
''')
code(r'''
def run_experiment(shots, n_cycles):
    arms = list(ARM_CFG.keys())
    order = (arms + arms[::-1]) * n_cycles
    nblk = len(order)
    jobs = [(blk, arm, h, g) for blk, arm in enumerate(order) for h in HAM for g in range(len(HAM[h]["groups"]))]
    cost = est_cost(len(jobs), shots)
    print("arms:", arms)
    print("bloques=%d circuitos=%d shots=%d coste_QPU_est≈%.1fs (tope %.0f)" % (nblk, len(jobs), shots, cost, MAX_QPU_SECONDS))
    if MODE == "qpu":
        if cost > MAX_QPU_SECONDS: raise RuntimeError("coste > MAX_QPU_SECONDS — baja SHOTS/N_CYCLES")
        if not QPU_CONFIRM: raise RuntimeError("QPU_CONFIRM=True para gastar cuenta")
    t0 = time.time()
    tcs = []
    for (blk, arm, h, g) in jobs:
        if MODE == "cpu":
            device.frac = blk / max(nblk - 1, 1)
        tcs.append(final_circuit(h, arm, g))
    print("transpile+DD+ruido %.1fs | RSS≈%.0f | DD pulses %s" % (time.time() - t0, mem_mb(), dict(_dd)))
    t0 = time.time()
    counts = execute(tcs, shots)
    print("run %.1fs" % (time.time() - t0))
    by = defaultdict(lambda: defaultdict(dict))
    for (blk, arm, h, g), c in zip(jobs, counts):
        by[(blk, arm)][h][g] = c
    recs = []
    for (blk, arm), hd in by.items():
        for h, gd in hd.items():
            his, se, h_re = his_from_counts(h, [gd[g] for g in range(len(HAM[h]["groups"]))])
            recs.append(dict(block=blk, arm=arm, H=h, HIS=his, SE=se, h_re=h_re))
    return pd.DataFrame(recs).sort_values(["H", "arm", "block"]).reset_index(drop=True)

def agg(df, h, arm):
    sub = df[(df.H == h) & (df.arm == arm)]
    x = sub.HIS.to_numpy(float); se = sub.SE.to_numpy(float); k = len(x)
    se_s = math.sqrt(np.nansum(se ** 2)) / max(k, 1)
    se_b = float(np.std(x, ddof=1) / math.sqrt(k)) if k > 1 else 0.0
    return float(np.nanmean(x)), max(se_s, se_b), k

df_main = run_experiment(SHOTS, N_CYCLES)
dd_main = dict(_dd)
print(df_main.groupby(["H", "arm"]).HIS.agg(["mean", "std", "count"]).round(4))
''')

md("## 8. Veredicto estricto")
code(r'''
def verdict_from(df, dd_pulses, off_band_vals=None):
    v = {}
    for h in HAM:
        mb, sb, kb = agg(df, h, "baseline")
        mb2, sb2, _ = agg(df, h, "baseline2")
        me, se, ke = agg(df, h, "eqg")
        entry = dict(HIS_off=mb, HIS_on=me, delta=me - mb, z=z_diff(me, se, mb, sb),
                     null_delta=mb2 - mb, null_z=z_diff(mb2, sb2, mb, sb), n=ke)
        entry["pass_"] = bool(entry["delta"] > 0 and entry["z"] >= GATE_Z)
        for arm in ("eqg_remap", "eqg_dd"):
            if arm in set(df.arm):
                ma, sa, _ = agg(df, h, arm)
                entry[arm] = dict(HIS=ma, delta=ma - mb, z=z_diff(ma, sa, mb, sb))
        v[h] = entry
    reasons = []
    in_band = {h: STRESS_BAND[0] <= v[h]["HIS_off"] <= STRESS_BAND[1] for h in v}
    if not all(in_band.values()):
        reasons.append("OFF fuera de banda %s: %s" % (STRESS_BAND, {h: round(v[h]["HIS_off"], 3) for h in v}))
    if not all(abs(v[h]["null_z"]) < GATE_Z for h in v):
        reasons.append("control nulo |z|>=%.1f: %s" % (GATE_Z, {h: round(v[h]["null_z"], 2) for h in v}))
    if dd_pulses.get("eqg", 0) <= 0 and len(ARM_CFG["eqg"]["dd"]) > 0:
        reasons.append("Manos sin pulsos")
    if reasons:
        gate = "PRUEBA_INVALIDA"
    elif all(v[h]["pass_"] for h in v):
        gate = "PRODUCTO_OK"
    else:
        gate = "PRODUCTO_NO"
    return gate, v, reasons, in_band

def print_verdict(tag, gate, v, reasons, in_band):
    print("=" * 74)
    print("  EQG ON vs OFF | %s | %s | %s" % (EQG_VERSION, MODE, tag))
    print("=" * 74)
    for h, e in v.items():
        print("%-8s OFF=%.4f%s  ON=%.4f  Δ=%+.4f  z=%+.2f  %s | nulo Δ=%+.4f z=%+.2f" % (
            h, e["HIS_off"], "" if in_band[h] else "(!banda)", e["HIS_on"], e["delta"], e["z"],
            "PASS" if e["pass_"] else "NO", e["null_delta"], e["null_z"]))
        for arm in ("eqg_remap", "eqg_dd"):
            if arm in e:
                print("          ablación %-9s HIS=%.4f Δ=%+.4f z=%+.2f" % (arm, e[arm]["HIS"], e[arm]["delta"], e[arm]["z"]))
    print("-" * 74)
    print("COMPUERTA:", gate)
    for r in reasons: print("  motivo:", r)

gate, verdict, reasons, in_band = verdict_from(df_main, dd_main)
print_verdict("nominal stress=%.3f" % (device.stress if device else float("nan")), gate, verdict, reasons, in_band)
print("Layouts: baseline=%s  eqg=%s | DD en %s" % (ARM_CFG["baseline"]["layout"], ARM_CFG["eqg"]["layout"], ARM_CFG["eqg"]["dd"]))
''')

md(r'''
## 9. Sensibilidad al estrés (CPU)

Repite el experimento con multiplicadores sobre el estrés calibrado (p. ej. 1.35× = más hostil). El OFF saldrá de banda a propósito (la banda solo vale para el nominal): aquí interesa si la ganancia de EQG **se mantiene significativa** al endurecer el ruido.
''')
code(r'''
sweep = {}
if MODE == "cpu" and len(STRESS_SWEEP) > 1:
    for mult in STRESS_SWEEP:
        if abs(mult - 1.0) < 1e-9:
            continue
        device.stress = STRESS_NOM * mult
        setup_eqg()
        dfm = run_experiment(max(1024, SHOTS // 2), max(1, N_CYCLES - 1))
        dd_m = dict(_dd)
        g_, v_, r_, ib_ = verdict_from(dfm, dd_m)
        sweep[mult] = dict(OFF={h: v_[h]["HIS_off"] for h in v_}, ON={h: v_[h]["HIS_on"] for h in v_},
                           delta={h: v_[h]["delta"] for h in v_}, z={h: v_[h]["z"] for h in v_},
                           null_z={h: v_[h]["null_z"] for h in v_})
        print("\n× %.2f  → OFF %s | ON %s | Δ %s | z %s" % (
            mult, {h: round(x, 3) for h, x in sweep[mult]["OFF"].items()},
            {h: round(x, 3) for h, x in sweep[mult]["ON"].items()},
            {h: round(x, 3) for h, x in sweep[mult]["delta"].items()},
            {h: round(x, 2) for h, x in sweep[mult]["z"].items()}))
    device.stress = STRESS_NOM
    setup_eqg()
else:
    print("sin barrido (QPU o STRESS_SWEEP de un solo valor)")
''')

md("## 10. Figura y reporte")
code(r'''
arms_plot = [a for a in ("baseline", "baseline2", "eqg_remap", "eqg_dd", "eqg") if a in set(df_main.arm)]
colors = {"baseline": "#c0392b", "baseline2": "#e6a29a", "eqg_remap": "#2980b9", "eqg_dd": "#8e44ad", "eqg": "#27ae60"}
fig, axes = plt.subplots(1, 3, figsize=(15, 4.2))
for ax, h in zip(axes[:2], HAM):
    ms = [agg(df_main, h, a) for a in arms_plot]
    ax.bar(arms_plot, [m[0] for m in ms], yerr=[m[1] for m in ms], color=[colors[a] for a in arms_plot], capsize=4, edgecolor="k", lw=.5)
    ax.axhspan(STRESS_BAND[0], STRESS_BAND[1], color="gray", alpha=0.15, label="banda OFF")
    ax.set_ylim(0, 1.05); ax.set_ylabel("HIS_span"); ax.set_title(h); ax.tick_params(axis="x", rotation=30); ax.legend(fontsize=8)
ax = axes[2]
hs = list(HAM.keys())
ax.barh(hs, [verdict[h]["delta"] for h in hs], xerr=[verdict[h]["delta"] / verdict[h]["z"] if verdict[h]["z"] not in (0, float("nan")) and not math.isnan(verdict[h]["z"]) else 0 for h in hs], color="#27ae60", capsize=4)
ax.axvline(0, color="k"); ax.set_xlabel("Δ HIS (ON − OFF)"); ax.set_title(gate)
plt.tight_layout(); fig.savefig(OUT / "eqg_stress.png", dpi=140, bbox_inches="tight"); plt.show()

report = dict(version=EQG_VERSION, fingerprint=FP, mode=MODE, gate=gate, reasons=reasons, in_band=in_band,
              stress_nominal=STRESS_NOM, calibration=CALIB, verdict=verdict, sweep=sweep, motor=MOTOR,
              arms={a: dict(layout=c["layout"], dd=c["dd"]) for a, c in ARM_CFG.items()}, dd_pulses=dd_main,
              load=dict(N=N, qaoa_p=QAOA_P, hea_layers=HEA_LAYERS, idle_us=IDLE_US, shots=SHOTS, cycles=N_CYCLES,
                        dd_thr=DD_FRICTION_THR, remap_thr=REMAP_FRICTION_THR),
              records=df_main.to_dict(orient="records"), created=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
path = OUT / f"report_{MODE}.json"
path.write_text(json.dumps(report, indent=2, default=lambda o: float(o) if hasattr(o, "item") else str(o)))
(OUT / "summary.txt").write_text("gate=%s\n%s\n" % (gate, "\n".join(
    "%s OFF=%.4f ON=%.4f delta=%+.4f z=%+.2f" % (h, e["HIS_off"], e["HIS_on"], e["delta"], e["z"]) for h, e in verdict.items())))
print("saved", path)
require_eqg()
print("RSS≈%.0f MB" % mem_mb())
''')

md(r'''
## Uso

1. `MODE="cpu"` → **Run All**. El notebook calibra el estrés con el OFF, congela el multiplicador y mide ON.
2. `PRODUCTO_OK` solo si en **T1 y T5**: Δ>0 y z ≥ 2, el control nulo no se separa (|z|<2), el OFF cae en [0.60, 0.75] y Manos aplicó DD. Si falla algo de validez → `PRUEBA_INVALIDA` (no es un "NO" del producto).
3. Hardware: `MODE="qpu"` y `QPU_CONFIRM=True` **solo después** de congelar la configuración. Sin perilla de estrés en QPU: si el OFF sale fuera de banda, sube `IDLE_US` o las capas y repite.

Copyright (c) 2026 Arturo Salvador Balderas Hernández — Elastic License 2.0. Qiskit Apache-2.0.
''')

nb.cells = C
nb.metadata = {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
               "language_info": {"name": "python"}}
nbf.validate(nb)
nbf.write(nb, "/mnt/user-data/outputs/EQG_vs_baseline_estres.ipynb")
print("ok", len(C))
