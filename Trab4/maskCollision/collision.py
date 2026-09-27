def singleton(class_):
    instances = { }
    def getinstance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)	
        return instances[class_]
    return getinstance

@singleton
class Collider ():
    def lidar_colisao(self, o1, o2):
        o1.lidar_colisao(o2)

    def lidar_pato(self, pato, outro):
        outro.lidar_pato(pato)

    def lidar_cursor(self, cursor, outro):
        outro.lidar_cursor(cursor)

    def colisao_pato_cursor (self, pato, cursor):
        x = cursor.coord[0] + cursor.sprite.get_rect().center[0] - pato.sprite.get_rect().center[0]
        y = cursor.coord[1] + cursor.sprite.get_rect().center[1] - pato.sprite.get_rect().center[1]
        pato.coord = (x,y)