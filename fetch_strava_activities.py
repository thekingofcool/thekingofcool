import requests
import time
import os

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
    ONE_MILE_DISTANCE = 1609.34
    ONE_K_DISTANCE = 1000

    # Initialize PB variables and their dates
    marathon_pb = float('inf')
    marathon_pb_date = None
    half_marathon_pb = float('inf')
    half_marathon_pb_date = None
    ten_k_pb = float('inf')
    ten_k_pb_date = None
    five_k_pb = float('inf')
    five_k_pb_date = None
    one_mile_pb = float('inf')
    one_mile_pb_date = None
    one_k_pb = float('inf')
    one_k_pb_date = None

    # Calculate normalized PBs and record PB dates
    for activity in activities:
        if activity['type'] == 'Run':
            distance = activity['distance']
            elapsed_time = activity['elapsed_time']
            activity_date = activity.get('start_date_local', activity['start_date'])  # Prefer local date if available

            if distance >= MARATHON_DISTANCE:
                normalized_time = calculate_normalized_time(elapsed_time, distance, MARATHON_DISTANCE)
                if normalized_time and normalized_time < marathon_pb:
                    marathon_pb = normalized_time
                    marathon_pb_date = activity_date

            if distance >= HALF_MARATHON_DISTANCE:
                normalized_time = calculate_normalized_time(elapsed_time, distance, HALF_MARATHON_DISTANCE)
                if normalized_time and normalized_time < half_marathon_pb:
                    half_marathon_pb = normalized_time
                    half_marathon_pb_date = activity_date

            if distance >= TEN_K_DISTANCE:
                normalized_time = calculate_normalized_time(elapsed_time, distance, TEN_K_DISTANCE)
                if normalized_time and normalized_time < ten_k_pb:
                    ten_k_pb = normalized_time
                    ten_k_pb_date = activity_date

            if distance >= FIVE_K_DISTANCE:
                normalized_time = calculate_normalized_time(elapsed_time, distance, FIVE_K_DISTANCE)
                if normalized_time and normalized_time < five_k_pb:
                    five_k_pb = normalized_time
                    five_k_pb_date = activity_date

            if distance >= ONE_MILE_DISTANCE:
                normalized_time = calculate_normalized_time(elapsed_time, distance, ONE_MILE_DISTANCE)
                if normalized_time and normalized_time < one_mile_pb:
                    one_mile_pb = normalized_time
                    one_mile_pb_date = activity_date

            if distance >= ONE_K_DISTANCE:
                normalized_time = calculate_normalized_time(elapsed_time, distance, ONE_K_DISTANCE)
                if normalized_time and normalized_time < one_k_pb:
                    one_k_pb = normalized_time
                    one_k_pb_date = activity_date

    # Convert inf to None for no records, and format PB dates
    def pb_result(pb, pb_date):
        if pb == float('inf'):
            return "N/A"
        date_str = pb_date[:10] if pb_date else ""
        return f"{format_time(int(pb))} ({date_str})"

    # Format UTC+8 time
    utc8_time = time.gmtime(time.time() + 8 * 3600)
    last_updated_str = time.strftime('%Y-%m-%d %H:%M:%S', utc8_time)

    strava_content = f"""
## Strava Statistics
- Username: {stats.get('username', 'N/A')}
- Total Distance ({current_year}): {total_distance_current_year / 1000:.2f} km
- Marathon PB: {pb_result(marathon_pb, marathon_pb_date)}
- Half-Marathon PB: {pb_result(half_marathon_pb, half_marathon_pb_date)}
- 10K PB: {pb_result(ten_k_pb, ten_k_pb_date)}
- 5K PB: {pb_result(five_k_pb, five_k_pb_date)}
- 1 Mile PB: {pb_result(one_mile_pb, one_mile_pb_date)}
- 1K PB: {pb_result(one_k_pb, one_k_pb_date)}

*Last Updated: {last_updated_str}*
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
