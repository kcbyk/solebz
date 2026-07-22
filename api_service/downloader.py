import requests
import os

def download_file_to_disk(url: str, output_path: str, progress_callback=None):
    proxies = {
        "http": "socks5h://127.0.0.1:1055",
        "https": "socks5h://127.0.0.1:1055",
    }
    response = requests.get(url, stream=True, proxies=proxies)
    response.raise_for_status()
    total_size = int(response.headers.get('content-length', 0))
    
    downloaded = 0
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if progress_callback:
                    progress_callback(downloaded, total_size)
    return output_path
