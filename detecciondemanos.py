import cv2
import mediapipe as mp
import numpy as np

mp_hands = mp.solutions.hands
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

class DetectorSenas:
    def __init__(self):
        # Detector de manos (hasta 2 manos simultáneas)
        self.hands = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        
        # Detector de pose corporal completa
        self.pose = mp_pose.Pose(
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        
        self.cap = cv2.VideoCapture(0)
    
    def obtener_landmarks_manos(self, frame):
        """Retorna lista de 21 puntos por mano detectada"""
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        resultado = self.hands.process(rgb)
        
        landmarks_list = []
        
        if resultado.multi_hand_landmarks:
            for hand_landmarks in resultado.multi_hand_landmarks:
                # Extraer coordenadas normalizadas (x, y, z)
                puntos = []
                for lm in hand_landmarks.landmark:
                    puntos.extend([lm.x, lm.y, lm.z])
                landmarks_list.append(np.array(puntos))  # 63 valores por mano
                
                # Dibujar en frame para visualización
                mp_drawing.draw_landmarks(
                    frame, hand_landmarks, mp_hands.HAND_CONNECTIONS
                )
        
        return landmarks_list, frame
    
    def obtener_landmarks_pose(self, frame):
        """Retorna 33 puntos del cuerpo completo"""
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        resultado = self.pose.process(rgb)
        
        if resultado.pose_landmarks:
            puntos = []
            for lm in resultado.pose_landmarks.landmark:
                puntos.extend([lm.x, lm.y, lm.z, lm.visibility])
            return np.array(puntos)  # 132 valores
        
        return None
    
    def detectar(self):
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            # Obtener landmarks de manos y pose
            manos_landmarks, frame = self.obtener_landmarks_manos(frame)
            pose_landmarks = self.obtener_landmarks_pose(frame)
            
            # Aquí se podrían agregar funciones para interpretar los landmarks
            # y detectar gestos específicos de lenguaje de señas
            
            cv2.imshow('Detección de Manos y Pose', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        self.cap.release()
        cv2.destroyAllWindows()