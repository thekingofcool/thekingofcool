import requests
import json
import time
import os

# 替换为你的 Strava API 客户端 ID 和客户端密钥
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")


def refresh_access_token():
    """Refresh the Strava access token"""
    url = "https://www.strava.com/oauth/token"
    
    # Check if environment variables exist
    if not all([CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN]):
        raise ValueError("Missing required environment variables. Please check CLIENT_ID, CLIENT_SECRET, and REFRESH_TOKEN")
    
    payload = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'refresh_token': REFRESH_TOKEN,
        'grant_type': 'refresh_token'
    }
    
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        tokens = response.json()
        return tokens['access_token'], tokens['refresh_token']
    
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        print(f"Response content: {response.text if 'response' in locals() else 'No response'}")
        raise Exception(f"Error refreshing access token. Status code: {response.status_code if 'response' in locals() else 'No response'}")


def get_strava_stats(access_token):
    url = "https://www.strava.com/api/v3/athlete"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Error fetching data from Strava API: {response.status_code}")

def get_strava_activities(access_token):
    url = "https://www.strava.com/api/v3/athlete/activities"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    params = {
        "per_page": 200,
        "page": 1
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Error fetching activities from Strava API: {response.status_code}")


# Add this function before the update_readme function
def format_time(seconds):
    """Convert seconds to HH:MM:SS format"""
    if seconds is None:
        return "N/A"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    remaining_seconds = int(seconds % 60)
    
    return f"{hours:02d}:{minutes:02d}:{remaining_seconds:02d}"


def update_readme(stats, activities):
    readme_path = "README.md"
    with open(readme_path, "r") as file:
        readme_content = file.read()

    # 计算当前年度总距离
    current_year = time.localtime().tm_year
    total_distance_current_year = sum(activity['distance'] for activity in activities if activity['start_date'].startswith(str(current_year)))

    # 获取 PB 信息
    marathon_pb = min((activity['elapsed_time'] for activity in activities if activity['type'] == 'Run' and activity['distance'] >= 42195), default=None)
    half_marathon_pb = min((activity['elapsed_time'] for activity in activities if activity['type'] == 'Run' and activity['distance'] >= 21097.5), default=None)
    ten_k_pb = min((activity['elapsed_time'] for activity in activities if activity['type'] == 'Run' and activity['distance'] >= 10000), default=None)
    five_k_pb = min((activity['elapsed_time'] for activity in activities if activity['type'] == 'Run' and activity['distance'] >= 5000), default=None)

    # 更新 README 内容
    new_content = f"""
    ## Strava Statistics

    - Username: {stats['username']}
    - Total Distance (Current Year): {total_distance_current_year / 1000:.2f} km
    - Marathon PB: {format_time(marathon_pb)}
    - Half-Marathon PB: {format_time(half_marathon_pb)}
    - 10K PB: {format_time(ten_k_pb)}
    - 5K PB: {format_time(five_k_pb)}
    """
    print(new_content)
    with open(readme_path, "w") as file:
        file.write(readme_content + new_content)

if __name__ == "__main__":
    access_token, refresh_token = refresh_access_token()
    stats = get_strava_stats(access_token)
    activities = get_strava_activities(access_token)
    update_readme(stats, activities)
