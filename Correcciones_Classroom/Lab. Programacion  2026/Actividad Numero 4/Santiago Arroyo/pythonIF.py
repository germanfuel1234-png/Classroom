# BIENVENIDO AL PROGRAMA PARA CALCULAR SI SOS MAYOR O MENOR DE EDAD Y TU GRUPO DE EDAD

edad = int(input("Ingresá una edad:\n"))
if edad < 18:
    print(f"Menor de edad.\n")
else:
    print(f"Mayor de edad.\n")
     
#GRUPO DE EDAD

if edad >= 0 and edad <= 4:
    print(f"Tu grupo de edad es de 0-4\n")

if edad >= 5 and edad <= 13:
    print(f"Tu grupo de edad es de 5-13\n")

if edad >= 14 and edad <= 17:
    print(f"Tu grupo de edad es de 14-17\n")

if edad >= 18 and edad <= 30:
    print(f"Tu grupo de edad es de 18-30\n")

if edad >= 31 and edad <= 60:
    print(f"Tu grupo de edad es de 31-60\n")

if edad >= 61 and edad <= 80:
    print(f"Tu grupo de edad es de 61-80\n")

if edad >= 81 and edad <=122:
    print(f"Tu grupo de edad es de 81+\n")

