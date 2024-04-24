import requests
import random
import time
import re
import os

from progress.bar import IncrementalBar

def sleep():
    t = 0.01
    t += t * random.uniform(-0.1, 0.1)  # Add some variance
    time.sleep(t)
    
def human_readable_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
    i = 0
    while size_bytes >= 1024 and i < len(suffixes)-1:
        size_bytes /= 1024.0
        i += 1
    f = ('%.2f' % size_bytes).rstrip('0').rstrip('.')
    return '%s %s' % (f, suffixes[i])

def fetch_audio_location(asset_id, place_id, roblox_cookie):
    while True:
        body_array = [{
            "assetId": asset_id,
            "assetType": "Audio",
            "requestId": "0"
        }]

        headers = {
            "User-Agent": "Roblox/WinInet",
            "Content-Type": "application/json",
            "Cookie": f".ROBLOSECURITY={roblox_cookie}",
            "Roblox-Place-Id": place_id,
            "Accept": "*/*",
            "Roblox-Browser-Asset-Request": "false"
        }

        response = requests.post('https://assetdelivery.roblox.com/v2/assets/batch', headers=headers, json=body_array)

        if response.status_code == 200:
            locations = response.json()

            if locations:
                obj = locations[0]
                if obj.get("locations") and obj["locations"][0].get("location"):
                    audio_url = obj["locations"][0]["location"]
                    return audio_url

        # Wait before retrying
        time.sleep(0.5)

def sanitize_filename(name):
    sanitized_name = re.sub(r'[\\/*?"<>|]', '', name)
    sanitized_name = sanitized_name.replace(" ", "_")  # Replace spaces with underscores
    return sanitized_name

def fetch_asset_name(asset_id):
    while True:
        response = requests.get(f"https://economy.roproxy.com/v2/assets/{asset_id}/details")

        if response.status_code == 200:
            asset_info = response.json()
            asset_name = asset_info.get("Name")
            if asset_name:
                return asset_name

        # Wait before retrying
        time.sleep(0.5)
        
def download_all_audio_files(roblox_cookie, place_id, asset_ids):
    for asset_id in asset_ids:
        asset_name = fetch_asset_name(asset_id)  # Fetch the asset name here
        if asset_name:
            sanitized_asset_name = sanitize_filename(asset_name)  # Sanitize the asset name
            audio_url = fetch_audio_location(asset_id, place_id, roblox_cookie) # Fetch the audio url

            if audio_url:
                response = requests.get(audio_url)
                if response.status_code == 200:
                    # Create a folder for downloaded audio files
                    os.makedirs("audio_files", exist_ok=True)

                    # Remove newline characters from the asset name
                    sanitized_asset_name = sanitized_asset_name.replace('\n', '')

                    file_name = sanitized_asset_name
                    file_path = os.path.join("audio_files", file_name + ".ogg")
                    
                    total_size = int(response.headers.get('content-length', 0))
                    downloaded_size = 0
                    
                    bar = IncrementalBar(f"Downloading {sanitized_asset_name}:", max=total_size, suffix='%(percent)d%% [Elapsed: %(elapsed_td)s / Estimated Time: %(eta_td)s]')
                    with open(file_path, "wb") as f:
                        for chunk in response.iter_content(chunk_size=1024):
                            if chunk:
                                f.write(chunk)
                                downloaded_size += len(chunk)
                                bar.next(len(chunk))
                                sleep()
                                
                    print(f"\nDownloaded {sanitized_asset_name}: ({human_readable_size(total_size)})")

    # Display a message after downloading all assets
    print("All audio assets have been downloaded.")
    
if __name__ == "__main__":
    roblox_cookie = input("Enter your Roblox cookie (.ROBLOSECURITY): ")
    place_id = input("Enter the Roblox place ID: ")
    asset_ids = input("Enter the asset IDs separated by commas: ").split(',')
    
    download_all_audio_files(roblox_cookie, place_id, asset_ids)
