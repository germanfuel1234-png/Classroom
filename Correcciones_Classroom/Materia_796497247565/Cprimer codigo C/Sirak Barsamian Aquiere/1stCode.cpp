#include <stdio.h>

int main ()
{
 int hrstrabajadas;
 float costohr;
 float sueldo;
 printf("Ingresar las horas trabajadas por el empleado:");
 scanf("%i", &hrstrabajadas);
 printf("Ingrese el pago por hora del empleado:");
 scanf("%f", &costohr);
 sueldo=hrstrabajadas*costohr;
 printf("El sueldo del empleado es:");
 printf("%f", sueldo);
getchar();
return 0; 
}
