import pygame
from ModuleBase import Module

class PyGameServices(Module):

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(PyGameServices, cls).__new__(cls)
            cls.screen = None
            cls.joystick = None
        return cls.instance

    @classmethod
    def run_once_in_thread(cls):

        pygame.init()
        pygame.display.init()
        pygame.font.init()
       

    @classmethod
    def run(cls):
        # if cls.screen: # run if screen initialized
        #     print("screen init")
        #     for event in pygame.event.get(pump=True):
        #         if event.type == pygame.QUIT:
        #             pygame.quit()

        pygame.event.pump()

    @classmethod
    def get_pygame(cls):
        return pygame

    @classmethod
    def get_screen(cls, caption, mode = (1920, 1080)):
        pygame.display.set_caption(caption)
        cls.screen = pygame.display.set_mode(mode)
        return cls.screen

    @classmethod
    def get_joystick(cls, ID = 0):
        if cls.joystick is None:
            print("Joystick count: ", pygame.joystick.get_count())
            cls.joystick = pygame.joystick.Joystick(ID)
            cls.joystick.init()

        return cls.joystick

