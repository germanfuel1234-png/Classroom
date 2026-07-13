'''
TICKETS
Se ha pedido crear un modulo para generar tickets que contenga lo siguiente:

Un menú con 3 opciones - Alta ticket , Leer ticket , Salir.
Alta ticket : nombre, sector,asunto, problema
Al terminar de ingresar el ticket se deberá mostrar por pantalla el mismo,
sumándose el numero de ticket (que sera un numero random entre 1000,
9999) y una leyenda que pida acordarse del numero
un menu que nos pregunte si deseamos crear otro ticket, en caso de ser no
que nos regrese al menu principal, de lo contrario que nos regrese a la
pantalla de alta.
leer ticket: número ticket
al ingresar el numero nos mostrara por pantalla el ticket almacenado
debajo del mismo aparece una leyenda que nos preguntara si deseamos leer
otro ticket, teniendo la funcionalidad similar a la anteriormente mencionada.
Salir : el programa finaliza y se cierra pidiéndonos una confirmacion
'''
tickets = []
def generar_ticket(nombre, sector, asunto, msj):
    import random
    ticket_num = random.randint(1000, 9999)
    tickets.append((ticket_num, nombre, sector, asunto, msj))
    return ticket_num, nombre, sector, asunto, msj

def leer_ticket(ticket_num):
    for ticket in tickets:
        if ticket[0] == ticket_num:
            return ticket
    return None

def confirmar_salida():
    confirmacion = input("¿Está seguro que desea salir? (s/n): ")
    return confirmacion.lower() == 's'

while True:
    print("Practica integradora - 1er app - Clase 11")
    print("TICKETS")
    print("Elegir opción:")
    print("1. Generar un nuevo ticket")
    print("2. Leer un ticket")
    print("3. Salir")
    opcion = input("Seleccione: ")
    if opcion == "1":
        print("Ingrese los datos para generar un nuevo ticket")
        nombre = input("Ingrese su nombre: ")
        sector = input("Ingrese su sector: ")
        asunto = input("Ingrese asunto: ")
        msj = input("Ingrese un mensaje: ")
        print("="*25)
        print("Se genero el siguiente Ticket")
        print("="*25)
        ticket_num, nombre, sector, asunto, msj = generar_ticket(nombre, sector, asunto, msj)
        print("Número de ticket:", ticket_num)
        print(f"Ticket generado para {nombre} en el sector {sector} con el asunto '{asunto}' y el mensaje '{msj}'.")
        print("Recuerde su número de ticket.")    
        opc = input("¿Desea generar otro ticket? (s/n): ")
        if opc.lower() != 's':
            continue
    elif opcion == "2":
        ticket_num = int(input("Ingrese el número de ticket que desea leer: "))
        ticket = leer_ticket(ticket_num)
        if ticket:
            print("="*25)
            print("Ticket encontrado:")
            print("="*25)
            print(f"Número de ticket: {ticket[0]}")
            print(f"Nombre: {ticket[1]}")
            print(f"Sector: {ticket[2]}")
            print(f"Asunto: {ticket[3]}")
            print(f"Mensaje: {ticket[4]}")
        else:
            print("Ticket no encontrado.")
        opc = input("¿Desea leer otro ticket? (s/n): ")
        if opc.lower() != 's':
            continue
    elif opcion == "3":
        if confirmar_salida():
            print("Programa finalizado.")
            break
        else:
            continue
    else:
        print("Opción no válida. Intente nuevamente.")
