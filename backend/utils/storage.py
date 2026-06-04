import os
import json
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from backend.config import DATA_DIR

class JSONStorage:
    """
    Simule une base de données Firestore en stockant les documents dans des fichiers JSON locaux.
    Permet de faire tourner le POC en local en toute autonomie.
    """
    
    def __init__(self):
        self.users_file = os.path.join(DATA_DIR, "users.json")
        self.gaps_file = os.path.join(DATA_DIR, "gaps.json")
        self.courses_file = os.path.join(DATA_DIR, "courses.json")
        self.chats_file = os.path.join(DATA_DIR, "chats.json")
        
        # Initialiser les fichiers s'ils n'existent pas
        for file_path in [self.users_file, self.gaps_file, self.courses_file, self.chats_file]:
            if not os.path.exists(file_path):
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump([], f, ensure_ascii=False, indent=2)

    def _read_file(self, file_path: str) -> List[Dict[str, Any]]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []

    def _write_file(self, file_path: str, data: List[Dict[str, Any]]):
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # --- CHAT & PROMPTS ---
    def save_chat_message(self, user_id: str, role: str, content: str) -> Dict[str, Any]:
        chats = self._read_file(self.chats_file)
        message = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        chats.append(message)
        self._write_file(self.chats_file, chats)
        return message

    def get_chat_history(self, user_id: str) -> List[Dict[str, Any]]:
        chats = self._read_file(self.chats_file)
        history = [c for c in chats if c["user_id"] == user_id]
        return sorted(history, key=lambda x: x["timestamp"])

    # --- KNOWLEDGE GAPS ---
    def save_gap(self, user_id: str, gap: Dict[str, Any]) -> Dict[str, Any]:
        gaps = self._read_file(self.gaps_file)
        gap_doc = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "topic": gap["topic"],
            "gap_description": gap["gap_description"],
            "confidence": gap["confidence"],
            "embedding": gap.get("embedding", []),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "processed": False  # Indique si cette lacune a déjà été intégrée dans un cours
        }
        gaps.append(gap_doc)
        self._write_file(self.gaps_file, gaps)
        return gap_doc

    def get_unprocessed_gaps(self, user_id: str) -> List[Dict[str, Any]]:
        gaps = self._read_file(self.gaps_file)
        return [g for g in gaps if g["user_id"] == user_id and not g.get("processed", False)]

    def mark_gaps_as_processed(self, gap_ids: List[str]):
        gaps = self._read_file(self.gaps_file)
        for g in gaps:
            if g["id"] in gap_ids:
                g["processed"] = True
        self._write_file(self.gaps_file, gaps)

    # --- COURSES, QUIZZES & PODCASTS ---
    def save_course(self, user_id: str, topic: str, course_content: str, quiz: List[Dict[str, Any]], podcast_script: List[Dict[str, str]], podcast_audio: str = None) -> Dict[str, Any]:
        courses = self._read_file(self.courses_file)
        course_doc = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "topic": topic,
            "course_content": course_content,
            "quiz": quiz,
            "podcast_script": podcast_script,
            "podcast_audio": podcast_audio,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        courses.append(course_doc)
        self._write_file(self.courses_file, courses)
        return course_doc

    def get_user_courses(self, user_id: str) -> List[Dict[str, Any]]:
        courses = self._read_file(self.courses_file)
        user_courses = [c for c in courses if c["user_id"] == user_id]
        return sorted(user_courses, key=lambda x: x["timestamp"], reverse=True)

    def get_all_gaps_global(self) -> List[Dict[str, Any]]:
        """Pour les statistiques du dashboard Manager"""
        return self._read_file(self.gaps_file)
        
    def reset_all_data(self):
        """Réinitialise toutes les données (pratique pour les démos)"""
        for file_path in [self.users_file, self.gaps_file, self.courses_file, self.chats_file]:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)
