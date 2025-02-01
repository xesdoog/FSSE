import base64
import json
from Crypto.Cipher import AES

aes_key  = b'\xa7\xca\x9f3f\xd8\x92\xc2\xf0\xbe\xf4\x174\x1c\xa9q\xb6\x9a\xe9\xf7\xba\xcc\xcf\xfc\xf4<b\xd1\xd7\xd0!\xf9' # AES-256 (32 bytes)
init_vec = b'tu89geji340t89u2' # AES block size (16 bytes)


def decrypt_sav(base64_str: str):
    """Decrypts a Base64-encoded .sav file and returns the content as JSON."""

    base64_bytes = base64.b64decode(base64_str)
    aes_cipher   = AES.new(aes_key, AES.MODE_CBC, init_vec)
    plain_bytes  = aes_cipher.decrypt(base64_bytes)
    pad_length   = plain_bytes[-1]
    plain_bytes  = plain_bytes[:-pad_length]
    json_string  = plain_bytes.decode("utf-8")

    try:
        return json.loads(json_string)
    except json.JSONDecodeError as e:
        raise ValueError("Decrypted file does not contain valid JSON: " + str(e))


def encrypt_sav(json_data: object):
    """Encrypts a JSON object into a Base64-encoded .sav file."""
    json_string  = json.dumps(json_data, indent = 4)
    plain_bytes  = json_string.encode("utf-8")
    pad_length   = AES.block_size - (len(plain_bytes) % AES.block_size)
    plain_bytes  += bytes([pad_length]) * pad_length
    aes_cipher   = AES.new(aes_key, AES.MODE_CBC, init_vec)
    cipher_bytes = aes_cipher.encrypt(plain_bytes)

    return base64.b64encode(cipher_bytes).decode("utf-8")


def read_save_file(path: str):
    """Reads Fallout Shelter's Vault*.sav files, decrypts the content and returns it as JSON."""
    with open(path, "r") as f:
        base64_string = f.read().strip()
        return decrypt_sav(base64_string)


def write_save_file(path: str, json_data: object):
    if not path:
        path = './Vault1.sav'

    with open(path, "w") as f:
        base64_data = encrypt_sav(json_data)
        f.write(base64_data)
        f.flush()
        f.close()

def get_lunchbox_count(lunchboxes_by_type: list, type: int):
    count = 0
    for entry in lunchboxes_by_type:
        if entry == type:
            count += 1

    return count


def save_to_json(data, path: str):
    try:
        if path.endswith(".sav"):
            json_path = path.replace(".sav", ".json")
        json_object = json.dumps(data, indent = 4)
        with open(json_path, 'w') as f:
            f.write(json_object)
            f.flush()
            f.close()
    except Exception as e:
        print("Error:", e)


def update_lunchbox_count(vault: list, type: int, count: int):
    lunchboxes_by_type: list = vault["LunchBoxesByType"]
    if count > get_lunchbox_count(lunchboxes_by_type, type):
        lunchboxes_by_type.extend([type])
    elif count < get_lunchbox_count(lunchboxes_by_type, type):
        for _ in range(get_lunchbox_count(lunchboxes_by_type, type) - count):
            if type in lunchboxes_by_type:
                lunchboxes_by_type.remove(type)
    vault["LunchBoxesCount"] = len(lunchboxes_by_type)


def get_dweller_names(dwellers_list: list):
    dweller_names = []
    for entry in dwellers_list:
        full_name = entry["name"] + " " + entry["lastName"]
        dweller_names.append(full_name)
    
    return dweller_names
