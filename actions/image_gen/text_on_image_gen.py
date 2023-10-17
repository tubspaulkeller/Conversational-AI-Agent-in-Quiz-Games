from PIL import Image, ImageDraw, ImageFont
import random
from actions.common.common import get_dp_inmemory_db, get_credentials, setup_logging
from actions.session.sessionhandler import SessionHandler
import logging
logger = setup_logging()

def get_image_config(get_basic_image):
    image_configs = {
        'single_choice.png': {
            'text_font_size': 40,
            'text_color': (255, 255, 255),
            'max_width': 480,
            'config_width': 180,
            'config_height': -160,
            'stroke_width': 1,
            'bar_x_offset': -200,
            'bar_y_offset': 80,
            'color': (255, 215, 0),
            'badges_and_positions': [
                (0, (300, 80)),
                (1, (390, 80)),
                (2, (480, 80)),
                (3, (570, 80)),
                (4, (660, 80)),
                (5, (750, 80)),
                (6, (840, 80)),
                (7, (930, 80)),
                (8, (1020, 80)),
                (9, (1100, 80))
            ]
        },
        'multi_choice.png': {
            'text_font_size': 40,
            'text_color': (255, 255, 255),
            'max_width': 250,
            'config_width': 100,
            'config_height': -160,
            'stroke_width': 1,
            'bar_x_offset': -170,
            'bar_y_offset': 90,
            'color': (255, 215, 0),
            'badges_and_positions': [
                (0, (200, 100)),
                (1, (300, 100)),
                (2, (400, 100)),
                (3, (500, 100)),
                (4, (600, 100)),
                (5, (700, 100)),
                (6, (800, 100)),
                (7, (900, 100)),
                (8, (1000, 100)),
                (9, (1100, 100))
            ]
        },
        'open_quest.png': {
            'text_font_size': 40,
            'text_color': (255, 255, 255),
            'max_width': 450,
            'config_width': 120,
            'config_height': -130,
            'stroke_width': 1,
            'bar_x_offset': -170,
            'bar_y_offset': 80,
            'color': (255, 215, 0),
            'badges_and_positions': [
                (0, (200, 100)),
                (1, (300, 100)),
                (2, (400, 100)),
                (3, (500, 100)),
                (4, (600, 100)),
                (5, (700, 100)),
                (6, (800, 100)),
                (7, (900, 100)),
                (8, (1000, 100)),
                (9, (1100, 100))
            ]
        }
    }
    return image_configs.get(get_basic_image, {})

def set_configs_for_image(image_path, text, font_size, text_color, max_width, config_width, config_height, stroke_width):
    try:
        # Open the image
        image = Image.open(image_path)

        # Create an ImageDraw object
        draw = ImageDraw.Draw(image)

        # Maximum width for the text to fit within
        max_width = image.width - max_width 
        # Initialize flag for text fitting
        text_fits = False

        while not text_fits:
            font, font_size = get_font(font_size=font_size)

            # Calculate text width and height
            text_width, text_height = draw.textbbox((0, 0), text, font=font)[2:]
            # Check if text fits within the maximum width
            #print("textwidht %s, maxwidht %s"%(text_width, max_width))
            if text_width <= max_width:
                text_fits = True
            else:
                # Reduce font size
                font_size -= 1

                # Break the loop if font size becomes too small
                if font_size < 1:
                    break

        x = ((image.width - text_width) // 2) + config_width  # Adjust the value here to move the text more to the right or left
        y = (image.height - font_size) // 2 + config_height # Adjust the value here to move the text more up or down

        # draw
        draw.text((x, y), text, font=font, fill=text_color, stroke_width=stroke_width,
            stroke_fill="black")
        return image
    except Exception as e:  
        logger.exception(e)  

def get_texts_and_positions(get_basic_image, width, height, curr_level, points_of_group, stars, achievements, quest_points):
    image_configs = {
        'single_choice.png': [
            ("5 Fragepunkte", (width - 100, height - 60)),
            ("Level: %s" % curr_level, (int(width / 2) + 300, 0)),
            ("Score: %s" % points_of_group, (int(width / 2) + 575, 0)),
            ("Sterne: %s" % stars, (int(width / 2) + 25, 0)),
            ("Abzeichen: %s" % len(achievements), (int(width / 2) - 275, 0))
        ],
        'multi_choice.png': [
            ("%s Fragepunkte" % quest_points, (width - 80, height - 60)),
            ("Level: %s" % curr_level, (int(width / 2) + 295, 0)),
            ("Score: %s" % points_of_group, (int(width / 2) + 570, 0)),
            ("Sterne: %s" % stars, (int(width / 2) + 10, 0)),
            ("Abzeichen: %s" % len(achievements), (int(width / 2) - 290, 0))
        ],
        'open_quest.png': [
            ("%s Fragepunkte" % quest_points, (width - 80, height - 60)),
            ("Level: %s" % curr_level, (int(width / 2) + 295, 0)),
            ("Score: %s" % points_of_group, (int(width / 2) + 570, 0)),
            ("Sterne: %s" % stars, (int(width / 2) + 10, 0)),
            ("Abzeichen: %s" % len(achievements), (int(width / 2) - 290, 0))
        ]
    }
    return image_configs.get(get_basic_image, [])[:5] 

async def add_text_to_image(text, image_path, output_path, session_object, quest_id, loop, mates_number=None):
    '''
    create question as image and fill the image fill infos about current game elements like points, level, badges
    '''
    try:
        # get scores, level, badges
        session_handler = SessionHandler()
        mode = loop if loop else None
        curr_level = session_object['level'] if session_object else 0
        achievements = session_object['achievements'] if session_object else []
        stars = session_object['stars'] if session_object else 0
        points_of_group =session_object['total_points'] if session_object else 0
        max_game_points = await session_handler.max_points()
        quest_points = 20 if quest_id[-1] == "o" else 5
        percentage_to_next_level = 0
        # calculate percentage to reach the next level
        if points_of_group > 0:
            # get level                       
            level_points = [(1, max_game_points - 53), (2, max_game_points - 43), (3, max_game_points - 22), (4, max_game_points)]
            next_level = curr_level + 1
            if next_level <= len(level_points):
                points_required_for_next_level = level_points[next_level - 1][1]
                
                # KLOK MODE: we caluclate the percentage to reach the next level with the average score 
                if mode == 'KLOK':
                    avg_points = points_of_group/mates_number
                    if curr_level > 0:
                        points_to_next_level = (avg_points - level_points[curr_level - 1][1]) / (points_required_for_next_level - level_points[curr_level - 1][1])
                    else: 
                        points_to_next_level = avg_points / points_required_for_next_level
                else:
                    if curr_level > 0:
                        points_to_next_level = (points_of_group - level_points[curr_level - 1][1]) / (points_required_for_next_level - level_points[curr_level - 1][1])
                    else: 
                        points_to_next_level = points_of_group / points_required_for_next_level
                
                percentage_to_next_level = round(points_to_next_level * 100)

        percent = percentage_to_next_level if percentage_to_next_level  else 0
        text_color = (255,255,255)

        # settings for background image depends on the single, multiple or open quest
        get_basic_image = image_path.split("/")[-1]
        image_config = get_image_config(get_basic_image)
        
        if not image_config:
            raise ValueError("Invalid image type")

        image = set_configs_for_image(image_path, text, font_size=image_config['text_font_size'],
                                    text_color=image_config['text_color'], max_width=image_config['max_width'],
                                    config_width=image_config['config_width'], config_height=image_config['config_height'],
                                    stroke_width=image_config['stroke_width'])

        width, height = image.size
        bar_width = int(width * 0.6)
        bar_x = int((width - bar_width) / 2) + image_config['bar_x_offset']
        bar_y = int(height * 0.8) + image_config['bar_y_offset']
        color = image_config['color']

        texts_and_positions = get_texts_and_positions(get_basic_image, width, height, curr_level, points_of_group, stars, achievements, quest_points)
        
        # Draw progress bar and badges
        image_with_progress = draw_progress_bar_and_badges(image, percent, texts_and_positions, bar_x, bar_y, bar_width, color, image_config['badges_and_positions'], achievements)

        # Save the image
        image_with_progress.save(output_path)
    except Exception as e: 
        logger.exception(e)  

def draw_progress_bar_and_badges(image, percent, texts_and_positions, bar_x, bar_y, bar_width, color, badges_and_positions, achievements):
    # Draw progress bar
    image_with_progress = draw_progress_bar(image, percent, texts_and_positions, bar_x, bar_y, bar_width, color)

    for index, badge_name in enumerate(achievements):
        badge_image = Image.open(f'actions/image_gen/input/icons/{badge_name}.png')
        position = badges_and_positions[index][1]

        # ohne Mask (Rand der Icons)
        if badge_name == 'SINGLE_CHOICE' or badge_name == 'MULTIPLE_CHOICE':
            image_with_progress.paste(badge_image, position)
        else:
            image_with_progress.paste(badge_image, position, mask=badge_image)

    return image_with_progress

def draw_progress_bar(image, percent, texts_and_positions, bar_x, bar_y, bar_width, color):
    '''
    draw a progess bar on question image
    '''
    try:
        width, height = image.size

        # Bestimme die Abmessungen des Ladebalkens
        bar_height = 40
     
        # Zeichne den leeren Ladebalken
        draw = ImageDraw.Draw(image)
        draw.rectangle((bar_x, bar_y, bar_x + bar_width, bar_y + bar_height), outline='black')

        # Berechne die Breite des gefüllten Ladebalkens
        fill_width = int(bar_width * (percent / 100))

        # Zeichne den gefüllten Ladebalken
        draw.rectangle((bar_x, bar_y, bar_x + fill_width, bar_y + bar_height), fill=color)
    
        # Schriftgröße für die Texte
        font, font_size = get_font(font_size=45)

        texts_and_positions.append((f"{percent}%", (int((width - bar_width) / 2) + 325, bar_y + int((bar_height - 45) / 2) - 6)))
        
        # Texte zeichnen
        for text, position in texts_and_positions:
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_x = position[0] - text_bbox[2]
            text_y = position[1]
            draw.text((text_x, text_y), text, fill='white', font=font)

        return image

    except Exception as e: 
        logger.exception(e) 
        return None

def get_font(font_size): 
    try:
        
        font = ImageFont.truetype(r"./Verdana.ttf", font_size)
    except OSError as e:
        font_size = 100
        font = ImageFont.load_default() 
        logger.exception(e) 
    return font, font_size

def add_text_to_achievements_image(image_path, output_path, session_object):
    '''
    creates image with all reached scores, level, badges and so on.
    '''
    try:
        achievements = session_object['achievements'] if session_object else []
       # achievements = ["KORREKTE_ANTWORT","QUIZ_MASTER", "SCHNELLES_ANTWORTEN", "TEAMWORK", "SINGLE_CHOICE","MULTIPLE_CHOICE","NATURTALENT","OFFENE_FRAGE", "GOAL", "GESAMTSIEGER"]

        level = session_object['level'] if session_object else 0
        stars = session_object['stars'] if session_object else 0
        total_points = session_object['total_points'] if session_object else 0

        output_string = f"Punkte: {total_points} Level: {level} Abzeichen: {len(achievements)} Sterne: {stars}"
        text_color = (255,255,255)
        image = set_configs_for_image(image_path, output_string, 20, text_color, max_width=-300, config_width=0,config_height=-150,stroke_width= 1)
        
        # draw badges 
        badges_and_positions = [
        (0, (30, 130)),
        (1, (260, 130)),
        (2, (490, 130)),
        (3, (30, 210)),
        (4, (260, 210)),
        (5, (490, 210)),
        (6, (30, 290)),
        (7, (260, 290)),
        (8, (490, 290)),
        (9, (30, 370)),
        ]
        # paint badges
        for index, badge_name in enumerate(achievements):
            badge_image = Image.open(f'actions/image_gen/input/mini_batches/{badge_name}.png')
            position = badges_and_positions[index][1]
            image.paste(badge_image, position, mask=badge_image)
        # Save the image
        image.save(output_path)
    except Exception as e: 
        logger.exception(e)  

def add_table_on_leaderboard(tab_data, output_path):
    '''
    creates image with the rank of teams
    '''
    try:
        image_path = 'actions/image_gen/input/ranking.png'
        # Prepare leaderboard data
        max_line_length = int(get_credentials("MAX_LINE_LENGTH"))
        formatted_leaderboard_data = []
        # prepare data
        for entry in tab_data:
            rank, name, score, date = entry
            entry = f"{rank}. {name}, {score} Punkte, {date}"
            parts = entry.split(", ")
            name_part = parts[0]
            score_date_part = ", ".join(parts[1:])
            
            words = name_part.split()  # Split the name part into individual words
            lines = []
            current_line = ""
            for word in words:
                # split words ih they are too long
                if len(current_line) + len(word) > max_line_length:
                    threshold = len(word) - (max_line_length + len(current_line))
                    lines.append(current_line + " " + word[:threshold] + "-")
                    current_line = word[threshold:]
                else:
                    if current_line:
                        current_line += " "
                    current_line += word
            
            if current_line:
                lines.append(current_line)
            
            formatted_name_part = "\n".join(lines)
            formatted_entry = f"{formatted_name_part}, {score_date_part}"
            formatted_leaderboard_data.append(formatted_entry)
        
        # Concatenate formatted leaderboard data
        leaderboard_string = "\n".join(formatted_leaderboard_data)
        image = set_configs_for_image(image_path, leaderboard_string, font_size = 40, text_color = (255,255,255), max_width=600, config_width=180,config_height=-100,stroke_width= 1)

        # Save the image
        image.save(output_path)
    except Exception as e: 
        logger.exception(e) 
