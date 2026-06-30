def generate_and_save_token():
    random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    token_code = f"cz_{random_suffix}"
    expiry_time = int((time.time() + (10 * 60)) * 1000)
    created_time = int(time.time() * 1000)
    token_data = {"expiry": expiry_time, "created": created_time}
    
    # تأكد من الرابط ينتهي بـ /cz_active_tokens/{token_code}.json
    url = f"{FIREBASE_DB_URL}cz_active_tokens/{token_code}.json"
    response = requests.put(url, json=token_data)
    
    if response.status_code == 200:
        return token_code
    return None
