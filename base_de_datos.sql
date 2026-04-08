-- 1. CREAR BASE DE DATOS
CREATE DATABASE Alumnos_DB;
USE Alumnos_DB;
--mysql://root:tdNQJcClPBfxWQrOJkBeeiBYOUiJAqeM@maglev.proxy.rlwy.net:21450/railway
-- 2. CREAR TABLA estudiantes (SIN FK aún)
CREATE TABLE estudiantes(
    id_estudiante INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(40) NOT NULL,
    edad INT NOT NULL,
    carrera VARCHAR(40) NOT NULL,
    nota1 DECIMAL(4,2) NOT NULL,
    nota2 DECIMAL(4,2) NOT NULL,
    nota3 DECIMAL(4,2) NOT NULL
);

-- 3. CREAR TABLA usuarios (SIN FK aún)
CREATE TABLE usuarios(
    id_usuario INT PRIMARY KEY AUTO_INCREMENT,
    nombre_usuario VARCHAR(40) NOT NULL,
    contraseña VARCHAR(225) NOT NULL,
    rol VARCHAR(20) NOT NULL
);

-- 4. INSERTAR USUARIOS (ANTES de las relaciones)
INSERT INTO usuarios (nombre_usuario, contraseña, rol) VALUES
('admin_user', 'admin123', 'admin'),
('estudiante_user', 'estudiante123', 'estudiante'),
('profesor_user', 'profesor123', 'profesor');

-- 5. AGREGAR COLUMNA carrera a usuarios
ALTER TABLE usuarios ADD COLUMN carrera VARCHAR(100);

-- 6. AGREGAR id_estudiante a usuarios (para relación)
ALTER TABLE usuarios ADD COLUMN id_estudiante INT NULL AFTER id_usuario;

-- 7. CREAR FK de usuarios a estudiantes
ALTER TABLE usuarios
ADD CONSTRAINT fk_usuarios_estudiante
FOREIGN KEY (id_estudiante) REFERENCES estudiantes(id_estudiante)
ON DELETE SET NULL
ON UPDATE CASCADE;

-- 8. ÍNDICE ÚNICO para evitar duplicados
ALTER TABLE usuarios
ADD UNIQUE INDEX idx_unique_estudiante (id_estudiante);

-- 9. CREAR TABLA historial_notas
CREATE TABLE historial_notas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_estudiante INT NOT NULL,
    nota1 DECIMAL(3,1) NOT NULL,
    nota2 DECIMAL(3,1) NOT NULL,
    nota3 DECIMAL(3,1) NOT NULL,
    promedio DECIMAL(4,2) NOT NULL,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    modificado_por VARCHAR(100),
    FOREIGN KEY (id_estudiante) REFERENCES estudiantes(id_estudiante)
);

-- 10. TRIGGER para guardar historial al actualizar notas
DELIMITER $$
CREATE TRIGGER guardar_historial
AFTER UPDATE ON estudiantes
FOR EACH ROW
BEGIN
    IF OLD.nota1 != NEW.nota1 OR OLD.nota2 != NEW.nota2 OR OLD.nota3 != NEW.nota3 THEN
        INSERT INTO historial_notas (id_estudiante, nota1, nota2, nota3, promedio)
        VALUES (NEW.id_estudiante, NEW.nota1, NEW.nota2, NEW.nota3,
                ROUND((NEW.nota1 + NEW.nota2 + NEW.nota3) / 3, 2));
    END IF;
END$$
DELIMITER ;

-- 11. CREAR TABLA log_actividad
CREATE TABLE log_actividad (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario VARCHAR(100) NOT NULL,
    accion VARCHAR(255) NOT NULL,
    detalle TEXT,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 12. TRIGGER para log automático al editar estudiantes
DELIMITER $$
CREATE TRIGGER log_editar_estudiante
AFTER UPDATE ON estudiantes
FOR EACH ROW
BEGIN
    INSERT INTO log_actividad (usuario, accion, detalle)
    VALUES ('sistema', 'editar_estudiante',
            CONCAT('ID:', NEW.id_estudiante, ' | ', OLD.nombre,
                   ' | N1:', OLD.nota1, '->', NEW.nota1,
                   ' N2:', OLD.nota2, '->', NEW.nota2,
                   ' N3:', OLD.nota3, '->', NEW.nota3));
END$$
DELIMITER ;

-- 13. VERIFICAR ESTRUCTURA
DESCRIBE usuarios;
DESCRIBE estudiantes;
DESCRIBE historial_notas;
DESCRIBE log_actividad;

-- 14. VER USUARIOS INSERTADOS
SELECT * FROM usuarios;


--DROP DATABASE estudiantes;
