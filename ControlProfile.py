from pubsub import pub
from ModuleBase import Module

class ControlProfile(Module):
    def __init__(self, max_percentage = 100, formula_modifier = 30, activate = 'A'):
        super().__init__()
        pub.subscribe(self.movement_listener, 'gamepad.movement')
        pub.subscribe(self.profile_listener, 'gamepad.profile')
        self.max_percentage = int(max_percentage)/100
        self.formula_modifier = float(formula_modifier)
        self.activate = activate
        self.profile_change = 'A'

    @staticmethod
    def power_function(A, B):
        if A >=0:
            return 1/B*(((B+1)**A)-1)
        else:
            return -1/B*(((B+1)**-A)-1)

    def movement_listener(self, message):
        if self.profile_change == self.activate:
            Strafe, Drive, Yaw, Updown, TiltFB, TiltLR = message["gamepad_movement"]
            Strafe = self.power_function(Strafe, self.formula_modifier)
            Drive = self.power_function(Drive, self.formula_modifier)
            Yaw = self.power_function(Yaw, self.formula_modifier)
            Updown = self.power_function(Updown, self.formula_modifier)
            TiltFB = self.power_function(TiltFB, self.formula_modifier)
            TiltLR = self.power_function(TiltLR, self.formula_modifier)

            Strafe *= self.max_percentage
            Drive *= self.max_percentage
            Yaw *= self.max_percentage
            Updown *= self.max_percentage
            TiltFB *= self.max_percentage
            TiltLR *= self.max_percentage

            pub.sendMessage("control.movement", message = {"control_movement": (Strafe, Drive, Yaw, Updown, TiltFB, TiltLR)})

    def profile_listener(self, message):
        self.profile_change = message["gamepad_profile"]

if __name__ == "__main__":
    pass
