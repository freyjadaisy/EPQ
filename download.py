import json
import os
import sys
import time

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_path = os.path.join(project_root, "src")
sys.path.append(src_path)
 
from YARS.src.yars.yars import YARS
from YARS.src.yars.utils import display_results, download_image

def extract_all_comment_text(comments):
    """
    Recursively extract text from all comments and their replies
    Returns a single string with all comment text
    """
    all_text = []
    
    for comment in comments:
        if isinstance(comment, dict):
            # Extract the comment body
            body = comment.get('body', '')
            if body:
                all_text.append(body)
            
            # Recursively extract text from replies
            replies = comment.get('replies', [])
            if replies:
                all_text.append(extract_all_comment_text(replies))
    
    return "\n\n".join(filter(None, all_text))

def scrape_subreddit(subreddit_name, limit=100, save_interval=10):
    miner = YARS()
    filename = f"{subreddit_name}_posts.json"
    
    # Check if we have an existing file to resume from
    posts_data = []
    processed_permalinks = set()
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                posts_data = json.load(f)
                processed_permalinks = {post.get('permalink', '') for post in posts_data}
                print(f"Resuming from existing file with {len(posts_data)} posts already processed.")
        except Exception as e:
            print(f"Error loading existing file: {e}")
            print("Starting fresh...")
    
    # Fetch posts from the subreddit
    print(f"Fetching {limit} posts from r/{subreddit_name}...")
    subreddit_posts = miner.fetch_subreddit_posts(subreddit_name, limit=limit, category="top", time_filter="year")
    
    # Process each post
    for i, post in enumerate(subreddit_posts, 1):
        permalink = post.get("permalink", "")
        
        # Skip already processed posts
        if permalink in processed_permalinks:
            print(f"Skipping already processed post {i}/{len(subreddit_posts)}...")
            continue
        
        try:
            print(f"Processing post {i}/{len(subreddit_posts)}...")
            post_details = miner.scrape_post_details(permalink)
            
            # Extract relevant information
            post_data = {
                "title": post.get("title", ""),
                "body": post_details.get("body", ""),
                "score": post.get("score", 0),
                "url": post.get("url", ""),
                "created_utc": post.get("created_utc", ""),
                "author": post.get("author", ""),
                "permalink": permalink,  # Store permalink for tracking
                "all_comment_text": extract_all_comment_text(post_details.get("comments", []))  # Add all comment text as one string
            }
            posts_data.append(post_data)
            processed_permalinks.add(permalink)
            
            # Save periodically
            if i % save_interval == 0:
                save_to_file(posts_data, filename)
                print(f"Saved progress: {len(posts_data)} posts")
                
        except Exception as e:
            print(f"Error processing post {i}: {e}")
            # Save what we have so far
            save_to_file(posts_data, filename)
            print(f"Saved {len(posts_data)} posts to {filename} before error")
            # Optional: add a small delay before continuing
            time.sleep(1)
    
    # Final save
    save_to_file(posts_data, filename)
    print(f"Successfully saved {len(posts_data)} posts to {filename}")
    
def save_to_file(data, filename):
    """Helper function to save data to a file"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    # Get subreddit name from command line argument or use default
    subreddit_name = sys.argv[1] if len(sys.argv) > 1 else "gardening"
    scrape_subreddit(subreddit_name)
