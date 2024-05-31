import boto3
import json
from botocore.exceptions import ClientError

s3_client = boto3.client('s3')
s3_resource = boto3.resource("s3")

BUCKET_NAME = 'my-bucket-1054f5c'
DB_FILE_KEY = 'database.json'

def read_data(ticket_id):
    try:
        response = s3_client.get_object(Bucket=BUCKET_NAME, Key=DB_FILE_KEY)
        db = json.loads(response['Body'].read())
        return db.get(ticket_id, 404)

    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            return 404
        else:
            raise

def write_data(data):
    try:
        # Try to get the existing database object
        try:
            response = s3_client.get_object(Bucket=BUCKET_NAME, Key=DB_FILE_KEY)
            db = json.loads(response['Body'].read())
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                print("No existing DB file, creating a new one.")
                db = {}
            else:
                print(f"Unexpected S3 client error: {e}")
                raise

        db[data["ticketId"]] = data
        s3_client.put_object(Bucket=BUCKET_NAME, Key=DB_FILE_KEY, Body=json.dumps(db))
        print("Data written successfully.")

    except Exception as e:
        print(f"Error writing data: {e}")
        raise


def delete_data(ticket_id):
    try:
        response = s3_client.get_object(Bucket=BUCKET_NAME, Key=DB_FILE_KEY)
        db = json.loads(response['Body'].read())

        db.pop(ticket_id, None)
        s3_client.put_object(Bucket=BUCKET_NAME, Key=DB_FILE_KEY, Body=json.dumps(db))

    except Exception as e:
        raise
