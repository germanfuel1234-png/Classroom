'''
Generador Contraseña
'''
def generar_contraseña_letras(longitud):
    import random
    import string
    caracteres = string.ascii_letters
    contraseña = ''.join(random.choice(caracteres) for _ in range(longitud))
    return contraseña
def generar_contraseña_numeros(longitud):
    import random
    caracteres = '0123456789'
    contraseña = ''.join(random.choice(caracteres) for _ in range(longitud))
    return contraseña
def generar_contraseña_letras_numeros(longitud):
    import random
    import string
    caracteres = string.ascii_letters + '0123456789'
    contraseña = ''.join(random.choice(caracteres) for _ in range(longitud))
    return contraseña
def generar_contraseña_completa(longitud):
    import random
    import string
    caracteres = string.ascii_letters + '0123456789' + string.punctuation
    contraseña = ''.join(random.choice(caracteres) for _ in range(longitud))
    return contraseña

while True:
    print("Practica integradora - 2da app - Clase 11")
    print("="*25)
    print("GENERADOR DE CONTRASEÑA v0.1")
    print("="*25)
    print("Seleccione una de las siguientes opciones:")
    print("1. Generar contraseña solo de letras")
    print("2. Generar contraseña solo de números")
    print("3. Generar contraseña de letras y números")
    print("4. Generar contraseña de letras, números y caracteres")
    print("0. Salir")
    opc = input("Escriba la opción seleccionada: ")
    if opc == "1":
        longitud = int(input("Ingrese la longitud de la contraseña: "))
        print("Contraseña generada:", generar_contraseña_letras(longitud))
    elif opc == "2":
        longitud = int(input("Ingrese la longitud de la contraseña: "))
        print("Contraseña generada:", generar_contraseña_numeros(longitud))
    elif opc == "3":
        longitud = int(input("Ingrese la longitud de la contraseña: "))
        print("Contraseña generada:", generar_contraseña_letras_numeros(longitud))
    elif opc == "4":
        longitud = int(input("Ingrese la longitud de la contraseña: "))
        print("Contraseña generada:", generar_contraseña_completa(longitud))
    elif opc == "0":
        print("Gracias por usar el generador de contraseñas. ¡Hasta luego!")
        break