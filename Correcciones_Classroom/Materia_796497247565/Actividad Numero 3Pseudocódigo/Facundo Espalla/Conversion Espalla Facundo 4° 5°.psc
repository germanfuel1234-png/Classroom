//Programa de conversion de cm a M, c a F, Millas a kilometros
//Medidas cm corresponde a los centrimetros y los M seria Metros
//
Algoritmo Conversion
	Definir cm,M,C,F,mi,km Como Real
	//OUPUT 
	Escribir "Bienvenido a la conversion de cm a M "
	Escribir "ingrese los centrimetros que quiera transformar a Metros"
	Leer cm 
	M=cm/100
	Escribir "la converesion de cm a M es de ", M " Metros"
	Escribir "--------------------------------------------------" 
	Escribir "Despues de esto vamos a ver la conversion de Celsuis a Fahrenheit"
	//Medidas C° correspónde a celsuis y los F° seria fahrenheit
	//OUPUT
	Escribir "ingrese los celsuis que quiera transformar a fahrenheit"
	Leer C
	F=(C*1.8)+32
	Escribir "la conversion de Celsuis a Fahrenheit es de " , F " fahrenheit" 
	Escribir "----------------------------------------------------"
	Escribir "tras completar lo anterior vamos hacer lo mismo pero con la Millas a Kilometros"
	//Medidas mi corresponde a Millas y los kms seria Kilometros 
	//OUPUT
	Escribir "ingrese los Kilometros que quiera transformar a Millas"
	Leer mi
	km=mi*1.60934
	Escribir "la conversion de Kilometros a Millas es de " , km " Kilometros"
FinAlgoritmo
