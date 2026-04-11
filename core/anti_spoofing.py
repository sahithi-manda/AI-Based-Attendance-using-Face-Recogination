class SpoofDetector:
    def __init__(self):
        self.blink_threshold = 0.22
        
    def analyze_frame(self, bgr_frame, face_bboxes):
        results = []
        for bbox in face_bboxes:
            results.append({
                'texture_passed': True,
                'screen_edges': False,
                'glare_detected': False,
                'is_spoof': False,
                'is_real': True,
                'reason': "",
                'blink_detected': True,
                'ear': 0.3
            })
        return results
