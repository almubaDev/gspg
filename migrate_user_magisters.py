import os
import django
import logging

# Configurar entorno Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connection
from users.models import CustomUser
from gspg.models import Magister

def migrate_user_magisters():
    """
    Migra los datos de la relación ForeignKey antigua a la nueva relación ManyToMany
    """
    # Configurar logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    logger.info("Iniciando migración de datos de usuarios-magisteres")
    
    try:
        # Verificar si existe información en la tabla temporal de migración
        # Esto solo funcionará si la migración guardó la información en una tabla temporal
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM django_migrations WHERE app='users' AND name='0003_remove_customuser_magister_and_more'")
            if cursor.fetchone():
                logger.info("Migración encontrada, intentando recuperar datos")
                
                # Intentar ver si podemos recuperar la información de la tabla de usuarios
                try:
                    # Consultar directamente la tabla para obtener el mapeo usuario-magister anterior
                    cursor.execute("""
                        SELECT u.id, u.email, m.id 
                        FROM 
                            (SELECT * FROM users_customuser_old) u
                            LEFT JOIN gspg_magister m ON u.magister_id = m.id
                        WHERE 
                            u.magister_id IS NOT NULL
                    """)
                    user_magister_mappings = cursor.fetchall()
                    
                    if user_magister_mappings:
                        count = 0
                        for user_id, user_email, magister_id in user_magister_mappings:
                            try:
                                user = CustomUser.objects.get(id=user_id)
                                magister = Magister.objects.get(id=magister_id)
                                
                                # Añadir a magisteres y establecer como activo
                                user.magisteres.add(magister)
                                user.active_magister = magister
                                user.save()
                                
                                logger.info(f"Usuario {user_email} actualizado con magister {magister.name}")
                                count += 1
                            except (CustomUser.DoesNotExist, Magister.DoesNotExist) as e:
                                logger.error(f"Error al actualizar usuario {user_email}: {str(e)}")
                        
                        logger.info(f"Migración completada: {count} usuarios actualizados con enfoque 1")
                    else:
                        logger.warning("No se encontraron mapeos de usuario-magister en la tabla antigua")
                except Exception as e:
                    logger.error(f"Error al intentar recuperar datos: {str(e)}")
                    
                    # Enfoque alternativo: buscar en la base de datos directamente
                    logger.info("Intentando enfoque alternativo...")
                    
                    # Si hay una tabla de respaldo creada durante la migración
                    try:
                        cursor.execute("SELECT id, email FROM users_customuser")
                        users = cursor.fetchall()
                        
                        # Obtener el campo magister_id si existe
                        cursor.execute("PRAGMA table_info(users_customuser)")
                        columns = cursor.fetchall()
                        has_magister = any(col[1] == 'magister_id' for col in columns)
                        
                        if has_magister:
                            count = 0
                            for user_id, user_email in users:
                                cursor.execute("SELECT magister_id FROM users_customuser WHERE id = %s", [user_id])
                                result = cursor.fetchone()
                                if result and result[0]:
                                    magister_id = result[0]
                                    try:
                                        user = CustomUser.objects.get(id=user_id)
                                        magister = Magister.objects.get(id=magister_id)
                                        
                                        user.magisteres.add(magister)
                                        user.active_magister = magister
                                        user.save()
                                        
                                        count += 1
                                        logger.info(f"Usuario {user_email} actualizado con magister {magister.name}")
                                    except (CustomUser.DoesNotExist, Magister.DoesNotExist) as e:
                                        logger.error(f"Error al actualizar usuario {user_email}: {str(e)}")
                            
                            logger.info(f"Migración completada: {count} usuarios actualizados con enfoque 2")
                    except Exception as e:
                        logger.error(f"Error en enfoque alternativo: {str(e)}")
            else:
                logger.warning("No se encontró la migración necesaria")
    
    except Exception as e:
        logger.error(f"Error en la migración: {str(e)}")
    
    # Enfoque manual como último recurso
    logger.info("Iniciando recorrido manual de usuarios")
    users = CustomUser.objects.all()
    count = 0
    
    # Preguntar al usuario para cada usuario sin magisteres asignados
    for user in users:
        if not user.magisteres.exists():
            logger.info(f"Usuario: {user.email} (ID: {user.id})")
            magister_input = input(f"Ingresa el ID del magister para {user.email} (o 'skip' para omitir): ")
            
            if magister_input.lower() != 'skip':
                try:
                    magister_id = int(magister_input)
                    magister = Magister.objects.get(id=magister_id)
                    
                    user.magisteres.add(magister)
                    user.active_magister = magister
                    user.save()
                    
                    logger.info(f"Usuario {user.email} actualizado con magister {magister.name}")
                    count += 1
                except (ValueError, Magister.DoesNotExist) as e:
                    logger.error(f"Error al asignar magister: {str(e)}")
    
    logger.info(f"Migración manual completada: {count} usuarios actualizados")
    
    # Resumen final
    total_users = CustomUser.objects.count()
    users_with_magisteres = CustomUser.objects.filter(magisteres__isnull=False).distinct().count()
    users_with_active = CustomUser.objects.filter(active_magister__isnull=False).count()
    
    logger.info(f"Resumen final:")
    logger.info(f"Total de usuarios: {total_users}")
    logger.info(f"Usuarios con magisteres: {users_with_magisteres}")
    logger.info(f"Usuarios con magister activo: {users_with_active}")
    logger.info(f"Usuarios sin magisteres: {total_users - users_with_magisteres}")

if __name__ == "__main__":
    migrate_user_magisters()