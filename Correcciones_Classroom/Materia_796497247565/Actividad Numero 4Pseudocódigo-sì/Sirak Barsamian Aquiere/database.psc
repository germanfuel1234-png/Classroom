Algoritmo database
	definir dni, año, edad Como entero
	definir lugar, domi, estcv, prov, nom como caracter  
	definir op como entero
	escribir "Ingrese su edad" 
	leer edad  
	si edad >= 18 entonces 
		
		año <- 2026-edad 
	escribir "aguarde un momento..."  
	esperar 2 Segundos
	escribir "Ingrese su nombre" 
	leer nom
	escribir "Ingrese su lugar de nacimiento" 
	leer lugar
	escribir "ingrese su estado civil" 
	leer estcv   
	escribir "Ingrese su pais de residencia" 
	leer pais
	escribir "ingrese en la provincia que reside" 
	leer prov 
	escribir "ingrese el domicilio que reside" 
	leer domi
SiNo
	escribir "Usted es menor de edad."
FinSi   
escribir "aguarde un momento..."  
esperar 2 Segundos
escribir "¿Quiere visualizar sus datos? escriba 1 para si, escriba 2 para no"   
Leer op
Si op = 1 Entonces
	escribir "Nombre: " nom 
	escribir "Naciste en el año " año 
	escribir "Pais: " pais 
	escribir "Estado civil: " estcv
 	escribir "Lugar de nacimiento: " lugar  
 	escribir "Lugar de residencia: " domi  
	escribir "¡Gracias por ingresar sus datos!"
SiNo
	escribir "¡Gracias por ingresar sus datos!"
FinSi
FinAlgoritmo



