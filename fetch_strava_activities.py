import requests
import json
import time
import os

# 替换为你的 Strava API 客户端 ID 和客户端密钥
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")

def refresh_access_token():
    url = "https://www.strava.com/oauth/token"
    payload = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'refresh_token': REFRESH_TOKEN,
        'grant_type': 'refresh_token'
    }
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        tokens = response.json()
        return tokens['access_token'], tokens['refresh_token']
    else:
        raise Exception(f"Error refreshing access token: {response.status_code}")

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

def format_time(seconds):
    if seconds is None:
        return "N/A"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{hours:02}:{minutes:02}:{seconds:02}"

def update_readme(stats, activities):
    readme_path = "README.md"

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

    with open(readme_path, "w") as file:
        file.write(new_content)

if __name__ == "__main__":
    access_token, refresh_token = refresh_access_token()
    stats = get_strava_stats(access_token)
    activities = get_strava_activities(access_token)
    update_readme(stats, activities)
