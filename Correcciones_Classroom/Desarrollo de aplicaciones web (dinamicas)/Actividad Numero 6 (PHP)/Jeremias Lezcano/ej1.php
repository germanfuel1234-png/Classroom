<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Verificar Edad</title>
</head>
<body>

<form method="post">
    <label for="edad">Ingrese su edad:</label>
    <input type="text" id="edad" name="edad">
    <button type="submit">Enviar</button>
</form>

<?php
if ($_SERVER["REQUEST_METHOD"] == "POST") {
    $edad = $_POST['edad'];

    if ($edad < 18) {
        echo "Eres menor de edad.";
    } elseif ($edad >= 18 && $edad < 65) {
        echo "Eres mayor de edad pero aún no estás jubilado.";
    } else {
        echo "Eres jubilado.";
    }
}
?>

</body>
</html>