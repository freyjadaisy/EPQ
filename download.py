import json
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_path = os.path.join(project_root, "src")
sys.path.append(src_path)
 
from YARS.src.yars.yars import YARS
from YARS.src.yars.utils import display_results, download_image

def scrape_subreddit(subreddit_name, limit=100):
    miner = YARS()
    
    # Fetch posts from the subreddit
    print(f"Fetching {limit} posts from r/{subreddit_name}...")
    subreddit_posts = miner.fetch_subreddit_posts(subreddit_name, limit=limit, category="top", time_filter="week")
    
    # Create a list to store post data
    posts_data = []
    
    # Process each post
    for i, post in enumerate(subreddit_posts, 1):
        print(f"Processing post {i}/{len(subreddit_posts)}...")
        permalink = post["permalink"]
        post_details = miner.scrape_post_details(permalink)
        
        # Extract relevant information
        post_data = {
            "title": post.get("title", ""),
            "body": post_details.get("body", ""),
            "score": post.get("score", 0),
            "url": post.get("url", ""),
            "created_utc": post.get("created_utc", ""),
            "author": post.get("author", "")
        }
        posts_data.append(post_data)
    
    # Save to file
    filename = f"{subreddit_name}_posts.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(posts_data, f, indent=2, ensure_ascii=False)
    
    print(f"Successfully saved {len(posts_data)} posts to {filename}")

if __name__ == "__main__":
    # Get subreddit name from command line argument or use default
    subreddit_name = sys.argv[1] if len(sys.argv) > 1 else "gardening"
    scrape_subreddit(subreddit_name)
