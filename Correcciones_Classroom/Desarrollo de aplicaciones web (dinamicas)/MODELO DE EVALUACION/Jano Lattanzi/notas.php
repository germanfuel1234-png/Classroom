
<!DOCTYPE html>
<html>
<head>
    <title>Notas</title>
</head>
<body>

    <h2>Ingresá una nota del 1 al 10</h2>

    <form method="POST">
        <label>Nota:</label>
        <input type="number" name="nota" min="1" max="10" required>
        <button type="submit">Enviar</button>
    </form>

    <?php
    if ($_SERVER["REQUEST_METHOD"] == "POST") {

        $nota = $_POST["nota"];

        if ($nota < 4) {
            echo "<p>Desaprobado. Debes recuperar.</p>";
        } elseif ($nota >= 4 && $nota <= 6) {
            echo "<p>Aprobado. Buen intento.</p>";
        } else {
            echo "<p>Promocionado. ¡Excelente rendimiento!</p>";
        }
    }
    ?>

</body>
</html>