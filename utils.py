from os import path, remove
import datetime


def path_url_exists(path_url):
    """ Método de verificación de ruta. """
    if path.exists(path_url):
        return True
    return False

def remove_picture_profile(profile_name):
    """ Método para eliminar foto de perfil del usuario. """
    path_url = "app/uploads/profile_pictures/" + profile_name
    if path_url_exists(path_url):
        remove(path_url)

def random_name(name_base):
    """ Método para generar un nombre aleatorio. """
    suffix = datetime.datetime.now().strftime("%y%m%d_%H%M%S")
    filename = "_".join([name_base, suffix])
    return filename