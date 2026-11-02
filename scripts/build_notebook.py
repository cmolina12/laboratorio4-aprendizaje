import nbformat as nbf, sys, json, os

OUT = sys.argv[1]
ANALISIS = sys.argv[2] if len(sys.argv) > 2 else None  # json con textos de análisis
txt = json.load(open(ANALISIS)) if ANALISIS and os.path.exists(ANALISIS) else {}
def T(key, default="*(pendiente)*"):
    return txt.get(key, default)

cells = []
def md(s): cells.append(nbf.v4.new_markdown_cell(s.strip("\n")))
def code(s): cells.append(nbf.v4.new_code_cell(s.strip("\n")))

md(r"""
# Laboratorio 4 - Segmentación de imágenes con técnicas de agrupación
## Caso: DermAlpes

**Curso:** ISIS2611 - Aprendizaje de Máquina

**Integrantes:**
- Camilo Molina
- Natalia Erazo

**Objetivo:** construir un método no supervisado que delimite automáticamente la lesión en imágenes dermatoscópicas agrupando sus píxeles con K-medias según color y posición, ajustarlo con un protocolo que no use las imágenes de prueba, y analizar críticamente dónde falla y qué riesgos tiene su uso con nuevas poblaciones.

**Fuente de los datos:** ISIC 2016 – *Skin Lesion Analysis Toward Melanoma Detection*, tarea 1 (segmentación de lesiones). https://challenge.isic-archive.com/landing/2016/37/
> Gutman, D., Codella, N. C. F., Celebi, E., Helba, B., Marchetti, M., Mishra, N., & Halpern, A. (2016). *Skin Lesion Analysis toward Melanoma Detection: A Challenge at the International Symposium on Biomedical Imaging (ISBI) 2016, hosted by the International Skin Imaging Collaboration (ISIC)*. arXiv:1605.01397.

Las máscaras se tomaron del archivo oficial `ISBI2016_ISIC_Part1_Training_GroundTruth.zip` y las imágenes originales (licencia CC-0) del ISIC Archive (`https://isic-archive.s3.amazonaws.com/images/ISIC_xxxxxxx.jpg`); se verificó que cada imagen tenga exactamente las mismas dimensiones que su máscara.

### Contenido
0. Configuración del entorno
1. Pipeline de preparación y representación
2. Agrupación y selección de K con silueta
3. Construcción de la máscara de la lesión
4. Ajuste del método (incluye la actividad de verificación con IAG)
5. Evaluación en las imágenes de prueba
6. Video
7. Análisis de resultados
8. Uso de herramientas de IA generativa
9. Bonos
""")

md("## 0. Configuración del entorno")
code(r"""
import time
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image
from scipy import ndimage as ndi

import sklearn
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.cluster import KMeans, MeanShift, estimate_bandwidth
from sklearn.metrics import (silhouette_score, f1_score, v_measure_score,
                             precision_score, recall_score)
from sklearn.decomposition import PCA

pd.set_option("display.max_columns", 50)
pd.set_option("display.precision", 3)
sns.set_theme(style="whitegrid")

SEED = 42             # semilla única: K-medias y muestra de la silueta
ANCHO = 128           # ancho (px) al que se reducen todas las imágenes
N_SILUETA = 2000      # tamaño de la muestra de píxeles para la silueta
K_RANGO = range(2, 9) # K entre 2 y 8

DATA = Path("data")
AJUSTE = ["ISIC_0000085", "ISIC_0000086", "ISIC_0000089", "ISIC_0000094", "ISIC_0000108",
          "ISIC_0000114", "ISIC_0000116", "ISIC_0000122", "ISIC_0000133", "ISIC_0000137",
          "ISIC_0000150", "ISIC_0000153", "ISIC_0000156", "ISIC_0000157", "ISIC_0000112"]
PRUEBA = ["ISIC_0000087", "ISIC_0000105", "ISIC_0000110", "ISIC_0000123", "ISIC_0000128"]
assert len(AJUSTE) == 15 and len(PRUEBA) == 5 and not set(AJUSTE) & set(PRUEBA)

print("numpy", np.__version__, "| scikit-learn", sklearn.__version__, "| pandas", pd.__version__)
""")

md(r"""
## 1. Pipeline de preparación y representación

### 1.1 Carga y preparación de imágenes y máscaras
Las imágenes originales miden entre 963×629 y 2592×1944 píxeles. Agrupar millones de píxeles con K-medias para 10 configuraciones × 7 valores de K × 15 imágenes sería muy costoso, así que **todas las imágenes se reducen a 128 px de ancho** conservando la proporción (≈128×96 = 12 288 píxeles). A esta resolución la lesión sigue claramente visible y el borde se conserva con un error de ±1 píxel reducido.

- La imagen se redimensiona con interpolación bilineal (suaviza ruido y pelos finos).
- La máscara se redimensiona **con vecino más cercano** para que siga siendo binaria, y se convierte de {0, 255} a {0, 1}.
""")
code(r"""
def cargar(id_imagen, ancho=ANCHO):
    # Devuelve la imagen RGB (uint8, H×W×3) y la máscara de referencia (0/1, H×W) al mismo tamaño.
    img = Image.open(DATA / "images" / f"{id_imagen}.jpg").convert("RGB")
    msk = Image.open(DATA / "masks" / f"{id_imagen}_Segmentation.png")
    assert img.size == msk.size, f"{id_imagen}: imagen y máscara con tamaños distintos"
    alto = round(img.height * ancho / img.width)
    img = np.asarray(img.resize((ancho, alto), Image.BILINEAR))
    msk = np.asarray(msk.resize((ancho, alto), Image.NEAREST))
    msk = (msk == 255).astype(np.uint8)          # 0 = piel/fondo, 1 = lesión
    return img, msk

# Solo se cargan las imágenes de AJUSTE. Las de prueba se cargan únicamente en la sección 5.
datos_aj = {i: cargar(i) for i in AJUSTE}

resumen = pd.DataFrame([{"imagen": i, "tamaño reducido (H×W)": f"{im.shape[0]}×{im.shape[1]}",
                         "valores máscara": str(np.unique(m).tolist()),
                         "% lesión": 100 * m.mean()} for i, (im, m) in datos_aj.items()])
resumen
""")
code(r"""
fig, axes = plt.subplots(3, 5, figsize=(16, 8.5))
for ax, (i, (im, m)) in zip(axes.ravel(), datos_aj.items()):
    ax.imshow(im); ax.contour(m, levels=[0.5], colors="lime", linewidths=1.2)
    ax.set_title(f"{i}  ({100*m.mean():.0f}% lesión)", fontsize=9); ax.axis("off")
fig.suptitle("Imágenes de ajuste con el contorno de la máscara de referencia (verde)")
plt.tight_layout(); plt.show()
""")
md(r"""
Observaciones iniciales: las lesiones suelen ser **más oscuras** que la piel y estar cerca del centro, pero hay variabilidad importante: lesiones muy pequeñas (ISIC_0000114, ~3 % de la imagen), lesiones grandes que tocan el borde, **viñeteado oscuro** en las esquinas producido por el dermatoscopio, pelos, burbujas de gel y lesiones de bajo contraste. Todas las pieles del conjunto son claras, lo cual es relevante para la discusión de sesgos.
""")

md(r"""
### 1.2 Representación de cada píxel y pipeline de Scikit-learn
Cada imagen se convierte en una matriz con **un píxel por fila** y las columnas $[\beta R, \beta G, \beta B, \lambda x, \lambda y]$:

1. `PixelesRGBXY`: transforma la imagen H×W×3 en una matriz (H·W)×5 con R, G, B divididos por 255 y las coordenadas normalizadas $x = col/(W-1)$, $y = fila/(H-1)$, todo en $[0,1]$.
2. `PesosColorPosicion(beta, lam)`: multiplica las tres columnas de color por β y las dos de posición por λ. Al ser hiperparámetros del estimador, se modifican con `set_params` sin cambiar la implementación.
3. `KMeans(n_clusters=K)`.

Con β = 0 las columnas de color quedan en cero (solo posición) y con λ = 0 las de posición quedan en cero (solo color).
""")
code(r"""
class PixelesRGBXY(BaseEstimator, TransformerMixin):
    # Imagen (H, W, 3) uint8  ->  matriz (H*W, 5) con [R, G, B, x, y] en [0, 1].
    def fit(self, X, y=None):
        return self

    def __sklearn_is_fitted__(self):   # transformador sin estado: no aprende nada de los datos
        return True

    def transform(self, X):
        h, w, _ = X.shape
        filas, cols = np.mgrid[0:h, 0:w]
        color = X.reshape(-1, 3).astype(float) / 255.0
        pos = np.column_stack([(cols / (w - 1)).ravel(), (filas / (h - 1)).ravel()])
        return np.hstack([color, pos])


class PesosColorPosicion(BaseEstimator, TransformerMixin):
    # Multiplica el color por beta y la posición por lam: [bR, bG, bB, lx, ly].
    def __init__(self, beta=1.0, lam=0.0):
        self.beta = beta
        self.lam = lam

    def fit(self, X, y=None):
        return self

    def __sklearn_is_fitted__(self):   # transformador sin estado: no aprende nada de los datos
        return True

    def transform(self, X):
        return X * np.array([self.beta] * 3 + [self.lam] * 2)


def crear_pipeline(beta=1.0, lam=0.0, k=2):
    return Pipeline([
        ("pixeles", PixelesRGBXY()),
        ("pesos", PesosColorPosicion(beta=beta, lam=lam)),
        ("kmeans", KMeans(n_clusters=k, n_init=5, random_state=SEED)),
    ])


# Verificación del pipeline sobre una imagen
img0, _ = datos_aj["ISIC_0000085"]
pipe = crear_pipeline(beta=1, lam=0.5, k=3)
X = pipe[:-1].transform(img0)
print("forma de la matriz de píxeles:", X.shape)
print("rangos por columna (β=1, λ=0.5):", np.round(X.min(0), 2), np.round(X.max(0), 2))
pipe.set_params(pesos__beta=0, pesos__lam=1)          # solo posición
print("β=0, λ=1 -> máx. por columna:", np.round(pipe[:-1].transform(img0).max(0), 2))
pipe.set_params(pesos__beta=1, pesos__lam=0)          # solo color
print("β=1, λ=0 -> máx. por columna:", np.round(pipe[:-1].transform(img0).max(0), 2))
pipe
""")

md(r"""
## 2. Agrupación y selección de K

### 2.1 Combinaciones de β y λ
Como K-medias y la silueta solo dependen de distancias relativas, lo que importa es la **razón λ/β**. Se fija β = 1 y se varía λ (excepto en la configuración de solo posición), cubriendo desde "el color domina" hasta "la posición domina":

| # | β | λ | λ/β |
|---|---|---|---|
| 1 | 1 | 0 | 0 (solo color) |
| 2–9 | 1 | 0.1, 0.25, 0.5, 0.75, 1, 1.5, 2, 3 | 0.1 … 3 |
| 10 | 0 | 1 | ∞ (solo posición) |

Como referencia de escala: la diferencia típica de color entre lesión y piel es de 0.2–0.4 por canal, y la distancia entre dos píxeles en extremos opuestos de la imagen es ≈1.4. Con λ/β ≥ 1 la posición empieza a pesar tanto como el color.
""")
code(r"""
CONFIGS = [dict(nombre="solo color", beta=1.0, lam=0.0)]
CONFIGS += [dict(nombre=f"λ/β={r:g}", beta=1.0, lam=r) for r in [0.1, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0]]
CONFIGS += [dict(nombre="solo posición", beta=0.0, lam=1.0)]
ORDEN_CFG = [c["nombre"] for c in CONFIGS]
pd.DataFrame(CONFIGS)
""")

md(r"""
### 2.2 Selección de K con el coeficiente de silueta
Para cada imagen y combinación (β, λ) se ajusta K-medias con K = 2, …, 8 y se elige el K con **mayor coeficiente de silueta**. Calcular la silueta exacta sobre ~12 000 píxeles es $O(n^2)$, por lo que se usa una **muestra aleatoria reproducible de 2 000 píxeles por imagen, con semilla 42**. La muestra es la misma para todas las configuraciones y valores de K de una imagen, de modo que las comparaciones son justas. K-medias se ajusta con todos los píxeles (`n_init=5`, `random_state=42`).

La selección de K usa solo las características de los píxeles; **las máscaras de referencia no intervienen**. Se guardan las etiquetas de todos los K (no solo del elegido) para poder analizar después la relación entre K, silueta y Dice.
""")
code(r"""
def indices_silueta(n_pixeles, n=N_SILUETA, seed=SEED):
    return np.random.RandomState(seed).choice(n_pixeles, size=min(n, n_pixeles), replace=False)


def agrupar_todos_k(img, beta, lam):
    # Ajusta K-medias para cada K del rango y devuelve {K: (etiquetas, silueta)}.
    pipe = crear_pipeline(beta, lam)
    X = pipe[:-1].transform(img)
    idx = indices_silueta(len(X))
    salida = {}
    for k in K_RANGO:
        pipe.set_params(kmeans__n_clusters=k)
        etiquetas = pipe.fit(img)[-1].labels_
        salida[k] = (etiquetas, silhouette_score(X[idx], etiquetas[idx]))
    return salida


def k_por_silueta(resultados_k):
    return max(resultados_k, key=lambda k: resultados_k[k][1])
""")
code(r"""
t0 = time.time()
GRUPOS = {}   # (imagen, config) -> {K: (etiquetas, silueta)}
for i, (img, _) in datos_aj.items():
    for c in CONFIGS:
        GRUPOS[(i, c["nombre"])] = agrupar_todos_k(img, c["beta"], c["lam"])
print(f"{len(GRUPOS)} combinaciones imagen×configuración, {len(GRUPOS)*len(K_RANGO)} ajustes de K-medias "
      f"en {time.time()-t0:.0f} s")

sil = pd.DataFrame([{"imagen": i, "config": c, "K": k, "silueta": s}
                    for (i, c), d in GRUPOS.items() for k, (_, s) in d.items()])
k_sel = (sil.loc[sil.groupby(["imagen", "config"])["silueta"].idxmax()]
            .pivot(index="imagen", columns="config", values="K")[ORDEN_CFG])
k_sel
""")
code(r"""
fig, axes = plt.subplots(1, 2, figsize=(15, 4.5))
prom = sil.groupby(["config", "K"])["silueta"].mean().unstack(0)[ORDEN_CFG]
prom.plot(ax=axes[0], marker="o", cmap="viridis")
axes[0].set_title("Silueta promedio (15 imágenes de ajuste) según K"); axes[0].set_ylabel("silueta")
axes[0].legend(fontsize=8, ncol=2)
sns.heatmap(k_sel.apply(lambda s: s.value_counts()).fillna(0).astype(int).reindex(list(K_RANGO)).fillna(0),
            annot=True, fmt=".0f", cmap="Blues", ax=axes[1], cbar=False)
axes[1].set_title("Número de imágenes en que la silueta eligió cada K"); axes[1].set_ylabel("K elegido")
plt.tight_layout(); plt.show()
""")
md(r"""
La silueta tiende a preferir **K = 2** cuando domina el color: lesión oscura vs. piel clara es la partición más "limpia" en el espacio RGB. A medida que la posición gana peso, aparecen particiones espaciales (bandas o regiones de la imagen) y la silueta sube a K ≈ 5. Con solo posición los píxeles forman una rejilla uniforme sin estructura de grupos: la silueta siempre elige K = 4 (los cuatro cuadrantes), una partición geométrica que nada tiene que ver con la lesión.
""")

md(r"""
## 3. Construcción de la máscara de la lesión

K-medias entrega grupos pero no dice cuál es la lesión. Para cada grupo se calculan características que **no usan la máscara de referencia**:

- **Luminancia media** $L = 0.299R + 0.587G + 0.114B$: las lesiones pigmentadas son más oscuras que la piel.
- **Fracción en el borde**: porcentaje de los píxeles del grupo que caen en una franja del 5 % junto al borde de la imagen. El dermatoscopio produce **viñeteado** (esquinas negras) que es oscuro pero no es lesión.
- **Tamaño** (fracción de la imagen) y **distancia del centroide espacial al centro**, como información descriptiva.

Se comparan dos criterios:

**Criterio A – grupo más oscuro.** La lesión es el grupo de menor luminancia media. Es el criterio más simple posible y sirve de línea base.

**Criterio B – grupos oscuros fuera del borde + limpieza.**
1. Se marcan como lesión todos los grupos cuya luminancia está por debajo del punto medio entre el grupo más oscuro y el más claro: $L_k < (L_{min}+L_{max})/2$. Esto permite que una lesión con dos tonos (centro oscuro y periferia café) quede formada por varios grupos, lo que ocurre cuando K > 2.
2. Se descartan los grupos con más del 30 % de sus píxeles en la franja de borde (viñeteado, sombras de las esquinas). Si se descartaran todos, se toma el grupo oscuro con menor presencia en el borde.
3. Se rellenan los huecos (`binary_fill_holes`) y se conserva solo la **componente conexa más grande**: la lesión es una región compacta y única, mientras que pelos, poros o manchas sueltas generan fragmentos pequeños.
""")
code(r"""
PESOS_LUM = np.array([0.299, 0.587, 0.114])
FRANJA_BORDE = 0.05
MAX_FRAC_BORDE = 0.30


def caracteristicas_grupos(img, etiquetas):
    h, w, _ = img.shape
    rgb = img.reshape(-1, 3) / 255.0
    filas, cols = np.mgrid[0:h, 0:w]
    filas, cols = filas.ravel() / (h - 1), cols.ravel() / (w - 1)
    borde = (cols < FRANJA_BORDE) | (cols > 1 - FRANJA_BORDE) | (filas < FRANJA_BORDE) | (filas > 1 - FRANJA_BORDE)
    filas_out = []
    for k in np.unique(etiquetas):
        sel = etiquetas == k
        filas_out.append({"grupo": k,
                          "luminancia": rgb[sel].mean(0) @ PESOS_LUM,
                          "tamaño": sel.mean(),
                          "frac_borde": borde[sel].mean(),
                          "dist_centro": np.hypot(cols[sel].mean() - 0.5, filas[sel].mean() - 0.5)})
    return pd.DataFrame(filas_out).set_index("grupo")


def mascara_criterio_a(img, etiquetas):
    car = caracteristicas_grupos(img, etiquetas)
    return (etiquetas == car["luminancia"].idxmin()).reshape(img.shape[:2]).astype(np.uint8)


def mascara_criterio_b(img, etiquetas):
    car = caracteristicas_grupos(img, etiquetas)
    umbral = (car["luminancia"].min() + car["luminancia"].max()) / 2
    oscuros = car[car["luminancia"] < umbral]
    lesion = oscuros[oscuros["frac_borde"] <= MAX_FRAC_BORDE].index
    if len(lesion) == 0:
        lesion = [oscuros["frac_borde"].idxmin()]
    m = np.isin(etiquetas, lesion).reshape(img.shape[:2])
    m = ndi.binary_fill_holes(m)
    comp, n = ndi.label(m)
    if n > 1:
        tamaños = ndi.sum(m, comp, range(1, n + 1))
        m = comp == (np.argmax(tamaños) + 1)
    return m.astype(np.uint8)


CRITERIOS = {"A: más oscuro": mascara_criterio_a, "B: oscuros sin borde + limpieza": mascara_criterio_b}
""")
md(r"""
Ejemplo del cálculo de las características de grupo en una imagen con viñeteado fuerte (ISIC_0000133, esquinas negras) con λ/β = 0.75 y el K elegido por silueta. El grupo más oscuro es el de las esquinas, con casi todos sus píxeles en la franja de borde: el criterio A lo toma como lesión (Dice = 0) y el criterio B lo descarta.
""")
code(r"""
ej_img, ej_msk = datos_aj["ISIC_0000133"]
ej_k = k_por_silueta(GRUPOS[("ISIC_0000133", "λ/β=0.75")])
ej_lab = GRUPOS[("ISIC_0000133", "λ/β=0.75")][ej_k][0]
display(caracteristicas_grupos(ej_img, ej_lab))
fig, axes = plt.subplots(1, 4, figsize=(15, 3.4))
axes[0].imshow(ej_img); axes[0].set_title("original")
axes[1].imshow(ej_lab.reshape(ej_msk.shape), cmap="tab10"); axes[1].set_title(f"grupos (K={ej_k})")
for ax, (nom, f) in zip(axes[2:], CRITERIOS.items()):
    m = f(ej_img, ej_lab)
    ax.imshow(m, cmap="gray"); ax.contour(ej_msk, levels=[0.5], colors="lime")
    ax.set_title(f"{nom}\nDice={f1_score(ej_msk.ravel(), m.ravel()):.2f}", fontsize=9)
for ax in axes: ax.axis("off")
plt.tight_layout(); plt.show()
""")

md(r"""
## 4. Ajuste del método (solo imágenes de ajuste)

### 4.1 Métricas
- **Dice** entre la máscara estimada y la de referencia: `f1_score` sobre las máscaras aplanadas con la lesión como clase positiva. Es el criterio principal.
- **V-measure** entre las etiquetas de los grupos (K valores) y la máscara de referencia (2 valores). Mide qué tan bien la *agrupación* respeta la frontera lesión/piel, independientemente de qué grupos se elijan como lesión. Es información complementaria.

Para cada imagen y configuración se usa el K elegido por la silueta. Adicionalmente se calcula el Dice para **todos** los K para el análisis de la sección 4.4 (estos valores no se usan para elegir K).
""")
code(r"""
def dice(ref, est):
    return f1_score(ref.ravel(), est.ravel(), zero_division=0)


filas = []
for (i, c), d in GRUPOS.items():
    img, msk = datos_aj[i]
    k_opt = k_por_silueta(d)
    for k, (lab, s) in d.items():
        fila = {"imagen": i, "config": c, "K": k, "silueta": s, "elegido": k == k_opt,
                "v_measure": v_measure_score(msk.ravel(), lab)}
        for nom, f in CRITERIOS.items():
            fila[nom] = dice(msk, f(img, lab))
        filas.append(fila)
res_todos = pd.DataFrame(filas)
res = res_todos[res_todos["elegido"]].drop(columns="elegido").reset_index(drop=True)
res.head()
""")
code(r"""
largo = res.melt(id_vars=["imagen", "config", "K", "silueta", "v_measure"], value_vars=list(CRITERIOS),
                 var_name="criterio", value_name="dice")
tabla_ajuste = (largo.groupby(["config", "criterio"])
                     .agg(dice_prom=("dice", "mean"), dice_std=("dice", "std"), dice_min=("dice", "min"),
                          img_dice_menor_0_5=("dice", lambda s: int((s < 0.5).sum())),
                          v_measure_prom=("v_measure", "mean"), silueta_prom=("silueta", "mean"),
                          K_prom=("K", "mean"))
                     .reset_index().sort_values("dice_prom", ascending=False).reset_index(drop=True))
tabla_ajuste
""")
code(r"""
fig, axes = plt.subplots(1, 2, figsize=(15, 4.5), gridspec_kw={"width_ratios": [1.3, 1]})
piv = largo.pivot_table(index="config", columns="criterio", values="dice").reindex(ORDEN_CFG)
piv.plot(kind="bar", ax=axes[0], rot=30, color=["#9ecae1", "#3182bd"])
axes[0].set_title("Dice promedio en ajuste por configuración y criterio"); axes[0].set_ylabel("Dice promedio")
axes[0].set_ylim(0, 1)
vm = res.groupby("config")["v_measure"].mean().reindex(ORDEN_CFG)
vm.plot(kind="bar", ax=axes[1], rot=30, color="#756bb1")
axes[1].set_title("V-measure promedio en ajuste (K por silueta)"); axes[1].set_ylim(0, 1)
plt.tight_layout(); plt.show()
""")
code(r"""
fig, axes = plt.subplots(1, 2, figsize=(17, 6))
for ax, crit in zip(axes, CRITERIOS):
    hm = res.pivot(index="imagen", columns="config", values=crit)[ORDEN_CFG]
    sns.heatmap(hm, annot=True, fmt=".2f", cmap="RdYlGn", vmin=0, vmax=1, ax=ax, cbar=False, annot_kws={"size": 8})
    ax.set_title(f"Dice por imagen – criterio {crit}"); ax.set_xlabel("")
plt.tight_layout(); plt.show()
""")

md(r"""
### 4.2 Actividad de verificación con IAG (antes de elegir la configuración final)
Antes de seleccionar la configuración final se consultó a una herramienta de IAG (ver la conversación completa y el análisis en la sección 8). El prompt **no adjunta imágenes ni menciona el nombre del conjunto de datos**; describe las imágenes. La recomendación recibida se traduce a los parámetros de nuestro método y se evalúa en las 15 imágenes de ajuste exactamente con el mismo protocolo.
""")
code(r"""
# Recomendación de la IAG (ver sección 8). Se evalúa con K fijo, tal como la IAG lo sugirió,
# y también con K elegido por silueta, para separar el efecto de cada recomendación.
REC_IAG = __REC_IAG__


def criterio_iag(img, etiquetas):
    return __CRIT_IAG__


filas_iag = []
for i, (img, msk) in datos_aj.items():
    d = agrupar_todos_k(img, REC_IAG["beta"], REC_IAG["lam"])
    for modo, k in [("K fijo IAG", REC_IAG["K"]), ("K por silueta", k_por_silueta(d))]:
        lab = d[k][0]
        filas_iag.append({"imagen": i, "modo": modo, "K": k,
                          "dice criterio IAG": dice(msk, criterio_iag(img, lab)),
                          "dice criterio B": dice(msk, mascara_criterio_b(img, lab)),
                          "v_measure": v_measure_score(msk.ravel(), lab)})
res_iag = pd.DataFrame(filas_iag)
display(res_iag.groupby("modo")[["K", "dice criterio IAG", "dice criterio B", "v_measure"]].mean())
res_iag.pivot(index="imagen", columns="modo", values="dice criterio IAG").round(3).T
""")
md(T("iag_resultado"))

md(r"""
### 4.3 Selección de la configuración final
Se elige la combinación (configuración, criterio) con **mayor Dice promedio en ajuste**. Como desempate e información complementaria se revisan la desviación estándar, el peor caso, el número de imágenes con Dice < 0.5 y el V-measure.
""")
code(r"""
mejor = tabla_ajuste.iloc[0]
segunda = tabla_ajuste[tabla_ajuste["config"] != mejor["config"]].iloc[0]
cfg_final = next(c for c in CONFIGS if c["nombre"] == mejor["config"])
CONFIG_FINAL = dict(beta=cfg_final["beta"], lam=cfg_final["lam"], criterio=mejor["criterio"])
TOP2 = [mejor["config"], segunda["config"]]
print("Configuración final:", CONFIG_FINAL)
print(f"Dice promedio en ajuste = {mejor['dice_prom']:.3f} ± {mejor['dice_std']:.3f}  |  "
      f"V-measure promedio = {mejor['v_measure_prom']:.3f}")
print("Dos configuraciones con mayor Dice promedio:", TOP2)
""")
md(T("justificacion_final"))

md(r"""
### 4.4 Visualización de los grupos: las dos mejores configuraciones vs. solo color y solo posición
Cada grupo se pinta con el color promedio de sus píxeles; el contorno verde es la máscara de referencia y el número es el Dice del criterio final con el K elegido por silueta. Además de las configuraciones exigidas (las dos mejores, solo color y solo posición) se agrega λ/β = 2 para ilustrar qué pasa cuando la posición domina. Se eligieron cinco imágenes representativas: un éxito (ISIC_0000137), la lesión de bajo contraste (ISIC_0000094), la lesión diminuta (ISIC_0000114) y los dos peores casos de la configuración final (ISIC_0000116 e ISIC_0000150).
""")
code(r"""
def pintar_grupos(img, etiquetas):
    rgb = img.reshape(-1, 3).astype(float)
    out = np.zeros_like(rgb)
    for k in np.unique(etiquetas):
        out[etiquetas == k] = rgb[etiquetas == k].mean(0)
    return out.reshape(img.shape).astype(np.uint8)


crit_final = CRITERIOS[CONFIG_FINAL["criterio"]]
cfgs_vis = list(dict.fromkeys(TOP2 + ["solo color", "λ/β=2", "solo posición"]))
imgs_vis = ["ISIC_0000137", "ISIC_0000094", "ISIC_0000114", "ISIC_0000116", "ISIC_0000150"]

fig, axes = plt.subplots(len(imgs_vis), 1 + 2 * len(cfgs_vis), figsize=(2.3 * (1 + 2 * len(cfgs_vis)), 2.6 * len(imgs_vis)))
for r, i in enumerate(imgs_vis):
    img, msk = datos_aj[i]
    axes[r, 0].imshow(img); axes[r, 0].set_ylabel(i, fontsize=9)
    axes[r, 0].set_title("original" if r == 0 else "", fontsize=9)
    for j, c in enumerate(cfgs_vis):
        d = GRUPOS[(i, c)]; k = k_por_silueta(d); lab = d[k][0]
        m = crit_final(img, lab)
        a1, a2 = axes[r, 1 + 2 * j], axes[r, 2 + 2 * j]
        a1.imshow(pintar_grupos(img, lab)); a1.set_title(f"{c}\ngrupos K={k}", fontsize=9)
        a2.imshow(m, cmap="gray"); a2.contour(msk, levels=[0.5], colors="lime", linewidths=1)
        a2.set_title(f"máscara  Dice={dice(msk, m):.2f}", fontsize=9)
for ax in axes.ravel(): ax.set_xticks([]); ax.set_yticks([])
plt.tight_layout(); plt.show()
""")
md(T("visualizacion"))

md(r"""
### 4.5 Relación entre K, silueta y Dice
Para la configuración final se compara, para cada K, la silueta promedio y el Dice promedio (calculado para *todos* los K solo con fines de análisis), y el Dice que se habría obtenido con el K "oráculo" que maximiza el Dice de cada imagen (que no es utilizable en la práctica porque requiere la máscara).
""")
code(r"""
sub = res_todos[res_todos["config"] == TOP2[0]]
crit = CONFIG_FINAL["criterio"]
porK = sub.groupby("K")[["silueta", crit, "v_measure"]].mean()
fig, axes = plt.subplots(1, 2, figsize=(14, 4.2))
porK.plot(ax=axes[0], marker="o"); axes[0].set_title(f"{TOP2[0]}: promedio por K (15 imágenes)")
axes[0].set_ylim(0, 1); axes[0].legend(["silueta", "Dice (criterio final)", "V-measure"])
axes[1].scatter(res_todos["silueta"], res_todos[crit], s=8, alpha=.35, c=res_todos["K"], cmap="viridis")
axes[1].set_xlabel("silueta"); axes[1].set_ylabel("Dice"); axes[1].set_title("Todas las imágenes, configuraciones y K")
plt.tight_layout(); plt.show()

oraculo = sub.groupby("imagen")[crit].max()
elegido = sub[sub["elegido"]].set_index("imagen")[crit]
print(f"Correlación de Spearman silueta–Dice (todas las combinaciones): "
      f"{res_todos[['silueta', crit]].corr('spearman').iloc[0, 1]:.3f}")
print(f"Dice promedio con K por silueta: {elegido.mean():.3f} | con K oráculo: {oraculo.mean():.3f}")
pd.DataFrame({"K silueta": sub[sub['elegido']].set_index('imagen')['K'],
              "Dice K silueta": elegido,
              "K oráculo": sub.loc[sub.groupby('imagen')[crit].idxmax()].set_index('imagen')['K'],
              "Dice K oráculo": oraculo}).round(3)
""")
md(T("k_silueta"))

md(r"""
### 4.6 Casos de fallo en ajuste (configuración final)
""")
code(r"""
fallo = res[res["config"] == TOP2[0]].set_index("imagen")[[crit, "K", "silueta", "v_measure"]].sort_values(crit)
fallo.head(5)
""")
md(T("fallos_ajuste"))

md(r"""
## 5. Evaluación en las imágenes de prueba
Se cargan por primera vez las cinco imágenes de prueba y se aplica `CONFIG_FINAL` **sin ninguna modificación**: mismos β, λ, rango de K, muestra de silueta (tamaño y semilla), criterio de máscara y parámetros del criterio.
""")
code(r"""
datos_pr = {i: cargar(i) for i in PRUEBA}
filas_pr, vis_pr = [], {}
for i, (img, msk) in datos_pr.items():
    d = agrupar_todos_k(img, CONFIG_FINAL["beta"], CONFIG_FINAL["lam"])
    k = k_por_silueta(d); lab, s = d[k]
    m = CRITERIOS[CONFIG_FINAL["criterio"]](img, lab)
    vis_pr[i] = (lab, m)
    filas_pr.append({"imagen": i, "K": k, "silueta": s, "Dice": dice(msk, m),
                     "V-measure": v_measure_score(msk.ravel(), lab),
                     "precisión": precision_score(msk.ravel(), m.ravel(), zero_division=0),
                     "recall": recall_score(msk.ravel(), m.ravel(), zero_division=0),
                     "% lesión ref": 100 * msk.mean(), "% lesión est": 100 * m.mean()})
tabla_prueba = pd.DataFrame(filas_pr).set_index("imagen")
tabla_prueba.loc["PROMEDIO"] = tabla_prueba.mean()
tabla_prueba
""")
code(r"""
fig, axes = plt.subplots(len(PRUEBA), 4, figsize=(13, 2.9 * len(PRUEBA)))
for r, i in enumerate(PRUEBA):
    img, msk = datos_pr[i]; lab, m = vis_pr[i]
    paneles = [(img, "original"), (pintar_grupos(img, lab), f"grupos K={tabla_prueba.loc[i, 'K']:.0f}"),
               (m, f"máscara estimada  Dice={tabla_prueba.loc[i, 'Dice']:.2f}"), (msk, "máscara de referencia")]
    for ax, (p, t) in zip(axes[r], paneles):
        ax.imshow(p, cmap="gray" if p.ndim == 2 else None); ax.set_title(t, fontsize=9)
        ax.set_xticks([]); ax.set_yticks([])
    axes[r, 0].set_ylabel(i, fontsize=9)
    axes[r, 2].contour(msk, levels=[0.5], colors="lime", linewidths=1)
plt.tight_layout(); plt.show()
""")
code(r"""
aj_final = res[res["config"] == TOP2[0]][CONFIG_FINAL["criterio"]]
comp = pd.DataFrame({"ajuste (15)": [aj_final.mean(), aj_final.std(), aj_final.median(), aj_final.min()],
                     "prueba (5)": [tabla_prueba.loc[PRUEBA, "Dice"].mean(), tabla_prueba.loc[PRUEBA, "Dice"].std(),
                                    tabla_prueba.loc[PRUEBA, "Dice"].median(), tabla_prueba.loc[PRUEBA, "Dice"].min()]},
                    index=["Dice promedio", "desv. estándar", "mediana", "mínimo"])
comp
""")
md(T("prueba"))

md(r"""
## 6. Video
El video (máximo 3 minutos, dirigido a DermAlpes y a un público no especializado) se entrega por Bloque Neón. Su guion sigue esta estructura: (1) el problema: delimitar la lesión para que el dermatólogo la mida, sin diagnosticar; (2) cómo funciona: cada píxel se describe por su color y su posición, K-medias agrupa píxeles parecidos y una regla elige los grupos oscuros que no están en el borde; (3) resultados de prueba con las imágenes y el Dice; (4) casos de fallo; (5) precauciones de uso: revisión humana obligatoria y validación en la población real de DermAlpes.

**Enlace al video:** *(agregar enlace)*
""")

md("## 7. Análisis de resultados")
md("### 7.1 ¿Qué efecto tuvo incluir la posición de los píxeles?\n\n" + T("p1"))
md("### 7.2 Relación entre K, la silueta y el Dice\n\n" + T("p2"))
md("### 7.3 Comparación entre ajuste y prueba\n\n" + T("p3"))
md("### 7.4 Dos limitaciones del modelo\n\n" + T("p4"))
md("### 7.5 Falsos positivos, falsos negativos, sesgos y generalización en DermAlpes\n\n" + T("p5"))

md("## 8. Uso de herramientas de IA generativa\n\n" + T("iag_seccion"))

md(r"""
## 9. Bonos

### Bono A. Visualización del espacio de representación con PCA
Se toma una imagen de ajuste y una muestra de 3 000 píxeles (semilla 42) representados con la configuración final $[\beta R, \beta G, \beta B, \lambda x, \lambda y]$. Se proyectan a 2 dimensiones con PCA y se colorean por grupo de K-medias y por la máscara de referencia.
""")
code(r"""
img_b, msk_b = datos_aj["ISIC_0000089"]
pipe_b = crear_pipeline(CONFIG_FINAL["beta"], CONFIG_FINAL["lam"])
d_b = agrupar_todos_k(img_b, CONFIG_FINAL["beta"], CONFIG_FINAL["lam"])
k_b = k_por_silueta(d_b); lab_b = d_b[k_b][0]
Xb = pipe_b[:-1].transform(img_b)
idx_b = np.random.RandomState(SEED).choice(len(Xb), 3000, replace=False)
pca = PCA(n_components=2, random_state=SEED).fit(Xb)
Z = pca.transform(Xb[idx_b])

fig, axes = plt.subplots(1, 3, figsize=(17, 4.8))
axes[0].imshow(img_b); axes[0].contour(msk_b, levels=[0.5], colors="lime"); axes[0].axis("off")
axes[0].set_title("ISIC_0000089")
sc = axes[1].scatter(Z[:, 0], Z[:, 1], c=lab_b[idx_b], cmap="tab10", s=6)
axes[1].legend(*sc.legend_elements(), title="grupo", fontsize=8); axes[1].set_title(f"PCA coloreado por grupo (K={k_b})")
sc = axes[2].scatter(Z[:, 0], Z[:, 1], c=msk_b.ravel()[idx_b], cmap="coolwarm", s=6)
axes[2].legend(*sc.legend_elements(), title="referencia", fontsize=8); axes[2].set_title("PCA coloreado por máscara de referencia")
for ax in axes[1:]: ax.set_xlabel("PC1"); ax.set_ylabel("PC2")
plt.tight_layout(); plt.show()
print("varianza explicada:", np.round(pca.explained_variance_ratio_, 3),
      "| cargas PC1 [R,G,B,x,y]:", np.round(pca.components_[0], 2), "| PC2:", np.round(pca.components_[1], 2))
""")
md(T("bonoA"))

md(r"""
### Bono B. Comparación con mean shift
**Cómo funciona.** Mean shift estima la densidad de los puntos con un núcleo (kernel) de radio *h* (el **ancho de banda**) y desplaza iterativamente cada punto semilla hacia la media de los puntos dentro de su ventana, es decir, sube por el gradiente de la densidad hasta llegar a una moda. Los puntos que convergen a la misma moda forman un grupo. **No requiere fijar K**: el número de grupos es el número de modas de la densidad, que queda determinado por el ancho de banda. Un *h* pequeño detecta muchas modas (muchos grupos pequeños); uno grande suaviza la densidad y fusiona modas (pocos grupos). Aquí *h* se estima con `estimate_bandwidth` (cuantil de distancias entre vecinos) y se usa `bin_seeding=True` para reducir las semillas. Su costo es mucho mayor que el de K-medias, por eso se usa una resolución de 64 px de ancho.

Se aplica a una imagen de ajuste con la misma representación de la configuración final y se construye la máscara con el mismo criterio final.
""")
code(r"""
id_ms = "ISIC_0000137"
img_ms, msk_ms = cargar(id_ms, ancho=64)
X_ms = crear_pipeline(CONFIG_FINAL["beta"], CONFIG_FINAL["lam"])[:-1].transform(img_ms)
filas_ms = []
for q in [0.1, 0.2, 0.3]:
    bw = estimate_bandwidth(X_ms, quantile=q, n_samples=1000, random_state=SEED)
    t0 = time.time(); ms = MeanShift(bandwidth=bw, bin_seeding=True).fit(X_ms); t_ms = time.time() - t0
    m = CRITERIOS[CONFIG_FINAL["criterio"]](img_ms, ms.labels_)
    filas_ms.append({"método": f"mean shift (cuantil {q})", "ancho de banda": bw, "K": len(np.unique(ms.labels_)),
                     "Dice": dice(msk_ms, m), "tiempo (s)": t_ms, "_lab": ms.labels_, "_m": m})
t0 = time.time(); d_km = agrupar_todos_k(img_ms, CONFIG_FINAL["beta"], CONFIG_FINAL["lam"]); t_km = time.time() - t0
k_km = k_por_silueta(d_km); m_km = CRITERIOS[CONFIG_FINAL["criterio"]](img_ms, d_km[k_km][0])
filas_ms.append({"método": "K-medias (K por silueta, 7 ajustes)", "ancho de banda": np.nan, "K": k_km,
                 "Dice": dice(msk_ms, m_km), "tiempo (s)": t_km, "_lab": d_km[k_km][0], "_m": m_km})
tabla_ms = pd.DataFrame(filas_ms)
display(tabla_ms.drop(columns=["_lab", "_m"]))

fig, axes = plt.subplots(2, len(filas_ms) + 1, figsize=(4 * (len(filas_ms) + 1), 6))
axes[0, 0].imshow(img_ms); axes[0, 0].set_title(id_ms); axes[1, 0].imshow(msk_ms, cmap="gray"); axes[1, 0].set_title("referencia")
for j, f in enumerate(filas_ms, start=1):
    axes[0, j].imshow(pintar_grupos(img_ms, f["_lab"])); axes[0, j].set_title(f"{f['método']}\nK={f['K']}", fontsize=9)
    axes[1, j].imshow(f["_m"], cmap="gray"); axes[1, j].contour(msk_ms, levels=[0.5], colors="lime")
    axes[1, j].set_title(f"Dice={f['Dice']:.2f}  t={f['tiempo (s)']:.1f}s", fontsize=9)
for ax in axes.ravel(): ax.axis("off")
plt.tight_layout(); plt.show()
""")
md(T("bonoB"))

nb = nbf.v4.new_notebook(cells=cells)
nb.metadata = {"kernelspec": {"display_name": "Python (ML Labs)", "language": "python", "name": "ml-labs"},
               "language_info": {"name": "python"}}
src = nbf.writes(nb)
rec = txt.get("REC_IAG", 'dict(beta=1.0, lam=0.3, K=3)  # PROVISIONAL: reemplazar por la recomendación real')
crit = txt.get("CRIT_IAG", "mascara_criterio_a(img, etiquetas)  # PROVISIONAL")
src = src.replace("__REC_IAG__", json.dumps(rec)[1:-1]).replace("__CRIT_IAG__", json.dumps(crit)[1:-1])
open(OUT, "w").write(src)
print("ok", len(cells), "celdas")
