<!DOCTYPE html>
<html>
<head>
    <title>Menú Desplegable de Años</title>
</head>
<body>

    <h2>Seleccioná un año</h2>

    <select name="anio">
        <?php
        for ($anio = 2020; $anio <= 2030; $anio++) {

            if ($anio == 2026) {
                echo "<option value='$anio'>$anio - Año Actual</option>";
            } else {
                echo "<option value='$anio'>$anio</option>";
            }

        }
        ?>
    </select>

</body>
</html>