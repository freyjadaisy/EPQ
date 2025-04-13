import json
import re
import sys
import os
import csv
from collections import Counter
import numpy as np
from scipy.stats import chi2_contingency

def analyze_posts(file_prefix, results, baseline_ratio=None):
    # Construct the filename
    filename = f"{file_prefix}_posts.json"
    
    try:
        # Read the JSON file
        with open(filename, 'r') as f:
            data = json.load(f)
        
        # Combine all text from title and body fields
        all_text = ""
        for post in data:
            title = post.get("title", "")
            body = post.get("body", "")
            all_comment_text = post.get("all_comment_text", "")
            
            # Combine and add to all_text
            all_text += " " + title + " " + body + " " + all_comment_text
        
        # Tokenize into words (convert to lowercase, remove punctuation)
        words = re.findall(r'\b\w+\b', all_text.lower())
        
        # Count word frequencies
        word_counts = Counter(words)
        
        # Sort by frequency in descending order and filter out words that appear only once
        sorted_words = [(word, count) for word, count in word_counts.most_common() if count > 1]
        
        # Analyze anxiety-related words
        anxiety_stats = analyze_anxiety_words(words)
        
        # Calculate anxiety word ratio for this subreddit
        current_ratio = anxiety_stats['percentage_of_all_words'] / 100  # Convert from percentage to ratio
        
        # Add results to the dictionary
        results[file_prefix] = {
            'total_words': len(words),
            'unique_words': len(word_counts),
            'anxiety_word_count': anxiety_stats['total_anxiety_words'],
            'unique_anxiety_words': anxiety_stats['unique_anxiety_words'],
            'anxiety_word_percentage': anxiety_stats['percentage_of_all_words'],
            'anxiety_word_coverage': anxiety_stats['percentage_of_anxiety_list_found'],
            'word_frequency': sorted_words,
            'anxiety_word_frequency': anxiety_stats['anxiety_counts'],
            'anxiety_word_ratio': current_ratio
        }
        
        # Perform chi-square test for statistical significance if we have a baseline
        if baseline_ratio is not None:
            chi_square_results = chi_square_test(words, anxiety_stats, expected_ratio=baseline_ratio)
            results[file_prefix].update(chi_square_results)
            results[file_prefix]['baseline_source'] = 'askreddit' if baseline_ratio else 'default'
        
        print(f"Analyzed {filename} successfully")
        return True
            
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        return False
    except json.JSONDecodeError:
        print(f"Error: '{filename}' is not a valid JSON file.")
        return False
    except Exception as e:
        print(f"An error occurred with {filename}: {e}")
        return False

def analyze_anxiety_words(words):
    # List of 100 anxiety-related words
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
    
    # Count anxiety words
    anxiety_counts = Counter()
    total_anxiety_words = 0
    total_words = len(words)
    
    for word in words:
        if word in anxiety_words:
            anxiety_counts[word] += 1
            total_anxiety_words += 1
    
    # Return statistics
    return {
        'anxiety_counts': sorted(anxiety_counts.items(), key=lambda x: x[1], reverse=True),
        'total_anxiety_words': total_anxiety_words,
        'unique_anxiety_words': len(anxiety_counts),
        'percentage_of_all_words': (total_anxiety_words/total_words)*100 if total_words > 0 else 0,
        'percentage_of_anxiety_list_found': (len(anxiety_counts)/len(anxiety_words))*100 if anxiety_words else 0
    }

def chi_square_test(words, anxiety_stats, expected_ratio=0.005):
    """
    Perform chi-square test to determine if anxiety words appear
    more frequently than expected by random chance
    
    Parameters:
    - words: list of all words in the corpus
    - anxiety_stats: dictionary of anxiety word statistics
    - expected_ratio: expected frequency of anxiety words in general text (default 0.5%)
    
    Returns dictionary with chi-square statistics
    """
    try:
        from scipy.stats import chi2_contingency
        
        total_words = len(words)
        anxiety_count = anxiety_stats['total_anxiety_words']
        non_anxiety_count = total_words - anxiety_count
        
        # Create observed contingency table [anxiety words, non-anxiety words]
        observed = np.array([anxiety_count, non_anxiety_count])
        
        # Expected values based on expected_ratio
        expected = np.array([
            total_words * expected_ratio,
            total_words * (1 - expected_ratio)
        ])
        
        # Perform chi-square test (we use [observed] and [expected] to create 2x1 tables)
        chi2, p, dof, _ = chi2_contingency([observed, expected])
        
        return {
            'chi2_statistic': chi2,
            'chi2_p_value': p,
            'chi2_significant': p < 0.05,
            'expected_anxiety_ratio': expected_ratio,
            'expected_anxiety_count': expected[0],
            'observed_to_expected_ratio': anxiety_count / expected[0] if expected[0] > 0 else float('inf')
        }
    except ImportError:
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
    # First, write the summary data
    with open(output_filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write the header with additional statistical columns
        writer.writerow(['File Prefix', 'Total Words', 'Unique Words', 'Anxiety Words Count', 
                        'Unique Anxiety Words', 'Anxiety Word %', 'Anxiety List Coverage %',
                        'Chi2 Statistic', 'Chi2 P-Value', 'Statistically Significant', 
                        'Expected Anxiety Count', 'Observed/Expected Ratio', 'Baseline Source'])
        
        # Write each file's summary data
        for prefix, data in results.items():
            writer.writerow([
                prefix, 
                data['total_words'],
                data['unique_words'],
                data['anxiety_word_count'],
                data['unique_anxiety_words'],
                f"{data['anxiety_word_percentage']:.2f}%",
                f"{data['anxiety_word_coverage']:.2f}%",
                f"{data.get('chi2_statistic', 'N/A'):.4f}" if data.get('chi2_statistic') is not None else 'N/A',
                f"{data.get('chi2_p_value', 'N/A'):.6f}" if data.get('chi2_p_value') is not None else 'N/A',
                "Yes" if data.get('chi2_significant') else "No",
                f"{data.get('expected_anxiety_count', 'N/A'):.2f}" if data.get('expected_anxiety_count') is not None else 'N/A',
                f"{data.get('observed_to_expected_ratio', 'N/A'):.2f}" if data.get('observed_to_expected_ratio') is not None else 'N/A',
                baseline_source
            ])
        
        # Add a blank row for separation
        writer.writerow([])
        writer.writerow(["Detailed Word Frequency Analysis"])
        writer.writerow([])
        
        # For each file, write the detailed word frequency
        for prefix, data in results.items():
            writer.writerow([f"Word frequencies for {prefix}_posts.json:"])
            writer.writerow(['Word', 'Count'])
            
            # Write regular word frequencies
            for word, count in data['word_frequency'][:50]:  # Limit to top 50
                writer.writerow([word, count])
                
            writer.writerow([])
            writer.writerow([f"Anxiety-related word frequencies for {prefix}_posts.json:"])
            writer.writerow(['Word', 'Count'])
            
            # Write anxiety word frequencies
            for word, count in data['anxiety_word_frequency']:
                writer.writerow([word, count])
                
            writer.writerow([])  # Add space between files
    
    print(f"Results written to {output_filename}")

def main():
    results = {}
    
    # Check if askreddit file exists first
    askreddit_file = "askreddit_posts.json"
    baseline_ratio = None
    baseline_source = "default (0.5%)"
    
    # Process askreddit first to establish baseline if it exists
    if os.path.exists(askreddit_file):
        print("Processing AskReddit first to establish baseline ratio...")
        analyze_posts('askreddit', results)
        baseline_ratio = results['askreddit']['anxiety_word_ratio']
        baseline_source = f"askreddit ({baseline_ratio*100:.3f}%)"
        print(f"Using AskReddit baseline ratio: {baseline_ratio*100:.3f}%")
    else:
        print("AskReddit data not found, using default ratio of 0.5%")
        baseline_ratio = 0.005  # Default fallback
    
    # Find all JSON files matching the pattern
    json_files = [f for f in os.listdir('.') if f.endswith('_posts.json') and f != askreddit_file]
    
    if not json_files and not os.path.exists(askreddit_file):
        print("No JSON files matching '*_posts.json' pattern found in the current directory.")
        return
    
    # Process each file using the established baseline
    for json_file in json_files:
        # Extract the prefix (remove _posts.json)
        prefix = json_file.replace('_posts.json', '')
        analyze_posts(prefix, results, baseline_ratio)
    
    # Write results to CSV
    write_to_csv(results, baseline_source)

if __name__ == "__main__":
    main()
