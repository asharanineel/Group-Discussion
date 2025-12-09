def get_score_color(score):
    """Returns color based on score 1-10."""
    if score >= 8: return "#28a745" # Green
    if score >= 5: return "#ffc107" # Orange
    return "#dc3545" # Red

def get_feedback_email_content(user_name, gd_topic, user_responses, eval_data):
    """
    Generates Professional HTML Email with Tables.
    eval_data is the Dictionary from evaluation.py
    """
    
    acoustics = eval_data.get("acoustics", {})
    linguistics = eval_data.get("linguistics", {})
    corrections = linguistics.get("corrections", [])
    overall_score = eval_data.get("overall_score", 0)
    
    # Helper to generate rows
    def metric_row(name, metric_obj):
        score = metric_obj.get('score', 0)
        color = get_score_color(score)
        return f"""
        <tr>
            <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>{name}</strong></td>
            <td style="padding: 10px; border-bottom: 1px solid #ddd;">
                <span style="background-color: {color}; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold;">{score}/10</span>
            </td>
            <td style="padding: 10px; border-bottom: 1px solid #ddd;">{metric_obj.get('status', 'N/A')}</td>
            <td style="padding: 10px; border-bottom: 1px solid #ddd; font-size: 13px; color: #555;">{metric_obj.get('feedback', '')}</td>
        </tr>
        """

    # Corrections HTML
    correction_rows = ""
    if corrections:
        for c in corrections:
            correction_rows += f"""
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #eee; color: #dc3545;"><s>{c.get('mistake')}</s></td>
                <td style="padding: 8px; border-bottom: 1px solid #eee; color: #28a745;"><strong>{c.get('correction')}</strong></td>
                <td style="padding: 8px; border-bottom: 1px solid #eee; font-size: 12px;">{c.get('reason')}</td>
            </tr>
            """
    else:
        correction_rows = "<tr><td colspan='3' style='padding:10px;'>No major grammatical errors detected. Good job!</td></tr>"

    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #333; background-color: #f4f4f4; padding: 20px; }}
            .container {{ max-width: 700px; margin: 0 auto; background: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
            h2 {{ color: #2c3e50; border-bottom: 2px solid #2c3e50; padding-bottom: 10px; }}
            h3 {{ color: #16a085; margin-top: 25px; }}
            .score-box {{ text-align: center; background: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; border: 1px solid #e9ecef; }}
            .big-score {{ font-size: 32px; font-weight: bold; color: {get_score_color(overall_score)}; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            th {{ text-align: left; background-color: #f8f9fa; padding: 10px; border-bottom: 2px solid #ddd; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>AI Interviewer Feedback</h2>
            <p>Dear {user_name},</p>
            <p>Here is your detailed performance report for the topic: <strong>{gd_topic}</strong>.</p>
            
            <div class="score-box">
                <div>Overall Performance Score</div>
                <div class="big-score">{overall_score}/10</div>
                <div style="font-size: 12px; color: #777;">Based on Acoustics, Grammar, and Content</div>
            </div>

            <h3>🗣️ Acoustic Analysis (How You Sound)</h3>
            <table>
                <thead>
                    <tr>
                        <th width="20%">Metric</th>
                        <th width="15%">Score</th>
                        <th width="20%">Status</th>
                        <th>Feedback</th>
                    </tr>
                </thead>
                <tbody>
                    {metric_row("Speaking Pace", acoustics.get("wpm", {}))}
                    {metric_row("Tone / Pitch", acoustics.get("tone", {}))}
                    {metric_row("Energy Level", acoustics.get("energy", {}))}
                </tbody>
            </table>

            <h3>📝 Linguistic Analysis (Content Quality)</h3>
            <table>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Grammar</strong></td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;"><span style="font-weight:bold;">{linguistics.get('grammar_score')}/10</span></td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Filler Words Found:</strong> {linguistics.get('filler_word_count')}</td>
                </tr>
                 <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Clarity</strong></td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;"><span style="font-weight:bold;">{linguistics.get('clarity_score')}/10</span></td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Repeated Words:</strong> {", ".join(linguistics.get('repeated_words', []))}</td>
                </tr>
                 <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Etiquette</strong></td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;"><span style="font-weight:bold;">{linguistics.get('etiquette_score')}/10</span></td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;"></td>
                </tr>
            </table>

            <h3>🔧 Grammar & Improvement Area</h3>
            <table>
                <thead>
                    <tr>
                        <th width="30%">Your Mistake</th>
                        <th width="30%">Corrected Version</th>
                        <th>Why?</th>
                    </tr>
                </thead>
                <tbody>
                    {correction_rows}
                </tbody>
            </table>

            <div style="margin-top: 30px; padding: 15px; background-color: #e8f6f3; border-left: 5px solid #1abc9c; border-radius: 4px;">
                <strong>💡 Summary Feedback:</strong><br>
                {linguistics.get('feedback_summary', 'No summary generated.')}
            </div>

            <p style="margin-top: 30px; font-size: 12px; color: #aaa; text-align: center;">Generated by AI Interviewer System</p>
        </div>
    </body>
    </html>
    """

    text_content = f"Overall Score: {overall_score}/10. Please view the HTML email for detailed feedback."
    return html_content, text_content