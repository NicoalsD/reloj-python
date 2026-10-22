"""Settings that can be tuned without touching the logic."""

# Linux files the clock reads instead of using the time module.
PROC_STAT_PATH = "/proc/stat"
PROC_UPTIME_PATH = "/proc/uptime"
RTC_EPOCH_PATH = "/sys/class/rtc/rtc0/since_epoch"
LOCAL_ZONE_PATH = "/etc/localtime"
ZONEINFO_DIR = "/usr/share/zoneinfo/"

# Animation.
FRAMES_PER_SECOND = 10

# Screen layout, in terminal cells.
SCREEN_WIDTH, SCREEN_HEIGHT = 100, 27
CLOCK_LEFT, CLOCK_TOP = 3, 2
CLOCK_COLUMNS, CLOCK_ROWS = 46, 23
PANEL_LEFT, PANEL_RIGHT = 52, 97

# Features.
WORLD_ZONES = [
    ("Bogotá", "America/Bogota"),
    ("Madrid", "Europe/Madrid"),
    ("Tokio", "Asia/Tokyo"),
    ("Nueva York", "America/New_York"),
]
ALARM_RING_SECONDS = 60
POMODORO_FOCUS_SECONDS = 25 * 60
POMODORO_BREAK_SECONDS = 5 * 60
POMODORO_BELL_SECONDS = 3
DEFAULT_COUNTDOWN = (24, 12)   # (day, month): Christmas
SPIN_SECONDS = 1.5
RAINBOW_PERIOD_SECONDS = 4.0
