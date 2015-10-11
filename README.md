# Segunda mano

Este script intenta simplificar la repetitiva tarea de buscar algo en segunda mano evitándote hacer las mismas búsquedas una y otra vez en varios portales y dándote la posibilidad de añadir algún filtro extra mediante expresiones regulares.

La idea original surgió cuando buscaba una bicicleta de segunda mano para moverme por Madrid ya que ejecutando run.sh cada hora (mediante crontab en mi raspberry pi) obtenía en http://back.host22.com/bicis/ un listado único que consultar siempre disponible y actualizado.

El script acepta un fichero yaml para definir la búsqueda y generar el html resultante con el listado.
