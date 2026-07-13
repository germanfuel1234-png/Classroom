//Crear el Pseudocódigo para un programa que muestre en pantalla la edad del usuario
Algoritmo DNI_Usuario
	//Inicio al Algoritmo
	Definir Nombre,Lugar_de_nacimiento,Estado_Civil,Pais,Provincia,Domicilio Como Caracter
	Definir Año_de_nacimiento,DNI,Año_actual,Edad Como Entero
	//Salida a la pantalla del usuario (OUTPUT)
	Escribir "Ingrese su nombre: "
	//Guarda el dato del usuario en una variable (Input)
	Leer Nombre
	
	//Salida a la pantalla del usuario (OUTPUT)
	Escribir "Ingrese su año de nacimiento: "
	//Guarda el dato en una variable (Input)
	Leer Año_de_nacimiento 
	
	//Salida a la pantalla del usuario (OUTPUT)
	Escribir "Ingrese su Lugar_de_nacimiento: "
	//Guarda el dato en una variable (Input)
	Leer Lugar_de_nacimiento
	
	//Salida a la pantalla del usuario (OUTPUT)
	Escribir "Ingrese su Estado_Civil: "
	//Guarda el dato en una variable (Input)
	Leer Estado_Civil 
	
	//Salida a la pantalla del usuario (OUTPUT)
	Escribir "Ingrese su DNI: "
	//Guarda el dato en una variable (Input)
	Leer DNI 
	
	//Salida a la pantalla del usuario 
	Escribir "Ingrese su Pais:"
	//Guarda el dato en una variable (Input)
	Leer Pais
	
	//Salida a la pantalla deñ usuario (OUTPUT)
	Escribir "Ingrese su Provincia: "
	//Guarda el dato en una variable (Input
	Leer Provincia
	
	//Salida a la pantalla del usuario (OUTPUT)
	Escribir "Ingrese su Domicilio: "
	//Guarda el dato en una variable 
	Leer Domicilio
	
	//aignacion del año actual
	Año_actual <- 2026
	
	//expresion logica
	Edad <- Año_actual - Año_de_nacimiento
	
	//Salida a la pantalla del usuario (OUTPUT)
	Escribir "------ DATOS DEL USUARIO ------"
	Escribir "Nombre: ",Nombre
	Escribir "Edad: ",Edad
	Escribir "Lugar_de_nacimiento: ",Lugar_de_nacimiento
	Escribir "Estado_Civil: ",Estado_Civil
	Escribir "DNI: ",DNI
	Escribir "Pais: ",Pais
	Escribir "Provincia: ",Provincia
	Escribir "Domicilio: ",Domicilio
	
	//condicion mayor o  menor de Edad
	SI Edad >= 18 Entonces
		Escribir "Eres mayor de edad"
	SiNo
		Escribir "Eres menor de edad"
	FinSi
	
FinAlgoritmo

