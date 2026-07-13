Algoritmo Cartel_por_edad
			Definir edad Como Entero
			
			Escribir "Ingrese su edad:"
			Leer edad
			
			Si edad >= 0 Y edad <= 4 Entonces
				Escribir "Cartel: 0-4 años"
			SiNo
				Si edad >= 5 Y edad <= 13 Entonces
					Escribir "Cartel: 5-13 años"
				SiNo
					Si edad >= 14 Y edad <= 17 Entonces
						Escribir "Cartel: 14-17 años"
					SiNo
						Si edad >= 18 Y edad <= 30 Entonces
							Escribir "Cartel: 18-30 años"
						SiNo
							Si edad >= 31 Y edad <= 60 Entonces
								Escribir "Cartel: 31-60 años"
							SiNo
								Si edad >= 61 Y edad <= 80 Entonces
									Escribir "Cartel: 61-80 años"
								SiNo
									Escribir "Cartel: 81+ años"
								FinSi
							FinSi
						FinSi
					FinSi
				FinSi
			FinSi
    
FinAlgoritmo
