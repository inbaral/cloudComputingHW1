import json
from database import write_data
from datetime import datetime
import uuid

def lambda_handler(event, context):
    if 'queryStringParameters' not in event or 'plate' not in event['queryStringParameters'] or 'parkingLot' not in event['queryStringParameters']:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': "Missing required query parameters. Must contain 'plate' and 'parkingLot'."})
        }

    plate = event['queryStringParameters']['plate']
    parking_lot = event['queryStringParameters']['parkingLot']

    ticket_id = str(uuid.uuid4())
    entry_time = datetime.now().isoformat()

    data = {
        'ticketId': ticket_id,
        'plate': plate,
        'parkingLot': parking_lot,
        'entryTime': entry_time
    }

    print(f"Entry recorded: {data}")
    write_data(data)

    return {
        'statusCode': 200,
        'body': json.dumps({'ticketId': ticket_id})
    }
