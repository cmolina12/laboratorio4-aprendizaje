# Guion del video (≤ 3 min) – DermAlpes

Público: DermAlpes y personas no especializadas. Mostrar en pantalla las figuras del notebook indicadas.

**1. El problema (0:00–0:30)**
"En DermAlpes, los centros de salud envían fotos de lesiones de piel a dermatólogos en otras ciudades. Queremos una herramienta que dibuje automáticamente el contorno de la lesión para que el especialista pueda medir su tamaño y forma más rápido. La herramienta **no diagnostica**: solo delimita la zona. Y no tenemos fotos etiquetadas de nuestros pacientes, así que probamos un método que no necesita entrenamiento con ejemplos."
*Pantalla: galería de imágenes con el contorno verde (sección 1).*

**2. Cómo funciona (0:30–1:15)**
"Una foto está hecha de miles de puntos de color, los píxeles. A cada píxel le anotamos su color y su posición en la foto. Un algoritmo llamado K-medias reúne en grupos los píxeles que se parecen, como si separáramos un montón de cuentas por color. Probamos cuánto peso darle a la posición frente al color: lo que mejor funcionó fue darle casi todo el peso al color y muy poco a la posición. El número de grupos lo elige el propio método con una medida de qué tan bien separados quedan. Luego una regla decide cuáles grupos son la lesión: los más oscuros que no estén pegados al borde de la foto —porque el dermatoscopio oscurece las esquinas—; rellenamos huecos y nos quedamos con la mancha más grande."
*Pantalla: figura de grupos (sección 4.4) y ejemplo del viñeteado (sección 3).*

**3. Resultados de prueba (1:15–1:50)**
"Ajustamos el método con 15 fotos y lo probamos, sin cambiar nada, con 5 fotos que no había visto. Medimos la coincidencia con el contorno dibujado por dermatólogos con un puntaje de 0 a 1: obtuvimos 0,88 en promedio, casi igual que en las fotos de ajuste (0,89). Cuando el método marca algo como lesión, casi siempre acierta; pero suele quedarse corto en el borde."
*Pantalla: figura y tabla de prueba (sección 5).*

**4. Cuándo falla (1:50–2:25)**
"Falla sobre todo con lesiones claras, rosadas o con bordes difusos, como esta (ISIC_0000110): solo encuentra el centro y la lesión parece más pequeña de lo que es. También puede confundirse con enrojecimiento de la piel, pelos gruesos o lesiones con partes separadas."
*Pantalla: ISIC_0000110, ISIC_0000116, ISIC_0000123.*

**5. Precauciones (2:25–3:00)**
"Todas las fotos que usamos son de piel clara y de lesiones pigmentadas. Como el método se basa en que la lesión es más oscura que la piel, podría funcionar mucho peor en pieles más oscuras, en lesiones poco pigmentadas o con otras cámaras e iluminación. Antes de usarla, DermAlpes debe probarla con fotos de sus propios pacientes, revisando los resultados por tipo de piel. Y siempre el contorno debe ser una sugerencia que el dermatólogo revisa y corrige, nunca una medida final."
