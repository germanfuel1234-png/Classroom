'''
La trifecta
Se busca crear un programa que realize diversas tareas, para ello
deberemos implementar lo siguiente:

Variables
Bucles
Condicionales
Operadores Logicos
Operadores Aritmeticos
Asignación de valores
Input
Print

Requisitos a cumplir:

Al iniciar se nos debe pedir ingresar un numero, si este es mayor a
0 el programa inicia, de lo contrario finaliza (tambien si se ingresa
otra cosa que no sea un numero).
Se debe poder ingresar una Palabra o Frase y contar cuantos
caracteres tiene dicha palabra o frase
Con el valor obtenido en el punto anterior calcular su Factorial, una
vez hecho esto , decirnos si el resultado es par o impar.
Se deben imprimir los resultados por pantalla en cada paso.
Una vez cumplido esto, deberemos volver a pedir el ingreso de un
número y realizar la verificación del punto 1
'''
print("Practica integradora - Clase 8")
inicio = int(input("Ingrese un número para iniciar el programa: "))
if inicio != 0:
    while True:
        palabra = input("Ingrese una palabra o frase: ")
        longitud = len(palabra)
        print(f"La cantidad de caracteres es: {longitud}")
        
        factorial = 1
        for i in range(1, longitud + 1):
            factorial *= i
        
        print(f"El factorial de {longitud} es: {factorial}")
        
        if factorial % 2 == 0:
            print("El resultado es par.")
        else:
            print("El resultado es impar.")
        
        inicio = int(input("Ingrese un número para continuar o 0 para finalizar: "))
        if inicio == 0:
            print("Programa finalizado.")
            break
else:
    print("Programa finalizado.")
