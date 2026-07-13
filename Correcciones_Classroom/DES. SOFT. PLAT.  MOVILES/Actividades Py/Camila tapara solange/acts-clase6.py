'''
Realizar un programa que me diga si un numero es par o impar

Realizar un programa que genere la tabla de multiplicar de un numero ingresado por el
usuario (de1 1 al 10)

Realizar un programa que le pida al usuario su nombre y edad y nos diga si es mayor de
edad

Realizar un programa donde el usuario ingrese una palabra y un numero e imprima por
pantalla la palabra ingresa tantas veces como el numero ingresado

Realizar un programa que sume los números ingresados por el usuario hasta que se
ingrese un 0. Al finalizar nos debe mostrar la suma por pantalla
'''
def par_o_impar(numero):
    if numero % 2 == 0:
        return "El número es par."
    else:
        return "El número es impar."

def tabla_multiplicar(numero):
    tabla = []
    for i in range(1, 11):
        tabla.append(f"{numero} x {i} = {numero * i}")
    return tabla

def mayor_de_edad(nombre, edad):
    if edad >= 18:
        return f"{nombre} es mayor de edad."
    else:
        return f"{nombre} es menor de edad."

def repetir_palabra(palabra, numero):
    return palabra * numero

def sumar_hasta_cero():
    suma = 0
    while True:
        numero = float(input("Ingrese un número (0 para finalizar): "))
        if numero == 0:
            break
        suma += numero
    return suma

while True:
    print("Practica - Clase 6")
    print("Elegir opción:")
    print("1. Determinar si un número es par o impar")
    print("2. Generar tabla de multiplicar")
    print("3. Verificar si es mayor de edad")
    print("4. Repetir palabra")
    print("5. Sumar números hasta ingresar 0")
    opcion = input("Opción: ")
    if opcion == "1":
        numero = int(input("Ingrese un número: "))
        print(par_o_impar(numero))
    elif opcion == "2":
        numero = int(input("Ingrese un número para generar su tabla de multiplicar: "))
        tabla = tabla_multiplicar(numero)
        for linea in tabla:
            print(linea)
    elif opcion == "3":
        nombre = input("Ingrese su nombre: ")
        edad = int(input("Ingrese su edad: "))
        print(mayor_de_edad(nombre, edad))
    elif opcion == "4":
        palabra = input("Ingrese una palabra: ")
        numero = int(input("Ingrese un número: "))
        print(repetir_palabra(palabra, numero))
    elif opcion == "5":
        print(f"La suma de los números ingresados es: {sumar_hasta_cero()}")
    else:
        print("Opción no válida. Intente nuevamente.")