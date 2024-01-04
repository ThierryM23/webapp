
import logging
import boto3
from botocore.exceptions import ClientError
import os
from dotenv import load_dotenv


load_dotenv()
consumer_key = os.getenv('AWS_ACCESS_KEY_ID')
consumer_secret = os.getenv('AWS_SECRET_ACCESS_KEY')


def upload_file(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket
    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_name)

    # Upload the file   \app\static\images\photos\fondo.png
    s3_client = boto3.client('s3',aws_access_key_id=consumer_key,
                  aws_secret_access_key=consumer_secret)
    try:
        s3_client.upload_file(file_name, bucket, object_name, ExtraArgs={'ACL': 'public-read'})       
    except ClientError as e:
        print(e)
        return False
    except FileNotFoundError as f:
        print(f)
    return True

def listar(bucket, directorio=None):
    """
    Args:
        bucket (_type_): bucket to List
        directorio (_type_, optional): directory under the bucket. Defaults to None.
    """
    # Crear una instancia de cliente S3
    s3 = boto3.client('s3',aws_access_key_id=consumer_key,
                  aws_secret_access_key=consumer_secret)
    imagenes = []
    # Nombre del bucket S3 y directorio si hay
    if directorio  is None:
        response = s3.list_objects_v2(Bucket=bucket)
    else:
        response = s3.list_objects_v2(Bucket=bucket, Prefix=directorio)

    for content in response.get('Contents', []):
        print(content['Key'])
        if content['Key'] != directorio +"/" : 
            imagenes.append('https://myappauberge.s3.us-east-2.amazonaws.com/' + content['Key'])
    
    return imagenes


def del_image(bucket, file_key):
    """_summary_

    Args:
        bucket (_type_): Bucket to del
        file_key (_type_): file name and directory of the file to delete

    Returns:
        Boolean: True if delete the file False if not
    """
    # Borrar el archivo
    s3 = boto3.client('s3',aws_access_key_id=consumer_key,
                  aws_secret_access_key=consumer_secret)   
    try:
        s3.delete_object(Bucket=bucket, Key=file_key)       
    except ClientError as e:
        print(e)
        return False
    return True




if __name__ == '__main__':
    # Nombre del archivo local y el nombre que tendría en S3
    filename = 'fondo.png'
    archivo_local = "static/images/photos/{}".format(filename)
    nombre_en_s3 = 'photos/'  + filename
    directorio = None
    directorio = 'photos'
    imagenes = []

    # Nombre del bucket de S3
    nombre_bucket = 'myappauberge'
        
    response = upload_file(archivo_local, nombre_bucket, nombre_en_s3)
    print(response)

    
    # Imprimir la lista de archivos 
    response = listar(nombre_bucket,directorio)
    print(response)




#print(archivo_local)
#print(nombre_en_s3)

#response = upload_file(archivo_local, nombre_bucket, nombre_en_s3)
#print(response)


#asignar el Public_read
#boto3.resource('s3').ObjectAcl(nombre_bucket,nombre_en_s3).put(ACL='public-read')
#s3_resource = boto3.resource('s3')
#acl = s3_resource.ObjectAcl(nombre_bucket, nombre_en_s3)
#print(acl)