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


Para construir un notebook de Kaggle eficiente y reproducible que genere el archivo submission.zip exigido por la competición, la estructura recomendada se organiza en un flujo modular de 5 etapas: configuración del entorno, compilación/verificación local de cada benchmark y empaquetado final.
1. Configuración del Entorno e Importaciones
El entorno de Kaggle incluye el paquete de simulación kickmix en los archivos del dataset de la competencia. El notebook debe comenzar añadiendo kickmix al sistema e importando la biblioteca Qualtran.
 * Acciones clave:
   * Configurar sys.path para localizar kickmix.so o instalar los paquetes requeridos.
   * Importar Qualtran, kickmix (km), numpy y la librería zipfile para la generación de archivos binarios .kmb y compresión ZIP.
import os
import sys
import zipfile
import numpy as np

# Vincular la ruta de kickmix proporcionada por la plataforma
sys.path.append('/kaggle/input/google-verifiable-quantum-circuit-compilation/kickmix')
import kickmix as km
from qualtran import QBit

2. Módulo Tarea I: Compilación y Exportación de invsqrt
Esta sección compila el circuito para la función de fase 1/\sqrt{x}.
 * Requisitos del circuito:
   * Registro de entrada nombrado exactamente x con 22 qubits.
   * Espacio de trabajo auxiliar que debe retornar a \vert{}0\rangle.
 * Salida requerida:
   * invsqrt.kmb (o invsqrt.kmx).
 * Prueba local:
   * Ejecutar el simulador de kickmix verificando que la fase acumulada no exceda la tolerancia 2^{-24}/\sqrt{x} en 0 fallos (k=0).
def build_invsqrt_circuit():
    builder = km.Builder()
    x = builder.add_register('x', 22)
    
    # ... Lógica de normalización, interpolación polinomial y Newton-Raphson ...
    
    circuit = builder.finish()
    return circuit

invsqrt_circuit = build_invsqrt_circuit()
# Guardar archivo binario serializado
invsqrt_circuit.save_kmb("invsqrt.kmb")

3. Módulo Tarea II: Compilación y Exportación de dqi
En este bloque se construye el decodificador de síndromes para el código de Reed-Solomon [4095, 4025, 71] sobre \mathbb{F}_{2^{12}}.
 * Requisitos del circuito:
   * Manejo del registro cuántico del síndrome s (840 qubits) y lectura del registro clásico c (49.140 bits).
   * Limpieza total de los qubits auxiliares del algoritmo de Euclides extendido (EEA) e Itoh-Tsujii.
 * Salida requerida:
   * dqi.kmb (o dqi.kmx).
 * Prueba local:
   * Muestrear disparos pseudoaleatorios con el evaluador local verificando que la tasa de falla acotada \epsilon^+ se mantenga estrictamente por debajo de 1/16.
def build_dqi_circuit():
    builder = km.Builder()
    # Definición de registros e implementación del algoritmo EEA
    
    circuit = builder.finish()
    return circuit

dqi_circuit = build_dqi_circuit()
dqi_circuit.save_kmb("dqi.kmb")

4. Módulo Tarea III: Compilación y Exportación de dfthcsos
Esta tarea requiere la generación conjunta de los oráculos numéricos y los binarios de rotación de ángulos para el complejo FeMoCo.
 * Requisitos del módulo:
   * Creación de submission.npz: Generar el diccionario NumPy con los rangos (R, B, C), vectores u_b^{(\rho)}, coeficientes w_b^{(\rho c)}, desplazamientos W^{(\rho c)} y la estructura del árbol de Givens \mathcal{T}.
   * Generación de oráculos angle_k: Crear la familia de circuitos angle_k_0.kmb a angle_k_{K-1}.kmb respetando el límite máximo de 128 qubits por circuito.
 * Salida requerida:
   * Subdirectorio dfthcsos/ conteniendo submission.npz y todos los oráculos de ángulo.
os.makedirs("dfthcsos", exist_ok=True)

# 1. Exportar variables numéricas clásicas
np.savez(
    "dfthcsos/submission.npz",
    R=R_val, B=B_val, C=C_val,
    u=u_vectors, w=w_coeffs, W=W_offsets,
    tree=tree_structure
)

# 2. Generar y exportar los oráculos de ángulos (angle_k)
for k in range(K_batches):
    builder = km.Builder()
    selection = builder.add_register('selection', num_select_bits)
    # Definir registros 'word_0', ... 'word_J-1'
    
    angle_circuit = builder.finish()
    assert angle_circuit.num_qubits <= 128, f"Circuito angle_{k} excede el límite de 128 qubits"
    angle_circuit.save_kmb(f"dfthcsos/angle_k_{k}.kmb")

5. Verificación Local Integral y Empaquetado en submission.zip
Antes de generar el archivo ZIP final, es crucial invocar los scripts de verificación oficiales incluidos en el entorno de la competencia para confirmar que la entrega satisface todos los requisitos de precisión espectral y conservación de espacio de trabajo.
# 1. Ejecutar verificación cruzada con el verificador oficial de la competencia
from verifiers import verify_all_tasks

verification_results = verify_all_tasks(
    invsqrt_path="invsqrt.kmb",
    dqi_path="dqi.kmb",
    dfthcsos_dir="dfthcsos"
)
print("Resultados de Verificación Local:", verification_results)

# 2. Crear el archivo submission.zip en la raíz de trabajo de Kaggle
files_to_zip = ["invsqrt.kmb", "dqi.kmb"]

with zipfile.ZipFile("submission.zip", "w", zipfile.ZIP_DEFLATED) as zipf:
    for file in files_to_zip:
        zipf.write(file, arcname=file)
    
    # Agregar carpeta dfthcsos/ y su contenido
    for root, _, files in os.walk("dfthcsos"):
        for file in files:
            file_path = os.path.join(root, file)
            zipf.write(file_path, arcname=os.path.join("dfthcsos", file))

print("submission.zip generado con éxito.")

Resumen de la Jerarquía Generada en el Archivo ZIP
Al finalizar el notebook, la estructura resultante dentro de submission.zip debe coincidir con el siguiente esquema de archivos:
| Ruta dentro de submission.zip | Descripción del Contenido | Requisito Principal |
|---|---|---|
| invsqrt.kmb | Circuito 1/\sqrt{x} | Registro x (22 qubits), 0 fallos (k=0). |
| dqi.kmb | Decodificador Reed-Solomon | Registros s y c, tasa de falla \epsilon^+ < 1/16. |
| dfthcsos/submission.npz | Parámetros numéricos DFTHC | Cumplimiento de pisos \Lambda > 49,0 y E_{\text{gap}} > 3,914898. |
| dfthcsos/angle_k_0.kmb ... | Familias de oráculos de ángulo | Máximo 128 qubits por archivo. |
