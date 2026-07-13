'''
Realizar un programa que le pida al usuario su nombre y lo muestre en mayúsculas

Realizar un programa que le pida al usuario un numero y le sume 5 , el resultado debe
mostrarce por pantalla

Realizar un programa que le pida al usuario su nombre y apellido , Mostrarlos en un
mensaje de bienvenida por la pantalla

Ingresar 5 numeros y calcular su promedio , el resultado mostrarlo por pantalla

Realizar un programa que muestre cualquier frase ingresada por el usuario en
minuscula
'''

def mostrar_nombre_mayusculas(nombre):
    return nombre.upper()

def sumar_cinco(numero):
    return numero+5
def mensaje_bienvenida(nombre, apellido):
    return f"Bienvenido {nombre} {apellido}!"

def calcular_promedio(numeros):
    return sum(numeros)/len(numeros)

def mostrar_frase_minuscula(frase):
    return frase.lower()

while True:
    print("Practica - Clase 5")
    print("Elegir opción:")
    print("1. Mostrar nombre en mayúsculas")
    print("2. Sumar 5 a un número")
    print("3. Mostrar mensaje de bienvenida")
    print("4. Calcular promedio de 5 números")
    print("5. Mostrar frase en minúsculas")
    opcion = input("Opción: ")
    if opcion == "1":
        nombre = input("Ingrese su nombre: ")
        print(mostrar_nombre_mayusculas(nombre))
    elif opcion == "2":
        numero = float(input("Ingrese un número: "))
        print(sumar_cinco(numero))
    elif opcion == "3":
        nombre = input("Ingrese su nombre: ")
        apellido = input("Ingrese su apellido: ")
        print(mensaje_bienvenida(nombre, apellido))
    elif opcion == "4":
        numeros = []
        for i in range(5):
            numero = float(input(f"Ingrese el número {i+1}: "))
            numeros.append(numero)
        print(calcular_promedio(numeros))
    elif opcion == "5":
        frase = input("Ingrese una frase: ")
        print(mostrar_frase_minuscula(frase))
    else:
        print("Opción no válida. Intente nuevamente.")
        