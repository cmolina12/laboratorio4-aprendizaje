# Prompt para la actividad de verificación con IAG

Copiar en la herramienta de IAG (sin adjuntar imágenes y sin mencionar el nombre del conjunto de datos). Guardar el historial completo (capturas o enlace) para anexarlo al notebook.

---

Estoy segmentando imágenes de dermatoscopia sin supervisión usando K-medias. Las imágenes son fotografías RGB tomadas con dermatoscopio de lesiones pigmentadas de piel (lunares y lesiones melanocíticas), en su mayoría sobre piel clara. La lesión suele ser una mancha café o café oscura, a veces con zonas negras, rojizas o grisáceas, y generalmente está cerca del centro, aunque su tamaño varía mucho: desde un 3 % hasta casi un 40 % de la imagen. Algunas imágenes tienen esquinas negras por el viñeteado del dermatoscopio, pelos, burbujas de gel, pecas alrededor o zonas enrojecidas. Reduzco cada imagen a 128 px de ancho.

Cada píxel lo represento con el vector [β·R, β·G, β·B, λ·x, λ·y], donde R, G, B están normalizados a [0, 1] y las coordenadas x, y también están normalizadas a [0, 1]. β controla el peso del color y λ el de la posición.

1. ¿Qué valores de β y λ (o qué razón λ/β) me recomiendas?
2. ¿Qué valor de K me recomiendas?
3. Después de agrupar, ¿qué criterio automático me recomiendas para decidir qué grupos corresponden a la lesión y construir una máscara binaria? Dámelo de forma concreta, que pueda implementar en Python.

---

Interacción de seguimiento sugerida (si la respuesta da rangos en vez de valores): "Si tuvieras que darme un único valor de β, λ y K para todas las imágenes, ¿cuáles serían?"

Después de la consulta: pasar la respuesta para actualizar `REC_IAG` y `criterio_iag` en la sección 4.2 del notebook y completar la sección 8.
