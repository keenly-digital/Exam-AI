def remove_duplicate_questions(json_data):
    """Remove duplicate questions from all topics in the JSON data.
    Handles dynamic topic keys (topic0, topic1, etc.) and maintains question uniqueness across all topics.
    """
    if "topics" not in json_data:
        raise ValueError("Input JSON must have a 'topics' key.")

    seen_questions = set()
    # Local function for fast normalization
    def normalize(s): return s.strip().lower()

    for topic_key, topic_data in json_data["topics"].items():
        cleaned_questions = []
        for question in topic_data["questions"]:
            q_text_norm = normalize(question["question"])
            if q_text_norm not in seen_questions:
                seen_questions.add(q_text_norm)
                cleaned_questions.append(question)
            else:
                print(f"Removing duplicate question from {topic_key}: "
                      f"Q{question.get('question_number', '')} - {question['question'][:50]}...")
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
