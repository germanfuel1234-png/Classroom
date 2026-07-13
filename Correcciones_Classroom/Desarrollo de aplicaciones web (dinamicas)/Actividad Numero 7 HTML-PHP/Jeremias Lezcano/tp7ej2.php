<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Número Primo</title>
</head>
<body>

<form method="post">
    <label for="num">Ingrese un número:</label>
    <input type="number" id="num" name="num" required>
    <button type="submit">Verificar</button>
</form>

<?php
if ($_SERVER["REQUEST_METHOD"] == "POST") {
    $num = $_POST["num"];
    $esPrimo = true;

    if ($num <= 1) {
        $esPrimo = false;
    } else {
        for ($i = 2; $i < $num; $i++) {
            if ($num % $i == 0) {
                $esPrimo = false;
                break;
            }
        }
    }

    if ($esPrimo) {
        echo "<p>$num es un número primo.</p>";
    } else {
        echo "<p>$num no es un número primo.</p>";
    }
}
?>

</body>
</html>