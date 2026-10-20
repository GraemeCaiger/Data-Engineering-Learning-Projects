import requests
import pandas as pd


Schedule_URL = "https://www.emfcamp.org/schedule/2026.json"

def get_json():
	try:
		response = requests.get(Schedule_URL, timeout=30) # Send a web request to the schedule URL and stop waiting after 30 seconds.
		response.raise_for_status() # Raise an error if the server returned an unsuccessful status code. this would look like 
		return response.json() 		# Read the response body as JSON data and return it to the caller.
	except requests.RequestException as exc: # Catch request-related errors so they do not crash the whole program.
		print(f"Request failed: {exc}") # Show the error message to help explain why the download failed.
		return None



json_data = get_json()
if json_data is not None:
	df = pd.DataFrame(json_data)
	print(df.head())
	print(df.columns)
	print(df.info())