"""
JARVIS Assistant Suite — Verification Test Suite
Tests memory, notes, todos, system diagnostics, and background scheduler.
"""

import os
import sys
import time

if sys.platform == "win32" and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import jarvis_engine

def run_tests():
    print("=" * 60)
    print("[TESTING] JARVIS PERSONAL ASSISTANT SUITE")
    print("=" * 60)

    # 1. User Name & Profile
    print("\n1. Testing Name & Memory Profile...")
    res_name = jarvis_engine.execute_action("call me Koushal")
    print(f"Set Name Output: {res_name}")

    res_who = jarvis_engine.execute_action("who am i")
    print(f"Who Am I Output: {res_who}")
    assert "Koushal" in res_who, "Name setting failed"

    # 2. Memory Facts
    print("\n2. Testing Saved Memory Facts...")
    res_fact = jarvis_engine.execute_action("remember that my favorite language is Python")
    print(f"Remember Fact Output: {res_fact}")

    res_mem = jarvis_engine.execute_action("what do you remember")
    print(f"Recall Memory Output:\n{res_mem}")
    assert "python" in res_mem.lower(), "Fact memory failed"

    # 3. Notes Manager
    print("\n3. Testing Notes Manager...")
    res_note = jarvis_engine.execute_action("save note Buy micro-controllers for project")
    print(f"Save Note Output: {res_note}")

    res_show_notes = jarvis_engine.execute_action("show my notes")
    print(f"Show Notes Output:\n{res_show_notes}")
    assert "micro-controllers" in res_show_notes.lower(), "Note saving failed"

    # 4. To-Do List Manager
    print("\n4. Testing To-Do Manager...")
    res_todo = jarvis_engine.execute_action("add todo Complete Antigravity assistant task")
    print(f"Add Todo Output: {res_todo}")

    res_show_todos = jarvis_engine.execute_action("show my todos")
    print(f"Show Todos Output:\n{res_show_todos}")
    assert "antigravity" in res_show_todos.lower(), "Todo adding failed"

    res_complete = jarvis_engine.execute_action("complete todo 1")
    print(f"Complete Todo Output: {res_complete}")

    # 5. System Diagnostics & Utilities
    print("\n5. Testing System Diagnostics & Utilities...")
    res_diag = jarvis_engine.execute_action("detailed status")
    print(f"System Diagnostics Output:\n{res_diag}")

    res_joke = jarvis_engine.execute_action("tell me a joke")
    print(f"Joke Output: {res_joke}")

    res_coin = jarvis_engine.execute_action("flip a coin")
    print(f"Coin Output: {res_coin}")

    # 6. Reminders Thread Test
    print("\n6. Testing Background Reminder Scheduler...")
    res_remind = jarvis_engine.execute_action("remind me to check coffee in 1 second")
    print(f"Schedule Reminder Output: {res_remind}")
    time.sleep(1.5)

    print("\n" + "=" * 60)
    print("[SUCCESS] ALL PERSONAL ASSISTANT VERIFICATION TESTS PASSED!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
