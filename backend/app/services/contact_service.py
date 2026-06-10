from app.services.ingest_service import load_emails


def get_contacts():

    emails = load_emails()

    contacts = {}

    for email in emails:

        sender = email["sender"]

        if sender not in contacts:

            contacts[sender] = {
                "email": sender,
                "message_count": 0,
                "threads": set()
            }

        contacts[sender]["message_count"] += 1
        contacts[sender]["threads"].add(email["thread_id"])

    result = []

    for contact in contacts.values():

        result.append({
            "email": contact["email"],
            "message_count": contact["message_count"],
            "thread_count": len(contact["threads"])
        })

    return result