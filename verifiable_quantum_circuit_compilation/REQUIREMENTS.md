# Mandatory notebook acceptance contract — Google Quantum AI Verifiable Quantum Circuit Compilation
Source of benchmark specifications: `verificable.pdf` (Khattar et al., October 22 2026), especially §§II–III. Operational Kaggle packaging must additionally be checked against the current official competition data/rules; the paper does not itself establish the exact ZIP layout.

## Non-negotiable build process
1. Read this file and the benchmark-specific official verifier and reference code BEFORE generating or revising a notebook. Never claim execution, PASS, score or submission without recorded evidence.
2. Notebook must run from a clean Kaggle kernel using competition-mounted inputs, with no QPU, external secrets or undeclared local dependencies; detect paths, check dependencies and Kickmix, report time/RAM/versions, fail clearly on missing prerequisites.
3. Build actual serialized Kickmix `.kmb` candidates, not float-only surrogates. Verify preserved input/output, zeroed scratch, correct phases including HMR/R correction, and benchmark tolerances. Circuit hash changes verifier challenges; don't hard-code sampled answers.
4. Run official verifier at development smoke level and at full competition acceptance settings; distinguish them. Capture exit codes, stdout/stderr, JSON, SHA-256, metrics. Any FAIL, ERROR, SKIP, TIMEOUT or absent report blocks readiness.
5. Compute scores ONLY with official verifier and compare with reproducible baseline. Never substitute naive gate-count formula or projected improvement.
6. Validate official competition packaging format against current Kaggle instructions before constructing `/kaggle/working/submission.zip`. Do not produce or advertise submission.zip if any mandatory gate fails. Inspect ZIP integrity and manifest against validated outputs.
7. Save Version / Run All and Kaggle acceptance are external platform gates: mark PENDING until observed, never self-certify.

## Paper-specific contracts
### I. invsqrt (§III A)
- np=10; exactly one named quantum input register `x` of 22 distinct qubits; x in [1, 3,133,452]. Other qubits scratch; x preserved and scratch zeroed.
- Target phase exp(2πi β/sqrt(x)), default β=1. Phase tolerance 2^-24 β/sqrt(x) turns, checked against integer-square-root reference in 64-bit fixed point.
- Full verification 64 shots for EACH x = 200,540,928 shots; ZERO failures. SHA-256 of canonical `.kmb` plus competition salt seeds tests.
- Score S=Q*C; C includes Toffolis, T/4, and official analytic synthesis cost of non-Clifford Z_POW rotations based on residual phase margin. Never use Q*(Toffoli+T/4) alone when rotations exist.
- Paper reference: Q=260, 7735 Toffoli, 1 T, 37 rotations; paper approximate score 2.08e6 (official verifier is authoritative).
### II. DQI (§III B)
- GF(2^12), m=4095, n=70, ell=35, syndrome 840 quantum bits; c is 49,140 classical bits. Preserve syndrome, clear workspace, apply (-1)^(c·bin(e(s))) on promised decodable inputs.
- Official N=102400 shots sampled from specified weight distribution and Fiat-Shamir circuit hash; calculate one-sided Clopper–Pearson epsilon+ at confidence 1-2^-128.
- Score S=R(epsilon+) Q^2 T, T includes cleanup, p0=1/2; epsilon+ >= 1/16 => no finite score. Baseline 1893 qubits and 5,725,461 Toffolis.
### III. DFTHC / chemistry (§III C)
- FeMo-co N=76, eta=113. Fixed baseline symmetry shift S0 and beta1,0. Optimize permitted factorization and angle-oracle/tree artifacts; don't claim a single .kmb alone is full chemistry submission.
- Verify every valid vector address 64 times in forward and reverse traversal, unchanged address, clean workspace, corrected phase; EACH Angles_k circuit <=128 qubits.
- Residuals epsilon1<=0.020 Ha and epsilon2<=0.020 Ha; all metrics finite; 0<Egap<2Lambda, Egap>3.914898 Ha, Lambda>49.0 Ha. Fixed Eupper=-22140.27335 Ha.
- Score S=lambda_eff*Ttot*Qtot, lambda_eff=sqrt(Egap*(2Lambda-Egap)), with official modeled costs; rejected checks => infinite score. Overall Qtot is not capped at 128.

## Readiness states
- BUILDABLE: clean Run All and genuine artifacts.
- VERIFIED: official full verifier PASS for every required benchmark and valid packaging.
- COMPETITIVE: VERIFIED plus measured improvement over reference using official metrics.
- SUBMITTED: Kaggle has actually processed the generated artifact and returned a result.
A notebook can be BUILDABLE without being VERIFIED; never conflate these states.
