'''
Crea una tupla con los meses del año, pide números al usuario, si el numero
esta entre 1 y la longitud máxima de la tupla, muestra el contenido de esa
posición sino muestra un mensaje de error. El programa termina cuando el
usuario introduce un cero.

Pide números y mételos en una lista, cuando el usuario meta un 0 ya
dejaremos de insertar. Por último, muestra los números ordenados de menor
a mayor.

Crea una tupla con números, pide un numero por teclado e indica cuantas
veces se repite.

Vamos a crear un programa en python donde vamos a declarar un
diccionario para guardar los precios de las distintas frutas. El programa
pedirá el nombre de la fruta y la cantidad que se ha vendido y nos mostrará
el precio final de la fruta a partir de los datos guardados en el diccionario.
'''
def meses_del_año():
    meses = ("Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre")
    while True:
        numero = int(input("Ingrese un número entre 1 y 12 (0 para finalizar): "))
        if numero == 0:
            print("Programa finalizado.")
            break
        elif 1 <= numero <= len(meses):
            print(f"El mes correspondiente al número {numero} es: {meses[numero - 1]}")
        else:
            print("Número fuera de rango. Intente nuevamente.")

def ordenar_numeros():
    numeros = []
    while True:
        numero = int(input("Ingrese un número (0 para finalizar): "))
        if numero == 0:
            break
        numeros.append(numero)
    numeros.sort()
    print("Números ordenados de menor a mayor:")
    for num in numeros:
        print(num)

def contar_repeticiones():
    numeros = (1, 2, 3, 4, 5, 2, 3, 1, 4, 5)
    numero = int(input("Ingrese un número para contar sus repeticiones: "))
    conteo = numeros.count(numero)
    print(f"El número {numero} se repite {conteo} veces en la tupla.")
    
def calcular_precio():
    precios = {
        "manzana": 0.5,
        "banana": 0.3,
        "naranja": 0.4,
        "pera": 0.6
    }
    fruta = input("Ingrese el nombre de la fruta: ").lower()
    cantidad = int(input("Ingrese la cantidad vendida: "))
    if fruta in precios:
        precio_final = precios[fruta] * cantidad
        print(f"El precio final de {cantidad} {fruta}(s) es: ${precio_final:.2f}")
    else:
        print("Fruta no encontrada en el diccionario.")

while True:
    print("Practica - Clase 11")
    print("Elegir opción:")
    print("1. Mostrar mes por número")
    print("2. Ordenar números")
    print("3. Contar repeticiones")
    print("4. Calcular precio de fruta")
    opcion = input("Opción: ")
    if opcion == "1":
        meses_del_año()
    elif opcion == "2":
        ordenar_numeros()
    elif opcion == "3":
        contar_repeticiones()
    elif opcion == "4":
        calcular_precio()
    else:
        print("Opción no válida. Intente nuevamente.")