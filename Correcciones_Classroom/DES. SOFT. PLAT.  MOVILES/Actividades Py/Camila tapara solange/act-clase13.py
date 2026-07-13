'''calculadora'''
from tkinter import Tk, Entry, Button, StringVar

digito = ""

def tomar_digito(n):
    global digito
    digito = digito + str(n)
    calculo.set(digito)

def resultado():
    global digito
    try:
        total = str(eval(digito))
        calculo.set(total)
        digito = total
    except:
        calculo.set("Error")

def limpiar_completo():
    global digito
    calculo.set("")
    digito = ""

# Ventana
ventana = Tk()
ventana.configure(background="light blue")
ventana.title("Calculadora")
ventana.geometry("300x285")
ventana.resizable(False, False)

# Pantalla
calculo = StringVar()

datos = Entry(
    ventana,
    bg="black",
    fg="white",
    textvariable=calculo
)
datos.grid(columnspan=4, ipadx=70, ipady=10)

# Fila 1
Button(ventana, text="7", width=6, height=2,
       command=lambda: tomar_digito(7)).grid(row=1, column=0)

Button(ventana, text="8", width=6, height=2,
       command=lambda: tomar_digito(8)).grid(row=1, column=1)

Button(ventana, text="9", width=6, height=2,
       command=lambda: tomar_digito(9)).grid(row=1, column=2)

Button(ventana, text="/", width=6, height=2,
       command=lambda: tomar_digito("/")).grid(row=1, column=3)

# Fila 2
Button(ventana, text="4", width=6, height=2,
       command=lambda: tomar_digito(4)).grid(row=2, column=0)

Button(ventana, text="5", width=6, height=2,
       command=lambda: tomar_digito(5)).grid(row=2, column=1)

Button(ventana, text="6", width=6, height=2,
       command=lambda: tomar_digito(6)).grid(row=2, column=2)

Button(ventana, text="*", width=6, height=2,
       command=lambda: tomar_digito("*")).grid(row=2, column=3)

# Fila 3
Button(ventana, text="1", width=6, height=2,
       command=lambda: tomar_digito(1)).grid(row=3, column=0)

Button(ventana, text="2", width=6, height=2,
       command=lambda: tomar_digito(2)).grid(row=3, column=1)

Button(ventana, text="3", width=6, height=2,
       command=lambda: tomar_digito(3)).grid(row=3, column=2)

Button(ventana, text="-", width=6, height=2,
       command=lambda: tomar_digito("-")).grid(row=3, column=3)

# Fila 4
Button(ventana, text="0", width=6, height=2,
       command=lambda: tomar_digito(0)).grid(row=4, column=0)

Button(ventana, text=".", width=6, height=2,
       command=lambda: tomar_digito(".")).grid(row=4, column=1)

Button(ventana, text="=", width=6, height=2,
       command=resultado).grid(row=4, column=2)

Button(ventana, text="+", width=6, height=2,
       command=lambda: tomar_digito("+")).grid(row=4, column=3)

# Limpiar
Button(ventana, text="C", width=28, height=2,
       command=limpiar_completo).grid(row=5, column=0, columnspan=4)

ventana.mainloop()