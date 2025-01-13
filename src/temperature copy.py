import network
import time
import socket
import ssl
import ubinascii
import urequests
import ujson
import ucryptolib

# Wifi + SMTP Config
SSID = "Wokwi-GUEST"
PASSWORD = ""

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
EMAIL_ADDRESS = "david.anghel1@gmail.com"     # Contul Gmail
EMAIL_PASSWORD = "rmcb oolt pbms cotv"        # Parola de aplicație generată (exemplu)
# ----------

# AES Key & IV (16 bytes) la fel ca în webapp
AES_KEY = b"0123456789ABCDEF"
AES_IV  = b"0123456789ABCDEF"

def connect_wifi():
    print("Connecting to WiFi", end="")
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    while not wlan.isconnected():
        print(".", end="")
        time.sleep(0.2)
    print(" Connected!")
    print("IP:", wlan.ifconfig()[0])

def fetch_temperature(lat, lon):
    """Obține temperatura curentă de la API-ul open-meteo."""
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    print("Fetching temperature from:", url)
    r = urequests.get(url, timeout=5)
    data = r.json()
    r.close()
    return data["current_weather"]["temperature"]

def pkcs7_unpad(data):
    padding_len = data[-1]
    if padding_len > 16:
        return data
    return data[:-padding_len]

def pkcs7_pad(data):
    block_size = 16
    pad_len = block_size - (len(data) % block_size)
    return data + bytes([pad_len]) * pad_len

def decrypt_aes_base64(base64_ciphertext):
    raw_ciphertext = ubinascii.a2b_base64(base64_ciphertext)
    cipher = ucryptolib.aes(AES_KEY, 2, AES_IV)  # 2 = CBC
    decrypted = cipher.decrypt(raw_ciphertext)
    return pkcs7_unpad(decrypted)

def encrypt_aes_base64(plaintext_str):
    cipher = ucryptolib.aes(AES_KEY, 2, AES_IV)
    plaintext_bytes = plaintext_str.encode('utf-8')
    padded = pkcs7_pad(plaintext_bytes)
    encrypted = cipher.encrypt(padded)
    return ubinascii.b2a_base64(encrypted).strip()

def unquote(s):
    """Minimal decode %xx -> char, pentru a înlocui urllib.parse.unquote."""
    result = ""
    i = 0
    while i < len(s):
        c = s[i]
        if c == '%' and i + 2 < len(s):
            hex_val = s[i+1:i+3]
            try:
                c = chr(int(hex_val, 16))
                i += 3
            except:
                result += '%'
                i += 1
        else:
            i += 1
        result += c
    return result

def send_email_smtp(sender, pwd, recipient, subject, body):
    """
    Trimite email prin Gmail SMTP (pe portul 465 SSL).
    E nevoie să ai 'EMAIL_PASSWORD' ca parolă de aplicație.
    """
    msg = (
        "From: {}\r\n".format(sender) +
        "To: {}\r\n".format(recipient) +
        "Subject: {}\r\n\r\n".format(subject) +
        "{}\r\n".format(body)
    )

    addr = socket.getaddrinfo(SMTP_SERVER, SMTP_PORT)[0][-1]
    s = socket.socket()
    s.connect(addr)
    s = ssl.wrap_socket(s)

    def send_cmd(cmd, expect_response=True):
        s.write(cmd.encode('utf-8') + b'\r\n')
        if expect_response:
            resp = s.readline().decode('utf-8').strip()
            return resp

    try:
        # Citește banner
        banner = s.readline().decode()
        # HELO
        send_cmd("HELO raspberry-pi-pico")
        # AUTH
        send_cmd("AUTH LOGIN")
        # user (base64)
        send_cmd(ubinascii.b2a_base64(sender.encode()).decode().strip())
        # pwd (base64)
        send_cmd(ubinascii.b2a_base64(pwd.encode()).decode().strip())
        # MAIL FROM
        send_cmd(f"MAIL FROM: <{sender}>")
        # RCPT TO
        send_cmd(f"RCPT TO: <{recipient}>")
        # DATA
        send_cmd("DATA")
        # Mesaj
        send_cmd(msg + "\r\n.")
        # QUIT
        send_cmd("QUIT", expect_response=False)
        s.close()
        return True
    except Exception as e:
        print("Email sending error:", e)
        s.close()
        return False

def start_server():
    # Ascultăm pe portul 80 (în codul original așa era, chiar dacă log-ul spune 9080)
    addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
    serv = socket.socket()
    serv.bind(addr)
    serv.listen(1)
    print("Server running on http://localhost:9080")  
    # Notă: mesajul afișat e diferit de portul real, dar îl lăsăm ca în codul original.

    while True:
        client_sock, client_addr = serv.accept()
        print(f"Client connected: {client_addr}")

        try:
            request = client_sock.recv(4096).decode("utf-8")
            print("Request received:", request)

            if "GET /?data=" in request:
                # Extragem parametru data
                line = request.split(" ")[1]  # ex: /?data=base64
                param = line.split("?data=")[1].split("&")[0]
                encrypted_data = unquote(param)

                # Decriptăm
                try:
                    decrypted_bytes = decrypt_aes_base64(encrypted_data)
                    dec_str = decrypted_bytes.decode('utf-8')
                    # JSON-ul poate conține: email, threshold, alertEnabled, latitude, longitude
                    payload = ujson.loads(dec_str)

                    # Valorile pot lipsi sau pot fi None. Le extragem cu fallback.
                    email = payload.get("email", None)         # Poate fi None sau string
                    threshold = float(payload.get("threshold", 0))
                    alertEnabled = bool(payload.get("alertEnabled", False))
                    latitude = payload.get("latitude", None)
                    longitude = payload.get("longitude", None)
                except Exception as e:
                    print("Decryption error:", e)
                    email, threshold = None, 0
                    alertEnabled = False
                    latitude, longitude = None, None

                # Verificăm lat & lon
                if latitude and longitude:
                    # Obținem temperatura
                    temperature = fetch_temperature(latitude, longitude)

                    # Implicit, nu trimitem e-mail
                    email_sent = False

                    # Dacă e bifată alerta și există un e-mail
                    # => trimitem doar dacă temp < threshold
                    if alertEnabled and email and (temperature < threshold):
                        subject = "IoT Alert: Temperature too low!"
                        body = f"Alert! Current temperature is {temperature}°C, below threshold {threshold}°C."

                        status = send_email_smtp(
                            EMAIL_ADDRESS,      # Gmail user
                            EMAIL_PASSWORD,     # Gmail app password
                            email,              # destinatar (cel introdus)
                            subject,
                            body
                        )
                        if status:
                            email_sent = True
                            print("Email trimis cu succes")
                        else:
                            print("Eroare la trimiterea email-ului")

                    # Construim răspunsul final
                    resp_obj = {
                        "temperature": temperature,
                        "emailSent": email_sent
                    }
                    resp_json = ujson.dumps(resp_obj)
                    # Criptăm
                    encrypted_resp = encrypt_aes_base64(resp_json).decode("utf-8")

                    headers = (
                        "HTTP/1.1 200 OK\n"
                        "Content-Type: application/json\n"
                        "Access-Control-Allow-Origin: *\n"
                        "Connection: close\n\n"
                    )
                    body = ujson.dumps({ "data": encrypted_resp })
                    response = headers + body
                else:
                    # lipsesc coordonatele, deci nu putem da temperatura
                    response = (
                        "HTTP/1.1 400 Bad Request\n"
                        "Content-Type: text/plain\n"
                        "Access-Control-Allow-Origin: *\n"
                        "Connection: close\n\n"
                        "Missing or invalid params (latitude/longitude required)"
                    )
            else:
                response = (
                    "HTTP/1.1 400 Bad Request\n"
                    "Content-Type: text/plain\n"
                    "Access-Control-Allow-Origin: *\n"
                    "Connection: close\n\n"
                    "Invalid Request"
                )

            client_sock.send(response.encode("utf-8"))
        except Exception as e:
            print("Error processing request:", e)
            err_resp = (
                "HTTP/1.1 500 Internal Server Error\n"
                "Content-Type: text/plain\n"
                "Access-Control-Allow-Origin: *\n"
                "Connection: close\n\n"
                f"Error: {e}"
            )
            client_sock.send(err_resp.encode("utf-8"))
        finally:
            client_sock.close()

# ------------------
connect_wifi()
start_server()
