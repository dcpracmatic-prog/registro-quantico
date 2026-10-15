# **Edge Quantum Guard** (EQG)

**¿Qué es?**

**EQG** (*Edge Quantum Guard*) es un sistema inteligente de control en bucle cerrado diseñado para operar en tiempo real sobre hardware cuántico NISQ. Su propósito central es neutralizar los fluctuadores bi-estables (TLS) y la degradación por ruido ambiental antes de que destruyan la superposición de los cúbits o invaliden los resultados de algoritmos variacionales (como QAOA).

## **The Goal**
>
| Variable / Parameter | Ideal / Target Value (Good / Frictionless State) |
|---|---|
| T2s_free (Free Ramsey coherence time) | ≥ 155.46 µs (healthy state) |
| T2_cpmg (CPMG decoupling coherence) | ≥ 212.91 µs |
| T2_xy4 (XY4 sequence coherence) | ≥ 224.07 µs |
| det_kHz (TLS frequency detuning) | ~ -27.05 kHz (stable nominal) |
| ZZ (Residual spin-spin cross-interaction) | ~ -0.27 kHz (with CPMG / shielding) |
| ΔHIS (Hamiltonian Integrity Score gain) | ≥ +0.25 (ideal post-filtering survival) |
| SEδ (Standard error of improvement) | Minimized (→ 0) |

La intención existencial de EQG es precisamente guiar de forma activa al hardware desde su estado de alta fricción o degradado hasta alcanzar y sostener las métricas objetivo de un estado saludable y sin fricción:


•Recuperación de Coherencia (T2s_free, T2_cpmg, T2_xy4): EQG actúa preventivamente para que los tiempos de coherencia libre y desacoplada alcancen o superen los umbrales ideales (>= 155.46 µs, >= 212.91 µs y >= 224.07 µs respectivamente), evitando la decoherencia prematura.

•Estabilización de Frecuencia y Acoplamiento (det_kHz y ZZ): A través de sondeos rápidos, el sistema detecta desviaciones del TLS para mantener la desintonización en su valor nominal estable (~ -27.05 kHz) y suprimir el acoplamiento cruzado espín-espín residual a niveles óptimos (~ -0.27 kHz).

•Maximización de la Integridad (ΔHIS): Garantiza una supervivencia ideal post-filtrado del hamiltoniano con una ganancia de integridad (ΔHIS >= +0.25).

•Significancia Estadística (SEδ): Minimiza el error estándar de la mejora (-> 0), asegurando mediante un control estricto que la ventaja observada sea robusta y estadísticamente incuestionable.


## El Ciclo Operativo de EQG

EQG is the productized control plane for quantum workloads:


1. **Observe** hardware health without elevated privileges  
2. **Select** layout via MORPH  
3. **Decide** minimal intervention (hold / remap / conditional DD)  
4. **Actuate** via Centinela sequences  
5. **Score** outcomes with HIS (and SE/z in validation pipelines)

## delivery for validation 
*pre - production*

> 
- executable files (.ipynb)
- Conceptual optimization proposals 
- optimal connection of internal modules (Ablation)
- validation of improvements vs the goal (full EQG in CPU)
- packaged repository if the goal is reached 


## delivery for production 
*after achieve goal in CPU*

>
- Quick confirmation of EQG in QPU (professional level + Ablation)
- Full validation in QPU (if cost-effective)
- CLI for automation and CI smoke
- Helm chart for Cloud private catalog (Software → Helm)
- Marketing strategy and business model 
