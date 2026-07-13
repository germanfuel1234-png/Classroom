//voy hacer que el usuario lo puede Leer y lo interpete lo que hizo "programa", que es en resumido que piden todo sobre ti al viajar un avion
Algoritmo FichaUsuarioMayorMenorEdad
	Definir nombre, lugarNac, estadoCivil, pais, provincia, domicilio Como Cadena
	Definir dni, añoNac, edad, añoActual Como Entero
	
	//vamos que el usuario que lea si es mayor o igual a 18 podes pasar y continuar el programa sino se para hasta que reinicie el programa
	
	Escribir "ingrese la edad"
	Leer edad
	Si edad >= 18 Entonces
		Escribir "Estado: mayor de edad"
	Escribir "_____Ingresa Tu Visa para entrar a Argentina_____"
	
	Escribir "Ingrese nombre completo:";
	Leer nombre
	
	Escribir "Ingrese año de nacimiento: ";
	Leer añoNac
	
	Escribir "Ingrese año actual:";
	Leer añoActual
	
	Escribir "Ingrese lugar de nacimiento:";
	Leer lugarNac
	
	Escribir "Ingrese estado civil:";
	Leer estadoCivil
	
	Escribir "Ingrese DNI:";
	Leer dni
	
	Escribir "Ingrese tu país:";
	Leer pais
	
	Escribir "Ingrese tu provincia:";
	Leer provincia
	
	Escribir "Ingrese tu domicilio:";
	Leer domicilio
	
	edad <- añoActual-añoNac
	//montrado la informacion del todo lo que hice
	Escribir "mostrando su nombre ", nombre
	Escribir "mostrando su nacimiento " , añonac
	Escribir "mostrando su año actual " , añoActual
	Escribir "mostrando su lugar de nacimiento " , lugarNac
	Escribir "mostrando su estado Civil  " , estadoCivil
	Escribir "mostrando su DNI " , dni
	Escribir "mostrando su pais" , pais
	Escribir "mostrando su provincia " , provincia
	Escribir "mostrando su domicilio " , domicilio
	
	SiNo 
		Escribir "Estado: MENOR DE EDAD"
	FinSi
	
FinAlgoritmo