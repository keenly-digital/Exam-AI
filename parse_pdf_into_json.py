import json
import re
import os
import logging
from typing import Dict, List, Pattern, Match, Optional, Tuple, Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)


class TopicProcessor:
    # Configurable option letters
    OPTION_LETTERS = ['A', 'B', 'C', 'D', 'E', 'F', 'G']

    def __init__(self) -> None:
        """
        Initialize regex patterns for topics, case studies, questions, answers, and explanations.
        Patterns are robust to separators, spacing, and case.
        """
        self.topic_pattern = re.compile(
            r"Topic\s*[:\-,]?\s*(\d+)(?:\s*[,:\-]\s*([^\n]+?))?\n(.+?)(?=(Topic\s*[:\-,]?\s*\d+|Case Study[:\s-]*\d+|$))",
            re.DOTALL | re.IGNORECASE
        )

        self.case_study_pattern: Pattern = re.compile(
            r"Case Study[:\s-]*(\d+)\n(.+?)\n(.+?)(?=(Topic\s+\d+[\s,:-]|Case Study[:\s-]*\d+|$))",
            re.DOTALL | re.IGNORECASE
        )
        self.question_pattern: Pattern = re.compile(
            r"(?:QUESTION|Question)[:\s]*(\d+)\n(.+?)(?=(?:QUESTION|Question)[:\s]*\d+|Topic\s+\d+[\s,:-]|Case Study[:\s-]*\d+|$)",
            re.DOTALL | re.IGNORECASE
        )
        # Not used in improved extraction but kept for reference:
        self.answer_pattern: Pattern = re.compile(
            r"(?:Correct Answer|Answer)[:\s]*([A-G][\.\-:\)\s]*)?(.*)",
            re.IGNORECASE
        )
        self.explanation_pattern: Pattern = re.compile(
            r"Explanation[\s:-]*\s*(.+?)(?=(?:Question[:\s]*\d+|Topic\s+\d+[\s,:-]|Case Study[:\s-]*\d+|$))",
            re.DOTALL | re.IGNORECASE
        )
        self.note_pattern = re.compile(r"^\s*not(e)?[\.:]?\s*$", re.IGNORECASE)

    def process_text(self, text: str) -> Dict[str, Any]:
        """
        Process text content and return structured topic data.
        """
        all_topics_data: Dict[str, Any] = {}

        # Get ALL questions first (with their positions)
        all_questions: Dict[int, Dict[str, Any]] = {
            q_match.start(): self.process_question_match(q_match)
            for q_match in self.question_pattern.finditer(text)
        }

        # Process topics and case studies
        topics_found: List[Match] = self.extract_topics(text)

        if not topics_found:
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
                all_topics_data["topic0"]["questions"].extend(
                    remaining_questions)

        return all_topics_data

    def extract_topics(self, text: str) -> List[Match]:
        """
        Extract all topic and case study matches from text.
        """
        topic_matches = list(self.topic_pattern.finditer(text))
        case_study_matches = list(self.case_study_pattern.finditer(text))
        return topic_matches + case_study_matches

    def process_topic_match(self, match: Match) -> Dict[str, Any]:
        """
        Process a single topic or case study match.
        """
        if match.re == self.topic_pattern:
            topic_number = match.group(1)
            topic_name = match.group(2).strip() if match.group(2) else ""
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
        """
        Extract case study text from content.
        """
        case_study_match = re.search(
            r"(?s)(Topic\s+\d+[\s,:-]|Case Study[:\s-]*\d+\n).+?\n(.+?)(?=Question[:\s]*\d+)",
            text,
            re.DOTALL | re.IGNORECASE
        )
        if case_study_match:
            case_study_text = case_study_match.group(2).strip()
            case_study_text = re.sub(
                r'Question[:\s]*\d+.*', '', case_study_text, flags=re.DOTALL | re.IGNORECASE)
            return case_study_text if case_study_text and not case_study_text.isspace() else ""
        return ""

    def extract_questions(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract questions from text content.
        """
        questions: List[Dict[str, Any]] = []
        for question_match in self.question_pattern.finditer(text):
            question_data = self.process_question_match(question_match)
            questions.append(question_data)
        return questions

    def process_question_match(self, question_match: Match) -> Dict[str, Any]:
        """
        Process a single question match and return structured data.
        """
        question_number = question_match.group(1)
        full_question_text = question_match.group(2).strip()

        # Split text at any "Correct Answer"/"Answer", accepting optional colon/space/newline
        parts = re.split(
            r'(?:Correct Answer|Answer)\s*[:：]?\s*', full_question_text, 1, flags=re.IGNORECASE
        )
        question_with_options = parts[0].strip()
        answer_explanation_text = parts[1] if len(parts) > 1 else ""

        # --- Smart, context-aware option extraction block (improved) ---
        question_lines = question_with_options.splitlines()
        question_lines_clean = []
        option_lines = []
        temp_option_lines = []
        for line in question_lines:
            # Aggressive: match A.  A)  A:  A-  A )  A . etc.
            if re.match(r"^[A-G][\.\)\:\-\s]+\s*", line):
                temp_option_lines.append(line.strip())
            elif line.strip().lower().startswith("explanation"):
                # Stop collecting question if explanation starts (even if "Answer" is missing)
                break
            else:
                if temp_option_lines:
                    if len(temp_option_lines) >= 2:
                        option_lines = temp_option_lines
                        temp_option_lines = []
                    else:
                        question_lines_clean.extend(temp_option_lines)
                        temp_option_lines = []
                question_lines_clean.append(line.strip())
        # In case options are at the end
        if temp_option_lines and len(temp_option_lines) >= 2:
            option_lines = temp_option_lines
        elif temp_option_lines:
            question_lines_clean.extend(temp_option_lines)

        # Remove empty lines from question_lines_clean
        question_text = "\n".join(q for q in question_lines_clean if q)
        options = option_lines

        # --- End smart option extraction block ---

        # Extract answer (robust to newline after label)
        answer = []
        if answer_explanation_text:
            answer_lines = answer_explanation_text.strip().splitlines()
            for line in answer_lines:
                line = line.strip()
                if not line or line.lower().startswith('explanation'):
                    continue
                # Remove trailing dots/commas etc.
                answer_candidate = line.strip(" .:,;-")
                option_letters = re.findall(r"[A-G]", answer_candidate)
                if option_letters:
                    answer = option_letters
                else:
                    answer = [answer_candidate]
                break  # Only take the first valid line

        # Extract explanation (must NOT be in question block)
        explanation_match = self.explanation_pattern.search(
            answer_explanation_text)
        explanation = explanation_match.group(
            1).strip() if explanation_match else ""

        # Extra fallback: If explanation appears in question, but no answer, move it out
        if not answer and question_text.lower().strip().endswith('explanation'):
            explanation = question_text
            question_text = ''

        if explanation and not answer:
            logging.warning(
                f"Question {question_number} has explanation but no answer! Raw block: '{full_question_text}' Answer: '{answer_explanation_text}' explanation: '{explanation}'")

        return {
            "question_number": question_number,
            "question": question_text,
            "options": options,
            "answer": answer,
            "explanation": explanation
        }

    @staticmethod
    def save_to_json(data: Dict[str, Any], output_dir: str, filename: str) -> str:
        """
        Save data to JSON file and return the file path.
        """
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, filename)
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            logging.info(f"Saved output to {output_path}")
        except Exception as e:
            logging.error(f"Failed to save output: {e}", exc_info=True)
            raise
        return output_path


def process_content(text: str) -> Dict[str, Any]:
    """
    Convenience function to process content without instantiating TopicProcessor.
    """
    processor = TopicProcessor()
    return processor.process_text(text)

# Example usage (uncomment for CLI use):
# if __name__ == "__main__":
#     logging.info("Running TopicProcessor as a script. Place your sample input in 'sample.txt'.")
#     try:
#         with open("sample.txt", "r", encoding="utf-8") as f:
#             sample_text = f.read()
#         processor = TopicProcessor()
#         data = processor.process_text(sample_text)
#         processor.save_to_json(data, ".", "output.json")
#         logging.info("Parsing complete. Output saved to output.json.")
#     except FileNotFoundError:
#         logging.error("sample.txt not found. Please provide an input file for testing.")
