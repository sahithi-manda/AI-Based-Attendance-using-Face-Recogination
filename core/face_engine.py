import face_recognition
import cv2
import numpy as np
from core import db_handler

class FaceEngine:
    def __init__(self):
        # Cache of known face encodings and names from DB to avoid hitting DB every frame
        self.known_face_encodings = []
        self.known_students = []
        self.reload_known_faces()
        
    def reload_known_faces(self):
        self.known_face_encodings = []
        self.known_students = db_handler.get_all_student_encodings()
        for student in self.known_students:
            self.known_face_encodings.append(student['encoding'])
            
    def get_face_encoding(self, image):
        """
        Takes an RGB BGR numpy image, detects faces and returns the encoding of the first face.
        Returns None if no face is found.
        """
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        # Find all face locations
        face_locations = face_recognition.face_locations(rgb_image)
        if not face_locations:
            return None
        # We assume one face for registration
        encodings = face_recognition.face_encodings(rgb_image, face_locations)
        if encodings:
            return encodings[0]
        return None

    def recognize_faces(self, bgr_frame):
        """
        Finds all faces in frame and returns their bounding boxes, names, and student_ids.
        Returns a list of dicts:
        [{'bbox': (top, right, bottom, left), 'name': 'John Doe', 'student_id': 1}, ...]
        """
        # Resize frame of video to 1/4 size for faster face recognition processing
        small_frame = cv2.resize(bgr_frame, (0, 0), fx=0.25, fy=0.25)

        # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
        
        results = []
        
        for face_encoding, face_location in zip(face_encodings, face_locations):
            # Scale back up face locations since the frame we detected in was scaled to 1/4 size
            top, right, bottom, left = face_location
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4
            
            bbox = (top, right, bottom, left)
            name = "Unknown"
            student_id = None
            
            if self.known_face_encodings:
                # Optimized Euclidean distance using NumPy for smooth performance on Ryzen 3
                known_encodings_np = np.array(self.known_face_encodings)
                face_distances = np.linalg.norm(known_encodings_np - face_encoding, axis=1)
                
                if len(face_distances) > 0:
                    best_match_index = np.argmin(face_distances)
                    # Match tolerance 0.55 is slightly stricter than the library default (0.6) to reduce false matches
                    if face_distances[best_match_index] <= 0.55:
                        student = self.known_students[best_match_index]
                        name = student['name']
                        student_id = student['student_id']
                        
            results.append({
                'bbox': bbox,
                'name': name,
                'student_id': student_id
            })
            
        return results
