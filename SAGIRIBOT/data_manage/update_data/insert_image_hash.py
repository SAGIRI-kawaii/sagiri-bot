from SAGIRIBOT.basics.aio_mysql_excute import execute_sql


async def insert_image_hash(path: str, image_hash: str, path_class: str) -> None:
    path = path.replace("\\", "\\\\")
    try:
        sql = "insert into ImageHash (dir,imageHash,class) values ('%s','%s','%s')" \
              % \
              (path, image_hash, path_class)
        await execute_sql(sql)
    except Exception:
        pass
