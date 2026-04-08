# database.py
import mysql.connector
import pandas as pd

def conectar():
    conexion = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="Alumnos_DB"
    )
    return conexion


def obtenerusuarios(username):
    conn = conectar()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT u.id_usuario, u.nombre_usuario, u.contraseña, u.rol,
               u.carrera,
               e.id_estudiante, e.nombre AS nombre_estudiante,
               e.edad, e.carrera AS carrera_estudiante,
               e.nota1, e.nota2, e.nota3,
               ROUND((e.nota1 + e.nota2 + e.nota3)/3, 2) AS promedio
        FROM usuarios u
        LEFT JOIN estudiantes e ON u.id_estudiante = e.id_estudiante
        WHERE u.nombre_usuario = %s
    """, (username,))
    usuario = cursor.fetchone()
    cursor.close()
    conn.close()
    return usuario


def obtenerestudiantes():
    conn = conectar()
    df = pd.read_sql("SELECT * FROM estudiantes", conn)
    conn.close()
    return df


def estudiante_existe(nombre, carrera, edad, cursor):
    cursor.execute("""
        SELECT COUNT(*) FROM estudiantes
        WHERE LOWER(nombre) = LOWER(%s)
          AND LOWER(carrera) = LOWER(%s)
          AND edad = %s
    """, (nombre.strip(), carrera.strip(), int(edad)))
    return cursor.fetchone()[0] > 0


def insertarestudiante(datos):
    conn = conectar()
    cursor = conn.cursor()
    if estudiante_existe(datos["nombre"], datos["carrera"], datos["edad"], cursor):
        cursor.close()
        conn.close()
        raise ValueError("Ya existe un estudiante con ese nombre, carrera y edad.")
    cursor.execute("""
        INSERT INTO estudiantes (nombre, edad, carrera, nota1, nota2, nota3)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (datos["nombre"], datos["edad"], datos["carrera"],
          datos["nota1"], datos["nota2"], datos["nota3"]))
    conn.commit()
    cursor.close()
    conn.close()


def buscar_estudiantes(nombre):
    conn = conectar()
    cursor = conn.cursor(dictionary=True)
    if nombre.strip():
        cursor.execute("""
            SELECT * FROM estudiantes
            WHERE LOWER(nombre) LIKE LOWER(%s)
            ORDER BY nombre
        """, (f"%{nombre.strip()}%",))
    else:
        cursor.execute("SELECT * FROM estudiantes ORDER BY nombre")
    resultado = cursor.fetchall()
    cursor.close()
    conn.close()
    return resultado


def obtener_estudiantes_por_carrera(carrera):
    conn = conectar()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id_estudiante, nombre, edad, carrera, nota1, nota2, nota3,
               ROUND((nota1 + nota2 + nota3)/3, 2) AS promedio
        FROM estudiantes
        WHERE LOWER(carrera) = LOWER(%s)
        ORDER BY nombre
    """, (carrera,))
    resultado = cursor.fetchall()
    cursor.close()
    conn.close()
    return resultado


def editar_estudiante(datos):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE estudiantes
        SET nombre = %s, edad = %s, carrera = %s,
            nota1 = %s, nota2 = %s, nota3 = %s
        WHERE id_estudiante = %s
    """, (
        datos["nombre"], datos["edad"], datos["carrera"],
        datos["nota1"], datos["nota2"], datos["nota3"],
        datos["id_estudiante"]
    ))
    conn.commit()
    filas = cursor.rowcount
    cursor.close()
    conn.close()
    if filas == 0:
        raise ValueError("No se encontró el estudiante con ese ID.")


def eliminar_estudiante(id_estudiante):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM estudiantes WHERE id_estudiante = %s", (id_estudiante,))
    conn.commit()
    filas = cursor.rowcount
    cursor.close()
    conn.close()
    if filas == 0:
        raise ValueError("No se encontró el estudiante con ese ID.")


def obtener_top_estudiantes(limite=10):
    conn = conectar()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT nombre, carrera, nota1, nota2, nota3,
               ROUND((nota1 + nota2 + nota3) / 3, 2) AS promedio
        FROM estudiantes
        ORDER BY promedio DESC
        LIMIT %s
    """, (limite,))
    resultado = cursor.fetchall()
    cursor.close()
    conn.close()
    return resultado


# ── HISTORIAL ─────────────────────────────────────────────────────────────────
def obtener_historial(id_estudiante):
    conn = conectar()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT nota1, nota2, nota3, promedio,
               DATE_FORMAT(fecha, '%%d/%%m/%%Y %%H:%%i') AS fecha_fmt
        FROM historial_notas
        WHERE id_estudiante = %s
        ORDER BY fecha DESC
    """, (id_estudiante,))
    resultado = cursor.fetchall()
    cursor.close()
    conn.close()
    for r in resultado:
        r['nota1']    = float(r['nota1'])
        r['nota2']    = float(r['nota2'])
        r['nota3']    = float(r['nota3'])
        r['promedio'] = float(r['promedio'])
    return resultado


# ── STATS CARRERA ─────────────────────────────────────────────────────────────
def obtener_stats_carrera(carrera):
    conn = conectar()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT
            COUNT(*)                                               AS total,
            ROUND(AVG((nota1+nota2+nota3)/3), 2)                  AS promedio_carrera,
            ROUND(MAX((nota1+nota2+nota3)/3), 2)                  AS mejor_promedio,
            ROUND(MIN((nota1+nota2+nota3)/3), 2)                  AS peor_promedio,
            SUM(CASE WHEN (nota1+nota2+nota3)/3 >= 3.0 THEN 1 ELSE 0 END) AS aprobados,
            SUM(CASE WHEN (nota1+nota2+nota3)/3 <  3.0 THEN 1 ELSE 0 END) AS reprobados
        FROM estudiantes
        WHERE LOWER(carrera) = LOWER(%s)
    """, (carrera,))
    stats = cursor.fetchone()
    cursor.close()
    conn.close()
    for k in ['promedio_carrera', 'mejor_promedio', 'peor_promedio']:
        if stats and stats[k] is not None:
            stats[k] = float(stats[k])
    return stats


# ── POSICIÓN EN CARRERA ───────────────────────────────────────────────────────
def obtener_posicion_carrera(id_estudiante, carrera):
    conn = conectar()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT posicion FROM (
            SELECT id_estudiante,
                   RANK() OVER (ORDER BY (nota1+nota2+nota3)/3 DESC) AS posicion
            FROM estudiantes
            WHERE LOWER(carrera) = LOWER(%s)
        ) ranking
        WHERE id_estudiante = %s
    """, (carrera, id_estudiante))
    resultado = cursor.fetchone()
    cursor.close()
    conn.close()
    return resultado['posicion'] if resultado else None


# ── INSERTAR MASIVO ───────────────────────────────────────────────────────────
def insertar_masivo(df_raw):
    resultado = {"insertados": 0, "duplicados": 0, "vacios": 0, "invalidos": 0, "errores": []}
    columnas_requeridas = ['nombre', 'edad', 'carrera', 'nota1', 'nota2', 'nota3']

    df = df_raw.copy()
    df.columns = [c.strip().lower() for c in df.columns]

    faltantes = [c for c in columnas_requeridas if c not in df.columns]
    if faltantes:
        raise ValueError(f"Columnas faltantes en el Excel: {', '.join(faltantes)}")

    df = df[columnas_requeridas]
    antes = len(df)
    df = df.dropna(how='all').dropna(subset=columnas_requeridas)
    resultado["vacios"] += antes - len(df)

    df['nombre']  = df['nombre'].astype(str).str.strip().str.title()
    df['carrera'] = df['carrera'].astype(str).str.strip().str.title()

    for col in ['edad', 'nota1', 'nota2', 'nota3']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    antes = len(df)
    df = df.dropna(subset=['edad', 'nota1', 'nota2', 'nota3'])
    resultado["invalidos"] += antes - len(df)

    mask_edad = (df['edad'] >= 15) & (df['edad'] <= 80)
    for _, row in df[~mask_edad].iterrows():
        resultado["errores"].append(f"Edad inválida ({int(row['edad'])}) — {row['nombre']}")
    resultado["invalidos"] += (~mask_edad).sum()
    df = df[mask_edad]

    for nota in ['nota1', 'nota2', 'nota3']:
        mask = (df[nota] >= 0) & (df[nota] <= 5)
        for _, row in df[~mask].iterrows():
            resultado["errores"].append(f"{nota} inválida ({row[nota]}) — {row['nombre']}")
        resultado["invalidos"] += (~mask).sum()
        df = df[mask]

    antes = len(df)
    df = df.drop_duplicates(subset=['nombre', 'carrera', 'edad'])
    resultado["duplicados"] += antes - len(df)

    if len(df) == 0:
        return resultado

    conn = conectar()
    cursor = conn.cursor()

    for _, row in df.iterrows():
        try:
            if estudiante_existe(row['nombre'], row['carrera'], row['edad'], cursor):
                resultado["duplicados"] += 1
                resultado["errores"].append(
                    f"Ya existe en BD — {row['nombre']} ({row['carrera']}, {int(row['edad'])} años)")
                continue
            cursor.execute("""
                INSERT INTO estudiantes (nombre, edad, carrera, nota1, nota2, nota3)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (row['nombre'], int(row['edad']), row['carrera'],
                  float(row['nota1']), float(row['nota2']), float(row['nota3'])))
            resultado["insertados"] += 1
        except Exception as e:
            resultado["errores"].append(f"Error insertando {row['nombre']}: {str(e)}")
            resultado["invalidos"] += 1

    conn.commit()
    cursor.close()
    conn.close()
    return resultado


# ════════════════════════════════════════════════════════════════════════════
#  FUNCIONES ADMIN
# ════════════════════════════════════════════════════════════════════════════

# ── ESTADÍSTICAS GLOBALES ─────────────────────────────────────────────────────
def obtener_stats_globales():
    """Estadísticas generales para el dashboard admin."""
    conn = conectar()
    cursor = conn.cursor(dictionary=True)

    # Stats de estudiantes
    cursor.execute("""
        SELECT
            COUNT(*)                                               AS total_estudiantes,
            ROUND(AVG((nota1+nota2+nota3)/3), 2)                  AS promedio_global,
            SUM(CASE WHEN (nota1+nota2+nota3)/3 >= 3.0 THEN 1 ELSE 0 END) AS aprobados,
            SUM(CASE WHEN (nota1+nota2+nota3)/3 <  3.0 THEN 1 ELSE 0 END) AS reprobados,
            COUNT(DISTINCT carrera)                                AS total_carreras
        FROM estudiantes
    """)
    stats = cursor.fetchone()

    # Stats por carrera
    cursor.execute("""
        SELECT carrera,
               COUNT(*) AS total,
               ROUND(AVG((nota1+nota2+nota3)/3), 2) AS promedio,
               SUM(CASE WHEN (nota1+nota2+nota3)/3 < 3.0 THEN 1 ELSE 0 END) AS reprobados
        FROM estudiantes
        GROUP BY carrera
        ORDER BY promedio DESC
    """)
    por_carrera = cursor.fetchall()

    # Total usuarios por rol
    cursor.execute("""
        SELECT rol, COUNT(*) AS total
        FROM usuarios
        GROUP BY rol
    """)
    usuarios_rol = cursor.fetchall()

    cursor.close()
    conn.close()

    # Convertir Decimal a float
    for k in ['promedio_global']:
        if stats and stats[k] is not None:
            stats[k] = float(stats[k])
    for r in por_carrera:
        r['promedio']   = float(r['promedio'])   if r['promedio']   else 0
        r['reprobados'] = int(r['reprobados'])    if r['reprobados'] else 0

    return {
        "stats":       stats,
        "por_carrera": por_carrera,
        "usuarios_rol": usuarios_rol,
    }


# ── GESTIÓN DE USUARIOS ───────────────────────────────────────────────────────
def obtener_todos_usuarios():
    """Devuelve todos los usuarios para el panel de gestión."""
    conn = conectar()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id_usuario, nombre_usuario, rol, carrera,
               id_estudiante
        FROM usuarios
        ORDER BY rol, nombre_usuario
    """)
    resultado = cursor.fetchall()
    cursor.close()
    conn.close()
    return resultado


def crear_usuario(datos):
    """Crea un nuevo usuario. datos: nombre_usuario, contraseña, rol, carrera, id_estudiante."""
    conn = conectar()
    cursor = conn.cursor()
    # Verificar que no exista
    cursor.execute("SELECT COUNT(*) FROM usuarios WHERE nombre_usuario = %s",
                   (datos["nombre_usuario"],))
    if cursor.fetchone()[0] > 0:
        cursor.close()
        conn.close()
        raise ValueError("Ya existe un usuario con ese nombre.")
    cursor.execute("""
        INSERT INTO usuarios (nombre_usuario, contraseña, rol, carrera, id_estudiante)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        datos["nombre_usuario"],
        datos["contraseña"],
        datos["rol"],
        datos.get("carrera") or None,
        datos.get("id_estudiante") or None,
    ))
    conn.commit()
    cursor.close()
    conn.close()


def editar_usuario(datos):
    """Edita un usuario existente por id_usuario."""
    conn = conectar()
    cursor = conn.cursor()
    # Si viene contraseña nueva la actualizamos, si no la dejamos igual
    if datos.get("contraseña"):
        cursor.execute("""
            UPDATE usuarios
            SET nombre_usuario = %s, contraseña = %s, rol = %s,
                carrera = %s, id_estudiante = %s
            WHERE id_usuario = %s
        """, (
            datos["nombre_usuario"], datos["contraseña"], datos["rol"],
            datos.get("carrera") or None, datos.get("id_estudiante") or None,
            datos["id_usuario"],
        ))
    else:
        cursor.execute("""
            UPDATE usuarios
            SET nombre_usuario = %s, rol = %s,
                carrera = %s, id_estudiante = %s
            WHERE id_usuario = %s
        """, (
            datos["nombre_usuario"], datos["rol"],
            datos.get("carrera") or None, datos.get("id_estudiante") or None,
            datos["id_usuario"],
        ))
    conn.commit()
    filas = cursor.rowcount
    cursor.close()
    conn.close()
    if filas == 0:
        raise ValueError("No se encontró el usuario.")


def eliminar_usuario(id_usuario):
    """Elimina un usuario por id_usuario."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM usuarios WHERE id_usuario = %s", (id_usuario,))
    conn.commit()
    filas = cursor.rowcount
    cursor.close()
    conn.close()
    if filas == 0:
        raise ValueError("No se encontró el usuario.")


# ── LOG DE ACTIVIDAD ──────────────────────────────────────────────────────────
def registrar_log(usuario, accion, detalle=""):
    """Inserta un registro en el log de actividad."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO log_actividad (usuario, accion, detalle)
        VALUES (%s, %s, %s)
    """, (usuario, accion, detalle))
    conn.commit()
    cursor.close()
    conn.close()


def obtener_log(limite=100):
    conn = conectar()
    cursor = conn.cursor(dictionary=True)

    query = f"""
        SELECT usuario, accion, detalle,
               DATE_FORMAT(fecha, '%%d/%%m/%%Y %%H:%%i:%%s') AS fecha_fmt
        FROM log_actividad
        ORDER BY fecha DESC
        LIMIT {int(limite)}
    """

    cursor.execute(query)
    resultado = cursor.fetchall()
    cursor.close()
    conn.close()
    return resultado


# ── ALERTAS — carreras con alto porcentaje de reprobados ─────────────────────
def obtener_alertas():
    """
    Devuelve carreras donde más del 30% de estudiantes está reprobando.
    Umbral configurable cambiando el 0.30 abajo.
    """
    conn = conectar()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT carrera,
               COUNT(*) AS total,
               SUM(CASE WHEN (nota1+nota2+nota3)/3 < 3.0 THEN 1 ELSE 0 END) AS reprobados,
               ROUND(
                   SUM(CASE WHEN (nota1+nota2+nota3)/3 < 3.0 THEN 1 ELSE 0 END)
                   / COUNT(*) * 100, 1
               ) AS pct_reprobados
        FROM estudiantes
        GROUP BY carrera
        HAVING pct_reprobados >= 30
        ORDER BY pct_reprobados DESC
    """)
    alertas = cursor.fetchall()
    cursor.close()
    conn.close()
    for a in alertas:
        a['reprobados']     = int(a['reprobados'])
        a['pct_reprobados'] = float(a['pct_reprobados'])
    return alertas


if __name__ == "__main__":
    conn = conectar()
    print("conexion exitosa")
    conn.close()