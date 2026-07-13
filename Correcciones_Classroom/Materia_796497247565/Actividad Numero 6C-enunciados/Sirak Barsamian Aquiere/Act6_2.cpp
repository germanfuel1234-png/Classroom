#include <stdio.h>

int main ()
{  
    int diamt, altura, radio;
    float volumen, pi;
    printf("Ingresar el diametro del cilindro, en metros: ");
    scanf ("i%", & diamt);
    printf("Ingresar la altura del cilindro, en metros: ");
    scanf ("%i", & altura);
    pi= 3,141593;
    radio=diamt/2/pi;
    volumen=pi*(radio*radio)*altura;
    printf("El volumen del cilindro es: " "%f", volumen); (" metros cuadrados");
    getchar();
    return 0;
}
