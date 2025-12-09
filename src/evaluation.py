# import os
# import numpy as np
# import librosa
# import parselmouth
# from openai import OpenAI
# import config

# # Initialize OpenAI Client
# client = None
# if config.OPENAI_API_KEY:
#     client = OpenAI(api_key=config.OPENAI_API_KEY)

# def get_acoustic_metrics(file_path):
#     """
#     Analyzes the physics of the voice: Pitch, Energy, Speed potential.
#     """
#     print(f"   [Evaluation] Analyzing Acoustics for {file_path}...")
    
#     try:
#         # Load audio for Energy/Duration (Librosa)
#         # SR=None maintains native sampling rate
#         y, sr = librosa.load(file_path, sr=None) 
#         duration = librosa.get_duration(y=y, sr=sr)
#         rms = librosa.feature.rms(y=y)
#         avg_energy = np.mean(rms)
        
#         # Load audio for Pitch (Parselmouth/Praat - Gold Standard)
#         sound = parselmouth.Sound(file_path)
#         pitch = sound.to_pitch()
#         pitch_values = pitch.selected_array['frequency']
        
#         # Filter out silence (0 Hz) to get actual voice pitch
#         pitch_values = pitch_values[pitch_values != 0]
        
#         if len(pitch_values) > 0:
#             pitch_mean = np.mean(pitch_values)
#             pitch_std = np.std(pitch_values) # Calculates "Monotone" vs "Dynamic"
#         else:
#             pitch_mean = 0
#             pitch_std = 0

#         return {
#             "duration": duration,
#             "energy": avg_energy,
#             "pitch_mean": pitch_mean,
#             "pitch_variability": pitch_std,
#             "success": True
#         }
#     except Exception as e:
#         print(f"   [Evaluation] Acoustic analysis failed: {e}")
#         return {"success": False, "error": str(e)}

# def get_linguistic_metrics(text_content):
#     """
#     Analyzes the content using GPT Evaluation.
#     """
#     if not client:
#         return "OpenAI Client not initialized."

#     print("   [Evaluation] Evaluating Linguistics (GPT-4o-mini)...")
    
#     system_prompt = """
#     You are an expert Corporate Communications Coach evaluating a candidate in a Group Discussion (GD).
#     Analyze the provided transcript text. 
    
#     Return a structured critique covering:
#     1. **Grammar & Vocabulary:** Rate (1-10) and list 2 improvements.
#     2. **Clarity & Structure:** Did they use the PREP method (Point, Reason, Example)?
#     3. **Filler Words:** Identify usage of 'um', 'uh', 'like', 'basically' (if visible in text).
#     4. **GD Etiquette:** Is the language polite yet assertive? (e.g., 'I disagree' vs 'I see your point, but').
    
#     Be concise and direct.
#     """
    
#     try:
#         response = client.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=[
#                 {"role": "system", "content": system_prompt},
#                 {"role": "user", "content": f"Transcript: \"{text_content}\""}
#             ]
#         )
#         return response.choices[0].message.content
#     except Exception as e:
#         return f"Error generating linguistic feedback: {e}"

# def generate_full_report(text_input, audio_path=None):
#     """
#     Generates the final report string.
#     If audio_path is provided, includes Acoustic metrics.
#     If only text_input is provided, generates only Linguistic metrics.
#     """
#     report_lines = []
#     report_lines.append("\n" + "="*50)
#     report_lines.append(" CORPORATE SKILLS EVALUATION REPORT ")
#     report_lines.append("="*50)

#     word_count = len(text_input.split())
    
#     # --- Step 1: Acoustics (Only if audio exists) ---
#     if audio_path and os.path.exists(audio_path):
#         acoustics = get_acoustic_metrics(audio_path)
        
#         if acoustics.get("success"):
#             # Derived Metrics
#             duration = acoustics['duration']
#             wpm = (word_count / duration) * 60 if duration > 0 else 0
            
#             # Pace Verdict
#             if wpm < 110: pace_status = "Slow (Risk of sounding underconfident)"
#             elif 110 <= wpm <= 170: pace_status = "Optimal (Corporate Standard)"
#             else: pace_status = "Fast (Risk of sounding nervous)"
            
#             # Tone Verdict (Pitch Std Dev)
#             # Normal conversational speech has std dev > 20Hz typically
#             if acoustics['pitch_variability'] < 20:
#                 tone_status = "Monotone / Flat (Needs more modulation)"
#             else:
#                 tone_status = "Dynamic / Engaging"

#             # Energy Verdict
#             # RMS values depend on recording volume, 0.01 is a conservative threshold
#             energy_status = 'High/Good' if acoustics['energy'] > 0.01 else 'Low (Speak Louder)'

#             report_lines.append(f"\n--- 🗣️ ACOUSTIC PARAMETERS (HOW YOU SOUND) ---")
#             report_lines.append(f"• Speaking Rate:   {int(wpm)} Words Per Minute")
#             report_lines.append(f"  -> Verdict:      {pace_status}")
#             report_lines.append(f"• Tone Variance:   {acoustics['pitch_variability']:.2f} Hz")
#             report_lines.append(f"  -> Verdict:      {tone_status}")
#             report_lines.append(f"• Energy Level:    {energy_status}")
#         else:
#              report_lines.append(f"\n--- 🗣️ ACOUSTIC PARAMETERS ---")
#              report_lines.append(f"Audio analysis failed: {acoustics.get('error')}")
#     else:
#         report_lines.append(f"\n--- 🗣️ ACOUSTIC PARAMETERS ---")
#         report_lines.append("No audio file provided. Analysis based on text content only.")

#     # --- Step 2: Linguistics ---
#     gpt_feedback = get_linguistic_metrics(text_input)

#     report_lines.append(f"\n--- 📝 LINGUISTIC PARAMETERS (WHAT YOU SAID) ---")
#     report_lines.append(f"• Word Count:      {word_count}")
#     report_lines.append(f"• Transcript:      \"{text_input}\"\n")
#     report_lines.append(f"--- 🤖 AI COACH FEEDBACK ---")
#     report_lines.append(gpt_feedback)
#     report_lines.append("="*50)

#     return "\n".join(report_lines)

import os
import numpy as np
import librosa
import parselmouth
from openai import OpenAI
import config
import json

# Initialize OpenAI Client
client = None
if config.OPENAI_API_KEY:
    client = OpenAI(api_key=config.OPENAI_API_KEY)

def map_score(value, min_val, max_val, target_min, target_max):
    """
    Maps a value from one range [min_val, max_val] to a target score range [target_min, target_max].
    """
    # Clamp value
    if value < min_val: value = min_val
    if value > max_val: value = max_val
    
    # Linear Interpolation
    ratio = (value - min_val) / (max_val - min_val)
    score = target_min + ratio * (target_max - target_min)
    return score

def get_raw_audio_metrics(file_path):
    """
    Extracts raw numbers from a single audio file.
    """
    try:
        # Load audio (sr=None preserves native sampling rate)
        y, sr = librosa.load(file_path, sr=None)
        
        # Calculate raw metrics
        duration = librosa.get_duration(y=y, sr=sr)
        rms = librosa.feature.rms(y=y)
        avg_energy = np.mean(rms)
        
        sound = parselmouth.Sound(file_path)
        pitch = sound.to_pitch()
        pitch_values = pitch.selected_array['frequency']
        pitch_values = pitch_values[pitch_values != 0]
        
        pitch_std = np.std(pitch_values) if len(pitch_values) > 0 else 0

        return {
            "duration": float(duration),
            "energy": float(avg_energy),
            "pitch_std": float(pitch_std),
            "valid": True
        }
    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")
        return {"valid": False}

def analyze_acoustics_logic(avg_metrics, total_word_count):
    """
    Converts AVERAGED metrics into Scores (1-10) and Feedback.
    """
    duration = avg_metrics.get("total_duration", 0)
    pitch_std = avg_metrics.get("avg_pitch", 0)
    energy = avg_metrics.get("avg_energy", 0)

    # ---------------------------------------------------------
    # 1. Speaking Rate (WPM)
    # ---------------------------------------------------------
    wpm = (total_word_count / duration) * 60 if duration > 0 else 0
    wpm_score = 0
    wpm_status = ""
    wpm_feedback = ""

    if wpm < 110:
        # TOO SLOW (Score 1-5)
        wpm_score = map_score(wpm, 0, 110, 1, 5)
        wpm_status = "Slow"
        wpm_feedback = "Your pace is too slow. This risks sounding underconfident or hesitant. Aim for 130+ WPM."
    
    elif 110 <= wpm < 130:
        # MODERATE / SLIGHTLY SLOW (Score 6-7)
        wpm_score = map_score(wpm, 110, 130, 6, 7.9)
        wpm_status = "Moderate"
        wpm_feedback = "Your pace is acceptable but slightly on the slower side. Try to pick up the tempo slightly."
    
    elif 130 <= wpm <= 160:
        # OPTIMAL (Score 8-10)
        wpm_score = map_score(wpm, 130, 160, 8, 10)
        wpm_status = "Optimal"
        wpm_feedback = "Excellent pacing. You are speaking at a clear, professional, and engaging speed."
    
    else: # > 160
        # TOO FAST (Score drops from 7 down to 1)
        # The faster you go above 160, the lower the score
        wpm_score = max(1, 7 - ((wpm - 160) / 10))
        wpm_status = "Fast"
        wpm_feedback = "You are speaking too fast. This indicates nervousness. Pause to breathe and articulate clearly."

    # ---------------------------------------------------------
    # 2. Tone / Pitch Dynamics (Variability in Hz)
    # ---------------------------------------------------------
    tone_score = 0
    tone_status = ""
    tone_feedback = ""
    
    if pitch_std < 20:
        # MONOTONE (Score 1-5)
        tone_score = map_score(pitch_std, 0, 20, 1, 5)
        tone_status = "Monotone"
        tone_feedback = "Your voice lacks variation. It sounds flat. Try emphasizing key words by changing your pitch."
    elif 20 <= pitch_std < 40:
        # MODERATE (Score 6-8)
        tone_score = map_score(pitch_std, 20, 40, 6, 8)
        tone_status = "Moderate Variation"
        tone_feedback = "Good start, but you can be even more expressive to command attention."
    else:
        # DYNAMIC (Score 9-10)
        # Cap score at 10
        tone_score = 10 if pitch_std > 80 else map_score(pitch_std, 40, 80, 9, 10)
        tone_status = "Dynamic"
        tone_feedback = "Excellent vocal modulation. You sound engaging and confident."

    # ---------------------------------------------------------
    # 3. Energy (RMS Amplitude)
    # ---------------------------------------------------------
    energy_score = 0
    energy_status = ""
    energy_feedback = ""

    # Thresholds adjusted for typical microphone input
    if energy < 0.015:
        # LOW (Score 1-5)
        energy_score = map_score(energy, 0, 0.015, 1, 5)
        energy_status = "Low"
        energy_feedback = "Your volume is too low. You risk sounding timid. Project your voice more."
    elif 0.015 <= energy < 0.04:
        # MODERATE (Score 6-8)
        energy_score = map_score(energy, 0.015, 0.04, 6, 8)
        energy_status = "Moderate"
        energy_feedback = "Good volume, though slightly more projection would convey more authority."
    else:
        # HIGH (Score 9-10)
        energy_score = 10 if energy > 0.1 else map_score(energy, 0.04, 0.1, 9, 10)
        energy_status = "High / Good"
        energy_feedback = "Excellent energy and projection. You sound authoritative."

    # Return structured data with INTEGER scores
    return {
        "wpm": {
            "val": int(wpm), 
            "score": int(round(wpm_score)), 
            "status": wpm_status, 
            "feedback": wpm_feedback
        },
        "tone": {
            "val": float(round(pitch_std, 2)), 
            "score": int(round(tone_score)), 
            "status": tone_status, 
            "feedback": tone_feedback
        },
        "energy": {
            "val": float(round(energy, 4)), 
            "score": int(round(energy_score)), 
            "status": energy_status, 
            "feedback": energy_feedback
        }
    }

def get_linguistic_metrics_json(text_content, acoustic_context):
    """
    Asks GPT to analyze text AND incorporates Acoustic context for better feedback.
    """
    if not client: return {}

    print("   [Evaluation] Evaluating Linguistics & Integrating Acoustics...")
    
    # We feed the acoustic verdict to the LLM so it generates holistic feedback
    acoustic_summary = (
        f"Acoustic Context: Speaking pace: {acoustic_context['wpm']['status']} (Score: {acoustic_context['wpm']['score']}/10). "
        f"Energy level: {acoustic_context['energy']['status']} (Score: {acoustic_context['energy']['score']}/10). "
        f"Tone: {acoustic_context['tone']['status']}."
    )

    system_prompt = f"""
    You are an expert Interview Coach. 
    {acoustic_summary}
    
    Analyze the candidate's transcript below. 
    
    You MUST return the result in valid JSON format.
    
    JSON Structure:
    {{
        "grammar_score": (int 1-10),
        "clarity_score": (int 1-10),
        "etiquette_score": (int 1-10),
        "filler_word_count": (int),
        "repeated_words": ["word1", "word2"],
        "feedback_summary": "2-3 sentences holistic feedback combining acoustic and linguistic performance.",
        "corrections": [
            {{"mistake": "phrase", "correction": "better version", "reason": "why"}}
        ]
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Transcript: \"{text_content}\""}
            ],
            temperature=0.3
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```"): content = content.replace("```json", "").replace("```", "")
        return json.loads(content)
    except Exception as e:
        print(f"Linguistic JSON failed: {e}")
        return {}

def generate_full_evaluation(text_input, audio_paths=[]):
    """
    Orchestrates the full evaluation over MULTIPLE audio files.
    """
    word_count = len(text_input.split())
    
    # 1. Process ALL Audio Files
    total_duration = 0
    total_energy = 0
    total_pitch = 0
    valid_files_count = 0

    if audio_paths:
        for path in audio_paths:
            if os.path.exists(path):
                raw = get_raw_audio_metrics(path)
                if raw["valid"]:
                    total_duration += raw["duration"]
                    total_energy += raw["energy"]
                    total_pitch += raw["pitch_std"]
                    valid_files_count += 1
    
    # Calculate Averages (avoid div by zero)
    avg_metrics = {
        "total_duration": total_duration, 
        "avg_energy": (total_energy / valid_files_count) if valid_files_count > 0 else 0,
        "avg_pitch": (total_pitch / valid_files_count) if valid_files_count > 0 else 0
    }
    
    # Generate Acoustic Scores
    acoustic_eval = analyze_acoustics_logic(avg_metrics, word_count)
    
    # 2. Linguistics (With Acoustic Context)
    linguistic_eval = get_linguistic_metrics_json(text_input, acoustic_eval)
    
    # 3. Overall Score
    g_score = float(linguistic_eval.get("grammar_score", 1))
    c_score = float(linguistic_eval.get("clarity_score", 1))
    w_score = float(acoustic_eval["wpm"]["score"])
    t_score = float(acoustic_eval["tone"]["score"])
    e_score = float(linguistic_eval.get("etiquette_score", 1))

    scores = [g_score * 0.25, c_score * 0.25, w_score * 0.20, t_score * 0.20, e_score * 0.10]
    overall_score = float(round(sum(scores), 1))

    return {
        "overall_score": overall_score,
        "word_count": int(word_count),
        "transcript": text_input,
        "acoustics": acoustic_eval,
        "linguistics": linguistic_eval
    }