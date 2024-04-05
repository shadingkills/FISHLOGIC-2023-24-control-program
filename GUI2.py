from ModuleBase import Module
from PyGameServices import PyGameServices
from pubsub import pub
import pygame
import numpy as np
from pygame import font

class GUI2(Module):
    def __init__(self):
        super().__init__()

        # variables
        self.movement = [0 for i in range(6)]
        self.mode = (1920,1200)
        self.gripper = 1
        self.invert = False
        self.profile = "A"
        self.motion = [0,0,0,0,0,0]

        font.init()
        

        # request from PyGameServices
        pygs = PyGameServices()
        self.screen = pygs.get_screen("Amphitrite GUI", self.mode)
        self.pygame = pygs.get_pygame()

        # Variables and initialization
        self.white = (255, 255, 255)
        self.black = (0, 0, 0)
        self.yellow = (255, 200, 0)
        self.asian_skin = (255,224,196)
        self.dark_skin = (226, 185, 143)
        self.dark_red = (113,2,0)
        self.grey = '#808080'
        self.lgrey = '#8A8D8B'
        self.turquoise = '#9cc3cd'
        self.blue = '#1F456E'
        self.em_1r_colour = self.black
        self.em_1l_colour = self.black
        self.em_2l_colour = self.black
        self.em_2r_colour = self.black

        

        #PUB SUB Init

        pub.subscribe(self.profile_handler,"gamepad.profile")
        pub.subscribe(self.direct_handler, "control.movement")# list



        self.ROV = pygame.image.load(r".\GUI Assets\ROV corner.png")
        self.background = self.pygame.Surface(self.mode)
        self.background.fill(self.pygame.Color(self.lgrey))
        self.comic_font_large = self.pygame.font.SysFont("Comic Sans MS", 160)
        self.comic_font_medium = self.pygame.font.SysFont("Comic Sans MS", 80)
        self.comic_font_small = self.pygame.font.SysFont("Comic Sans MS", 40)
        self.Arial = self.pygame.font.SysFont("Arial", 60)

    def triangle(self, colour, points):
         self.pygame.draw.polygon(surface=self.screen, color=colour, points=points)

    def circle(self,colour, coords, size):
         self.pygame.draw.circle(self.screen, (colour), (coords), size)

    def rect(self,colour, dimensions):
         self.pygame.draw.rect(self.screen, colour, self.pygame.Rect(dimensions))
    
    def rov_image(self):
         self.screen.blit(self.ROV, (1300, 670))

    def move_view(self):
       if self.motion == [0,0,0,0,0,0]:
        self.tester = self.Arial.render("stop", False, (0,0,0))
        self.screen.blit(self.tester,(500, 240))
       elif self.motion == [0,0,0,1,0,0]:
        self.tester = self.Arial.render("work", False, (0,0,0))
        self.screen.blit(self.tester,(500, 240))
       


    

    def profile_view(self):
        if self.profile == "A":
            coloring = self.blue
        elif self.profile == "B":
            coloring = self.yellow
        elif self.profile == "C":
            coloring = self.dark_red
        elif self.profile =="D":
            coloring = self.white
        self.rect(coloring, (1250, 740, 170, 170))
        self.profile_labeler = self.comic_font_small.render("Profile: ",False, (0,0,0))
        self.profile_data = self.Arial.render(str(self.profile), False, (0,0,0))
        self.screen.blit(self.profile_data,(380, 240))
        self.screen.blit(self.profile_labeler,(240, 250))

    def profile_handler(self, message):
        self.profile = message["gamepad_profile"]

    def direct_handler(self, message):
        self.motion = message["control_movement"]


    def run(self):
        self.screen.blit(self.background, (0, 0))
        self.rov_image()
        self.profile_view()
        self.move_view()
        
        

        self.pygame.display.flip()
     
