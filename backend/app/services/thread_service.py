from app.services.ingest_service import load_emails

def get_threads():

    emails = load_emails()

    threads = {}

    for email in emails:

        thread_id = email["thread_id"]

        if thread_id not in threads:
            threads[thread_id] = []

        threads[thread_id].append(email)

    return threads