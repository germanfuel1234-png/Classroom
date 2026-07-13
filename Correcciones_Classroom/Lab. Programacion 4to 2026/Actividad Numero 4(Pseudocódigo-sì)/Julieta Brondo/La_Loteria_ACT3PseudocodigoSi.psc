//LA LOTERIA!!!
Algoritmo La_Loteria
	//Inicio al Algoritmo 
	Definir numeroUsuario,numeroSecreto,diferencia Como Entero
	//Asignacion del numero secreto
	numeroSecreto <- 222
	
	//Salida a la pantalla del usuario (OUTPUT)
	Escribir "Ingrese un numero del 1 al 250." 
	//Giuarda el dato del usuario en una variable (Input)
	Leer numeroUsuario
	
	//Expresion logica
	diferencia <- Abs(numeroUsuario - numeroSecreto)
	
	Si diferencia = 0 Entonces
		//Salida a la pantalla del usuario (OUTPUT)
		Escribir "¡FELICIDADESS! Ganaste la loteria."
	SINo 
		si diferencia <= 5 Entonces
			//Salida a la pantalla del usuario (OUTPUT)
			Escribir "POR POCO"
		SINo 
			Si diferencia <= 15 Entonces
				//Salida a la pantalla del usuario (OUTPUT)
				Escribir "MUY CERCA"
			SINo 
				sI diferencia <= 25 Entonces
					//Salida a la pantalla del usuario (OUTPUT)
					Escribir "Lejos" 
				SINo 
					Escribir "Demasiado lejos :("
				FinSi
			FinSi
		FinSi
	FinSi
	//Fin del Algoritmo 
FinAlgoritmo
