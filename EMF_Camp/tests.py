
"""
import requests

spec = requests.get("https://emfcamp.github.io/camptions/openapi.json", timeout=10).json()

#print(spec["info"])             # title, description, version
#print(spec.get("servers"))      # base URL(s) of the actual API
#print(list(spec["paths"]))      # available endpoints

# servers=none
# spec ['/api/captions/stream/{venue_id}/sse', 
# '/api/captions/history/{venue_id}', '/api/venues', 
# '/api/venues/{venue_id}', '/api/sessions', '/api/sessions/{session_id}', 
# '/api/schedule/now-and-next', '/api/schedule/now-and-next/{venue_id}', '/health']

"""

import requests
import pandas as pd

r = requests.get("https://stages.emf.camp/api/venues", timeout=10)
print(r.json())   # find the venue IDs

r = requests.get("https://stages.emf.camp/api/captions/history/stage-a",
                 params={"limit": 100}, timeout=10)
df = pd.json_normalize(r.json())
