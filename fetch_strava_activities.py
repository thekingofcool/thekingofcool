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
        response.raise_for_status()
        
        tokens = response.json()
        return tokens['access_token'], tokens['refresh_token']
    
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        print(f"Response content: {response.text if 'response' in locals() else 'No response'}")
        raise Exception(f"Error refreshing access token. Status code: {response.status_code if 'response' in locals() else 'No response'}")


def get_strava_stats(access_token):
    url = "https://www.strava.com/api/v3/athlete"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Error fetching data from Strava API: {response.status_code}")


def get_strava_activities(access_token):
    url = "https://www.strava.com/api/v3/athlete/activities"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"per_page": 200, "page": 1}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Error fetching activities from Strava API: {response.status_code}")


def format_time(seconds):
    """Convert seconds to HH:MM:SS format"""
    if seconds is None:
        return "N/A"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    remaining_seconds = int(seconds % 60)
    
    return f"{hours:02d}:{minutes:02d}:{remaining_seconds:02d}"


def calculate_normalized_time(elapsed_time, actual_distance, target_distance):
    """Calculate normalized time based on actual distance"""
    if elapsed_time is None or actual_distance == 0:
        return None
    return (elapsed_time * target_distance) / actual_distance


def update_readme(stats, activities):
    readme_path = "README.md"
    
    if not os.path.exists(readme_path):
        base_content = """# My Strava Stats
This README is automatically updated with my latest Strava statistics.
"""
    else:
        with open(readme_path, "r", encoding='utf-8') as file:
            content = file.read()
            base_content = content.split("## Strava Statistics")[0].strip()

    current_year = time.localtime().tm_year
    total_distance_current_year = sum(activity['distance'] for activity in activities 
                                    if activity['start_date'].startswith(str(current_year)))

    # Constants for standard distances
    MARATHON_DISTANCE = 42195
    HALF_MARATHON_DISTANCE = 21097.5
    TEN_K_DISTANCE = 10000
    FIVE_K_DISTANCE = 5000

    # Initialize PB variables
    marathon_pb = float('inf')
    half_marathon_pb = float('inf')
    ten_k_pb = float('inf')
    five_k_pb = float('inf')

    # Calculate normalized PBs
    for activity in activities:
        if activity['type'] == 'Run':
            distance = activity['distance']
            elapsed_time = activity['elapsed_time']
            
            if distance >= MARATHON_DISTANCE:
                normalized_time = calculate_normalized_time(elapsed_time, distance, MARATHON_DISTANCE)
                marathon_pb = min(marathon_pb, normalized_time) if normalized_time else marathon_pb
            
            if distance >= HALF_MARATHON_DISTANCE:
                normalized_time = calculate_normalized_time(elapsed_time, distance, HALF_MARATHON_DISTANCE)
                half_marathon_pb = min(half_marathon_pb, normalized_time) if normalized_time else half_marathon_pb
            
            if distance >= TEN_K_DISTANCE:
                normalized_time = calculate_normalized_time(elapsed_time, distance, TEN_K_DISTANCE)
                ten_k_pb = min(ten_k_pb, normalized_time) if normalized_time else ten_k_pb
            
            if distance >= FIVE_K_DISTANCE:
                normalized_time = calculate_normalized_time(elapsed_time, distance, FIVE_K_DISTANCE)
                five_k_pb = min(five_k_pb, normalized_time) if normalized_time else five_k_pb

    # Convert inf to None for no records
    marathon_pb = None if marathon_pb == float('inf') else int(marathon_pb)
    half_marathon_pb = None if half_marathon_pb == float('inf') else int(half_marathon_pb)
    ten_k_pb = None if ten_k_pb == float('inf') else int(ten_k_pb)
    five_k_pb = None if five_k_pb == float('inf') else int(five_k_pb)

    strava_content = f"""

## Strava Statistics

- Username: {stats.get('username', 'N/A')}
- Total Distance ({current_year}): {total_distance_current_year / 1000:.2f} km
- Marathon PB: {format_time(marathon_pb)}
- Half-Marathon PB: {format_time(half_marathon_pb)}
- 10K PB: {format_time(ten_k_pb)}
- 5K PB: {format_time(five_k_pb)}

*Last Updated: {time.strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    full_content = f"{base_content}\n{strava_content}"
    with open(readme_path, "w", encoding='utf-8') as file:
        file.write(full_content)
    
    print("README.md has been updated successfully!")


if __name__ == "__main__":
    try:
        access_token, refresh_token = refresh_access_token()
        stats = get_strava_stats(access_token)
        activities = get_strava_activities(access_token)
        update_readme(stats, activities)
        print("Successfully updated Strava statistics!")
    except Exception as e:
        print(f"Error occurred: {e}")
        raise
