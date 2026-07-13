Algoritmo años_dni_pais_etc
	Definir nombre, lugar_nacimiento, estado_civil, dni, pais, provincia, domicilio Como Carácter
    Definir ano_nacimiento, edad Como Entero
    
    Escribir "Ingrese su nombre:"
    Leer nombre
    Escribir "Ingrese su año de nacimiento:"
    Leer ano_nacimiento
    Escribir "Ingrese su lugar de nacimiento:"
    Leer lugar_nacimiento
    Escribir "Ingrese su estado civil:"
    Leer estado_civil
    Escribir "Ingrese su DNI:"
    Leer dni
    Escribir "Ingrese su país:"
    Leer pais
    Escribir "Ingrese su provincia:"
    Leer provincia
    Escribir "Ingrese su domicilio:"
    Leer domicilio
    
    edad <- 2026 - ano_nacimiento
    
    Escribir "Nombre: ", nombre
    Escribir "Edad: ", edad, " años"
    
    Si edad >= 18 Entonces
        Escribir "MAYOR DE EDAD"
    SiNo
        Escribir "MENOR DE EDAD"
    FinSi
    
FinAlgoritmo
