<?php
$numero = "";
$mensaje = "";

if ($_SERVER["REQUEST_METHOD"] == "POST") {
    $numero = (int)$_POST["numero"];

    if ($numero < 1 || $numero > 100) {
        $mensaje = "Número inválido. Intenta de nuevo.";
    } else {
        $mensaje = "Número válido ingresado: $numero";
    }
}
?>

<!DOCTYPE html>
<html>
<head>
    <title>Validar número</title>
</head>
<body>

<h2>Ingresa un número entre 1 y 100</h2>

<form method="post">
    <input type="number" name="numero" required>
    <button type="submit">Enviar</button>
</form>

<p><?php echo $mensaje; ?></p>

</body>
</html>