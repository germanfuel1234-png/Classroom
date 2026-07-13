<!DOCTYPE html>
<html>
<head>
    <title>Altura para montaña rusa</title>
</head>
<body>

    <h2>Ingresá tu altura</h2>

    <form method="POST">
        <label>Altura en centímetros:</label>
        <input type="number" name="altura" required>
        <button type="submit">Enviar</button>
    </form>

    <?php
    if ($_SERVER["REQUEST_METHOD"] == "POST") {

        $altura = $_POST["altura"];

        if ($altura < 140) {
            echo "<p>No tienes la altura mínima para ingresar a la montaña rusa.</p>";
        } elseif ($altura >= 140 && $altura <= 195) {
            echo "<p>¡Acceso permitido! Disfruta del juego.</p>";
        } else {
            echo "<p>Superas la altura máxima permitida por seguridad.</p>";
        }
    }
    ?>

</body>
</html>