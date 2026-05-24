"""
test_task_breakdown.py
Unit tests for the task_breakdown module.

Run with:
    python test_task_breakdown.py            # built-in runner (verbose)
    python -m pytest test_task_breakdown.py  # pytest (if installed)
"""

import json
import unittest

from task_breakdown import breakdown_goal, breakdown_goal_json, _detect_category


class TestSubtaskCount(unittest.TestCase):

    def _assert_in_range(self, goal: str):
        result = breakdown_goal(goal)
        self.assertGreaterEqual(len(result), 3, f"Too few subtasks for: {goal!r}")
        self.assertLessEqual(len(result), 7, f"Too many subtasks for: {goal!r}")

    def test_short_goal_at_least_3(self):
        self._assert_in_range("Run")

    def test_medium_goal(self):
        self._assert_in_range("Study for my exams")

    def test_long_goal(self):
        self._assert_in_range("Build a full-stack web application with user auth and a dashboard")

    def test_all_demo_goals(self):
        goals = [
            "Build my portfolio website",
            "Study for my final university exams",
            "Train for a half marathon",
            "Launch my e-commerce startup",
            "Organize my daily life and build better habits",
            "Learn Spanish",
            "Fix the login bug in my app",
        ]
        for g in goals:
            self._assert_in_range(g)


class TestReturnTypes(unittest.TestCase):

    def test_returns_list(self):
        result = breakdown_goal("Build my portfolio website")
        self.assertIsInstance(result, list)

    def test_all_items_are_non_empty_strings(self):
        result = breakdown_goal("Create a mobile app for my fitness tracking")
        for item in result:
            self.assertIsInstance(item, str)
            self.assertGreater(len(item), 5)

    def test_json_output_is_valid(self):
        raw = breakdown_goal_json("Launch a business")
        parsed = json.loads(raw)
        self.assertIsInstance(parsed, list)
        self.assertGreater(len(parsed), 0)

    def test_json_matches_list_output(self):
        goal = "Study for my certification exam"
        self.assertEqual(breakdown_goal(goal), json.loads(breakdown_goal_json(goal)))


class TestCategoryDetection(unittest.TestCase):

    def test_software(self):
        self.assertEqual(_detect_category("Build a React web app with a REST API"), "software")

    def test_software_portfolio(self):
        self.assertEqual(_detect_category("Create my developer portfolio website"), "software")

    def test_studying(self):
        self.assertEqual(_detect_category("Study for my university final exam"), "studying")

    def test_studying_learn(self):
        self.assertEqual(_detect_category("Learn Python programming"), "studying")

    def test_fitness(self):
        self.assertEqual(_detect_category("Start a gym workout and lose weight"), "fitness")

    def test_fitness_marathon(self):
        self.assertEqual(_detect_category("Train for a marathon"), "fitness")

    def test_business(self):
        self.assertEqual(_detect_category("Launch my e-commerce startup"), "business")

    def test_business_freelance(self):
        self.assertEqual(_detect_category("Start a freelance consulting agency"), "business")

    def test_personal(self):
        self.assertEqual(_detect_category("Build a daily meditation habit"), "personal")

    def test_personal_organize(self):
        self.assertEqual(_detect_category("Organize my home and finances"), "personal")


class TestSubtaskContent(unittest.TestCase):

    def _words_in(self, result: list, *words) -> bool:
        combined = " ".join(result).lower()
        return any(w in combined for w in words)

    def test_software_subtasks_mention_key_concepts(self):
        result = breakdown_goal("Build a portfolio website")
        self.assertTrue(self._words_in(result, "architecture", "environment", "features", "deploy"))

    def test_studying_subtasks_mention_key_concepts(self):
        result = breakdown_goal("Prepare for my university exams")
        self.assertTrue(self._words_in(result, "notes", "practice", "review", "schedule"))

    def test_fitness_subtasks_mention_key_concepts(self):
        result = breakdown_goal("Train for a half marathon")
        self.assertTrue(self._words_in(result, "workout", "warm", "track", "nutrition"))

    def test_business_subtasks_mention_key_concepts(self):
        result = breakdown_goal("Launch my online business")
        self.assertTrue(self._words_in(result, "market", "mvp", "customer", "revenue"))

    def test_personal_subtasks_mention_key_concepts(self):
        result = breakdown_goal("Improve my daily habits and routine")
        self.assertTrue(self._words_in(result, "goal", "habit", "milestone", "accountable"))

    def test_no_duplicate_subtasks(self):
        result = breakdown_goal("Build a full-stack web application with authentication")
        self.assertEqual(len(result), len(set(result)))


class TestEdgeCases(unittest.TestCase):

    def test_empty_string(self):
        result = breakdown_goal("")
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_whitespace_only(self):
        result = breakdown_goal("   ")
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_unknown_category_falls_back_gracefully(self):
        result = breakdown_goal("Become a better cook")
        self.assertIsInstance(result, list)
        self.assertGreaterEqual(len(result), 3)

    def test_very_long_goal(self):
        long_goal = (
            "Build a full-featured e-commerce web application with user authentication, "
            "a product catalog, shopping cart, payment integration, and an admin dashboard"
        )
        result = breakdown_goal(long_goal)
        self.assertLessEqual(len(result), 7)

    def test_single_word_goal(self):
        result = breakdown_goal("Exercise")
        self.assertIsInstance(result, list)
        self.assertGreaterEqual(len(result), 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
