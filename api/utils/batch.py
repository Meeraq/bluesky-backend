import requests
import environ
env = environ.Env()

def add_contact_in_wati(user_type, name, phone):
    try:
        wati_api_endpoint = env("WATI_API_ENDPOINT")
        wati_authorization = env("WATI_AUTHORIZATION")
        wati_api_url = f"{wati_api_endpoint}/api/v1/addContact/{phone}"
        headers = {
            "content-type": "text/json",
            "Authorization": wati_authorization,
        }
        payload = {
            "customParams": [
                {
                    "name": "user_type",
                    "value": user_type,
                },
            ],
            "name": name,
        }
        response = requests.post(wati_api_url, headers=headers, json=payload)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        print(response.json())
        return response.json()
    except Exception as e:
        pass

