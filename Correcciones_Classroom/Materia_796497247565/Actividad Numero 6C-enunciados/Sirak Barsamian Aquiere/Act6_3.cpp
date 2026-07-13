#include <stdio.h>

int main()
//inicio del programa
{ 
    int euro1;
    //definir variable
    int euro2;
    int euro3;
    int media;
    printf("Ingrese el precio del producto del establecimiento N°1, en euros");
    //escribir (output)
    scanf ("%i", &euro1);
    //leer (intput)
    printf("Ingrese el precio del producto del establecimiento N°2, en euros ");
    scanf ("%i", &euro2);
    printf("Ingrese el precio del producto del establecimiento N°3, en euros");
    scanf ("%i", &euro3);
    media=(euro1+euro2+euro3)/3;
    //expresion logica
    printf ("El precio medio del producto es:" "i%", &media);
    getchar();
    return 0;
}
