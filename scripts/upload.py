import boto3
from botocore.exceptions import NoCredentialsError

ACCESS_KEY = ""
SECRET_KEY = ""


def file_upload(local_file, s3_bucket, s3_file) -> bool:
    """
    This function accesses the s3 storage bucket and places a new file
    there for access later.
    :param local_file:
    :param s3_bucket:
    :param s3_file:
    :return:
    """
    s3 = boto3.client(aws_acces_key_id=ACCESS_KEY, aws_secret_key_id=SECRET_KEY)

    try:
        s3.upload_file(local_file, s3_bucket, s3_file)
        print("Upload Successful")
        return True
    except FileNotFoundError:
        print("File Not Found")
        return False
    except FileExistsError:
        print("File may not exist")
        return False
    except NoCredentialsError:
        print("No login credentials found")
        return False