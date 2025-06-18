import streamlit as st
import json
import random
from pathlib import Path

def load_all_quiz_data(directory_path):
    """
    Loads and aggregates quiz data from all JSON files in a specified directory.

    This function scans the directory for files ending in '.json', reads each one,
    and collects all the exams into a single list. It includes robust error handling
    for missing directories, files, or malformed JSON.
    
    Args:
        directory_path (Path): The path to the directory containing quiz JSON files.

    Returns:
        list: A list of all exam dictionaries aggregated from the files, 
              or None if the directory doesn't exist. Returns an empty list
              if the directory is empty or contains no valid quiz files.
    """
    all_exams = []
    
    # Verify that the specified directory exists
    if not directory_path.is_dir():
        st.error(f"Error: The directory '{directory_path}' was not found.")
        st.info("Please create a 'json' folder in the same directory as the app and place your quiz JSON files (e.g., 'quiz_1.json') inside it.")
        return None

    # Find all files in the directory with a .json extension
    json_files = list(directory_path.glob("*.json"))

    if not json_files:
        st.warning(f"No JSON files were found in the '{directory_path}' directory.")
        return []

    # Loop through each found JSON file and process its content
    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Expecting a top-level key "exams" which contains a list of exam objects
                if "exams" in data and isinstance(data["exams"], list):
                    all_exams.extend(data["exams"])
                else:
                    st.warning(f"Skipping '{file_path.name}': The file does not have the expected format (a root key 'exams' containing a list).")
        except json.JSONDecodeError:
            st.error(f"Error parsing '{file_path.name}': This is not a valid JSON file. Please check its syntax.")
        except Exception as e:
            st.error(f"An unexpected error occurred while reading '{file_path.name}': {e}")
            
    return all_exams

def reset_quiz_state(full_reset=False):
    """
    Resets the Streamlit session state variables for a new quiz attempt.
    
    Args:
        full_reset (bool): If True, resets the entire application state including
                           mode.
    """
    st.session_state.question_index = 0
    st.session_state.score = 0
    st.session_state.user_answers = {}
    st.session_state.quiz_started = False
    st.session_state.current_random_question = None
    st.session_state.exam_date = None

    if full_reset:
        st.session_state.mode = "Exam Quiz"

def display_exam_question(exam):
    """
    Displays the current question for the selected exam, handles user input,
    and manages navigation between questions. In this mode, feedback is deferred until the end.
    """
    questions = exam.get("questions", [])
    q_index = st.session_state.question_index

    if q_index < len(questions):
        question = questions[q_index]
        st.subheader(f"Question {q_index + 1}/{len(questions)}")
        
        with st.container(border=True):
            st.write(question.get("question", "This question appears to be empty."))
            options_dict = question.get("options", {})
            options_list = [f"{k.upper()}) {v}" for k, v in options_dict.items()]
            
            with st.form(key=f"q_form_{q_index}"):
                user_answer = st.radio("Choose your answer:", options_list, key=f"q_{q_index}")
                submitted = st.form_submit_button("Submit and Next")

                if submitted:
                    # Process and store the answer
                    selected_key = user_answer.split(')')[0].lower()
                    st.session_state.user_answers[q_index] = selected_key
                    
                    is_correct = selected_key == question.get("answer", "").lower()
                    if is_correct:
                        st.session_state.score += 1
                    
                    # Increment index and rerun to show the next question
                    st.session_state.question_index += 1
                    st.rerun()
    else:
        # Once all questions are answered, show the final review
        show_final_score_and_review(exam)

def show_final_score_and_review(exam):
    """
    Displays the final score and provides a comprehensive review of all answers
    at the end of an exam, including the options for each question.
    """
    questions = exam.get("questions", [])
    st.header(f"Quiz Finished! Your Score: {st.session_state.score}/{len(questions)}")

    st.subheader("Review Your Answers")
    for i, q in enumerate(questions):
        user_ans_key = st.session_state.user_answers.get(i)
        correct_ans_key = q.get("answer", "").lower()
        options_dict = q.get("options", {})
        
        with st.container(border=True):
            # Display Question
            st.markdown(f"**Question {i+1}:** {q.get('question', '')}")
            st.markdown("---")
            
            # Display Options
            st.write("**Options:**")
            for key, value in options_dict.items():
                st.markdown(f"- **{key.upper()}:** {value}")
            st.markdown("---")

            # Display Result and Explanation
            if user_ans_key == correct_ans_key:
                st.success(f"Your answer: **{user_ans_key.upper()}**. Correct!")
            else:
                st.error(f"Your answer: **{user_ans_key.upper() if user_ans_key else 'Not answered'}**. Correct answer: **{correct_ans_key.upper()}**.")
            
            with st.expander("View Explanation"):
                st.info(q.get("solution", "No solution provided."))

def display_random_question(all_questions):
    """
    Selects and displays a random question. Solution is always shown instantly.
    """
    st.header("Random Question Mode")
    
    col1, col2 = st.columns([3, 1])
    with col2:
        # Button to fetch a new question
        if st.button("Get New Random Question", use_container_width=True):
            st.session_state.current_random_question = random.choice(all_questions)
            # Clear previous answer state
            if 'random_answer_submitted' in st.session_state:
                del st.session_state['random_answer_submitted']
            st.rerun()
    
    # Initialize with a question if none is selected
    if st.session_state.current_random_question is None:
         st.session_state.current_random_question = random.choice(all_questions)

    question = st.session_state.current_random_question
    if question:
        with st.container(border=True):
            st.write(question.get("question", ""))
            options_dict = question.get("options", {})
            options_list = [f"{k.upper()}) {v}" for k, v in options_dict.items()]

            with st.form(key="random_q_form"):
                user_answer = st.radio("Your answer:", options_list, key="random_q")
                submitted = st.form_submit_button("Submit")

                if submitted:
                    st.session_state.random_answer_submitted = True
                    st.session_state.last_random_answer = user_answer

            # Display feedback if an answer has been submitted
            if st.session_state.get('random_answer_submitted'):
                last_answer = st.session_state.get('last_random_answer', '')
                selected_key = last_answer.split(')')[0].lower()
                if selected_key == question.get("answer", "").lower():
                    st.success("Correct!")
                else:
                    st.error(f"Incorrect. The correct answer is {question.get('answer', 'N/A').upper()}.")
                with st.expander("View Explanation", expanded=True):
                    st.info(question.get("solution", "No solution provided."))


def main():
    """
    Main function to orchestrate the Streamlit application.
    """
    st.set_page_config(page_title="Finance Quiz", layout="wide")
    st.title("Corporate Governance and Finance Quiz")

    # --- Data Loading ---
    json_dir_path = Path("json/")
    exams = load_all_quiz_data(json_dir_path)

    if exams is None: # Critical error, e.g., folder not found
        return 
    if not exams: # Folder found, but empty or no valid files
        st.warning("Please add valid quiz JSON files to the 'json' directory to begin.")
        return
        
    all_questions = [q for exam in exams for q in exam.get("questions", [])]

    # --- State Initialization ---
    if 'mode' not in st.session_state:
        reset_quiz_state(full_reset=True)

    # --- Sidebar UI ---
    with st.sidebar:
        st.header("⚙️ Quiz Options")
        
        mode = st.radio("Choose Quiz Mode", ["Exam Quiz", "Random Question"], key="mode_selection")
        if mode != st.session_state.mode:
            st.session_state.mode = mode
            reset_quiz_state()
            st.rerun()
        
        st.divider()
        if st.button("🔄 Reset Quiz", use_container_width=True):
            reset_quiz_state(full_reset=True)
            st.rerun()

    # --- Main Page Logic ---
    if st.session_state.mode == "Exam Quiz":
        st.header("Exam Quiz Mode")
        exam_dates = sorted(list(set(exam["date"] for exam in exams)))
        
        # Set a default exam date if none is selected
        if st.session_state.exam_date is None and exam_dates:
            st.session_state.exam_date = exam_dates[0]

        selected_exam_date = st.selectbox("Select an Exam", exam_dates, index=exam_dates.index(st.session_state.exam_date) if st.session_state.exam_date in exam_dates else 0)

        if selected_exam_date != st.session_state.exam_date:
            st.session_state.exam_date = selected_exam_date
            reset_quiz_state()
            st.rerun()
            
        if not st.session_state.quiz_started:
            if st.button("▶️ Start Quiz", type="primary"):
                st.session_state.quiz_started = True
                st.rerun()
        else:
            # Find the first exam that matches the selected date
            exam = next((exam for exam in exams if exam["date"] == st.session_state.exam_date), None)
            if exam:
                display_exam_question(exam)

    elif st.session_state.mode == "Random Question":
        if all_questions:
            display_random_question(all_questions)
        else:
            st.warning("No questions are available in any of the loaded files.")

if __name__ == "__main__":
    main()
