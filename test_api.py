import requests

# Example for a well-known location (e.g., Times Square, New York)
test_url = "https://maps.googleapis.com/maps/api/streetview?size=600x300&location=40.758896,-73.985130&key=AIzaSyAes1mHa3VTn9T3hMUNJhlnJ_7DS4XT5so"
response = requests.get(test_url)

if response.status_code == 200:
    with open('test_image.jpg', 'wb') as file:
        file.write(response.content)