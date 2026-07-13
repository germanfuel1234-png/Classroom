//Carteles segun edad 
Algoritmo Grupo_Edad
	Definir edad Como Entero
	//salida a la pantalla del usuario (OUTPUT)
	Escribir "Ingrese su edad:"
	//guarda el dato del usuario en una variable (INPUT)
	Leer edad
	
	Si edad >= 0 Y edad <= 4 Entonces
		Escribir "Grupo de edad: 0-4"
		
	SiNo
		
		Si edad <= 13 Entonces
			Escribir "Grupo de edad: 5-13"
			
		SiNo
			
			Si edad <= 17 Entonces
				Escribir "Grupo de edad: 14-17"
				
			SiNo
				
				Si edad <= 30 Entonces
					Escribir "Grupo de edad: 18-30"
					
				SiNo
					
					Si edad <= 60 Entonces
						Escribir "Grupo de edad: 31-60"
						
					SiNo
						
						Si edad <= 80 Entonces
							Escribir "Grupo de edad: 61-80"
							
						SiNo
							Escribir "Grupo de edad: 81+"
							
						FinSi
					FinSi
				FinSi
			FinSi
		FinSi
	FinSi
	
FinAlgoritmo
