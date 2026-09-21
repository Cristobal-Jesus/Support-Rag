# Instrucciones del proyecto

El usuario ha pedido seguir la Google Python Style Guide:
https://google.github.io/styleguide/pyguide.html

- Aplicar la guía al código nuevo y a las modificaciones del código existente.
- Usar cuatro espacios y un máximo de 80 caracteres por línea, salvo las
  excepciones explícitas de la guía.
- Importar módulos con rutas absolutas; usar nombres cualificados al acceder a
  sus clases y funciones. Mantener separados y ordenados los grupos de imports.
- Añadir anotaciones de tipos y docstrings de estilo Google a las interfaces
  públicas: Args, Returns, Raises y Attributes cuando aporten información.
- Mantener nombres de código en inglés y explicaciones y comentarios en español.
- Evitar estado global mutable y documentar el motivo de cualquier supresión
  puntual de Pylint.
- Mantener la guía didáctica sincronizada con los cambios de código.
- Antes de entregar cambios, ejecutar desde la raíz del repositorio:
  `python -m black --check support_rag tests`,
  `python -m pylint support_rag tests` y
  `python -m unittest discover -s tests -v`.
- El alcance sigue siendo un prototipo de RAG multiagente construido por etapas.
  Describir con claridad qué etapas están implementadas y cuáles están pendientes.
