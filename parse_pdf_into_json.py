import json
import re
import os
from typing import Dict, List, Union, Pattern, Match, Optional, Tuple

# def load_cleaned_text(file_path):
#     with open(file_path, "r") as f:
#         return f.read()

# def extract_topics(text, topic_pattern, case_study_pattern):
#     topic_matches = list(topic_pattern.finditer(text))
#     case_study_matches = list(case_study_pattern.finditer(text))
    
#     # Return a combination of both matches
#     return topic_matches + case_study_matches

# def extract_case_study_text(text):
#     # Try to extract case study content after the topic/case study header
#     # This works for both "Topic X" and "Case Study: X" formats
#     case_study_match = re.search(r"(?s)(Topic \d+, |Case Study: \d+\n).+?\n(.+?)(?=Question: \d+)", text, re.DOTALL)
#     # case_study_match = re.search(r"Topic \d+:.+?(?=\nQuestion: \d+)", text, re.DOTALL)
#     # breakpoint()
#     if case_study_match:
#         case_study_text = case_study_match.group(2).strip()
#         case_study_text = re.sub(r'Question: \d+.*', '', case_study_text, flags=re.DOTALL)
        
#         # If the case study text is just whitespace or empty, return an empty string
#         if not case_study_text or case_study_text.isspace():
#             return ""
#         return case_study_text
#     return ""

# def clean_question_text(question_text):
#     # Remove option lines that look like "A.    C", "B.    B", etc.
#     cleaned_text = re.sub(r'\n[A-D]\.\s*[A-D]', '', question_text, flags=re.MULTILINE)
    
#     # Additional cleanup to remove any remaining option-like lines
#     cleaned_text = re.sub(r'\n[A-D]\..*', '', cleaned_text, flags=re.MULTILINE)
    
#     return cleaned_text.strip()

# def split_options(options):
#     first_occurrence = {}
#     last_occurrence = {}
#     option_counts = {}  # Track how many times each option appears

#     # First pass: Count occurrences of each option
#     for option in options:
#         key = option.split('.')[0].strip()
#         option_counts[key] = option_counts.get(key, 0) + 1

#     # Second pass: Store first and last occurrences
#     for option in options:
#         key = option.split('.')[0].strip()
        
#         # Store first occurrence if not already present
#         if key not in first_occurrence:
#             first_occurrence[key] = option
        
#         # If the option appears only once, it should be in both lists
#         if option_counts[key] == 1:
#             last_occurrence[key] = option
#         else:
#             # Otherwise, update last occurrence (overwrites previous)
#             last_occurrence[key] = option

#     # Convert dictionaries to lists in order (A, B, C, D)
#     sorted_keys = sorted(first_occurrence.keys())
#     first_list = [first_occurrence[key] for key in sorted_keys]
#     last_list = [last_occurrence[key] for key in sorted_keys]

#     return first_list, last_list
# def add_rest_to_question(question_text, rest_options):
#     # If there are no rest options, return the original question text
#     if not rest_options:
#         return question_text
    
#     # Join the rest options with newline
#     rest_content = "\n".join(rest_options)
#     # breakpoint()
    
#     # Add the rest options to the end of the question text
#     return f"{question_text}\n{rest_content}"

# def extract_questions(text, question_pattern, answer_pattern, explanation_pattern):
#     questions = []
#     for question_match in question_pattern.finditer(text):
#         question_number = question_match.group(1)
#         full_question_text = question_match.group(2).strip()
        
#         # First split the text at "Answer:" to separate options from answer/explanation
#         parts = re.split(r'Answer:', full_question_text, 1)
#         question_with_options = parts[0].strip()
#         answer_explanation_text = "Answer:" + parts[1] if len(parts) > 1 else ""


#         answer_match = answer_pattern.search(answer_explanation_text)
#         if answer_match and answer_match.group(1).strip():
#             answer_text = answer_match.group(1).strip()
            
#             # Remove any commas that might be present
#             answer_text = answer_text.replace(',', '')
            
#             # Check if the answer text contains spaces
#             if ' ' in answer_text:
#                 # Space-separated answers (like "A B C")
#                 answer = [a.strip() for a in answer_text.split() if a.strip() in ['A', 'B', 'C', 'D', 'E', 'F', 'G']]
#             else:
#                 # Concatenated answers (like "ABC")
#                 answer = [letter for letter in answer_text if letter in ['A', 'B', 'C', 'D', 'E', 'F', 'G']]
#         else:
#             # Ensure we have an empty array for no answers
#             answer = []
        
#         # Extract explanation from the separated text
#         explanation_match = explanation_pattern.search(answer_explanation_text)
#         explanation = explanation_match.group(1).strip() if explanation_match else ""
        
#         # The remaining text in question_with_options contains the question and options
#         # Extract options (A to E) with multi-line support
#         options = []
#         # Get each option block (A. through D.)
#         # option_blocks = re.findall(r'([A-D])\.\s+((?:(?!(?:[A-D]\. |\nAnswer:)).)+)', question_with_options, re.DOTALL)
#         option_blocks = re.findall(r'([A-G])\.\s+((?:(?!(?:[A-G]\. |\nAnswer:)).)+)', question_with_options, re.DOTALL)

        
#         for option_letter, option_content in option_blocks:
#             options.append(f"{option_letter}. {option_content.strip()}")
#         # breakpoint()
#         question_text = question_with_options
#         for option_letter, option_content in option_blocks:
#             option_text = f"{option_letter}. {option_content}"
#             question_text = question_text.replace(option_text, "").strip()
#             # question_text = re.sub(rf'\n{option_letter}\.\s*{re.escape(option_text.strip())}', '', question_text, flags=re.MULTILINE)
# # 
        
#         question_text = clean_question_text(question_text)
#         rest_options,final_options = split_options(options)
#         question_text = add_rest_to_question(question_text, rest_options)


#         questions.append({
#             "question_number": question_number,
#             "question": question_text,
#             "options": final_options,
#             "answer": answer,
#             "explanation": explanation
#         })
#     return questions

# def save_to_json(data, output_dir, filename):
#     os.makedirs(output_dir, exist_ok=True)
#     with open(os.path.join(output_dir, filename), "w") as f:
#         json.dump(data, f, indent=4, ensure_ascii=False)

# def main():
#     cleaned_text = load_cleaned_text("extracted_text.txt")
    
#     # Pattern for "Topic X, Name" format
#     topic_pattern = re.compile(r"Topic (\d+), (.+?)\n(.+?)(?=(Topic \d+, |Case Study: \d+|$))", re.DOTALL)
    
#     # Pattern for "Case Study: X" format
#     case_study_pattern = re.compile(r"Case Study: (\d+)\n(.+?)\n(.+?)(?=(Topic \d+, |Case Study: \d+|$))", re.DOTALL)
    
#     question_pattern = re.compile(r"Question: (\d+)\n(.+?)(?=(Question: \d+|Topic \d+, |Case Study: \d+|$))", re.DOTALL)
    
#     answer_pattern = re.compile(r"Answer:\s*([A-G,\s]+)(?=\n|$)")
    
#     # Enhanced explanation pattern
#     explanation_pattern = re.compile(r"Explanation:\s*(.+?)(?=(?:Question: \d+|Topic \d+, |Case Study: \d+|$))", re.DOTALL)

#     all_topics_data = {}
#     topics_found = extract_topics(cleaned_text, topic_pattern, case_study_pattern)

#     if not topics_found:
#         # Process as a single default topic
#         case_study_text = extract_case_study_text(cleaned_text)
#         questions = extract_questions(cleaned_text, question_pattern, answer_pattern, explanation_pattern)
#         all_topics_data["topic0"] = {
#             "topic_name": "",
#             "case_study": case_study_text,
#             "questions": questions
#         }
#     else:
#         for i, match in enumerate(topics_found):
#             # Check if this is a "Topic" match or a "Case Study" match
#             if match.re == topic_pattern:  # This is a Topic match
#                 topic_number = match.group(1)
#                 topic_name = match.group(2).strip()
#                 content = match.group(3).strip() or ""
#             else:  # This is a Case Study match
#                 topic_number = match.group(1)
#                 topic_name = f"Case Study {topic_number}"
#                 content = match.group(3).strip() or ""
            
#             # Extract case study text
#             # breakpoint()
#             case_study_text = extract_case_study_text(match.group(0))
#             if not case_study_text:
#                 case_study_text = ''
            
#             # Extract questions for this topic
#             questions = extract_questions(match.group(0), question_pattern, answer_pattern, explanation_pattern)
            
#             # Add the current topic to the all_topics_data dictionary
#             all_topics_data[f"topic{topic_number}"] = {
#                 "topic_name": topic_name,
#                 "case_study": case_study_text,
#                 "questions": questions
#             }

#     save_to_json(all_topics_data, "topic_json_files", "all_topics_830_new.json")
#     print("All topics saved to all_topics.json")

# if __name__ == "__main__":
#     main()

class TopicProcessor:
    def __init__(self):
        # Initialize regex patterns
        self.topic_pattern = re.compile(r"Topic (\d+), (.+?)\n(.+?)(?=(Topic \d+, |Case Study: \d+|$))", re.DOTALL)
        self.case_study_pattern = re.compile(r"Case Study: (\d+)\n(.+?)\n(.+?)(?=(Topic \d+, |Case Study: \d+|$))", re.DOTALL)
        self.question_pattern = re.compile(r"Question: (\d+)\n(.+?)(?=(Question: \d+|Topic \d+, |Case Study: \d+|$))", re.DOTALL)
        self.answer_pattern = re.compile(r"Answer:\s*([A-G,\s]+)(?=\n|$)")
        self.explanation_pattern = re.compile(r"Explanation:\s*(.+?)(?=(?:Question: \d+|Topic \d+, |Case Study: \d+|$))", re.DOTALL)

    def process_text(self, text: str) -> Dict:
        """
        Process text content and return structured data.
        
        Args:
            text: The text content to process
            
        Returns:
            Dictionary containing processed topic data
        """
        all_topics_data = {}
        topics_found = self.extract_topics(text)

        if not topics_found:
            # Process as a single default topic
            case_study_text = self.extract_case_study_text(text)
            questions = self.extract_questions(text)
            all_topics_data["topic0"] = {
                "topic_name": "",
                "case_study": case_study_text,
                "questions": questions
            }
        else:
            for i, match in enumerate(topics_found):
                topic_data = self.process_topic_match(match)
                all_topics_data[f"topic{topic_data['number']}"] = topic_data['data']

        return all_topics_data

    def extract_topics(self, text: str) -> List[Match]:
        """Extract all topic matches from text."""
        topic_matches = list(self.topic_pattern.finditer(text))
        case_study_matches = list(self.case_study_pattern.finditer(text))
        return topic_matches + case_study_matches

    def process_topic_match(self, match: Match) -> Dict:
        """Process a single topic match."""
        if match.re == self.topic_pattern:
            topic_number = match.group(1)
            topic_name = match.group(2).strip()
        else:
            topic_number = match.group(1)
            topic_name = f"Case Study {topic_number}"

        case_study_text = self.extract_case_study_text(match.group(0))
        questions = self.extract_questions(match.group(0))

        return {
            "number": topic_number,
            "data": {
                "topic_name": topic_name,
                "case_study": case_study_text or '',
                "questions": questions
            }
        }

    def extract_case_study_text(self, text: str) -> str:
        """Extract case study text from content."""
        case_study_match = re.search(
            r"(?s)(Topic \d+, |Case Study: \d+\n).+?\n(.+?)(?=Question: \d+)",
            text,
            re.DOTALL
        )
        if case_study_match:
            case_study_text = case_study_match.group(2).strip()
            case_study_text = re.sub(r'Question: \d+.*', '', case_study_text, flags=re.DOTALL)
            return case_study_text if case_study_text and not case_study_text.isspace() else ""
        return ""

    def extract_questions(self, text: str) -> List[Dict]:
        """Extract questions from text content."""
        questions = []
        for question_match in self.question_pattern.finditer(text):
            question_data = self.process_question_match(question_match)
            questions.append(question_data)
        return questions

    def process_question_match(self, question_match: Match) -> Dict:
        """Process a single question match and return structured data."""
        question_number = question_match.group(1)
        full_question_text = question_match.group(2).strip()
        
        # Split text at "Answer:" to separate options from answer/explanation
        parts = re.split(r'Answer:', full_question_text, 1)
        question_with_options = parts[0].strip()
        answer_explanation_text = "Answer:" + parts[1] if len(parts) > 1 else ""

        # Extract answer
        answer_match = self.answer_pattern.search(answer_explanation_text)
        if answer_match and answer_match.group(1).strip():
            answer_text = answer_match.group(1).strip()
            answer_text = answer_text.replace(',', '')
            
            if ' ' in answer_text:
                # Space-separated answers (like "A B C")
                answer = [a.strip() for a in answer_text.split() if a.strip() in ['A', 'B', 'C', 'D', 'E', 'F', 'G']]
            else:
                # Concatenated answers (like "ABC")
                answer = [letter for letter in answer_text if letter in ['A', 'B', 'C', 'D', 'E', 'F', 'G']]
        else:
            answer = []
        
        # Extract explanation
        explanation_match = self.explanation_pattern.search(answer_explanation_text)
        explanation = explanation_match.group(1).strip() if explanation_match else ""
        
        # Extract options
        options = []
        option_blocks = re.findall(
            r'([A-G])\.\s+((?:(?!(?:[A-G]\. |\nAnswer:)).)+)',
            question_with_options,
            re.DOTALL
        )
        
        for option_letter, option_content in option_blocks:
            options.append(f"{option_letter}. {option_content.strip()}")
        
        # Clean question text
        question_text = question_with_options
        for option_letter, option_content in option_blocks:
            option_text = f"{option_letter}. {option_content}"
            question_text = question_text.replace(option_text, "").strip()
        
        question_text = self.clean_question_text(question_text)
        rest_options, final_options = self.split_options(options)
        if rest_options and final_options:
            question_text = self.add_rest_to_question(question_text, rest_options)

            return {
                "question_number": question_number,
                "question": question_text,
                "options": final_options,
                "answer": answer,
                "explanation": explanation
            }
        return {
                "question_number": question_number,
                "question": question_text,
                "options": rest_options,
                "answer": answer,
                "explanation": explanation
            }

    def clean_question_text(self, question_text: str) -> str:
        """Clean the question text by removing option lines."""
        # Remove option lines that look like "A.    C", "B.    B", etc.
        cleaned_text = re.sub(r'\n[A-D]\.\s*[A-D]', '', question_text, flags=re.MULTILINE)
        
        # Additional cleanup to remove any remaining option-like lines
        cleaned_text = re.sub(r'\n[A-D]\..*', '', cleaned_text, flags=re.MULTILINE)
        
        return cleaned_text.strip()

    # def split_options(self, options: List[str]) -> Tuple[List[str], List[str]]:
    #     """Split options into first and last occurrences."""
    #     first_occurrence = {}
    #     last_occurrence = {}
    #     option_counts = {}

    #     # First pass: Count occurrences of each option
    #     for option in options:
    #         key = option.split('.')[0].strip()
    #         option_counts[key] = option_counts.get(key, 0) + 1

    #     # Second pass: Store first and last occurrences
    #     breakpoint()
    #     for option in options:
    #         key = option.split('.')[0].strip()
            
    #         if key not in first_occurrence:
    #             first_occurrence[key] = option
            
    #         if option_counts[key] == 1:
    #             last_occurrence[key] = option
    #         else:
    #             last_occurrence[key] = option

    #     # Convert dictionaries to lists in order (A, B, C, D)
    #     sorted_keys = sorted(first_occurrence.keys())
    #     first_list = [first_occurrence[key] for key in sorted_keys]
    #     last_list = [last_occurrence[key] for key in sorted_keys]

    #     return first_list, last_list
    def split_options(self, options: List[str]) -> Tuple[List[str], List[str]]:
        """Split options into first and last occurrences."""
        first_occurrence = {}
        last_occurrence = {}

        # First and Last Occurrence Tracking
        for option in options:
            key = option.split('.')[0].strip()
            
            # Store the first occurrence
            if key not in first_occurrence:
                first_occurrence[key] = option

            # Always update the last occurrence
            else:
                last_occurrence[key] = option
        # breakpoint()

        # Maintain order of first seen keys
        
        sorted_f_keys = list(first_occurrence.keys())
        sorted_l_keys = list(last_occurrence.keys())
        first_list = [first_occurrence[key] for key in sorted_f_keys]
        last_list = [last_occurrence[key] for key in sorted_l_keys]

        return first_list, last_list

    def add_rest_to_question(self, question_text: str, rest_options: List[str]) -> str:
        """Add rest options to the question text."""
        if not rest_options:
            return question_text
        
        rest_content = "\n".join(rest_options)
        return f"{question_text}\n{rest_content}"

    @staticmethod
    def save_to_json(data: Dict, output_dir: str, filename: str) -> str:
        """
        Save data to JSON file and return the file path.
        
        Args:
            data: Data to save
            output_dir: Directory to save the file
            filename: Name of the JSON file
            
        Returns:
            Path to the saved JSON file
        """
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, filename)
        with open(output_path, "w") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return output_path

def process_content(text: str) -> Dict:
    """
    Convenience function to process content without instantiating TopicProcessor.
    
    Args:
        text: Text content to process
        
    Returns:
        Processed topic data as dictionary
    """
    processor = TopicProcessor()
    return processor.process_text(text)