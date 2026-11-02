# Guion del video (≤ 3 min) – DermAlpes

Público: DermAlpes y personas no especializadas. Se graba recorriendo el notebook (`Laboratorio4.html` o el `.ipynb`). Al pasar por el código se muestra **solo la parte indicada**, unos segundos, y se explica en palabras sencillas: lo importante es la idea, no la sintaxis. Ensayar con cronómetro: cada parte dura ~1:30 (~200 palabras habladas).

---

## Parte 1 – Camilo (0:00–1:30): el problema y cómo se obtiene la máscara

**1. El problema (0:00–0:25)**
*Pantalla: título del notebook y luego la galería de la sección 1.1 (fotos con el contorno verde).*
"Hola, somos Camilo Molina y Natalia Erazo. En DermAlpes, los centros de salud envían fotos de lesiones de piel a dermatólogos en otras ciudades. DermAlpes quiere una herramienta que dibuje sola el contorno de la lesión, como este en verde, para que el especialista mida su tamaño y forma más rápido. **No diagnostica**: solo delimita. Como DermAlpes no tiene fotos etiquetadas de sus pacientes, usamos un método que no necesita ejemplos para aprender."

**2. Cada píxel como un dato (0:25–0:50)**
*Pantalla: sección 1.2, celda con `PixelesRGBXY`, `PesosColorPosicion` y `crear_pipeline`. Resaltar en `PesosColorPosicion` la línea `return X * np.array([self.beta] * 3 + [self.lam] * 2)`, que aplica los pesos y deja el vector [β·R, β·G, β·B, λ·x, λ·y].*
"Una foto son miles de puntos de color, los píxeles. En este código, cada píxel queda como cinco números: su color en rojo, verde y azul, y su posición. Los pesos beta y lambda deciden qué importa más, el color o la posición. Probamos diez combinaciones."
*Pantalla: celda `CONFIGS` (sección 2.1), un segundo.*

**3. Agrupar con K-medias y elegir K (0:50–1:10)**
*Pantalla: sección 2.2, celdas `agrupar_todos_k` y `k_por_silueta`; luego la figura de grupos de la sección 4.4.*
"Luego K-medias reúne los píxeles parecidos en grupos, como separar cuentas por color. ¿Cuántos grupos? Probamos de 2 a 8, y este código escoge el número que separa mejor los grupos, según una medida llamada silueta. Aquí se ve el resultado: cada color es un grupo."

**4. De los grupos a la máscara (1:10–1:30)**
*Pantalla: sección 3, celdas `caracteristicas_grupos` y `mascara_criterio_b`; luego la figura del viñeteado.*
"Falta decidir qué grupos son la lesión. Esta regla toma los grupos más oscuros que **no** estén pegados al borde, porque el dermatoscopio oscurece las esquinas, como se ve aquí. Después rellena los huecos y se queda con la mancha más grande. Natalia les cuenta qué tan bien funcionó."

---

## Parte 2 – Natalia (1:30–3:00): resultados, fallos y precauciones

**5. Cómo elegimos la configuración (1:30–1:50)**
*Pantalla: sección 4.1, tabla/mapa de calor de Dice por combinación; luego la celda `CONFIG_FINAL` (sección 4.3).*
"Con 15 fotos comparamos cada combinación con el contorno que dibujaron dermatólogos, con un puntaje de 0 a 1. Lo mejor fue darle casi todo el peso al color: la posición pesa solo una cuarta parte de lo que pesa el color."

**6. Resultados en prueba (1:50–2:20)**
*Pantalla: sección 5, celda `tabla_prueba` con la tabla y la figura original / máscara estimada / referencia.*
"Luego probamos el método, sin cambiarle nada, en 5 fotos que nunca había visto. Obtuvimos 0,88 en promedio, casi igual que en ajuste, 0,89. Son solo 5 fotos, así que es una estimación aproximada. Cuando marca algo como lesión casi siempre acierta, con una precisión de 0,97, pero suele quedarse un poco corto en el borde."

**7. Cuándo falla (2:20–2:40)**
*Pantalla: figura de prueba (sección 5): ISIC_0000110 y luego ISIC_0000123 (enrojecimiento). Después, figura de la sección 4.4: ISIC_0000150 (partes separadas).*
"Falla sobre todo con lesiones claras, rosadas o de bordes difusos, como esta: solo encuentra el centro y la lesión parece más pequeña de lo que es. También lo confunden el enrojecimiento de la piel, los pelos gruesos o las lesiones con partes separadas."

**8. Precauciones (2:40–3:00)**
*Pantalla: sección 7.5.*
"Ojo: todas las fotos eran de piel clara y lesiones pigmentadas. Como el método busca lo más oscuro, podría fallar en pieles más oscuras o con otras cámaras. DermAlpes debe probarlo antes con fotos de sus pacientes, por tipo de piel, y el contorno siempre debe ser una sugerencia que el dermatólogo revisa. Gracias."

---

**Consejos de grabación**
- Grabar cada parte por separado (por ejemplo, con Zoom o QuickTime compartiendo pantalla) y unirlas; o grabar en una sola llamada pasándose la pantalla en el minuto 1:30.
- Hacer zoom al navegador (Cmd +) para que el código y las tablas se lean.
- Si se pasan de 3:00, recortar primero las frases de transición y el tiempo en pantalla del código.
- Subir el video (YouTube no listado o Drive con acceso por enlace) y pegar el enlace en la sección 6 del notebook.
