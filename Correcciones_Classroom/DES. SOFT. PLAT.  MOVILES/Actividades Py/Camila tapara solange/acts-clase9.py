'''
Cree una funcion que calcule el promedio de N notas

Cree una funcion que determine si un color es primario o no, se debe imprimir por
pantalla la leyenda “el color X es primero “ o “el color X no es primario”

Cree una funcion que determine que numero de una serie de N numeros es mayor

Cree una funcion que dibuje un rectangulo de X filas y X columnas determinadas por el
usuario

Cree una funcion que calcule el Factorial de un numero entero positivo
'''
def promedio_N(notas):
    return sum(notas)/len(notas)

def color_primario(color):
    primarios = ["rojo", "azul", "amarillo"]
    if color in primarios:
        return f"El color {color} es primario."
    else:
        return f"El color {color} no es primario."
    
def mayor_numero(numeros):
    return max(numeros)

def dibujar_rectangulo(filas, columnas):
    for i in range(filas):
        print("* " * columnas)

def factorial(numero):
    if numero < 0:
        return "El número debe ser entero positivo."
    elif numero == 0 or numero == 1:
        return 1
    else:
        resultado = 1
        for i in range(2, numero + 1):
            resultado *= i
        return resultado

while True:
    print("Practica - Clase 9")
    print("Elegir opción:")
    print("1. Calcular promedio de notas")
    print("2. Determinar si un color es primario")
    print("3. Encontrar el número mayor en una serie")
    print("4. Dibujar un rectángulo")
    print("5. Calcular el factorial de un número")
    opcion = input("Opción: ")
    if opcion == "1":
        cantidad = int(input("¿Cuántas notas desea ingresar? "))
        notas = []
        for i in range(cantidad):
            nota = float(input(f"Ingrese la nota {i+1}: "))
            notas.append(nota)
        print(f"El promedio de las notas es: {promedio_N(notas)}")
    elif opcion == "2":
        color = input("Ingrese un color: ").lower()
        print(color_primario(color))
    elif opcion == "3":
        cantidad = int(input("¿Cuántos números desea ingresar? "))
        numeros = []
        for i in range(cantidad):
            numero = float(input(f"Ingrese el número {i+1}: "))
            numeros.append(numero)
        print(f"El número mayor es: {mayor_numero(numeros)}")
    elif opcion == "4":
        filas = int(input("Ingrese el número de filas: "))
        columnas = int(input("Ingrese el número de columnas: "))
        dibujar_rectangulo(filas, columnas)
    elif opcion == "5":
        num = int(input("Ingrese un número entero positivo: "))
        print(f"El factorial de {num} es: {factorial(num)}")
    else:
        print("Opción no válida. Intente nuevamente.")