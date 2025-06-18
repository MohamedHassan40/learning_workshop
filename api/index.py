from flask import Flask, render_template, request, redirect, url_for, session
import json
import os
import re
import requests

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)
app.secret_key = "aodsiasdioaosd"

# Load questions data
data_path = os.path.join(os.path.dirname(__file__), "data/questions.json")
with open(data_path, encoding='utf-8') as f:
    data = json.load(f)


def clean_surrogates(obj):
    if isinstance(obj, dict):
        return {k: clean_surrogates(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_surrogates(i) for i in obj]
    elif isinstance(obj, str):
        return re.sub(r'[\ud800-\udfff]', '', obj)
    return obj

@app.context_processor
def inject_data():
    return dict(data=clean_surrogates(data))

@app.route('/')
def index():
    session.clear()
    return render_template('index.html', intro=data['intro'], workshop_data=data)

@app.route('/phase/<int:phase_index>', methods=['GET', 'POST'])
def phase(phase_index):
    phases = data['phases']
    if phase_index < 0 or phase_index >= len(phases):
        return redirect(url_for('index'))

    phase = phases[phase_index]

    if request.method == 'POST':
        # Capture user info
        name = request.form.get('user_name')
        email = request.form.get('user_email')
        session['user_name'] = name
        session['user_email'] = email

        correct_count = 0
        total_questions = len(phase['questions'])
        feedback_list = []

        # Prepare payload for Formspree
        formspree_payload = {
            'name': name,
            'email': email
        }

        # Handle multiple-choice questions
        for i, q in enumerate(phase['questions']):
            key = f"phase{phase_index}_q{i}"
            correct_vals = q['correct'] if isinstance(q['correct'], list) else [q['correct']]

            # Determine selected answers
            if len(correct_vals) > 1:
                selected = request.form.getlist(key)
                is_correct = set(selected) == set(correct_vals)
            else:
                selected = request.form.get(key)
                is_correct = selected in correct_vals

            # Record for feedback
            if is_correct:
                correct_count += 1
            feedback_list.append({
                'question': q['question'],
                'selected': selected,
                'correct': correct_vals,
                'explanation': q.get('explanation'),
                'options': q['options'],
                'is_correct': is_correct
            })

            # Add to Formspree
            formspree_payload[key] = ','.join(selected) if isinstance(selected, list) else (selected or '')

        # Handle open-ended questions
        if 'open_ended' in phase:
            for q in phase['open_ended']:
                field_name = q['field_name']
                answer = request.form.get(field_name, '')
                formspree_payload[field_name] = answer  # Include in submission

        # Send to Formspree
        formspree_url = 'https://formspree.io/f/xvgrrvkw'
        try:
            requests.post(formspree_url, data=formspree_payload)
        except Exception as e:
            app.logger.warning(f"Formspree submission failed: {e}")

        # Save score
        session.setdefault('scores', {})[phase['id']] = correct_count

        return render_template(
            'feedback.html',
            phase_index=phase_index,
            phase=phase,
            correct_count=correct_count,
            total_questions=total_questions,
            feedback=feedback_list,
            total_phases=len(phases)
        )

    # GET request: render question form
    return render_template(
        'phase.html',
        phase_index=phase_index,
        phase=phase,workshop_data=data,
        total_phases=len(phases)
    )

@app.route('/final')
def final():
    if 'scores' not in session:
        return redirect(url_for('index'))

    total_score = sum(session['scores'].values())
    total_questions = sum(len(p['questions']) for p in data['phases'])
    return render_template('final.html', total_score=total_score, total_questions=total_questions)

import re
from urllib.parse import urlparse, parse_qs

def convert_to_embed_url(url):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    video_id = query_params.get("v", [""])[0]
    playlist_id = query_params.get("list", [""])[0]
    embed_url = f"https://www.youtube.com/embed/{video_id}"
    if playlist_id:
        embed_url += f"?list={playlist_id}"
    return embed_url


from flask import render_template
from urllib.parse import urlparse, parse_qs

@app.route('/videos')
def videos():
    youtube_videos = [
        {"title": "How to summarize selected text in Google Docs", "url": "https://www.youtube.com/watch?v=2xVlvfLNlV0&list=PLU8ezI8GYqs5zUuo096bI4_FFgeWAR1ug&index=9"},
        {"title": "How to use Help me Write in Gmail", "url": "https://www.youtube.com/watch?v=PRkCkKhO-3k&list=PLU8ezI8GYqs5zUuo096bI4_FFgeWAR1ug&index=12"},
        {"title": "How to translate captions in Google Meet", "url": "https://www.youtube.com/watch?v=VGqsYmuYgVs&list=PLU8ezI8GYqs5zUuo096bI4_FFgeWAR1ug&index=14"},
        {"title": "Voting in Google Docs", "url": "https://www.youtube.com/watch?v=Kx_gFG9_Ook&list=PLU8ezI8GYqs5zUuo096bI4_FFgeWAR1ug&index=21"},
        {"title": "Mail merge in Gmail", "url": "https://www.youtube.com/watch?v=tIXhg9fBEUY&list=PLU8ezI8GYqs5zUuo096bI4_FFgeWAR1ug&index=31"},
        {"title": "How to RSVP to a meeting with your location in Google Calendar", "url": "https://www.youtube.com/watch?v=xIQAPJAuSzo&list=PLU8ezI8GYqs5zUuo096bI4_FFgeWAR1ug&index=61"},
        {"title": "How to add a background image in Google Keep", "url": "https://www.youtube.com/watch?v=eT_be-GIsKQ&list=PLU8ezI8GYqs5zUuo096bI4_FFgeWAR1ug&index=63"},
        {"title": "Free hidden dictation tool in google docs", "url": "https://www.youtube.com/watch?v=CCpKu5VRmVM&list=PLouep20JDz2NQ-iczT4ewqag9Zx0_2zFj&index=5"},
        {"title": "Tab Groups In Google Chrome | Stay Organized With Tab Groups", "url": "https://www.youtube.com/watch?v=tsBX3Xk36m8&list=PLouep20JDz2NQ-iczT4ewqag9Zx0_2zFj&index=6"},
        {"title": "Unsend an email In Gmail | Gmail Hack", "url": "https://www.youtube.com/watch?v=CYYDMSL8tOc&list=PLouep20JDz2NQ-iczT4ewqag9Zx0_2zFj&index=7"},
        {"title": "Create Tasks In Gmail #shorts", "url": "https://www.youtube.com/watch?v=rSY-uuAQfek&list=PLouep20JDz2NQ-iczT4ewqag9Zx0_2zFj&index=8"},
        {"title": "Gmail's Hidden Side Tab: Huge Productivity Hack", "url": "https://www.youtube.com/watch?v=WTQI4dxCCgY&list=PLouep20JDz2NQ-iczT4ewqag9Zx0_2zFj&index=9"},
        {"title": "Create Google Docs in Seconds with this hack", "url": "https://www.youtube.com/watch?v=qs6_dgzbrXM&list=PLouep20JDz2NQ-iczT4ewqag9Zx0_2zFj&index=10"},
        {"title": "Have Gmail Give you Nudges about important Emails", "url": "https://www.youtube.com/watch?v=qCnaYXADycI&list=PLouep20JDz2NQ-iczT4ewqag9Zx0_2zFj&index=11"},
        {"title": "NotebookLM", "url": "https://www.youtube.com/watch?v=YTfhgzDZZ0w&t=2s"},

    ]

    # Function to convert watch URL to embed URL
    def convert_to_embed_url(url):
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        video_id = query_params.get("v", [""])[0]
        playlist_id = query_params.get("list", [""])[0]
        embed_url = f"https://www.youtube.com/embed/{video_id}"
        if playlist_id:
            embed_url += f"?list={playlist_id}"
        return embed_url

    # Update video URLs
    for video in youtube_videos:
        video["url"] = convert_to_embed_url(video["url"])

    return render_template("videos.html", videos=youtube_videos,workshop_data=data)




if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)