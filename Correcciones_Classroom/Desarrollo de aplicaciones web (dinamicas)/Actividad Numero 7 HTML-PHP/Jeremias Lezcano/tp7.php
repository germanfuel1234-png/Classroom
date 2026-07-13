<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Verificar Edad</title>
</head>
<body>

<form method="post">
    <label for="Ingrese un numero">Ingrese un numero:</label>
    <input type="text" id="num" name="num">
    <button type="submit">Enviar</button>
</form>

<?php
if ($_SERVER["REQUEST_METHOD"] === "POST" && isset($_POST['num'])) {
    $num = trim($_POST['num']);
    if ($num !== '') {
        echo "Tabla del $num<br>";
        for ($x = 1; $x <= 10; $x++) {
            echo "$num * $x = " . ($num * $x) . "<br>";
        }
    } else {
        echo "Ingrese un número válido.";
    }
}
?>

</body>
</html>