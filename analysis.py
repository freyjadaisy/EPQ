import json
import re
import sys
import os
import csv
from collections import Counter
import numpy as np
from scipy.stats import chi2_contingency

def analyze_posts(file_prefix, results, baseline_ratio=None):
    """
    Analyze a JSON file of Reddit posts to extract and analyze anxiety-related word usage.
    
    Parameters:
    - file_prefix: The prefix for the JSON filename (e.g., 'anxiety' for 'anxiety_posts.json')
    - results: A dictionary to store the analysis results
    - baseline_ratio: The expected ratio of anxiety words (from AskReddit or default)
    
    Returns:
    - True if analysis was successful, False otherwise
    """
    # Construct the complete filename from the provided prefix
    filename = f"{file_prefix}_posts.json"
    
    try:
        # Read the JSON file containing Reddit posts
        with open(filename, 'r') as f:
            data = json.load(f)
        
        # Combine all text from post title, body and comments into a single string
        # This creates a corpus of text for the entire subreddit
        all_text = ""
        for post in data:
            title = post.get("title", "")  # Post title
            body = post.get("body", "")    # Post content
            all_comment_text = post.get("all_comment_text", "")  # All comments combined
            
            # Concatenate with spaces to create one large text corpus
            all_text += " " + title + " " + body + " " + all_comment_text
        
        # Tokenize the text into individual words:
        # - Convert to lowercase to treat "Anxiety" and "anxiety" as the same word
        # - Remove punctuation and keep only word characters
        # - \b ensures we capture whole words only (not partial matches)
        words = re.findall(r'\b\w+\b', all_text.lower())
        
        # Count the frequency of each word in the corpus
        word_counts = Counter(words)
        
        # Create a sorted list of word frequencies, filtering out words that appear only once
        # This helps focus on more meaningful patterns rather than one-off mentions
        sorted_words = [(word, count) for word, count in word_counts.most_common() if count > 1]
        
        # Run specialized analysis to detect anxiety-related words in the corpus
        anxiety_stats = analyze_anxiety_words(words)
        
        # Calculate the ratio of anxiety words to total words (convert percentage to decimal)
        current_ratio = anxiety_stats['percentage_of_all_words'] / 100
        
        # Add all analysis results to the results dictionary for this subreddit
        results[file_prefix] = {
            'total_words': len(words),                        # Total word count in the corpus
            'unique_words': len(word_counts),                 # Number of unique words
            'anxiety_word_count': anxiety_stats['total_anxiety_words'],  # Count of anxiety words
            'unique_anxiety_words': anxiety_stats['unique_anxiety_words'],  # Count of unique anxiety words
            'anxiety_word_percentage': anxiety_stats['percentage_of_all_words'],  # % of words that are anxiety-related
            'anxiety_word_coverage': anxiety_stats['percentage_of_anxiety_list_found'],  # % of anxiety lexicon found
            'word_frequency': sorted_words,                   # List of all words and their frequencies
            'anxiety_word_frequency': anxiety_stats['anxiety_counts'],  # List of anxiety words and frequencies
            'anxiety_word_ratio': current_ratio               # Ratio of anxiety words to total words
        }
        
        # If we have a baseline ratio (from AskReddit or default), perform statistical significance testing
        if baseline_ratio is not None:
            # Chi-square test determines if the observed frequency of anxiety words
            # differs significantly from what would be expected based on the baseline
            chi_square_results = chi_square_test(words, anxiety_stats, expected_ratio=baseline_ratio)
            results[file_prefix].update(chi_square_results)  # Add statistical results to our data
            results[file_prefix]['baseline_source'] = 'askreddit' if baseline_ratio else 'default'
        
        print(f"Analyzed {filename} successfully")
        return True
            
    except FileNotFoundError:
        # Handle case where the JSON file doesn't exist
        print(f"Error: File '{filename}' not found.")
        return False
    except json.JSONDecodeError:
        # Handle case where the file exists but isn't valid JSON
        print(f"Error: '{filename}' is not a valid JSON file.")
        return False
    except Exception as e:
        # Catch any other unexpected errors
        print(f"An error occurred with {filename}: {e}")
        return False

def analyze_anxiety_words(words):
    """
    Identify and count anxiety-related words in a list of words.
    
    Parameters:
    - words: A list of all words in the corpus
    
    Returns:
    - Dictionary containing various anxiety word statistics
    """
    # Comprehensive list of 100 anxiety-related words
    # This lexicon was manually curated to capture various aspects of anxiety:
    # - Emotional states (anxiety, fear, panic)
    # - Physical symptoms (trembling, sweating, nausea)
    # - Treatments (therapy, medication, meditation)
    # - Medical terminology (ssri, diagnosis, psychiatrist)
    # - Coping mechanisms (breathing, grounding, mindfulness)
    anxiety_words = [
        "anxiety", "panic", "stress", "fear", "worry", "nervous", "anxious", "overwhelmed", 
        "dread", "scared", "terror", "phobia", "obsession", "compulsion", "trembling", 
        "shaking", "insomnia", "nausea", "sweating", "breathless", "hyperventilating", 
        "palpitations", "therapy", "medication", "psychiatrist", "psychologist", "counseling", 
        "depression", "trauma", "disorder", "attack", "agoraphobia", "claustrophobia", 
        "social", "ocd", "ptsd", "gad", "overthinking", "catastrophizing", "avoidance", 
        "reassurance", "rumination", "trigger", "coping", "mindfulness", "meditation", 
        "breathing", "xanax", "zoloft", "prozac", "lexapro", "ssri", "benzodiazepine", 
        "klonopin", "valium", "ativan", "buspar", "antidepressant", "symptoms", "diagnosis", 
        "recovery", "relapse", "chest", "tight", "dizzy", "lightheaded", "ibs", "stomach", 
        "tension", "muscle", "headache", "fatigue", "exhaustion", "tired", "irritable", 
        "health", "doctor", "hospital", "er", "emergency", "medicine", "pharmacist", 
        "prescription", "dose", "side-effects", "withdrawal", "dependence", "addiction", 
        "tolerance", "cbt", "exposure", "relaxation", "grounding", "techniques", "self-care", 
        "support", "group", "helpline", "crisis", "mental", "brain", "heart", "racing", "sleep"
    ]
    
    # Initialize counters for tracking anxiety word frequency
    anxiety_counts = Counter()      # Will track each anxiety word and its frequency
    total_anxiety_words = 0         # Running total of all anxiety word occurrences
    total_words = len(words)        # Total number of words in the corpus
    
    # Scan through all words in the corpus
    for word in words:
        # Check if the current word is in our anxiety lexicon
        if word in anxiety_words:
            anxiety_counts[word] += 1  # Increment the count for this specific anxiety word
            total_anxiety_words += 1   # Increment the total anxiety word counter
    
    # Return a comprehensive dictionary of anxiety word statistics
    return {
        # List of anxiety words found, sorted by frequency (most common first)
        'anxiety_counts': sorted(anxiety_counts.items(), key=lambda x: x[1], reverse=True),
        
        # Total number of anxiety words found (including duplicates)
        'total_anxiety_words': total_anxiety_words,
        
        # Number of unique anxiety words found (vocabulary breadth)
        'unique_anxiety_words': len(anxiety_counts),
        
        # Percentage of all words that are anxiety-related (prevalence)
        'percentage_of_all_words': (total_anxiety_words/total_words)*100 if total_words > 0 else 0,
        
        # Percentage of our anxiety lexicon that appears in the corpus (coverage)
        'percentage_of_anxiety_list_found': (len(anxiety_counts)/len(anxiety_words))*100 if anxiety_words else 0
    }

def chi_square_test(words, anxiety_stats, expected_ratio=0.005):
    """
    Perform chi-square test to determine if anxiety words appear
    more frequently than expected by random chance.
    
    The chi-square test compares observed frequencies with expected frequencies
    to determine if the difference is statistically significant or likely due to chance.
    
    Parameters:
    - words: list of all words in the corpus
    - anxiety_stats: dictionary of anxiety word statistics
    - expected_ratio: expected frequency of anxiety words in general text
      (default 0.5% if not provided, but typically uses AskReddit baseline)
    
    Returns:
    - Dictionary with chi-square statistics and interpretation
    """
    try:
        from scipy.stats import chi2_contingency
        
        # Get total counts
        total_words = len(words)
        anxiety_count = anxiety_stats['total_anxiety_words']
        non_anxiety_count = total_words - anxiety_count
        
        # Create observed contingency table [anxiety words, non-anxiety words]
        # This represents the actual distribution in our corpus
        observed = np.array([anxiety_count, non_anxiety_count])
        
        # Expected values based on expected_ratio (from baseline)
        # This represents what we would expect if the null hypothesis were true
        # (that anxiety words appear at the same rate as in the baseline)
        expected = np.array([
            total_words * expected_ratio,            # Expected anxiety words
            total_words * (1 - expected_ratio)       # Expected non-anxiety words
        ])
        
        # Perform chi-square test (we use [observed] and [expected] to create 2x1 tables)
        # This calculates whether the difference between observed and expected
        # is statistically significant
        chi2, p, dof, _ = chi2_contingency([observed, expected])
        
        # Return comprehensive results dictionary
        return {
            # The chi-square statistic - higher values indicate greater deviation from expected
            'chi2_statistic': chi2,
            
            # The p-value - probability that this deviation occurred by chance
            # (lower values indicate stronger evidence against the null hypothesis)
            'chi2_p_value': p,
            
            # Boolean indicating statistical significance at the 0.05 level
            'chi2_significant': p < 0.05,
            
            # The baseline ratio used for comparison
            'expected_anxiety_ratio': expected_ratio,
            
            # How many anxiety words we would expect based on the baseline
            'expected_anxiety_count': expected[0],
            
            # Ratio comparing actual vs expected (effect size)
            # Values above 1.0 indicate more anxiety words than expected
            # Values below 1.0 indicate fewer anxiety words than expected
            'observed_to_expected_ratio': anxiety_count / expected[0] if expected[0] > 0 else float('inf')
        }
    except ImportError:
        # Handle case where scipy is not installed
        print("Warning: scipy not installed. Chi-square test skipped.")
        return {
            'chi2_statistic': None,
            'chi2_p_value': None,
            'chi2_significant': None,
            'expected_anxiety_ratio': expected_ratio,
            'expected_anxiety_count': total_words * expected_ratio,
            'observed_to_expected_ratio': None
        }
    except Exception as e:
        # Handle any other errors in the statistical calculation
        print(f"Error performing chi-square test: {e}")
        return {
            'chi2_statistic': None,
            'chi2_p_value': None,
            'chi2_significant': None,
            'expected_anxiety_ratio': expected_ratio,
            'expected_anxiety_count': None,
            'observed_to_expected_ratio': None
        }

def write_to_csv(results, baseline_source, output_filename="anxiety_analysis_results.csv"):
    """
    Write analysis results to a CSV file.
    
    Parameters:
    - results: Dictionary containing analysis results for each subreddit
    - baseline_source: String describing the source of the baseline ratio
    - output_filename: Name of the CSV file to write
    """
    # Create new CSV file (or overwrite existing)
    with open(output_filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write the header row with column names
        # This defines the structure of our results table
        writer.writerow(['File Prefix', 'Total Words', 'Unique Words', 'Anxiety Words Count', 
                        'Unique Anxiety Words', 'Anxiety Word %', 'Anxiety List Coverage %',
                        'Chi2 Statistic', 'Chi2 P-Value', 'Statistically Significant', 
                        'Expected Anxiety Count', 'Observed/Expected Ratio', 'Baseline Source'])
        
        # Write each subreddit's summary data as a row
        for prefix, data in results.items():
            writer.writerow([
                prefix,                                  # Subreddit name
                data['total_words'],                     # Total word count
                data['unique_words'],                    # Unique word count
                data['anxiety_word_count'],              # Anxiety word count
                data['unique_anxiety_words'],            # Unique anxiety words
                f"{data['anxiety_word_percentage']:.2f}%",  # Anxiety words as percentage
                f"{data['anxiety_word_coverage']:.2f}%",    # Percentage of anxiety lexicon found
                
                # Format chi-square statistic (measure of deviation from expected)
                f"{data.get('chi2_statistic', 'N/A'):.4f}" if data.get('chi2_statistic') is not None else 'N/A',
                
                # Format p-value (probability of observed result under null hypothesis)
                f"{data.get('chi2_p_value', 'N/A'):.6f}" if data.get('chi2_p_value') is not None else 'N/A',
                
                # Simple Yes/No for statistical significance at p < 0.05
                "Yes" if data.get('chi2_significant') else "No",
                
                # Expected number of anxiety words based on baseline
                f"{data.get('expected_anxiety_count', 'N/A'):.2f}" if data.get('expected_anxiety_count') is not None else 'N/A',
                
                # Ratio of observed/expected (effect size measure)
                f"{data.get('observed_to_expected_ratio', 'N/A'):.2f}" if data.get('observed_to_expected_ratio') is not None else 'N/A',
                
                # Source of the baseline (AskReddit or default)
                baseline_source
            ])
        
        # Add separator before detailed word frequency analysis
        writer.writerow([])
        writer.writerow(["Detailed Word Frequency Analysis"])
        writer.writerow([])
        
        # For each analyzed subreddit, include detailed word frequency data
        for prefix, data in results.items():
            # Section header for general word frequencies
            writer.writerow([f"Word frequencies for {prefix}_posts.json:"])
            writer.writerow(['Word', 'Count'])
            
            # Write the top 50 most common words
            for word, count in data['word_frequency'][:50]:
                writer.writerow([word, count])
                
            # Add space before anxiety-specific word frequencies
            writer.writerow([])
            
            # Section header for anxiety word frequencies
            writer.writerow([f"Anxiety-related word frequencies for {prefix}_posts.json:"])
            writer.writerow(['Word', 'Count'])
            
            # Write all detected anxiety words and their counts
            for word, count in data['anxiety_word_frequency']:
                writer.writerow([word, count])
                
            writer.writerow([])  # Add space between subreddits
    
    print(f"Results written to {output_filename}")

def main():
    """
    Main function that orchestrates the entire analysis process:
    1. Processes AskReddit data first (if available) to establish baseline
    2. Analyzes all other subreddit data files
    3. Writes results to CSV
    """
    # Dictionary to store all analysis results
    results = {}
    
    # Check if AskReddit data is available to use as baseline
    askreddit_file = "askreddit_posts.json"
    baseline_ratio = None
    baseline_source = "default (0.5%)"
    
    # Process AskReddit first if available to establish baseline anxiety word ratio
    if os.path.exists(askreddit_file):
        print("Processing AskReddit first to establish baseline ratio...")
        analyze_posts('askreddit', results)
        
        # Extract the anxiety word ratio from AskReddit results to use as baseline
        baseline_ratio = results['askreddit']['anxiety_word_ratio']
        baseline_source = f"askreddit ({baseline_ratio*100:.3f}%)"
        print(f"Using AskReddit baseline ratio: {baseline_ratio*100:.3f}%")
    else:
        # If AskReddit data isn't available, use a default value
        print("AskReddit data not found, using default ratio of 0.5%")
        baseline_ratio = 0.005  # Default fallback (0.5%)
    
    # Find all JSON files matching the pattern '*_posts.json'
    # Exclude AskReddit since we've already processed it
    json_files = [f for f in os.listdir('.') if f.endswith('_posts.json') and f != askreddit_file]
    
    # Exit if no data files are found
    if not json_files and not os.path.exists(askreddit_file):
        print("No JSON files matching '*_posts.json' pattern found in the current directory.")
        return
    
    # Process each JSON file, comparing against the established baseline
    for json_file in json_files:
        # Extract the subreddit name from the filename
        prefix = json_file.replace('_posts.json', '')
        
        # Analyze this subreddit's posts, using the baseline for statistical comparison
        analyze_posts(prefix, results, baseline_ratio)
    
    # Write all results to CSV file
    write_to_csv(results, baseline_source)

# Entry point: Run main() when script is executed directly
if __name__ == "__main__":
    main()
