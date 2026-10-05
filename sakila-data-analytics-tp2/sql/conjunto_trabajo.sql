-- sql/conjunto_trabajo.sql
-- Extrae el conjunto de trabajo para la Variante 4 (Morosidad y Devoluciones)
SELECT 
    a.id_alquiler,
    a.fecha_alquiler,
    a.fecha_devolucion,
    c.id_cliente,
    c.nombre AS nombre_cliente,
    c.apellido AS apellido_cliente,
    p.id_pelicula,
    p.titulo,
    p.duracion_alquiler,
    p.costo_reposicion,
    p.tarifa_alquiler,
    cat.nombre AS categoria
FROM alquiler a
INNER JOIN inventario i ON a.id_inventario = i.id_inventario
INNER JOIN pelicula p ON i.id_pelicula = p.id_pelicula
INNER JOIN cliente c ON a.id_cliente = c.id_cliente
LEFT JOIN pelicula_categoria pc ON p.id_pelicula = pc.id_pelicula
LEFT JOIN categoria cat ON pc.id_categoria = cat.id_categoria
WHERE a.fecha_alquiler >= ?
ORDER BY a.fecha_alquiler ASC;