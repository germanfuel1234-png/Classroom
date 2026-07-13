import random
#LOTERIA
print(f"Bienvenido a la loteria, el numero ganador esta entre el 1 y el 20\n")

#Variable=Libreria.randint(Parametro)
numero_ganador=random.randint(1,20)
intentos=0


while intentos<3:
    intentos=intentos+1
    numero2=int(input("Ingrese un numero (el maximo de intentos son 3):\n"))
    print(f"Intento/s:{intentos}")

    dif=abs(numero_ganador-numero2)
    print(f"La diferencia entre el numero ingresado y el ganador es: {dif}\n")

    if numero2==numero_ganador:
        print(f"¡FELICIDADES! Ganaste la loteria.")

    if dif>10 and dif<20:
        print(f"El numero ganador esta muy lejos.\n")
    
    elif dif>5 and dif<9:
        print(f"El numero ganador esta lejos.\n")

    elif dif>1 and dif<4:
        print(f"El numero ganador esta cerca\n")

print(f"Perdiste... El numero ganador era {numero_ganador}")