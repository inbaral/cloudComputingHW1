import json
from datetime import datetime
from database import read_data, delete_data
import math

def lambda_handler(event, context):

    if 'queryStringParameters' not in event or 'ticketId' not in event['queryStringParameters']:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': "Missing 'ticketId' query parameter"})
        }

    ticket_id = event['queryStringParameters']['ticketId']
    entry_info = read_data(ticket_id)

    if entry_info == 404:
        return {
            'statusCode': 404,
            'body': json.dumps({'error': "Ticket ID not found"})
        }

    entry_time = datetime.fromisoformat(entry_info['entryTime'])

    # Calculate total parked time in minutes
    exit_time = datetime.now()
    total_time = (exit_time - entry_time).total_seconds() / 60

    # Calculate the charge based on $10 per hour, in 15-minute increments
    charge = math.floor(total_time / 15) * (10 / 4)

    # Remove the object from the data
    delete_data(ticket_id)

    # Return the results
    return {
        'statusCode': 200,
        'body': json.dumps({
            'licensePlate': entry_info['plate'],
            'totalParkedTime': f"{int(total_time)} minutes",
            'parkingLotId': entry_info['parkingLot'],
            'charge': f"${charge:.2f}"
        })
    }