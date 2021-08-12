import random
import numpy as np


class Agents:

    def __init__(self, novelty, difficulty, mock):
        self.novelty = novelty
        self.difficulty = difficulty
        self.mock = mock

        # Set looking bounds (vision cone)
        self.left_side = 7 / 8 * np.pi
        self.right_side = np.pi / 8

        self.id_to_cvar = None
        self.team_pos = None

        return None

    # Run agent behavoir here
    def act(self, state, id_to_cvar):
        if self.id_to_cvar is None:
            self.id_to_cvar = id_to_cvar

        commands = list()
        # Prime the spinny agents (used for detecting if something went wrong)
        for ind in range(4):
            # Always turn left
            commands.append("set ai_" + str(ind + 1) + " " + str(3))

        # Enemies move towards player
        if self.novelty == 3:
            commands = self.move_towards(state, commands)

        # Enemies move away from avg
        elif self.novelty == 5:
            commands = self.spread_out(state, commands)

        # Any other is pure random
        else:
            commands = []
            # Random behavoiur:
            for ind in range(4):
                action = random.choice(list(range(7))) + 1
                commands.append("set ai_" + str(ind + 1) + " " + str(action))

        # Enemies always check for facing to see if shoot
        commands = self.check_shoot(state, commands)

        # Enemies never shoot towards other enemies
        commands = self.check_enemies(state, commands)

        return commands

    # Move agent towards player
    def move_towards(self, state, commands):
        for ind, val in enumerate(state['enemies']):
            # Get info
            angle, sign = self.get_angle(state['player'], val)

            if angle < self.right_side:
                # Forward, left, right, shoot?
                action = random.choice([1, 3, 4, 7])
            else:
                if sign == -1.0:
                    # Turn right
                    action = 6
                else:
                    # Turn left
                    action = 5

            # Send ai action
            commands[ind] = "set ai_" + str(self.id_to_cvar[val['id']]) + " " + str(action)

        return commands

    def spread_out(self, state, commands):
        # Find avg pos
        avg_x = 0.0
        avg_y = 0.0
        for ind, val in enumerate(state['enemies']):
            avg_x = avg_x + val['x_position']
            avg_y = avg_y + val['y_position']

        avg_x = avg_x / len(state['enemies'])
        avg_y = avg_y / len(state['enemies'])

        # Do spread out logic
        for ind, val in enumerate(state['enemies']):
            # Get info
            pl = {'x_position': avg_x, 'y_position': avg_y}

            angle, sign = self.get_angle(pl, val)

            # If enemy is face towards player turn away
            if angle > self.left_side:
                # Forward, left, right, shoot?
                action = random.choice([1, 3, 4, 7])
            else:
                if sign == 1.0:
                    # Turn right
                    action = 6
                else:
                    # Turn left
                    action = 5

            # Send ai action
            commands[ind] = "set ai_" + str(self.id_to_cvar[val['id']]) + " " + str(action)

        return commands

    def check_shoot(self, state, commands):
        for ind, val in enumerate(state['enemies']):
            angle, sign = self.get_angle(state['player'], val)

            if angle < self.right_side:
                if np.random.rand() > 0.5:
                    # Shoot is action = 7
                    commands[ind] = "set ai_" + str(self.id_to_cvar[val['id']]) + " " + str(7)

        return commands

    # Enemies never shoot each other
    def check_enemies(self, state, commands):
        # From enemy
        for ind, val in enumerate(state['enemies']):
            # If an enemy is not shooting, dont mess with anything
            if '7' not in commands[ind]:
                continue

            # To enemy
            for ind2, val2 in enumerate(state['enemies']):
                # Check for self
                if ind == ind2:
                    continue

                angle, sign = self.get_angle(val2, val)

                # Smaller cone
                if angle < self.right_side / 2:
                    # random movement
                    action = random.choice([1, 2, 3, 4])
                    commands[ind] = "set ai_" + str(self.id_to_cvar[val['id']]) + " " + str(action)

        return commands

    # Utility function for getting angle from B-direction to A
    def get_angle(self, player, enemy):
        pl_x = player['x_position']
        pl_y = player['y_position']

        en_x = enemy['x_position']
        en_y = enemy['y_position']
        en_ori = enemy['angle'] * 2 * np.pi / 360

        # Get angle between player and enemy
        # Convert enemy ori to unit vector
        v1_x = np.cos(en_ori)
        v1_y = np.sin(en_ori)

        enemy_vector = np.asarray([v1_x, v1_y]) / np.linalg.norm(np.asarray([v1_x, v1_y]))

        # If its buggy throw random value out
        if np.linalg.norm(np.asarray([pl_x - en_x, pl_y - en_y])) == 0:
            return np.random.rand() * 3.14

        enemy_face_vector = np.asarray([pl_x - en_x, pl_y - en_y]) / np.linalg.norm(
            np.asarray([pl_x - en_x, pl_y - en_y]))

        angle = np.arccos(np.clip(np.dot(enemy_vector, enemy_face_vector), -1.0, 1.0))

        sign = np.sign(np.linalg.det(
            np.stack((enemy_vector[-2:], enemy_face_vector[-2:]))
        ))

        return angle, sign
