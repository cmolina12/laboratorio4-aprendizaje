# Guion del video (≤ 3 min) – DermAlpes

Público: DermAlpes y personas no especializadas. Se graba recorriendo el notebook (`Laboratorio4.html` o el `.ipynb`). Al pasar por el código se muestra **solo la parte indicada**, unos segundos, y se explica en palabras sencillas: lo importante es la idea, no la sintaxis. Ensayar con cronómetro: cada parte dura ~1:30 (~200 palabras habladas).

---

## Parte 1 – Camilo (0:00–1:30): el problema y cómo se obtiene la máscara

**1. El problema (0:00–0:25)**
*Pantalla: título del notebook y luego la galería de la sección 1.1 (fotos con el contorno verde).*
"Hola, somos Camilo Molina y Natalia Erazo. En DermAlpes, los centros de salud envían fotos de lesiones de piel a dermatólogos en otras ciudades. Queremos una herramienta que dibuje sola el contorno de la lesión, este en verde, para que el especialista mida su tamaño y forma más rápido. **No diagnostica**: solo delimita. Y como no tenemos fotos etiquetadas de nuestros pacientes, usamos un método que no necesita ejemplos para aprender."

**2. Cada píxel como un dato (0:25–0:50)**
*Pantalla: sección 1.2, celda con `PixelesRGBXY`, `PesosColorPosicion` y `crear_pipeline`. Resaltar la línea donde se arma el vector [β·R, β·G, β·B, λ·x, λ·y].*
"Una foto son miles de puntos de color, los píxeles. En este código, a cada píxel le anotamos cinco números: su color en rojo, verde y azul, y su posición en la foto. Estos dos pesos, beta y lambda, deciden qué importa más, el color o la posición. Probamos diez combinaciones."
*Pantalla: celda `CONFIGS` (sección 2.1), un segundo.*

**3. Agrupar con K-medias y elegir K (0:50–1:10)**
*Pantalla: sección 2.2, celdas `agrupar_todos_k` y `k_por_silueta`; luego la figura de grupos de la sección 4.4.*
"Luego K-medias reúne los píxeles parecidos en grupos, como separar cuentas por color. ¿Cuántos grupos? Probamos de 2 a 8, y este código se queda con el número cuyos grupos quedan mejor separados, según una medida llamada silueta. Aquí se ve el resultado: cada color es un grupo."

**4. De los grupos a la máscara (1:10–1:30)**
*Pantalla: sección 3, celdas `caracteristicas_grupos` y `mascara_criterio_b`; luego la figura del viñeteado.*
"Falta decidir qué grupos son la lesión. Esta regla toma los grupos más oscuros que **no** estén pegados al borde de la foto, porque el dermatoscopio oscurece las esquinas, como se ve aquí. Después rellena los huecos y se queda con la mancha más grande. Esa es nuestra máscara. Natalia les cuenta qué tan bien funcionó."

---

## Parte 2 – Natalia (1:30–3:00): resultados, fallos y precauciones

**5. Cómo elegimos la configuración (1:30–1:50)**
*Pantalla: sección 4.1, tabla/mapa de calor de Dice por combinación; luego la celda `CONFIG_FINAL` (sección 4.3).*
"Con 15 fotos de ajuste comparamos cada combinación con el contorno que dibujaron dermatólogos, usando un puntaje de 0 a 1. Lo mejor fue darle casi todo el peso al color y muy poco a la posición: un cuarto. También le preguntamos a ChatGPT qué haría; su propuesta sirvió para comparar, pero fijaba el número de grupos, y el laboratorio exige elegirlo con la silueta."

**6. Resultados en prueba (1:50–2:20)**
*Pantalla: sección 5, celda `tabla_prueba` con la tabla y la figura original / máscara estimada / referencia.*
"Luego probamos el método, sin cambiarle nada, en 5 fotos que nunca había visto. Obtuvimos 0,88 en promedio, casi igual que en ajuste, 0,89: el método se sostiene. Cuando marca algo como lesión casi siempre acierta, con una precisión de 0,97, pero suele quedarse un poco corto en el borde."

**7. Cuándo falla (2:20–2:40)**
*Pantalla: en la figura de prueba, ISIC_0000110; luego sección 4.6, casos de fallo (ISIC_0000116, ISIC_0000123).*
"Falla sobre todo con lesiones claras, rosadas o de bordes difusos, como esta: solo encuentra el centro y la lesión parece más pequeña de lo que es. También lo confunden el enrojecimiento de la piel, los pelos gruesos o las lesiones con partes separadas."

**8. Precauciones (2:40–3:00)**
*Pantalla: sección 7.5.*
"Ojo: todas las fotos eran de piel clara y lesiones pigmentadas. Como el método busca lo más oscuro, podría fallar en pieles más oscuras o con otras cámaras. DermAlpes debe probarlo antes con fotos de sus pacientes, por tipo de piel, y el contorno siempre debe ser una sugerencia que el dermatólogo revisa. Gracias."

---

**Consejos de grabación**
- Grabar cada parte por separado (por ejemplo, con Zoom o QuickTime compartiendo pantalla) y unirlas; o grabar en una sola llamada pasándose la pantalla en el minuto 1:30.
- Hacer zoom al navegador (Cmd +) para que el código y las tablas se lean.
- Si se pasan de 3:00, recortar primero el paso 5 (la mención a ChatGPT) y las frases de transición.
- Subir el video (YouTube no listado o Drive con acceso por enlace) y pegar el enlace en la sección 6 del notebook.
