Algoritmo la_loteria
	Definir numero_usuario, numero_ganador, diferencia Como Entero
    numero_ganador <- 67

    Escribir "Ingrese un numero:"
    Leer numero_usuario
    
    diferencia <- numero_ganador - numero_usuario
    
    Si diferencia < 0 Entonces
        diferencia <- diferencia * (-1)
    FinSi
    
    Si numero_usuario = numero_ganador Entonces
        Escribir "Felicidades Ganaste la Loteria!"
    SiNo
        Si diferencia <= 2 Entonces
            Escribir "MUY CERCA"
        SiNo
            Si diferencia <= 5 Entonces
                Escribir "Aproximado"
            SiNo
                Si diferencia <= 10 Entonces
                    Escribir "Por Poco"
                SiNo
                    Si diferencia <= 20 Entonces
                        Escribir "Por mucho"
                    SiNo
                        Escribir "MUY ALEJADO"
                    FinSi
                FinSi
            FinSi
        FinSi
    FinSi
FinAlgoritmo
