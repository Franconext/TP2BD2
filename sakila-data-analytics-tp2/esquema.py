TABLAS = {
    "rental": "alquiler",
    "film": "pelicula",
    "customer": "cliente",
    "inventory": "inventario",
    "category": "categoria",
    "film_category": "pelicula_categoria",
    "payment": "pago",
    "staff": "empleado",
    "store": "tienda",
    "address": "direccion",
    "city": "ciudad",
    "country": "pais",
    "actor": "actor",
    "film_actor": "pelicula_actor",
    "film_text": "pelicula_texto",
    "language": "idioma",
}

COLUMNAS = {
    # Tabla: alquiler (rental)
    "rental_id": "id_alquiler",
    "rental_date": "fecha_alquiler",
    "return_date": "fecha_devolucion",
    "customer_id": "id_cliente",
    "inventory_id": "id_inventario",
    "staff_id": "id_empleado",

    # Tabla: pelicula (film)
    "film_id": "id_pelicula",
    "title": "titulo",
    "rental_duration": "duracion_alquiler",
    "rental_rate": "tarifa_alquiler",
    "replacement_cost": "costo_reposicion",
    "rating": "clasificacion",

    # Tabla: cliente (customer)
    "customer_id": "id_cliente",
    "first_name": "nombre",
    "last_name": "apellido",
    "email": "email",
    "active": "activo",
    "store_id": "id_tienda",

    # Tabla: inventario (inventory)
    "inventory_id": "id_inventario",

    # Tabla: categoria (category)
    "category_id": "id_categoria",
    "name": "nombre",

    # Tabla: pelicula_categoria (film_category)
    # Comparte id_pelicula e id_categoria
}