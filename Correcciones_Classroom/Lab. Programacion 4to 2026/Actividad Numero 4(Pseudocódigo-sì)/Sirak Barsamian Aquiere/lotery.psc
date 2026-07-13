Algoritmo lotery
	Definir num, ganador, diferencia Como Entero
	ganador <- 50
	Escribir "Ingrese el numero:"
	Leer num
	diferencia <- n - ganador
	Si diferencia < 0 Entonces
		diferencia <- diferencia * (-1)
	FinSi
	Si n = ganador Entonces
		Escribir "Acertaste! Ganaste la Lotería!"
	Sino
		Si diferencia <= 3 Entonces
			Escribir "Por poco aciertas..."
		Sino
			Si diferencia <= 8 Entonces
				Escribir "Muy cerca!"
			Sino
				Si diferencia <= 15 Entonces
					Escribir "Cercano"
				Sino
					Si diferencia <= 25 Entonces
						Escribir "Te estas acercando"
					Sino
						Si diferencia <= 40 Entonces
							Escribir "Demasiado lejos..."
						Sino
							Escribir "Muy lejos..."
						FinSi
					FinSi
				FinSi
			FinSi
		FinSi
	FinSi
FinAlgoritmo
