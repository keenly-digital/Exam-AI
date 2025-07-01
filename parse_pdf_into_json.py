import json
import re
import os
from typing import Dict, List, Union, Pattern, Match, Optional, Tuple
   

class TopicProcessor:
    def __init__(self):
        # Regex patterns are unchanged
        self.topic_pattern = re.compile(r"Topic (\d+)\s*,\s*(.+?)\n(.+?)(?=(Topic \d+\s*,|Case Study: \d+|$))", re.DOTALL)
        self.case_study_pattern = re.compile(r"Case Study: (\d+)\n(.+?)\n(.+?)(?=(Topic \d+\s*,|Case Study: \d+|$))", re.DOTALL)
        self.question_pattern = re.compile(
            r"(?:QUESTION|Question)[:\s]*(\d+)\n(.+?)(?=(?:QUESTION|Question)[:\s]*\d+|Topic \d+, |Case Study: \d+|$)",
            re.DOTALL | re.IGNORECASE
        )
        self.answer_pattern = re.compile(
            r"(?:Correct Answer|Answer)[:\s]*([A-G,\s]+)(?=\n|$)",
            re.IGNORECASE
        )
        self.explanation_pattern = re.compile(r"Explanation:\s*(.+?)(?=(?:Question: \d+|Topic \d+, |Case Study: \d+|$))", re.DOTALL)
        self.placeholder_regex = re.compile(r'%%IMAGE_\d+%%')

    def _extract_images_from_text(self, text: str, placeholder_map: dict) -> Tuple[str, List[str]]:
        """Finds image placeholders in text, returns cleaned text and a list of URLs."""
        image_urls = []
        if not text:
            return "", []

        # Find all placeholders (e.g., %%IMAGE_0%%)
        placeholders = self.placeholder_regex.findall(text)
        
        for placeholder in placeholders:
            # Add the real URL to our list
            if placeholder in placeholder_map:
                image_urls.append(placeholder_map[placeholder])
            # Remove the placeholder from the text
            text = text.replace(placeholder, "").strip()
            
        return text, image_urls

    def process_text(self, text: str, placeholder_map: dict) -> Dict:
        # This function and its helpers below are unchanged in their core logic,
        # but they now pass the placeholder_map down to where it's needed.
        all_topics_data = {}
        all_questions = {
            q_match.start(): self._process_question_match(q_match, placeholder_map)
            for q_match in self.question_pattern.finditer(text)
        }
        
        topics_found = list(self.topic_pattern.finditer(text)) + list(self.case_study_pattern.finditer(text))
        
        if not topics_found:
            case_study_text, case_study_images = self._extract_images_from_text(self.extract_case_study_text(text), placeholder_map)
            all_topics_data["topic0"] = {
                "topic_name": "",
                "case_study_text": case_study_text,
                "case_study_images": case_study_images,
                "questions": list(all_questions.values())
            }
        else:
            prev_topic_end = 0
            for i, topic_match in enumerate(topics_found):
                topic_start = topic_match.start()
                topic_data = self._process_topic_match(topic_match, placeholder_map)
                topic_num = topic_data["number"]
                
                questions_in_gap = [q for pos, q in all_questions.items() if prev_topic_end <= pos < topic_start]
                if i == 0 and questions_in_gap:
                    all_topics_data["topic0"] = {"topic_name": "", "case_study_text": "", "case_study_images": [], "questions": questions_in_gap}
                
                all_topics_data[f"topic{topic_num}"] = topic_data["data"]
                prev_topic_end = topic_match.end()

            remaining_questions = [q for pos, q in all_questions.items() if pos >= prev_topic_end]
            if remaining_questions:
                if "topic0" not in all_topics_data:
                    all_topics_data["topic0"] = {"topic_name": "General Questions", "case_study_text": "", "case_study_images": [], "questions": []}
                all_topics_data["topic0"]["questions"].extend(remaining_questions)
        
        return all_topics_data

    def _process_topic_match(self, match: Match, placeholder_map: dict) -> Dict:
        if match.re == self.topic_pattern:
            topic_number, topic_name, content = match.group(1), match.group(2).strip(), match.group(3)
        else:
            topic_number, content = match.group(1), match.group(3)
            topic_name = f"Case Study {topic_number}"
        
        raw_case_study = self.extract_case_study_text(match.group(0))
        case_study_text, case_study_images = self._extract_images_from_text(raw_case_study, placeholder_map)

        questions = [self._process_question_match(q_match, placeholder_map) for q_match in self.question_pattern.finditer(content)]

        return {
            "number": topic_number,
            "data": {
                "topic_name": topic_name,
                "case_study_text": case_study_text,
                "case_study_images": case_study_images,
                "questions": questions
            }
        }

    def _process_question_match(self, question_match: Match, placeholder_map: dict) -> Dict:
        question_number = question_match.group(1)
        full_question_text = question_match.group(2).strip()
        
        parts = re.split(r'Correct Answer|Answer:', full_question_text, 1, re.IGNORECASE)
        question_with_options = parts[0]
        answer_explanation_text = "Answer:" + parts[1] if len(parts) > 1 else ""

        # Extract answer and explanation first
        answer_match = self.answer_pattern.search(answer_explanation_text)
        answer_text = answer_match.group(1).strip().replace(',', '') if answer_match else ""
        answer = [char for char in answer_text if char.isalpha()]
        
        raw_explanation = self.explanation_pattern.search(answer_explanation_text)
        explanation, explanation_images = self._extract_images_from_text(raw_explanation.group(1).strip() if raw_explanation else "", placeholder_map)

        # Separate question text from options
        options = re.findall(r'([A-G])\.\s+((?:(?![A-G]\.\s|\nCorrect Answer:|\nAnswer:).)+)', question_with_options, re.DOTALL)
        question_text_only = question_with_options
        for opt in options:
            question_text_only = question_text_only.replace(f"{opt[0]}. {opt[1]}", "")
        
        question_text, question_images = self._extract_images_from_text(question_text_only.strip(), placeholder_map)
        
        return {
            "question_number": question_number,
            "question_text": question_text,
            "question_images": question_images,
            "options": [f"{opt[0]}. {opt[1].strip()}" for opt in options],
            "answer": answer,
            "explanation_text": explanation,
            "explanation_images": explanation_images
        }

    def extract_case_study_text(self, text: str) -> str:
        # This helper now just extracts text, another function will process it
        case_study_match = re.search(r"(?s)(?:Overview|Case Study|General Information)(.+?)(?=Question: \d+|QUESTION \d+)", text, re.IGNORECASE)
        return case_study_match.group(1).strip() if case_study_match else ""

def process_content(text: str, placeholder_map: dict) -> Dict:
    processor = TopicProcessor()
    return processor.process_text(text, placeholder_map)