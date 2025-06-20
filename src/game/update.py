import random

import pygame

from src.utils.config import SCREEN_WIDTH, SPEED_INCREMENT
from src.entities.powerUp import PowerUp
from src.entities.obstacle import Obstacle
from src.utils.resources import logging, clock, GAME_OVER_SOUND, IMMORTALITY_SOUND, CLAIM_COIN_SOUND, COLLIDE_FIREBALL_SOUND
from src.utils.utils import ease_out_cubic


def update(self):
    if self.music_positon_game >= 108.877:
        self.music_positon_game = 0
    if self.music_positon_pause >= 240.0:
        self.music_positon_pause = 0

    self.cursor_tick += 1
    if self.cursor_tick >= 60:
        self.cursor_tick = 0

    if self.username_existing and not self.checked_username and not self.unlocked_user:
        self.check_username()
    if self.username_existing and self.checked_username and not self.unlocked_user:
        self.unlock_user()

    if self.show_list:
        self.pause = True
        step = (self.target_high_score_list_y - self.high_score_list_y) * 0.2
        if abs(step) > 0.5:
            self.high_score_list_y += step

    if not self.unlocked_user and self.username_existing:
        if not self.username in self.accounts:
            self.show_control_info = True

    pygame.mixer.music.set_volume(self.music_volume)

    if self.game_over:
        self.game_over_fade_in += 0.015
        self.game_over_time += clock.get_time() / 300.0
        progress = min(self.game_over_time / 8.0, 1.0)
        scale_eased = ease_out_cubic(progress)
        self.game_over_scale = 1 + scale_eased * 8

    if self.pause or self.game_over:
        return

    self.control_info_time -= 1

    self.dino.update(self.score, self.sound_volume)

    if not self.pause and not self.game_over:
        self.background_x -= self.obstacle_speed * 0.20
        if self.background_x <= -SCREEN_WIDTH - 800:
            self.background_x = 0
            self.background_flip = not self.background_flip
        self.background_x_2 -= self.obstacle_speed * 0.25
        if self.background_x_2 <= -SCREEN_WIDTH - 800:
            self.background_x_2 = 0
            self.background_flip_2 = not self.background_flip_2
        self.background_x_3 -= self.obstacle_speed * 0.50
        if self.background_x_3 <= -SCREEN_WIDTH - 800:
            self.background_x_3 = 0
            self.background_flip_3 = not self.background_flip_3
        self.background_x_4 -= self.obstacle_speed
        if self.background_x_4 <= -SCREEN_WIDTH - 800:
            self.background_x_4 = 0
            self.background_flip_4 = not self.background_flip_4

        self.progress_birds = min((self.score + self.progress_smoothed) / self.birds_score, 1)
        self.progress_day = min((self.score + self.progress_smoothed) / self.day_score, 1)
        self.progress_sky = min((self.score + self.progress_smoothed) / self.sky_score, 1)
        if self.score < 100:
            self.progress_smoothed = self.progress_smoothed + 0.5
        else:
            self.progress_smoothed = self.progress_smoothed + 0.9

    if not self.obstacles or self.obstacles[-1].x < SCREEN_WIDTH - random.randint(650, 850) - self.spacing:
        self.spacing += 2.5
        self.obstacles.append(Obstacle(self.score, self.power_up_type))
        logging.debug(f"Placed new obstacle")

    if -400 >= self.background_x:
        self.night_to_day_transition = True

    if self.background_x <= -500 and (
            self.night_to_day_transition_progress == 1 or self.night_to_day_transition_progress == 0):
        self.night_to_day_transition = False

    if self.night_to_day_transition:
        if 5000 <= self.score <= 7000:
            self.night_to_day_transition_progress = min(
                self.night_to_day_transition_progress + self.night_to_day_transition_speed, 1)

    for fireball in self.fireballs[:]:
        fireball.update()
        if fireball.complete_off_screen():
            logging.debug(f"Fireball complete off screen: {fireball.x + fireball.width < 0}")
            self.fireballs.remove(fireball)
            logging.debug("Removed fireball")

    for obstacle in self.obstacles[:]:
        obstacle.update(self.obstacle_speed)

        for fireball in self.fireballs[:]:
            if fireball.collides_with(obstacle):
                logging.debug("Obstacle collided with fireball")
                self.score += 100
                self.obstacles.remove(obstacle)
                self.fireballs.remove(fireball)
                COLLIDE_FIREBALL_SOUND.set_volume(self.sound_volume)
                COLLIDE_FIREBALL_SOUND.play()
                logging.debug("Removed obstacle")

        if obstacle.complete_off_screen():
            logging.debug(f"Obstacle complete off screen: {obstacle.x + obstacle.width[0] < 0}")
            self.obstacles.remove(obstacle)
            logging.debug("Removed obstacle")

        if obstacle.off_screen() and not obstacle.got_counted:
            logging.debug(f"Obstacle off screen: {obstacle.x + obstacle.width[0] < 0}")
            multiplicator = 2 if self.power_up_type == "multiplicator" else 1
            if obstacle.type == "double":
                self.score += 150 * multiplicator
            else:
                self.score += 100 * multiplicator
            obstacle.got_counted = True
            self.progress_smoothed = 0

            logging.info(f"Score: {self.score}")

        if obstacle.collides_with(self.dino, self.ducked) and not self.power_up_type == "immortality":
            logging.info("Dino collided with obstacle")
            self.save_scores()
            self.game_over = True
            pygame.mixer.music.stop()
            GAME_OVER_SOUND.set_volume(self.sound_volume)
            GAME_OVER_SOUND.play()

        self.obstacle_speed += SPEED_INCREMENT

    if not self.obstacles or self.obstacles[-1].x <= SCREEN_WIDTH - 400:
        self.power_up_spacing = True
    else:
        self.power_up_spacing = False

    if self.power_up_timer < 0:
        self.power_up_timer += 1

    if self.power_up_timer >= 0 and self.power_up_spacing and self.power_up_type is None:
        logging.debug(f"Placed new power up ({self.power_up_timer})")
        self.power_ups.append(PowerUp(self.score))
        self.power_up_timer = random.randint(30 * 60, 45 * 60)
        self.power_up_timer = -self.power_up_timer

    for power_up in self.power_ups[:]:
        power_up.update(self.obstacle_speed)
        if power_up.complete_off_screen():
            logging.debug(f"Power up complete off screen: {power_up.x + power_up.width < 0}")
            self.power_ups.remove(power_up)
            self.power_up_timer = random.randint(30 * 60, 45 * 60)
            self.power_up_timer = -self.power_up_timer
            logging.debug("Removed power up")

        if power_up.collides_with(self.dino) and self.power_up_type is None:
            logging.debug("Dino collided with power up")
            CLAIM_COIN_SOUND.set_volume(self.sound_volume)
            CLAIM_COIN_SOUND.play()
            if power_up.type == "multiplicator":
                self.power_up_type = "multiplicator"
                logging.info(f"Multiplicator power up")
            elif power_up.type == "immortality":
                self.power_up_type = "immortality"
                self.music_positon_game += pygame.mixer.music.get_pos() / 1000
                pygame.mixer.music.stop()
                IMMORTALITY_SOUND.set_volume(self.music_volume)
                IMMORTALITY_SOUND.play()
                logging.info("Immortality power up")
            elif power_up.type == "fly":
                self.power_up_type = "fly"
                logging.info("Fly power up")
            elif power_up.type == "fireball":
                self.power_up_type = "fireball"
                logging.info("Fireball power up")
            self.power_ups.remove(power_up)
            self.power_up_timer = 0
            logging.debug("Removed power up")

    if self.power_up_type is not None and self.power_up_timer >= 0:
        self.power_up_timer += 1
        if self.power_up_timer > 15 * 60:
            if self.power_up_type == "immortality":
                self.last_played_title = "game_music.wav"
                pygame.mixer.music.load('./assets/sounds/music/game_music.wav')
                pygame.mixer.music.play(-1, start=self.music_positon_game, fade_ms=500)
            self.power_up_timer = random.randint(30 * 60, 45 * 60)
            self.power_up_timer = -self.power_up_timer
            self.power_up_type = None
            logging.debug("Power up completed")

