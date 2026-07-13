#include <stdio.h>

int main ()
//inicio del codigo 
{  //definicion de variables enteras y reales
    int turismos, todoterrenos;
    float combturismo, combtodoterrenos, necesidades;
    //escribir un texto que aparezca en la pantalla del usuario (output)
    printf("Ingrese el n° de automoviles turistas: ");
    //leer la variable que se va ingresas (input)
    scanf("&i", &turismos);
    
    printf("¿Que capacidad, en litros, tiene cada deposito de combustible de ese tipo de vehiculo? ");
    scanf("%f", &combturismo);
    
    printf("Ingrese el n° de automoviles todoterrenos: ");
    scanf("&i", todoterrenos);
    
    printf("¿Que capacidad, en litros, tiene cada deposito de combustible de ese tipo de vehiculo? ");
    scanf("%f", &combtodoterrenos);
    //expresion logica
    necesidades=turismos*combturismo+todoterrenos*combtodoterrenos;
   
    printf("La cantidad de combustible necesario para abastecer a todos los vehiculos es de: ");
    printf("%f", &necesidades);
    //pide al sistema que de un caracter en el output
    getchar();
    //pide al sistema que le devuelva un numero en el output
    return 0;
}
