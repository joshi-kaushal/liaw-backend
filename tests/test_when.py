import unittest
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from app.bot.when import (
    parse_when,
    parse_add_input,
    format_confirmation_message,
    ParsedSchedule,
    get_timezone,
)

TZ = get_timezone("Asia/Kolkata")


class TestWhenParser(unittest.TestCase):
    def test_no_when_simple_task(self):
        schedule, title = parse_add_input("Buy groceries", TZ)
        now = datetime.now(TZ)
        self.assertEqual(schedule.due_date, now.date())
        self.assertIsNone(schedule.due_time)
        self.assertFalse(schedule.has_explicit_time)
        self.assertEqual(title, "Buy groceries")

    def test_command_prefix_stripped(self):
        schedule, title = parse_add_input("/add Buy groceries", TZ)
        now = datetime.now(TZ)
        self.assertEqual(schedule.due_date, now.date())
        self.assertIsNone(schedule.due_time)
        self.assertEqual(title, "Buy groceries")

    def test_non_date_start_word(self):
        # "May" without digit should not be treated as a date
        schedule, title = parse_add_input("/add May the force be with you", TZ)
        now = datetime.now(TZ)
        self.assertEqual(schedule.due_date, now.date())
        self.assertIsNone(schedule.due_time)
        self.assertEqual(title, "May the force be with you")

    def test_keyword_tomorrow_all_day(self):
        schedule, title = parse_add_input("/add tomorrow Buy milk", TZ)
        now = datetime.now(TZ)
        tomorrow = now.date() + timedelta(days=1)
        self.assertEqual(schedule.due_date, tomorrow)
        self.assertIsNone(schedule.due_time)
        self.assertFalse(schedule.has_explicit_time)
        self.assertEqual(title, "Buy milk")

    def test_keyword_tmrw(self):
        schedule, title = parse_add_input("tmrw Finish slides", TZ)
        now = datetime.now(TZ)
        tomorrow = now.date() + timedelta(days=1)
        self.assertEqual(schedule.due_date, tomorrow)
        self.assertIsNone(schedule.due_time)
        self.assertEqual(title, "Finish slides")

    def test_keyword_tomorrow_with_time(self):
        schedule, title = parse_add_input("/add tomorrow 5pm Team standup", TZ)
        now = datetime.now(TZ)
        tomorrow = now.date() + timedelta(days=1)
        self.assertEqual(schedule.due_date, tomorrow)
        self.assertEqual(schedule.due_time, "17:00")
        self.assertTrue(schedule.has_explicit_time)
        self.assertEqual(title, "Team standup")

    def test_keyword_tomorrow_with_at_time(self):
        schedule, title = parse_add_input("/add tomorrow at 10:30am Sprint review", TZ)
        now = datetime.now(TZ)
        tomorrow = now.date() + timedelta(days=1)
        self.assertEqual(schedule.due_date, tomorrow)
        self.assertEqual(schedule.due_time, "10:30")
        self.assertTrue(schedule.has_explicit_time)
        self.assertEqual(title, "Sprint review")

    def test_keyword_tonight(self):
        schedule, title = parse_add_input("/add tonight Watch movie", TZ)
        self.assertEqual(schedule.due_time, "21:00")
        self.assertTrue(schedule.has_explicit_time)
        self.assertEqual(title, "Watch movie")

    def test_relative_duration(self):
        schedule, title = parse_add_input("/add in 2 hours Check oven", TZ)
        now = datetime.now(TZ)
        expected_target = now + timedelta(hours=2)
        self.assertEqual(schedule.due_date, expected_target.date())
        self.assertEqual(
            schedule.due_time,
            f"{expected_target.hour:02d}:{expected_target.minute:02d}",
        )
        self.assertTrue(schedule.has_explicit_time)
        self.assertEqual(title, "Check oven")

    def test_weekday(self):
        schedule, title = parse_add_input("/add next monday Gym", TZ)
        now = datetime.now(TZ)
        self.assertEqual(schedule.due_date.weekday(), 0)
        self.assertGreater(schedule.due_date, now.date())
        self.assertIsNone(schedule.due_time)
        self.assertEqual(title, "Gym")

    def test_weekday_with_time(self):
        schedule, title = parse_add_input("/add friday at 3:30pm Weekly sync", TZ)
        now = datetime.now(TZ)
        self.assertEqual(schedule.due_date.weekday(), 4)
        self.assertGreaterEqual(schedule.due_date, now.date())
        self.assertEqual(schedule.due_time, "15:30")
        self.assertEqual(title, "Weekly sync")

    def test_named_date(self):
        schedule, title = parse_add_input("/add 25 oct Dentist appointment", TZ)
        self.assertEqual(schedule.due_date.month, 10)
        self.assertEqual(schedule.due_date.day, 25)
        self.assertIsNone(schedule.due_time)
        self.assertEqual(title, "Dentist appointment")

    def test_named_date_with_time_and_year(self):
        schedule, title = parse_add_input("/add 15 nov 2028 at 14:00 Workshop", TZ)
        self.assertEqual(schedule.due_date, date(2028, 11, 15))
        self.assertEqual(schedule.due_time, "14:00")
        self.assertEqual(title, "Workshop")

    def test_numeric_date_dmy(self):
        schedule, title = parse_add_input("/add 28/11 Submit report", TZ)
        self.assertEqual(schedule.due_date.month, 11)
        self.assertEqual(schedule.due_date.day, 28)
        self.assertIsNone(schedule.due_time)
        self.assertEqual(title, "Submit report")

    def test_numeric_date_ymd(self):
        schedule, title = parse_add_input("/add 2027-06-15 Renew passport", TZ)
        self.assertEqual(schedule.due_date, date(2027, 6, 15))
        self.assertIsNone(schedule.due_time)
        self.assertEqual(title, "Renew passport")

    def test_bare_time(self):
        schedule, title = parse_add_input("/add 10pm Call parents", TZ)
        self.assertEqual(schedule.due_time, "22:00")
        self.assertTrue(schedule.has_explicit_time)
        self.assertEqual(title, "Call parents")

    def test_format_confirmation_message_today_all_day(self):
        now = datetime.now(TZ)
        sched = ParsedSchedule(
            due_date=now.date(), due_time=None, has_explicit_time=False
        )
        msg = format_confirmation_message("Buy milk", sched, TZ)
        self.assertEqual(msg, "✅ Added: *Buy milk*")

    def test_format_confirmation_message_tomorrow_all_day(self):
        now = datetime.now(TZ)
        sched = ParsedSchedule(
            due_date=now.date() + timedelta(days=1),
            due_time=None,
            has_explicit_time=False,
        )
        msg = format_confirmation_message("Buy milk", sched, TZ)
        self.assertEqual(msg, "✅ Added: *Buy milk* for tomorrow")

    def test_format_confirmation_message_tomorrow_timed(self):
        now = datetime.now(TZ)
        sched = ParsedSchedule(
            due_date=now.date() + timedelta(days=1),
            due_time="17:00",
            has_explicit_time=True,
        )
        msg = format_confirmation_message("Team standup", sched, TZ)
        self.assertEqual(msg, "✅ Added: *Team standup* for tomorrow at 5:00 PM")

    def test_format_confirmation_message_future_date(self):
        sched = ParsedSchedule(
            due_date=date(2028, 5, 20),
            due_time="14:30",
            has_explicit_time=True,
        )
        msg = format_confirmation_message("Conference talk", sched, TZ)
        self.assertIn("20 May", msg)
        self.assertIn("2:30 PM", msg)


    def test_next_week(self):
        schedule, title = parse_add_input("/add next week Weekly report", TZ)
        now = datetime.now(TZ)
        self.assertEqual(schedule.due_date.weekday(), 0)
        self.assertGreater(schedule.due_date, now.date())
        self.assertIsNone(schedule.due_time)
        self.assertEqual(title, "Weekly report")

    def test_next_month(self):
        schedule, title = parse_add_input("/add next month Pay credit card", TZ)
        now = datetime.now(TZ)
        self.assertGreater(schedule.due_date, now.date())
        self.assertEqual(title, "Pay credit card")

    def test_plain_text_with_when(self):
        schedule, title = parse_add_input("tomorrow 5pm Team sync", TZ)
        now = datetime.now(TZ)
        tomorrow = now.date() + timedelta(days=1)
        self.assertEqual(schedule.due_date, tomorrow)
        self.assertEqual(schedule.due_time, "17:00")
        self.assertEqual(title, "Team sync")

    def test_bare_time_past_shifts_to_tomorrow(self):
        # 12:01am on any reasonable run time during the day has already passed
        schedule, title = parse_add_input("/add 12:01am Midnight reflection", TZ)
        now = datetime.now(TZ)
        # If current time is past 00:01, it must be shifted to tomorrow
        if (now.hour, now.minute) >= (0, 1):
            self.assertEqual(schedule.due_date, now.date() + timedelta(days=1))
        self.assertEqual(schedule.due_time, "00:01")
        self.assertEqual(title, "Midnight reflection")


if __name__ == "__main__":
    unittest.main()
