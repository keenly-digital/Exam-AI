import json
import re
import os
from typing import Dict, List, Union, Pattern, Match, Optional, Tuple
   

class TopicProcessor:
    def __init__(self):
        # Initialize regex patterns
        self.topic_pattern = re.compile(r"Topic (\d+)\s*,\s*(.+?)\n(.+?)(?=(Topic \d+\s*,|Case Study: \d+|$))", re.DOTALL)
        self.case_study_pattern = re.compile(r"Case Study: (\d+)\n(.+?)\n(.+?)(?=(Topic \d+\s*,|Case Study: \d+|$))", re.DOTALL)
        # self.question_pattern = re.compile(r"Question:\s*(\d+)\n(.+?)(?=(Question:\s*\d+|Topic \d+, |Case Study: \d+|$))", re.DOTALL)
        self.question_pattern = re.compile(
            r"(?:QUESTION|Question)[:\s]*(\d+)\n(.+?)(?=(?:QUESTION|Question)[:\s]*\d+|Topic \d+, |Case Study: \d+|$)", 
            re.DOTALL | re.IGNORECASE
        )
        # self.answer_pattern = re.compile(r"Answer:\s*([A-G,\s]+)(?=\n|$)")
        self.answer_pattern = re.compile(
            r"(?:Correct Answer|Answer)[:\s]*([A-G,\s]+)(?=\n|$)", 
            re.IGNORECASE
        )
        self.explanation_pattern = re.compile(r"Explanation:\s*(.+?)(?=(?:Question: \d+|Topic \d+, |Case Study: \d+|$))", re.DOTALL)

    # def process_text(self, text: str) -> Dict:
    #     """
    #     Process text content and return structured data.
        
    #     Args:
    #         text: The text content to process
            
    #     Returns:
    #         Dictionary containing processed topic data
    #     """
    #     all_topics_data = {}
    #     topics_found = self.extract_topics(text)
    #     if not topics_found:
    #         # Process as a single default topic
    #         case_study_text = self.extract_case_study_text(text)
    #         questions = self.extract_questions(text)
    #         all_topics_data["topic0"] = {
    #             "topic_name": "",
    #             "case_study": case_study_text,
    #             "questions": questions
    #         }
    #     else:
    #         for i, match in enumerate(topics_found):
    #             topic_data = self.process_topic_match(match)
    #             all_topics_data[f"topic{topic_data['number']}"] = topic_data['data']

    #     # json_string = json.dumps(all_topics_data, indent=4)
    #     # with open('test_json.json', 'w') as f:
    #     #     f.write(json_string)
    #     return all_topics_data

    def process_text(self, text: str) -> Dict:
        """New version that handles questions before topics
    
          Process text content and return structured data.
        
          Args:
              text: The text content to process
            
          Returns:
              Dictionary containing processed topic data
        """

        all_topics_data = {}
        
        # Get ALL questions first (with their positions)
        all_questions = {
            q_match.start(): self.process_question_match(q_match)
            for q_match in self.question_pattern.finditer(text)
        }
        
        # Process topics (original logic but tracks positions)
        topics_found = self.extract_topics(text)
        
        if not topics_found:
            # Original fallback if no topics found
            all_topics_data["topic0"] = {
                "topic_name": "",
                "case_study": self.extract_case_study_text(text),
                "questions": list(all_questions.values())
            }
        else:
            prev_topic_end = 0
            for i, topic_match in enumerate(topics_found):
                topic_start = topic_match.start()
                topic_data = self.process_topic_match(topic_match)
                topic_num = topic_data["number"]
                
                # Assign questions between topics to previous topic (or topic0)
                questions_in_gap = [
                    q for pos, q in all_questions.items()
                    if prev_topic_end <= pos < topic_start
                ]
                
                if i == 0 and questions_in_gap:  # Questions before first topic
                    all_topics_data["topic0"] = {
                        "topic_name": "",
                        "case_study": "",
                        "questions": questions_in_gap
                    }
                
                # Add the topic itself
                all_topics_data[f"topic{topic_num}"] = topic_data["data"]
                prev_topic_end = topic_match.end()
            
            # Handle questions after last topic
            remaining_questions = [
                q for pos, q in all_questions.items()
                if pos >= prev_topic_end
            ]
            if remaining_questions:
                if "topic0" not in all_topics_data:
                    all_topics_data["topic0"] = {
                        "topic_name": "General Questions",
                        "case_study": "",
                        "questions": []
                    }
                all_topics_data["topic0"]["questions"].extend(remaining_questions)
        
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
            r"(?s)(Topic \d+\s*, |Case Study: \d+\n).+?\n(.+?)(?=Question: \d+)",
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
        parts = re.split(r'Correct Answer|Answer:', full_question_text, 1)
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
