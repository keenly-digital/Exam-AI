import json
import re
import os
from typing import Dict, List, Tuple

class TopicProcessor:
    def __init__(self):
        self.topic_pattern = re.compile(r"Topic (\d+)\s*,\s*(.+?)\n(.+?)(?=(Topic \d+\s*,|Case Study: \d+|$))", re.DOTALL)
        self.case_study_pattern = re.compile(r"Case Study: (\d+)\n(.+?)\n(.+?)(?=(Topic \d+\s*,|Case Study: \d+|$))", re.DOTALL)
        self.question_pattern = re.compile(r"(?:QUESTION|Question)[:\s]*(\d+)\n(.+?)(?=(?:QUESTION|Question)[:\s]*\d+|Topic \d+, |Case Study: \d+|$)", re.DOTALL | re.IGNORECASE)
        self.answer_pattern = re.compile(r"(?:Correct Answer|Answer)[:\s]*([A-G,\s]+)(?=\n|$)", re.IGNORECASE)
        self.explanation_pattern = re.compile(r"Explanation:\s*(.+?)(?=(?:Question: \d+|Topic \d+, |Case Study: \d+|$))", re.DOTALL)
        self.placeholder_regex = re.compile(r'%%IMAGE_\d+%%')

    def _extract_images_from_text(self, text: str, placeholder_map: dict) -> Tuple[str, List[str]]:
        if not text: return "", []
        image_urls = [placeholder_map.get(p) for p in self.placeholder_regex.findall(text) if p in placeholder_map]
        cleaned_text = self.placeholder_regex.sub('', text).strip()
        return cleaned_text, image_urls

    def _process_question_match(self, question_match: "Match", placeholder_map: dict) -> Dict:
        question_number = question_match.group(1)
        full_question_text = question_match.group(2).strip()
        
        parts = re.split(r'Correct Answer|Answer:', full_question_text, 1, re.IGNORECASE)
        question_with_options = parts[0].strip()
        answer_explanation_text = "Answer:" + parts[1] if len(parts) > 1 else ""

        first_option_match = re.search(r'\n[A-G]\.', question_with_options)
        raw_question = question_with_options[:first_option_match.start()] if first_option_match else question_with_options

        question_text, question_images = self._extract_images_from_text(raw_question, placeholder_map)
        
        options_found = re.findall(r'([A-G])\.\s+((?:(?![A-G]\.\s|\nCorrect Answer:|\nAnswer:).)+)', question_with_options, re.DOTALL)
        options = [f"{opt[0]}. {opt[1].strip()}" for opt in options_found]

        answer_match = self.answer_pattern.search(answer_explanation_text)
        answer_text = answer_match.group(1).strip().replace(',', '') if answer_match else ""
        answer = [char for char in answer_text if char.isalpha()]
        
        raw_explanation_match = self.explanation_pattern.search(answer_explanation_text)
        raw_explanation = raw_explanation_match.group(1).strip() if raw_explanation_match else ""
        explanation_text, explanation_images = self._extract_images_from_text(raw_explanation, placeholder_map)
        
        return {
            "question_number": question_number, "question_text": question_text, "question_images": question_images,
            "options": options, "answer": answer, "explanation_text": explanation_text, "explanation_images": explanation_images
        }
    
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
            all_topics_data["topic0"] = {"topic_name": "General Questions", "questions": list(all_questions.values())}
        else:
            # Simplified logic for topic processing
            for match in topics_found:
                topic_number = match.group(1)
                topic_name = match.group(2).strip() if match.re == self.topic_pattern else f"Case Study {topic_number}"
                content = match.group(3)
                
                questions_in_topic = [self._process_question_match(q_match, placeholder_map) for q_match in self.question_pattern.finditer(content)]
                all_topics_data[f"topic{topic_number}"] = {"topic_name": topic_name, "questions": questions_in_topic}
        return all_topics_data

def process_content(text: str, placeholder_map: dict) -> Dict:
    processor = TopicProcessor()
    return processor.process_text(text, placeholder_map)