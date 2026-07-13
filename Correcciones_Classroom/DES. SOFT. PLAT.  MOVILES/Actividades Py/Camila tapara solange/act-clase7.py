'''
Se busca crear un juego para adivinar un numero generado de manera
random, para ello deberemos implementar lo siguiente:

Variables
Bucles
Condicionales
Operadores Logicos
Operadores Aritmeticos
Asignación de valores
Input
Print

Requisitos a cumplir:

El juego termina cuando el Jugador acierta el numero
o hace 5 intentos.
Cuando se pide ingresar el número se le debe indicar al
jugador el rango máximo y mínimo.
Si el jugador falla, se debe indicar si el número es
mayor o menor.
Al perder se le enviara un mensaje indicandole que ha
perdido y cual era el número.
Como ayuda inicial les voy a brindar las dos primeras lineas de su codigo

import random

numero_secreto = random.randint(1, 50)

random es un packete o modulo (ya veremos esto mas adelante) de
python el cual los ayudara a generar un numero justamente random entre
un rango de numeros
'''
import random
num_secreto= random.randint(1, 50)
intentos=0
print("Practica integradora - Clase 7")
print("Adivina el Número!")
while intentos<5:
    num_usuario=int(input("Ingrese un numero entre 1 y 50: "))
    intentos+=1
    if num_usuario==num_secreto:
        print("¡Felicidades! Has adivinado el número.")
        break
    elif num_usuario<num_secreto:
        print("El número es mayor.")
    else:
        print("El número es menor.")
    if intentos==5 and num_usuario!=num_secreto:
        print(f"Lo siento, has perdido. El número era {num_secreto}.")


