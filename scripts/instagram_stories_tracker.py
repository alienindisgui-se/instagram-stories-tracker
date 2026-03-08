#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Instagram Stories Tracker
Tracks Instagram stories using Instapeep API and sends Discord notifications.
"""

import json
import logging
import os
import time
from datetime import date, datetime, timezone
from typing import Dict, List, Optional

import httpx
import cloudscraper
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress HTTP request logging to INFO level, only log errors
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

class InstagramStoriesTracker:
    def __init__(self, config_file: str = "config/instagram_stories_config.json", data_file: str = "data/instagram_stories_history.json", analytics_file: str = "data/instagram_stories_analytics.json", discord_webhook: str = None):
        self.config_file = config_file
        self.data_file = data_file
        self.analytics_file = analytics_file
        self.discord_webhook = discord_webhook or os.getenv("INSTAGRAM_STORIES_DISCORD_WEBHOOK") or os.getenv("INSTAGRAM_TRACKER_DISCORD_WEBHOOK")
        
        # Load usernames
        self.usernames = self._load_usernames()

    def _load_usernames(self) -> list:
        """Load usernames from JSON config file."""
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                return config.get("usernames", [])
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return []

    def _fetch_user_stories(self, scraper, username: str) -> Optional[List[Dict]]:
        """Fetch stories for a user with retry logic."""
        for attempt in range(3):
            try:
                api_url = f"https://instapeep.com/api/stories/{username}"
                response = scraper.get(api_url, timeout=30)
                logger.info(f"API response status: {response.status_code}")

                if response.status_code != 200:
                    if attempt < 2:
                        logger.warning(f"Attempt {attempt + 1} failed for {username}, retrying...")
                        time.sleep(2)
                        continue
                    else:
                        logger.error(f"Failed to fetch data for {username}: HTTP {response.status_code}")
                        return None

                data = response.json()
                stories = data.get('stories', [])
                logger.info(f"Fetched data for {username}: {len(stories)} stories")

                has_stories = data.get('has_stories', True)
                if not has_stories or not stories:
                    logger.info(f"No active stories for {username}.")
                    return []

                return stories

            except Exception as e:
                if attempt < 2:
                    logger.warning(f"Attempt {attempt + 1} failed for {username}: {e}, retrying...")
                    time.sleep(2)
                    continue
                else:
                    logger.error(f"All attempts failed for {username}: {e}")
                    return None

        return None

    def load_history(self) -> Dict:
        """Load previous story history."""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                return {}
        return {}

    def save_history(self, history: Dict) -> None:
        """Save current story history."""
        # Ensure directory exists before saving
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump(history, f, indent=4)

    def load_analytics(self) -> Dict:
        """Load analytics data."""
        if os.path.exists(self.analytics_file):
            try:
                with open(self.analytics_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                return {}
        return {}

    def save_analytics(self, analytics: Dict) -> None:
        """Save analytics data."""
        os.makedirs(os.path.dirname(self.analytics_file), exist_ok=True)
        with open(self.analytics_file, 'w') as f:
            json.dump(analytics, f, indent=4)

    def update_analytics(self, username: str, new_stories_count: int) -> None:
        """Update analytics with new stories count."""
        analytics = self.load_analytics()
        today = date.today().isoformat()
        
        if username not in analytics:
            analytics[username] = {
                'total_stories': 0,
                'daily_counts': {},
                'first_seen': today,
                'last_seen': today
            }
        
        # Update total and daily counts
        analytics[username]['total_stories'] += new_stories_count
        analytics[username]['daily_counts'][today] = analytics[username]['daily_counts'].get(today, 0) + new_stories_count
        analytics[username]['last_seen'] = today
        
        self.save_analytics(analytics)

    def get_user_stats(self, username: str) -> Dict:
        """Get user statistics for embed display."""
        analytics = self.load_analytics()
        
        if username not in analytics:
            return {
                'total_stories': 0,
                'avg_per_day': 0.0,
                'days_tracked': 0
            }
        
        user_data = analytics[username]
        total_stories = user_data['total_stories']
        days_tracked = len(user_data['daily_counts'])
        avg_per_day = total_stories / days_tracked if days_tracked > 0 else 0.0
        
        return {
            'total_stories': total_stories,
            'avg_per_day': round(avg_per_day, 2),
            'days_tracked': days_tracked
        }

    def download_story_media(self, story_url: str, username: str, story_id: str, is_video: bool = False) -> Optional[bytes]:
        """Download story media from Instagram URL."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'Referer': 'https://www.instagram.com/'
            }
            response = httpx.get(story_url, headers=headers, timeout=30, follow_redirects=True)
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.error(f"Failed to download media from {story_url}: {e}")
            return None

    def send_batched_discord_notification(self, username: str, stories: List[Dict]):
        """Send batched notification to Discord with uploaded files and simple embed."""
        if not self.discord_webhook or not stories:
            logger.warning("No webhook or no stories to send.")
            return
        
        # Split stories into chunks of 10 (Discord attachment limit)
        chunk_size = 10
        story_chunks = [stories[i:i + chunk_size] for i in range(0, len(stories), chunk_size)]
        total_chunks = len(story_chunks)
        
        # Get user stats for footer
        stats = self.get_user_stats(username)
        
        # Send each chunk as separate message
        for chunk_idx, story_chunk in enumerate(story_chunks, 1):
            # Download media files for this chunk
            files_data = []
            
            for i, story in enumerate(story_chunk, 1):
                story_id = str(story.get('id', 'N/A'))
                story_url = story.get('url')
                is_video = story.get("media_type") == 2
                
                if story_url:
                    media_bytes = self.download_story_media(story_url, username, story_id, is_video)
                    if media_bytes:
                        # Create filename
                        ext = 'mp4' if is_video else 'jpg'
                        filename = f"{username}_{story_id[:15]}.{ext}"
                        
                        # Check file size (Discord limit is 8MB for regular users)
                        if len(media_bytes) > 8 * 1024 * 1024:  # 8MB
                            logger.warning(f"File too large for Discord upload: {filename} ({len(media_bytes)} bytes)")
                        else:
                            # Determine mimetype
                            mimetype = 'video/mp4' if is_video else 'image/jpeg'
                            files_data.append((f'file{i}', (filename, media_bytes, mimetype)))
            
            # Create simple embed
            story_word = "story" if len(story_chunk) == 1 else "stories"
            story_title = "Story" if len(story_chunk) == 1 else "Stories"
            title_suffix = f" ({chunk_idx}/{total_chunks})" if total_chunks > 1 else ""
            
            embed = {
                "title": f"📸 Instagram New {story_title} from @{username}{title_suffix}",
                "description": f"Found {len(story_chunk)} new {story_word}",
                "color": 5814783,  # Blue color
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "footer": {
                    "text": f"User Report: {stats['total_stories']} total stories | {stats['avg_per_day']} avg/day | {stats['days_tracked']} days tracked"
                }
            }
            
            # Send to Discord
            try:
                payload = {"embeds": [embed]}
                data = {"payload_json": json.dumps(payload)}
                files = {file_data[0]: file_data[1] for file_data in files_data} if files_data else None

                resp = httpx.post(self.discord_webhook, data=data, files=files, timeout=30)

                if resp.status_code not in (200, 204):
                    logger.error(f"Failed to send Discord chunk {chunk_idx}/{total_chunks}: {resp.text}")
                else:
                    uploaded_count = len(files_data)
                    story_word = "story" if len(story_chunk) == 1 else "stories"
                    logger.info(f"Successfully sent Discord chunk {chunk_idx}/{total_chunks} for {username} with {len(story_chunk)} {story_word} ({uploaded_count} files uploaded)")
            except Exception as e:
                logger.error(f"Error sending Discord chunk {chunk_idx}/{total_chunks}: {e}")

    def monitor_stories(self) -> None:
        """Main method to monitor Instagram stories."""
        if not self.discord_webhook:
            logger.warning("No Discord webhook configured, exiting.")
            return

        history = self.load_history()

        # Use cloudscraper with built-in Cloudflare bypass (no proxy needed)
        scraper = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
        )

        logger.info("Using cloudscraper with built-in Cloudflare bypass")

        # Check each user
        for username in self.usernames:
            logger.info(f"Checking {username}...")
            stories = self._fetch_user_stories(scraper, username)

            if stories is None:
                logger.error(f"Failed to fetch data for {username} after all retries")
                continue  # Skip to next user instead of aborting

            user_history = history.get(username, [])
            new_stories = []
            new_ids = []

            for story in stories:
                story_id = str(story["id"])
                if story_id not in user_history:
                    new_stories.append(story)
                    new_ids.append(story_id)

            if new_stories:
                logger.info(f"Found {len(new_stories)} new stories for {username}")
                self.send_batched_discord_notification(username, new_stories)
                self.update_analytics(username, len(new_stories))
            else:
                logger.info(f"No new stories found for {username}")

            history[username] = user_history + new_ids

        self.save_history(history)

def main():
    """Main entry point."""
    monitor = InstagramStoriesTracker()
    monitor.monitor_stories()

if __name__ == "__main__":
    main()