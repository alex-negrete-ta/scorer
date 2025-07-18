import pygame
import os
import requests


# Init and get screen resolution
pygame.init()
pygame.mixer.init()
info = pygame.display.Info()
screen_width = info.current_w
screen_height = info.current_h
width, height = screen_width, screen_height

# Set screen and scale factor
win = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
SCALE = screen_height / 1080  # Base reference from 1080p

# Define colors
white = [255, 255, 255]
black = [0, 0, 0]
powder_blue = [176, 224, 230]
steel_blue = [70, 130, 180]
airforce_blue = [93, 138, 168]
indian_red = [205, 92, 92]
rosy_brown = [188, 143, 143]
fire_brick = [178, 34, 34]
charcoal = [54, 69, 79]
slate_gray = [112, 128, 144]
gunmetal = [42, 52, 57]
dark_gray = [64, 64, 64]

# Background and spacing
reduce_height = int(50 * SCALE)
text_x = int(10 * SCALE)
x_offset = int(280 * SCALE)
points_offset = int(140 * SCALE)
center_x = screen_width / 2
center_y = screen_height / 2

# Winner display duration
WINNER_DISPLAY_DURATION = 10 * 1000  # ms

# Responsive fonts
label_font = pygame.font.SysFont("arialblack", int(80 * SCALE), bold=True)
score_font = pygame.font.SysFont("arialblack", int(300 * SCALE), bold=False)
numbers_font = pygame.font.SysFont("arialblack", int(80 * SCALE), bold=True)
time_font = pygame.font.SysFont("arialblack", int(70 * SCALE), bold=True)

# General font
font = "verdana"
font_size = int((center_x + center_y) / 14 * SCALE)

# Load scaled background
background_image = pygame.transform.scale(
    pygame.image.load(os.path.join('02_Assets', 'background.png')),
    (screen_width, screen_height)
)

# Load and scale logo
logo_width = int(384 * SCALE)
logo_height = int(216 * SCALE)
logo_img = pygame.transform.scale(
    pygame.image.load(os.path.join('02_Assets', 'logo.png')),
    (logo_width, logo_height)
)
logo_rect = logo_img.get_rect(midtop=(screen_width // 2, 0))

# Google Sheets CSV
GOOGLE_SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQGzn7wVZMkWaImxEyxxv4V4c6e_BPKdye7Wh5QX0D8KQ15Y8jFj4QOLAxvCnflR7XqonJoB7Ul1ynB/pub?output=csv"
response = requests.get(GOOGLE_SHEET_CSV_URL, timeout=10, headers={"Cache-Control": "no-cache"})

time_font = pygame.font.SysFont("arialblack", 70, bold=True)
font = "verdana" #verdana, dejavusans o arial black.
font_size = int((center_x + center_y)/14)

background_image = pygame.transform.scale(
                pygame.image.load(
                                  os.path.join('02_Assets','background.png')),
                                  (width,height)
                                   )

logo_img = pygame.transform.scale(
                pygame.image.load(
                                  os.path.join('02_Assets','logo.png')),
                                  (384,216)
                                   )

logo_rect = logo_img.get_rect(midtop=(width // 2, 0))


# Create a sound
peep_sound = pygame.mixer.Sound("beep.wav")

