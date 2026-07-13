Algoritmo age_rate
	definir edad Como Entero
	escribir "Ingrese su edad" 
	leer edad
	Si edad >= 0 y edad <= 4 Entonces
		Escribir "Eres un niño"
	FinSi
	Si edad >= 5 y edad <= 13  Entonces
		Escribir " Eres un pre-adolescente"
	FinSi
	Si edad >= 14 y edad <= 17 Entonces 
		Escribir "Eres un adolescente"
	FinSi
	Si edad >= 18 y edad <= 30 Entonces
		Escribir "Ya eres mayor de edad"
	FinSi
	Si edad >= 31 y edad <= 60 Entonces
		Escribir "Eres un adulto"
	FinSi
	Si edad >= 61 y edad <= 80 Entonces
		Escribir "Eres una persona anciana "
	FinSi
	Si edad >= 81 Y edad <= 100 Entonces
		Escribir "Eres una persona anciana"
	FinSi
FinAlgoritmo
