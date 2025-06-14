from flask import Flask, render_template, request, redirect, url_for, session
import json
import os
import re

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)
app.secret_key = "aodsiasdioaosd"

# Load questions data
DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "questions.json")
with open(DATA_PATH, encoding='utf-8') as f:
    data = json.load(f)


def clean_surrogates(obj):
    if isinstance(obj, dict):
        return {k: clean_surrogates(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_surrogates(i) for i in obj]
    elif isinstance(obj, str):
        return re.sub(r'[\ud800-\udfff]', '', obj)  # Remove surrogate characters
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
        correct_count = 0
        total_questions = len(phase['questions'])
        feedback_list = []

        for i, q in enumerate(phase['questions']):
            key_name = f"phase{phase_index}_q{i}"
            selected = request.form.get(key_name)
            is_correct = selected == q['correct']
            if is_correct:
                correct_count += 1

            feedback_list.append({
                "question": q["question"],
                "selected": selected,
                "correct": q["correct"],
                "explanation": q["explanation"],
                "options": q["options"],
                "is_correct": is_correct
            })

        if 'scores' not in session:
            session['scores'] = {}
        session['scores'][phase['id']] = correct_count

        return render_template(
            'feedback.html',
            phase_index=phase_index,
            phase=phase,
            correct_count=correct_count,
            total_questions=total_questions,
            feedback=feedback_list,
            total_phases=len(phases)
        )

    return render_template(
        'phase.html',
        phase_index=phase_index,
        phase=phase,
        total_phases=len(phases)
    )


@app.route('/final')
def final():
    if 'scores' not in session:
        return redirect(url_for('index'))

    total_score = sum(session['scores'].values())
    total_questions = sum(len(p['questions']) for p in data['phases'])

    return render_template('final.html', total_score=total_score, total_questions=total_questions)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
