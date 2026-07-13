//encontrar c, ancho, largo del triangulo
Proceso rectangulo
	Definir c, ancho, largo como real
	Escribir "ingresar el cateto 1 (ancho) del rectangulo"
	leer ancho
	Escribir "ingresar el cateto 2 (largo) del rectangulo"
	Leer largo

	c <- ((ancho * ancho) + (largo * largo))
	hipotenusa <- RC(c)
	Escribir "hipotenusa : ", hipotenusa
	
	
FinProceso
