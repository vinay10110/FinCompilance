import requests

backend_url = "https://fincompilance.onrender.com/vectorize"
frontend_origin = "https://fin-compilance.vercel.app"

# Simulate a preflight OPTIONS request
options_response = requests.options(
    backend_url,
    headers={
        "Origin": frontend_origin,
        "Access-Control-Request-Method": "POST"
    }
)

print("----- OPTIONS Response -----")
print("Status:", options_response.status_code)
print("Headers:")
for k, v in options_response.headers.items():
    print(f"{k}: {v}")


# Simulate a normal GET request with Origin
get_response = requests.get(
    backend_url,
    headers={"Origin": frontend_origin}
)

print("\n----- GET Response -----")
print("Status:", get_response.status_code)
print("Headers:")
for k, v in get_response.headers.items():
    print(f"{k}: {v}")
