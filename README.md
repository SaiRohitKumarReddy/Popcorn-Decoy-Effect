# Popcorn Choice Game - Student Mode

This is the student-facing prototype of the Popcorn Decoy classroom experiment.

## What it does

- Student enters a name and clicks **Continue**.
- A new student is automatically assigned to Group A or Group B.
- The balancing rule keeps the difference between the two group counts at no more than 1.
- Returning names keep their original group.
- Group A sees Small and Large.
- Group B sees Small, Medium, and Large.
- Clicking a popcorn card only selects it in the current Streamlit session.
- The choice is written to storage only after **Submit Response** is clicked.
- A submitted name cannot submit a second response.
- Names are normalized so `Rahul Sharma`, `rahul sharma`, and ` Rahul Sharma ` are treated as the same participant.

## Local storage

For this prototype, data is stored in:

`data/responses.csv`

The CSV contains:

- name_key
- name
- group
- choice
- status
- created_at
- submitted_at

Google Sheets can replace this local storage layer later without changing the student flow.

## Run in PyCharm

1. Open the `popcorn_student_mode` folder as a PyCharm project.
2. Open the PyCharm terminal.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Start the app:

```bash
streamlit run app.py
```

5. Open the local URL shown by Streamlit, normally:

`http://localhost:8501`

## Reset test data

Stop Streamlit, open `data/responses.csv`, and remove the participant rows while leaving the header row.
