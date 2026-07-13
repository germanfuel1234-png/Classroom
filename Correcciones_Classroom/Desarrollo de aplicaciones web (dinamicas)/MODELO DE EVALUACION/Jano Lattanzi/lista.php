<!DOCTYPE html>
<html>
<head>
    <title>Lista de números</title>
</head>
<body>

    <h2>Números del 1 al 15</h2>

    <ul>
        <?php
        for ($i = 1; $i <= 15; $i++) {

            if ($i % 2 == 0) {
                echo "<li>" . $i . "(PAR)</li>";
            } 
            else{
                echo "<li>" . $i . "</li>";
            }
          

        }
        ?>
    </ul>

</body>
</html>