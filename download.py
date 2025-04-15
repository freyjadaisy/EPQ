# Standard library imports for file operations, timing, and system functions
import json
import os
import sys
import time

# Set up paths to ensure we can import the YARS package regardless of where the script is executed from
current_dir = os.path.dirname(os.path.abspath(__file__))  # Get the directory containing this script
project_root = os.path.dirname(current_dir)               # Move up one level to project root
src_path = os.path.join(project_root, "src")              # Path to the src directory
sys.path.append(src_path)                                 # Add src directory to Python's path
 
# Import the Reddit scraping library (YARS = Yet Another Reddit Scraper)
# This allows us to fetch Reddit content without using the official API
from YARS.src.yars.yars import YARS
from YARS.src.yars.utils import display_results, download_image

def extract_all_comment_text(comments):
    """
    Recursively extract text from all comments and their replies.
    
    This function traverses through the nested comment structure that Reddit uses,
    where comments can have replies, and those replies can have further replies.
    
    Parameters:
    - comments: A list of comment dictionaries, potentially containing nested replies
    
    Returns:
    - A single string with all comment text, with comments separated by double newlines
    """
    all_text = []  # Initialize empty list to collect comment texts
    
    for comment in comments:
        if isinstance(comment, dict):  # Ensure we're working with a valid comment dict
            # Extract the comment's main text content
            body = comment.get('body', '')
            if body:
                all_text.append(body)  # Add this comment's text to our collection
            
            # Recursively process any replies to this comment
            replies = comment.get('replies', [])
            if replies:
                # Recursively extract text from nested replies and add to our collection
                all_text.append(extract_all_comment_text(replies))
    
    # Join all collected comment texts with double newlines to separate distinct comments
    # Filter out any None or empty strings first
    return "\n\n".join(filter(None, all_text))

def scrape_subreddit(subreddit_name, limit=100, save_interval=10):
    """
    Scrape posts and comments from a specified subreddit and save them to a JSON file.
    
    This function performs the main data collection workflow:
    1. Creates or loads an existing JSON file for the subreddit
    2. Fetches posts from the subreddit
    3. Processes each post to extract details and comments
    4. Saves data periodically to prevent data loss
    
    Parameters:
    - subreddit_name: Name of the subreddit to scrape (without the 'r/' prefix)
    - limit: Maximum number of posts to fetch (default 100)
    - save_interval: How often to save progress (default every 10 posts)
    """
    # Initialize the scraper
    miner = YARS()
    # Construct filename for storing results
    filename = f"{subreddit_name}_posts.json"
    
    # --- Resume From Existing File (if available) ---
    # This allows the script to pick up where it left off if interrupted
    posts_data = []  # Will hold all the post data we collect
    processed_permalinks = set()  # Track which posts we've already processed
    
    if os.path.exists(filename):
        try:
            # Try to load existing data file
            with open(filename, 'r', encoding='utf-8') as f:
                posts_data = json.load(f)
                # Create a set of permalinks we've already processed
                processed_permalinks = {post.get('permalink', '') for post in posts_data}
                print(f"Resuming from existing file with {len(posts_data)} posts already processed.")
        except Exception as e:
            # Handle any errors when loading the file
            print(f"Error loading existing file: {e}")
            print("Starting fresh...")
    
    # --- Fetch Posts from Subreddit ---
    print(f"Fetching {limit} posts from r/{subreddit_name}...")
    # Get posts from the subreddit (using top posts from past year for relevance)
    subreddit_posts = miner.fetch_subreddit_posts(
        subreddit_name, 
        limit=limit,
        category="top",     # Options: hot, new, top, rising
        time_filter="year"  # Options: hour, day, week, month, year, all
    )
    
    # --- Process Each Post ---
    for i, post in enumerate(subreddit_posts, 1):
        permalink = post.get("permalink", "")  # Unique identifier for the post
        
        # Skip posts we've already processed (when resuming)
        if permalink in processed_permalinks:
            print(f"Skipping already processed post {i}/{len(subreddit_posts)}...")
            continue
        
        try:
            print(f"Processing post {i}/{len(subreddit_posts)}...")
            # Fetch detailed information about the post, including all comments
            post_details = miner.scrape_post_details(permalink)
            
            # --- Extract Relevant Post Information ---
            post_data = {
                "title": post.get("title", ""),  # Post title
                "body": post_details.get("body", ""),  # Post content/description
                "score": post.get("score", 0),  # Upvote score
                "url": post.get("url", ""),  # External URL (if any)
                "created_utc": post.get("created_utc", ""),  # Post creation timestamp
                "author": post.get("author", ""),  # Username of poster
                "permalink": permalink,  # Reddit permalink (for tracking and referencing)
                "comments": post_details.get("comments", []),  # Full comment data structure
                "all_comment_text": extract_all_comment_text(post_details.get("comments", []))  # All comments as one string
            }
            
            # Add this post to our collection and mark it as processed
            posts_data.append(post_data)
            processed_permalinks.add(permalink)
            
            # --- Save Progress Periodically ---
            # This prevents data loss if the script is interrupted
            if i % save_interval == 0:
                save_to_file(posts_data, filename)
                print(f"Saved progress: {len(posts_data)} posts")
                
        except Exception as e:
            # Handle any errors that occur while processing a specific post
            print(f"Error processing post {i}: {e}")
            # Save what we have so far to prevent total data loss
            save_to_file(posts_data, filename)
            print(f"Saved {len(posts_data)} posts to {filename} before error")
            # Add a small delay to prevent hammering the server if something's wrong
            time.sleep(1)
    
    # --- Final Save ---
    save_to_file(posts_data, filename)
    print(f"Successfully saved {len(posts_data)} posts to {filename}")
    
def save_to_file(data, filename):
    """
    Helper function to save data to a JSON file.
    
    Parameters:
    - data: The data to save (typically a list of post dictionaries)
    - filename: Name of the file to save to
    """
    # Write the data as formatted JSON
    # ensure_ascii=False allows for proper saving of non-ASCII characters (like emojis)
    # indent=2 creates a nicely formatted, human-readable JSON file
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# Only execute the following code if this script is run directly (not imported)
if __name__ == "__main__":
    # Get subreddit name from command line argument or use default
    # Example usage: python download.py anxiety
    #   This would scrape r/anxiety
    subreddit_name = sys.argv[1] if len(sys.argv) > 1 else "gardening"
    
    # Start the scraping process
    scrape_subreddit(subreddit_name)
