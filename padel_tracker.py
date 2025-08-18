import pygame
import os
import constants_lanh as con
from datetime import datetime 
import sys
import requests
import csv
import platform
import serial
import threading
import keyboard
import serial.tools.list_ports
import time
import v01_padeltracker_dataexporter_lanh as ptexp
import v01_updater_lanh as appup
import license_key as lkey

# Version Number
version_number = "1.0.7"

# Set of ports already connected.
connected_ports = set()

# Find all the ports in the serial library and check if input comes from it.
def find_all_arduino_ports():
    '''
    Description:
    Find all the ports available and return it as a list.

    Input:
    None

    Output:
    aurdino_ports (list): All the ports thats uses CH340 or Arduino.
    '''
    #Lists all of the usb ports and gets the data.
    ports = serial.tools.list_ports.comports()
    arduino_ports = []

    # Goes through each port in ports and appends it if its name a way.
    for port in ports:
        #print(f"Found port: {port.device} - {port.description}")
        if 'CH340' in port.description or 'Arduino' in port.description:
            arduino_ports.append(port.device)
    return arduino_ports

#Constantly tries to listen for an arduino.
def listen_to_arduino(port):
    '''
    Description:
    listens for the information in serial between devices.
    Input:
    port (list): The list of objects from my COM (usb) ports.

    Output:
    ser (list): List of the information from the arduino connection.
    '''
    try:
        # It creates the connection, speed of data, and timeout.
        ser = serial.Serial(port, 9600, timeout=1)
        #print(f"Started listening to {port}")

        while True:
            #Checks if the port has bytes waiting to be sent.
            if ser.in_waiting > 0:
                #Reads the byte line and converts to python.
                raw = ser.readline()
                line = raw.decode(errors='ignore').strip().upper()
                #print(f"[{port}] Received: '{line}'")

                #Checks every entry of the option.
                if "ENTER" in line:
                    event = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_RETURN})
                    pygame.event.post(event)
                    #print("Posted KEYDOWN: ENTER")

                elif "SPACE" in line:
                    event = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_SPACE})
                    pygame.event.post(event)
                    #print("Posted KEYDOWN: SPACE")

                elif "RIGHT" in line:
                    event = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_RIGHT})
                    pygame.event.post(event)
                    #print("Posted KEYDOWN: RIGHT")

                elif "LEFT" in line:
                    event = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_LEFT})
                    pygame.event.post(event)
                    #print("Posted KEYDOWN: LEFT")

            # Buffer time.
            time.sleep(0.01)

    #Marks an error if there is an error.
    except serial.SerialException as e:
        print(f"[{port}] Serial error: {e}")
        connected_ports.discard(port)

    return ser

def arduino_commands():
    while True:
        ports = find_all_arduino_ports()
        for port in ports:
                if port not in connected_ports:
                    thread = threading.Thread(target=listen_to_arduino, args=(port,), daemon=True)
                    thread.start()
                    connected_ports.add(port)
        time.sleep(2) # Check every 2 seconds.

# License Platform.
def get_machine_id():
    '''
    Description: 
    Gets the computers unique name as an unique ID.

    Input:
    none

    Ouput:
    pc_id
    '''
    #It stores the computer unique ID as an object.
    pc_id = platform.node()
    return pc_id

#Checks the licenses.
def check_license(license_key):
    '''
    Description:
    It verifies the license of the user with the online database to verify.

    Input:
    license_key (str): The license name as it is in the data base.

    Output: 
    none.
    '''
    try:
        print("Checking license...")
        con.response.raise_for_status()  # throws error on bad request

        # Get the information from the csv and splits it into a dict.
        reader = csv.DictReader(con.response.text.splitlines())
        machine_id = get_machine_id()

        # Checks the licenses.
        for row in reader:
            print(f"Row: {row}")  # debug print

            if row.get("License Key", "").strip() == license_key.strip():
                status = row.get("Status", "").lower()
                if status != "active":
                    return False, "❌ License is not active"

                expiration_str = row.get("Expiration Date", "").strip()
                try:
                    exp_date = datetime.strptime(expiration_str, "%Y-%m-%d")
                except ValueError:
                    return False, f"⚠️ Invalid date format: '{expiration_str}'"

                if exp_date < datetime.now():
                    return False, "❌ License expired"

                return True, "✅ License verified"

        return False, "❌ License key not found"

    except requests.exceptions.Timeout:
        return False, "⚠️ License check timed out"
    except requests.exceptions.RequestException as e:
        return False, f"❌ Network error: {e}"
    except Exception as e:
        return False, f"❌ Unexpected error: {e}"

# Initialize the software.
pygame.init()
pygame.mixer.init()

# Set the font used for the software.
padel_font = pygame.font.SysFont(con.font, con.font_size, bold = True)
small_font = pygame.font.SysFont(con.font, 100, bold=True) 

# Set the Player Class
class Player (pygame.sprite.DirtySprite):
        def __init__(self, x_pos, y_pos,name, points, games, sets, color, font, font_small):
                '''
                Description:
                This class creates a player with a location on screen, points,
                and games.
                
                Inputs:
                x_pos(int): Position of the player on screen horizontally.
                y_pos (int): Position of the player on screen vertically.
                name (str): Name of the Player.
                points (int): Points of the game.
                games (int): Games won.
                color (tuple): A set of values for the color of the font/
                font_size (int): The size of the font

                Output:
                A player class
                '''
                pygame.sprite.DirtySprite.__init__(self)
                self.x_pos = x_pos
                self.y_pos = y_pos
                self.name = name
                self.points = points
                self.games = games
                self.set = sets
                self.color = color
                self.font = font
                self.font_small = font_small
                self.image = None
                self.rect = None
                self.update()
        
        # Updates the class.
        def update(self):
                '''
                Description:
                Updates the players class attributes on the pygame along with 
                the font size.

                Inputs:
                None

                Output:
                text (str): A text that will be displayed.

                ###Can probably move some of these to the constants.###

                '''
                 # Render the name
                name_surface = self.font_small.render(self.name, True, self.color)

                # Render each score part separately
                points_text = str(self.points)
                games_text = str(self.games)
                sets_text = str(self.set)

                # ➤ POINTS: render with white text on colored background
                points_surface = self.font.render(points_text, True, con.white)  # white text

                # Reduce background height by 20 pixels, and vertically center the points text
                reduced_height = points_surface.get_height() - con.reduce_height
                points_bg = pygame.Surface((points_surface.get_width() + 20, reduced_height), pygame.SRCALPHA)
                points_bg.fill(self.color)

                # Center the text vertically inside the reduced background
                text_y = (reduced_height - points_surface.get_height()) // 2
                points_bg.blit(points_surface, (con.text_x, text_y))

                # ➤ GAMES + SETS: render normally (no background)
                games_surface = self.font.render(f"  {games_text}", True, self.color)
                sets_surface = self.font.render(f"    {sets_text}", True, self.color)

                # Combine score parts horizontally
                total_width = (points_bg.get_width() + 
                                games_surface.get_width() + 
                                sets_surface.get_width() + 
                                con.reduce_height)
                height = max(
                            points_bg.get_height(), 
                            games_surface.get_height(), 
                            sets_surface.get_height()
                            )

                # Combine into one surface
                score_surface = pygame.Surface((total_width, height), pygame.SRCALPHA)
                x_offset = -con.x_offset
                score_surface.blit(sets_surface, (x_offset, 0))
                x_offset += sets_surface.get_width()
                score_surface.blit(games_surface, (x_offset, 0))
                x_offset += games_surface.get_width() + con.points_offset
                score_surface.blit(points_bg, (x_offset, 0))

                # Combine name + score_surface horizontally
                combined_width = name_surface.get_width() + 20 + score_surface.get_width()
                combined_height = max(
                                    name_surface.get_height(), 
                                    score_surface.get_height()-con.reduce_height
                                    )

                self.image = pygame.Surface((combined_width, combined_height), pygame.SRCALPHA)
                name_y = (combined_height - name_surface.get_height()) // 2
                score_y = (combined_height - score_surface.get_height()) // 2
                self.image.blit(name_surface, (0, name_y))
                self.image.blit(score_surface, (name_surface.get_width() + 20, score_y))

                self.rect = self.image.get_rect(topleft=(self.x_pos, self.y_pos))
                
        # Resets the points back to 0.       
        def reset_points(self):
               '''
               Description:
               Returns the points back to 0.

               Input:
               None

               Output:
               self.points (int): Back in 0.
               '''
               self.points = int(0)
               return 
        
        # Resets the games back to 0.
        def reset_game (self):
              '''
               Description:
               Returns the games back to 0.

               Input:
               None

               Output:
               self.games (int): Back in 0.
               '''
              self.games = int(0)
              return self.games

        # Resets the sets back to 0.
        def reset_set (self):
            '''
            Description:
            Returns the sets back to 0.

            Input:
            None

            Output:
            self.set (int): Back in 0.
            '''
            self.set = int(0)
            return self.set

# Runs the app
def main():
        # Set the Game run settings. Attaches image to window.
        run = True
        fps =10
        clock = pygame.time.Clock()

        #Sets sudden death to false
        sudden_death = False
        

        #Tracks the winner variables
        winner = None
        winner_start_time = None

        #Gives a time and timer to the enter key.
        enter_key_held = False
        enter_start_time = 0
        ENTER_HOLD_DURATION = 3000 

        # Variables to the score button.
        score_key_pressed = False
        score_key_time = 0
        score_pressed_duration = 3000

        # Last input time variable
        last_input_time = time.time()

        # Add variable to the switch player.
        player1_controls_left = True
        
        # Calling the background.
        background = pygame.Surface(con.win.get_size())
        background.blit(con.background_image,(0,0))

        # Setting the center of the screen.
        center_x = int(con.width/2)
        center_y = int(con.height/2)
        
        
        # Create player 1. #### Cand move to con ###
        player1_x = int(center_x/6 - 100)
        player1_y = int(center_y -200) 
        player1_color = con.marine_blue
        player1 = Player(
                        player1_x, 
                        player1_y, 
                        "Equipo 1", 
                        0, 
                        0,
                        0, 
                        player1_color,
                        con.score_font,
                        small_font
                        )

        # Create Player 2.  #### Can move to con ####              
        player2_x = int(center_x/6 - 100)
        player2_y = int(center_y + 150) 
        player2_color = con.fire_brick
        player2 = Player(
                        player2_x, 
                        player2_y, 
                        "Equipo 2", 
                        0, 
                        0,
                        0, 
                        player2_color,
                        con.score_font,
                        small_font
                         )

        # Group for convenience (optional)
        players = pygame.sprite.Group(player1, player2)

        # Create Timer
        match_started = False
        start_time = 0
        elapsed_time = 0
        
        #Starts the timer if the timer hasnt started.
        def start_timer(match_started, start_time):
            '''
            Description:
            Checks the timer, if false starts the timer.

            Input:
            match_started (bool): Checks if the match has started.
            start_time (int): Starts the time at 0.

            Output:
            start_time(int): The timer in ticks.
            match_started(bool): The boolean of the timer. 
            '''
            #nonlocal match_started, start_time
            match_started = True
            start_time = pygame.time.get_ticks()
            return start_time, match_started
        
        def reset_timer(match_started, start_time, elapsed_time):
            '''
            Description:
            Resets the timer and points back to 0.

            Input:
            match_started (bool): Checks if the match has started.
            start_time (int): Gets the current start_time.
            elapsed_time (int): Gets the elapsed time since it started.

            Output: 
            start_time (int): The timer in ticks.
            match_started (bool): The boolean of the timer. 
            elapsed_time (int): The elapsed time since enter.
            '''
            #nonlocal match_started, start_time, elapsed_time
            match_started = False
            start_time = 0
            elapsed_time = 0
            player1.reset_game()
            player1.reset_points()
            player1.reset_set()
            player2.reset_game()
            player2.reset_points()
            player2.reset_set()
            return match_started, start_time, elapsed_time

        # Switch sides function.
        def switch_sides():
            '''
            Description:
            Switches the position, and colors of both teams.

            Input: 
            none

            Output:
            players (dict): both clases of players

            '''
            # Swap y-positions
            player1.y_pos, player2.y_pos = player2.y_pos, player1.y_pos

            # Swap drawing order by swapping rects
            player1.rect.topleft = (player1.x_pos, player1.y_pos)
            player2.rect.topleft = (player2.x_pos, player2.y_pos)

            # Swap players in group to update rendering order
            players.empty()
            players.add(player1, player2)

            player1.update()
            player2.update()

            return players
        
        # Score points.
        def score_point(player, opponent):
            '''
            Description:
            Scores the points, games and sets.

            Inputs:
            player (obj): Player which the button will affect.
            opponent (obj): Other player.

            Ouput:
            player (obj): player with updated points.
            opponent (obj): opponent with updated points.
            '''
            nonlocal match_started, start_time, elapsed_time, winner, winner_start_time
            #Only starts if match has started.
            if not match_started:
                return  

            # Set Dictionary of scores and update players.
            score_steps = [0, 15, 30, 40]
            player.update()
            opponent.update()

            #If both players have 'AD', reset to deuce (40-40) and stop scoring
            if player.points == 'AD' and opponent.points == 'AD':
                player.points = 40
                opponent.points = 40
                player.update()
                opponent.update()
                return  # Exit immediately to prevent further scoring
            
            #If player has 'AD' and opponent scores, reset to 40-40
            if player.points == 40 and opponent.points == 'AD':
                player.points = 40
                opponent.points = 40
                player.update()
                opponent.update()
                return

            #If both players have 40 points (deuce), and player scores
            if player.points == 40 and opponent.points == 40:
                player.points = 'AD'

            #If player already has advantage and scores again → wins game
            elif player.points == 'AD':
                player.points = 'Game'
            
            nonlocal sudden_death
            if player.games == 6 and opponent.games == 6:
                sudden_death = True

            if sudden_death:
                # Increment point by 1
                if isinstance(player.points, int):
                    player.points += 1
                else:
                    player.points = 1
                
                  # Check for win (must win by 2 points and have at least 7)
                if player.points >= 7 and (player.points - opponent.points) >= 2:
                    player.set += 1
                    sudden_death = False  # reset sudden death
                    player.reset_game()
                    opponent.reset_game()
                    player.reset_points()
                    opponent.reset_points()
                    

            #Normal scoring steps (0 → 15 → 30 → 40)
            elif player.points in score_steps:
                idx = score_steps.index(player.points)
                if idx < len(score_steps) - 1:
                    player.points = score_steps[idx + 1]
                else:
                    # Player reached 40 but opponent less than 40 → player wins game
                    if opponent.points != 40:
                        player.points = 'Game'
                    else:
                        player.points = 40

            if player.games == 6 and opponent.games <= 4:
                player.reset_game()
                opponent.reset_game()
                player.reset_points()
                opponent.reset_points()
                player.set +=1

            elif player.games == 7 and opponent.games >= 5:
                player.reset_game()
                opponent.reset_game()
                player.reset_points()
                opponent.reset_points()
                player.set += 1

            # 5) If player wins the game, increase games and reset points for both
            if player.points == 'Game':
                player.games += 1
                player.reset_points()
                opponent.reset_points()
            
            if player.set == 2:
                winner = player.name + " Ganador"
                winner_start_time = pygame.time.get_ticks()

                p1_score = f"{player1.set}-{player1.games}-{player1.points}"
                p2_score = f"{player2.set}-{player2.games}-{player2.points}"
                

                ptexp.export_to_google_sheets(winner, p1_score, p2_score, elapsed_time,user_license, version_number)

                match_started, start_time, elapsed_time = reset_timer(match_started, start_time, elapsed_time)
                player.reset_game()
                opponent.reset_game()
                player.reset_points()
                opponent.reset_points()
                player.reset_set()
                opponent.reset_set()
                


            

            player.update()
            opponent.update()

            return player, opponent, winner, winner_start_time



        # While loop that keeps the app running.
        while run:
                #Each event in pygame it checks it.
                for event in pygame.event.get():

                    #If it quits, it quits.
                    if event.type == pygame.QUIT:
                        p1_score = f"{player1.set}-{player1.games}-{player1.points}"
                        p2_score = f"{player2.set}-{player2.games}-{player2.points}"
                        ptexp.export_to_google_sheets(winner, p1_score, p2_score, elapsed_time,user_license, version_number)
                        os.system("v01_updater_lanh.py")
                        print ('updating software')
                        quit()

                    #Checks if a key is pressed.
                    elif event.type == pygame.KEYDOWN:
                        last_input_time = time.time()
                        # Clear winner if LEFT, RIGHT or ENTER is pressed
                        if winner and event.key in [pygame.K_LEFT, pygame.K_RIGHT, pygame.K_RETURN]:
                            winner = None
                            winner_start_time = None

                        # Point if left key is pressed to the player who controls it. 
                        if event.key == pygame.K_LEFT and not score_key_pressed:
                            if player1_controls_left:
                                score_point(player1, player2)
                                con.peep_sound.play()
                            else:
                                score_point(player2, player1)
                                con.peep_sound.play()
                            score_key_pressed = True
                            score_key_time = pygame.time.get_ticks()

                        # Point if right key is pressed to the player who controls it. 
                        elif event.key == pygame.K_RIGHT and not score_key_pressed:
                            if player1_controls_left:
                                score_point(player2, player1)
                                con.peep_sound.play()
                            else:
                                score_point(player1, player2)
                                con.peep_sound.play()
                            score_key_pressed = True
                            score_key_time = pygame.time.get_ticks()
                        
                        

                        # Enter to start time, if it has started and pressed it resets.
                        elif event.key == pygame.K_RETURN:
                            if not match_started:
                                start_time, match_started = start_timer(match_started, start_time)
                                con.bell_sound.play()
                            else:
                                p1_score = f"{player1.set}-{player1.games}-{player1.points}"
                                p2_score = f"{player2.set}-{player2.games}-{player2.points}"
                                ptexp.export_to_google_sheets(winner, p1_score, p2_score, elapsed_time,user_license, version_number)
                                enter_key_held = True
                                enter_start_time = pygame.time.get_ticks()

                        #Checks if players control left, and switches sides.
                        elif event.key == pygame.K_SPACE:
                            switch_sides()
                            player1_controls_left = not player1_controls_left

                        #Quits the game if escape is pressed.
                        elif event.key == pygame.K_ESCAPE:
                            p1_score = f"{player1.set}-{player1.games}-{player1.points}"
                            p2_score = f"{player2.set}-{player2.games}-{player2.points}"
                            ptexp.export_to_google_sheets(winner, p1_score, p2_score, elapsed_time,user_license, version_number)
                            os.system("v01_updater_lanh.py")
                            print ('updating software')
                            quit()

                    #It resets the enter_key_held back to false after it releases.
                    elif event.type == pygame.KEYUP:
                        if event.key == pygame.K_RETURN:
                            enter_key_held = False
                
                                     
                 # Updating the game tick in fps values, and updating display.
                clock.tick(fps)

                # Draws the background
                con.win.blit(background, (0, 0))


                # Update and draw players
                players.update()                
                players.draw(con.win)

                # Get current time as a string
                current_time = datetime.now().strftime("%H:%M:%S")

                # Reset timer for inactivity.
                if match_started and (time.time() - last_input_time > 1800):
                    print("🔁 Match reset due to 30 minutes of inactivity.")

                    match_started = False
                    last_input_time = time.time()
                    p1_score = f"{player1.set}-{player1.games}-{player1.points}"
                    p2_score = f"{player2.set}-{player2.games}-{player2.points}"
                    ptexp.export_to_google_sheets(winner, p1_score, p2_score, elapsed_time, user_license, version_number)
                    match_started, start_time, elapsed_time = reset_timer(match_started, start_time, elapsed_time)

                # Render the time.
                time_surface = con.time_font.render(
                                            current_time, 
                                            True, 
                                            con.dark_gray
                                                 )
                con.win.blit(time_surface, (100, 50))

                #It gets the time it has transcured minus the start time in seconds.
                if match_started:
                    elapsed_time = (pygame.time.get_ticks() - start_time) // 1000

                #It gets the minutes and the seconds and formats it.
                minutes = elapsed_time // 60
                seconds = elapsed_time % 60
                formatted_time = f"{minutes:02}:{seconds:02}"

                # Render the timer text
                timer_surface = con.time_font.render(
                                                f"          T: {formatted_time}", 
                                                True, 
                                                con.dark_gray
                                                  )
                
                # Render the labels
                puntos_label_p1 = con.label_font.render(
                                            "     SETS    JUEGOS  PUNTOS", 
                                                        True, 
                                                        con.dark_gray
                                                        )
                con.win.blit(puntos_label_p1, (500, 200))  
                
                #It resets the game.
                if player1.set == 2:
                    con.win.blit(player1.image, player1.rect)
                elif player2.set == 2:
                    con.win.blit(player2.image, player2.rect)

                # Adjust position if needed of the timer and the logo.
                con.win.blit(timer_surface, (center_x + 190, 50))
                con.win.blit(con.logo_img, con.logo_rect) 

                # Check if Enter has been held long enough
                if enter_key_held:
                    if pygame.time.get_ticks() - enter_start_time >= ENTER_HOLD_DURATION:
                        #print("Resetting match due to Enter hold")
                        match_started, start_time, elapsed_time = reset_timer(match_started, start_time, elapsed_time)
                        enter_key_held = False

                # It checks if the score button has been pressed.
                if pygame.time.get_ticks() - score_key_time > score_pressed_duration:
                    score_key_pressed = False

                # Draws the victory
                if winner:
                    # Create the winner text surface with a smaller font
                    winner_surface = small_font.render(winner, True, (255, 255, 255))  # White text
                    winner_rect = winner_surface.get_rect(center=(con.width // 2, con.height // 2))

                    # Draw a semi-transparent dark grey background behind the text
                    bg_width = winner_rect.width + 40
                    bg_height = winner_rect.height + 20

                    # Create surface for background box
                    background_box = pygame.Surface((bg_width, bg_height), pygame.SRCALPHA)
                    background_box.fill((30, 30, 30, 200))  # Dark grey with alpha (0–255)

                    # Get background position
                    background_rect = background_box.get_rect(center=winner_rect.center)

                    # Blit the background first, then the text
                    con.win.blit(background_box, background_rect)
                    con.win.blit(winner_surface, winner_rect) 
                
                # in main loop (or right before it)
                pygame.display.update()
                

if __name__ == '__main__':
    #The computers user license in the data base.
    user_license = str(lkey.license_key)  # Could load this from a file or user input

    # Gets the user name and cheks if its valid from the function.
    is_valid, message = check_license(user_license)
    print(message)

    #If the license isvalid.
    if is_valid:
        
        # 🔸 Start Arduino listener in separate thread
        arduino_thread = threading.Thread(target=arduino_commands, daemon=True)
        arduino_thread.start()
        
        os.system("v01_updater_lanh.py")
        print ('it has been updated')
        # Run the program
        main()
        

    #Quit the program.
    else:
        import sys
        print("Exiting due to license issue.")
        sys.exit()
