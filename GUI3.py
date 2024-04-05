from ModuleBase import Module
from PyGameServices import PyGameServices
from pubsub import pub
import numpy as np

class GUI3(Module):
    def __init__(self):
        super().__init__()

        # variables
        self.movement = [0 for i in range(6)]
        self.mode = (1920,1200)
        self.gripper = 1

        # request from PyGameServices
        pygs = PyGameServices()
        self.screen = pygs.get_screen("Control Program GUI", self.mode)
        self.pygame = pygs.get_pygame()

        # Variables and initialization

        self.white = (255, 255, 255)
        self.black = (0, 0, 0)
        self.yellow = (255, 200, 0)
        self.asian_skin = (255,224,196)
        self.dark_skin = (226, 185, 143)
        self.dark_red = (113,2,0)
        self.turquoise = '#9cc3cd'
        self.blue = '#1F456E'
        self.em_1r_colour = self.black
        self.em_1l_colour = self.black
        self.em_2l_colour = self.black
        self.em_2r_colour = self.black

        self.TFL = 0
        self.TFR = 0
        self.TBL = 0
        self.TBR = 0
        self.TUF = 0
        self.TUB = 0

        #em backing colour
        self.em_1_colour = self.blue
        self.em_2_colour = self.yellow

        self.updown_colour = self.yellow

        self.em2r = False
        self.em2l = False
        self.em1r = False
        self.em1l = False
        self.thruster = [0,0,0,0,0,0]

        self.profile = "A"
        self.invert = False

        gripper_half = self.pygame.image.load(r'.\GUI Assets\Gripper  Half Open.png')
        self.gripper_half = self.pygame.transform.scale(gripper_half,(889,500))
        gripper_closed = self.pygame.image.load(r'.\GUI Assets\Gripper Closed.png')
        self.gripper_closed = self.pygame.transform.scale(gripper_closed,(889,500))
        gripper_full_opened =self.pygame.image.load(r".\GUI Assets\Gripper fully opened.png")
        self.gripper_full_opened = self.pygame.transform.scale(gripper_full_opened,(889,500))
        rov_upview = self.pygame.image.load(r".\GUI Assets\otodus_bottom_view.png")
        self.rov_upview = self.pygame.transform.scale(rov_upview,(400,400))

        self.background = self.pygame.Surface(self.mode)
        self.background.fill(self.pygame.Color(self.turquoise))
        self.comic_font_large = self.pygame.font.SysFont("Comic Sans MS", 160)
        self.comic_font_medium = self.pygame.font.SysFont("Comic Sans MS", 80)
        self.comic_font_small = self.pygame.font.SysFont("Comic Sans MS", 40)
        self.active_tools = ("gamepad.gripper", "gamepad.EM1", "gamepad.EM2", "gamepad.erector")

        # pubsub init
        pub.subscribe(self.direct_handler, "gamepad.direct")
        pub.subscribe(self.gripper_handler,"gamepad.gripper")
        pub.subscribe(self.thruster_handler, "thruster.power")

    def rect(self,colour, dimensions):
        self.pygame.draw.rect(self.screen, colour, self.pygame.Rect(dimensions))
        # (X coord, Y position from top, length, thickness)

    def triangle(self, colour, points):
        self.pygame.draw.polygon(surface=self.screen, color=colour, points=points)

    def dcircle(self,colour, coords, size):
        self.pygame.draw.circle(self.screen, (colour), (coords), size)

    def plottings(self, point_x, point_y, offset_x, offset_y):
        coord_x = point_x * 80 + offset_x
        coord_y = point_y * -80 + offset_y
        self.dcircle((0, 200, 0), (coord_x, coord_y), 20) 

    def updown(self, BLT, BRT):
        self.rect(self.yellow, (700, (450 + (-170 * (BLT + 1))), 50, ((BLT + 1) * 170)))
        self.rect(self.yellow, (800, (450 + (-170 * (BRT + 1))), 50, ((BRT + 1) * 170)))

    def dots_back(self):
        for i in range(4):
            self.dcircle((i * 50, i * 50, i * 50), (500, 200), 120 - i * 30)
            self.dcircle((i * 50, i * 50, i * 50), (200, 200), 120 - i * 30)

    def fl_thrust(self,color,TBF):
        def_pos_1 = (1340, 185)
        def_pos_2 = (1390, 235)
        test_pos_1 = (1340 + 100* -TBF ,185 - 100*-TBF)
        test_pos_2 = (1390 + 100* -TBF, 235 - 100*-TBF)
        self.pygame.draw.polygon(self.screen, color, [(test_pos_1), (test_pos_2), (def_pos_2), (def_pos_1)])

    def br_thrust(self,color,TBR):
        def_pos_1 = (1615, 460)
        def_pos_2 = (1665, 510)
        test_pos_1 = (1615 + 100*TBR ,460 - 100*TBR)
        test_pos_2 = (1665 + 100*TBR, 510 - 100*TBR)
        self.pygame.draw.polygon(self.screen, color, [(def_pos_1),(def_pos_2),(test_pos_2),(test_pos_1)])

    def fr_thrust(self,color,TBF):
        def_pos_1 = (1615, 235)
        def_pos_2 = (1665, 185)
        test_pos_1 = (1615 +100* - TBF ,235 + 100*-TBF)
        test_pos_2 = (1665 + 100* - TBF, 185+100*-TBF)
        self.pygame.draw.polygon(self.screen, color, [(def_pos_1),(def_pos_2),(test_pos_2),(test_pos_1)])

    def up_thrust(self, color_1,color_2, TBF):
        if TBF > 0:
             self.dcircle(color_1, (1501, 210), 40 * TBF)
        elif TBF < 0:
            self.dcircle(color_2, (1501, 210), 40 * -TBF)

    def down_thrust(self, color_1,color_2, TBF):
        if TBF > 0:
             self.dcircle(color_1, (1501, 490), 40 * TBF)
        elif TBF < 0:
            self.dcircle(color_2, (1501, 490), 40 * -TBF)

    def bl_thrust(self, color, TBF):
        def_pos_1 = (1340, 510)
        def_pos_2 = (1390, 460)
        test_pos_1 = (1340 - 100 * TBF, 510 - 100 * TBF)
        test_pos_2 = (1390 - 100 * TBF, 460 - 100 * TBF)
        self.pygame.draw.polygon(self.screen, color, [(def_pos_1), (def_pos_2), (test_pos_2), (test_pos_1)])


    def updown_markers(self):
        self.rect(self.white, (700, 365, 50, 85))
        self.rect(self.black, (700, 280, 50, 85))
        self.rect(self.white, (700, 195, 50, 85))
        self.rect(self.black, (700, 110, 50, 85))

        self.rect(self.white, (800, 365, 50, 85))
        self.rect(self.black, (800, 280, 50, 85))
        self.rect(self.white, (800, 195, 50, 85))
        self.rect(self.black, (800, 110, 50, 85))



    def thruster_data(self):
        if len(self.thruster) == 6:
            self.TFL, self.TFR, self.TBL, self.TBR, self.TUF, self.TUB = (self.thruster)
            self.TFL, self.TFR, self.TBL, self.TBR, self.TUF, self.TUB = (self.thruster[0])


    # pubsub handler
    def direct_handler(self, message):
        self.movement = message["gamepad_direct"]

    def gripper_handler(self, message):
        self.gripper = message["tool_state"]


    def thruster_handler(self, message):
        self.thruster = message["thruster_power"]
    

    # MAIN LOOP
    def run(self):

        self.screen.blit(self.background, (0, 0))
        LLR, LUD, RLR, RUD,BL,BR = (self.movement)
        self.thruster_data()
        self.dots_back()
        self.updown_markers()
        self.updown(BL, BR)
        self.plottings(LLR,-LUD,200,200)
        self.plottings(RLR,-RUD,500,200)
        self.rect(self.yellow, (1200, 365,  LLR*150, 85))
        self.rect(self.yellow, (1200, 600, -LLR*150, 85))
        self.fl_thrust(self.yellow, self.TFL)
        self.br_thrust(self.yellow, self.TBR)
        self.fr_thrust(self.yellow, self.TFR)
        self.bl_thrust(self.yellow, self.TBL)
       
        
        self.pygame.display.flip()
