import network
import time
import socket
import urequests


SSID = "Wokwi-GUEST"
PASSWORD = ""

def connect_to_wifi():
    print("Connecting to WiFi", end="")
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    while not wlan.isconnected():
        print(".", end="")
        time.sleep(0.1)
    print(" Connected!")
    print("IP Address:", wlan.ifconfig()[0])

def fetch_temperature(lat, lon):
    api_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    print("Fetching temperature from:", api_url)
    response = urequests.get(api_url, timeout=5)
    data = response.json()
    response.close()
    return data["current_weather"]["temperature"]

def start_server():
    addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
    server_socket = socket.socket()
    server_socket.bind(addr)
    server_socket.listen(1)
    print("Server running on http://localhost:9080")

    while True:
        client_socket, client_addr = server_socket.accept()
        print(f"Client connected: {client_addr}")
        request = client_socket.recv(1024).decode("utf-8")
        print("Request received:", request)
        try:
            if "GET" in request:
                _, query = request.split("?", 1)
                query = query.split(" ")[0]
                params = dict(param.split("=") for param in query.split("&"))
                latitude = params.get("latitude")
                longitude = params.get("longitude")

                if latitude and longitude:
                    temperature = fetch_temperature(latitude, longitude)
                    response_headers = (
                        "HTTP/1.1 200 OK\n"
                        "Content-Type: application/json\n"
                        "Access-Control-Allow-Origin: *\n"
                        "Connection: close\n\n"
                    )
                    response_body = f"{{\"temperature\": {temperature}}}"
                    response = response_headers + response_body
                else:
                    response = (
                        "HTTP/1.1 400 Bad Request\n"
                        "Content-Type: text/plain\n"
                        "Access-Control-Allow-Origin: *\n"
                        "Connection: close\n\n"
                        "Missing latitude or longitude"
                    )
            else:
                response = (
                    "HTTP/1.1 400 Bad Request\n"
                    "Content-Type: text/plain\n"
                    "Access-Control-Allow-Origin: *\n"
                    "Connection: close\n\n"
                    "Invalid Request"
                )
        except Exception as e:
            response = (
                "HTTP/1.1 500 Internal Server Error\n"
                "Content-Type: text/plain\n"
                "Access-Control-Allow-Origin: *\n"
                "Connection: close\n\n"
                f"{str(e)}"
            )
        client_socket.send(response.encode("utf-8"))
        client_socket.close()

connect_to_wifi()
start_server()
