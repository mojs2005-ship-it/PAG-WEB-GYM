"""End-to-end tests driven by a real Chrome browser against a real
running instance of the app (see conftest.py's `live_server`).

Each test simulates a real user flow: create a record through the UI,
navigate like a user would (clicking links, not hitting URLs directly),
and verify the result is visible on screen — the same thing a QA
tester clicking through the app manually would check.
"""

from pages import AddSessionPage, ExerciseDetailPage, HomePage, SessionsPage


def test_create_session_appears_in_sessions_list(driver, live_server):
    """Flow: create a session -> verify it shows up in the sessions list."""
    sessions_page = AddSessionPage(driver, live_server).open().create("Selenium Push Day")

    assert sessions_page.has_session("Selenium Push Day")


def test_create_exercise_appears_in_session_detail(driver, live_server):
    """Flow: create a session -> open it -> add an exercise -> verify it's listed."""
    sessions_page = AddSessionPage(driver, live_server).open().create("Selenium Leg Day")
    session_detail = sessions_page.open_session("Selenium Leg Day")

    session_detail = session_detail.add_exercise().create("Squat")

    assert session_detail.has_exercise("Squat")


def test_add_set_appears_in_exercise_detail_and_updates_dashboard(driver, live_server):
    """Flow: create session -> exercise -> set, verify the set is listed,
    then verify the home dashboard's total set count increased."""
    sets_before = HomePage(driver, live_server).open().total_sets

    sessions_page = AddSessionPage(driver, live_server).open().create("Selenium Pull Day")
    session_detail = sessions_page.open_session("Selenium Pull Day")
    session_detail = session_detail.add_exercise().create("Deadlift")
    exercise_detail = session_detail.open_exercise("Deadlift")

    exercise_detail: ExerciseDetailPage = exercise_detail.add_set().create(weight=225, reps=5)

    assert exercise_detail.has_set("225.0", 5)

    sets_after = HomePage(driver, live_server).open().total_sets
    assert sets_after == sets_before + 1


def test_delete_session_removes_it_from_list(driver, live_server):
    """Flow: create a session -> delete it (accepting the confirm dialog)
    -> verify it no longer appears in the sessions list (search/verification)."""
    sessions_page = AddSessionPage(driver, live_server).open().create("Selenium Temp Session")
    assert sessions_page.has_session("Selenium Temp Session")

    sessions_page.delete_session("Selenium Temp Session")
    sessions_page = SessionsPage(driver, live_server).open()

    assert not sessions_page.has_session("Selenium Temp Session")
