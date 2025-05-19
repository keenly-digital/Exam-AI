def remove_duplicate_questions(json_data):
    """Remove duplicate questions from all topics in the JSON data.
    Handles dynamic topic keys (topic0, topic1, etc.) and maintains question uniqueness across all topics.
    """
    seen_questions = set()
    # breakpoint()
    # Iterate through all topics in the JSON data
    for topic_key, topic_data in json_data["topics"].items():
        # breakpoint()
        cleaned_questions = []
        
        # Process each question in the current topic
        for question in topic_data["questions"]:
            question_text = question["question"].strip().lower()  # Normalize for comparison
            
            if question_text not in seen_questions:
                seen_questions.add(question_text)
                cleaned_questions.append(question)
            else:
                print(f"Removing duplicate question from {topic_key}: "
                      f"Q{question['question_number']} - {question['question'][:50]}...")
        
        # Update the current topic with cleaned questions
        topic_data["questions"] = cleaned_questions
    
    return json_data

# # Load your JSON file
# with open('/Users/dev/Documents/pdf_parser_final/response.json', 'r') as f:
#     data = json.load(f)

# # Process the data
# cleaned_data = remove_duplicate_questions(data)

# # Save the cleaned data back to file
# with open('cleaned_response.json', 'w') as f:
#     json.dump(cleaned_data, f, indent=2)

# print("Duplicate removal complete. Cleaned data saved to cleaned_response.json")