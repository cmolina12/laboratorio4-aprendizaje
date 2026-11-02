# laboratorio4-aprendizaje

Laboratorio 4 - Segmentación de imágenes con técnicas de agrupación (ISIS2611).

## Contenido

- `Laboratorio4.ipynb` / `Laboratorio4.html`: notebook principal con todo el desarrollo
  (pipeline de representación [βR, βG, βB, λx, λy], K-medias con selección de K por
  silueta, criterios de construcción de la máscara, ajuste con Dice y V-measure,
  evaluación en las imágenes de prueba, análisis de resultados y bonos A y B).
- `data/images`, `data/masks`: las 20 imágenes dermatoscópicas de ISIC 2016 (15 de ajuste
  y 5 de prueba) y sus máscaras de referencia. Las máscaras vienen de
  `ISBI2016_ISIC_Part1_Training_GroundTruth.zip` y las imágenes del ISIC Archive (CC-0).
- `enunciado/`: enunciado del laboratorio.
- `prompt_IAG.md`: prompt para la actividad de verificación con IAG.
- `guion_video.md`: guion del video (máximo 3 minutos).
- `scripts/build_notebook.py`: script que ensambla `Laboratorio4.ipynb` celda por celda
  (usado para poder versionar el contenido del notebook como texto).
- `scripts/analisis.py`: textos del análisis que el script anterior inserta en el notebook.
  Para regenerar el notebook desde cero:

  ```bash
  ../.venv/bin/python scripts/analisis.py scripts/analisis.json
  ../.venv/bin/python scripts/build_notebook.py Laboratorio4.ipynb scripts/analisis.json
  ../.venv/bin/python -m jupyter nbconvert --to notebook --execute --inplace Laboratorio4.ipynb
  ../.venv/bin/python -m jupyter nbconvert --to html Laboratorio4.ipynb
  ```
