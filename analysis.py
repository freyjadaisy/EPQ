import json
import re
import sys
import os
import csv
from collections import Counter

def analyze_posts(file_prefix, results):
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
            
            # Combine and add to all_text
            all_text += " " + title + " " + body
        
        # Tokenize into words (convert to lowercase, remove punctuation)
        words = re.findall(r'\b\w+\b', all_text.lower())
        
        # Count word frequencies
        word_counts = Counter(words)
        
        # Sort by frequency in descending order and filter out words that appear only once
        sorted_words = [(word, count) for word, count in word_counts.most_common() if count > 1]
        
        # Analyze anxiety-related words
        anxiety_stats = analyze_anxiety_words(words)
        
        # Add results to the dictionary
        results[file_prefix] = {
            'total_words': len(words),
            'unique_words': len(word_counts),
            'anxiety_word_count': anxiety_stats['total_anxiety_words'],
            'unique_anxiety_words': anxiety_stats['unique_anxiety_words'],
            'anxiety_word_percentage': anxiety_stats['percentage_of_all_words'],
            'anxiety_word_coverage': anxiety_stats['percentage_of_anxiety_list_found'],
            'word_frequency': sorted_words,
            'anxiety_word_frequency': anxiety_stats['anxiety_counts']
        }
        
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

def write_to_csv(results, output_filename="anxiety_analysis_results.csv"):
    # First, write the summary data
    with open(output_filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write the header
        writer.writerow(['File Prefix', 'Total Words', 'Unique Words', 'Anxiety Words Count', 
                        'Unique Anxiety Words', 'Anxiety Word %', 'Anxiety List Coverage %'])
        
        # Write each file's summary data
        for prefix, data in results.items():
            writer.writerow([
                prefix, 
                data['total_words'],
                data['unique_words'],
                data['anxiety_word_count'],
                data['unique_anxiety_words'],
                f"{data['anxiety_word_percentage']:.2f}%",
                f"{data['anxiety_word_coverage']:.2f}%"
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
    
    # Find all JSON files matching the pattern
    json_files = [f for f in os.listdir('.') if f.endswith('_posts.json')]
    
    if not json_files:
        print("No JSON files matching '*_posts.json' pattern found in the current directory.")
        return
    
    # Process each file
    for json_file in json_files:
        # Extract the prefix (remove _posts.json)
        prefix = json_file.replace('_posts.json', '')
        analyze_posts(prefix, results)
    
    # Write results to CSV
    write_to_csv(results)

if __name__ == "__main__":
    main()
