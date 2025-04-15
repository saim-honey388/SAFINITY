from kivy.uix.screenmanager import Screen

class SignupSelectionScreen(Screen):
    def go_to_phone_signup(self):
        self.manager.current = 'phone_signup'
        
    def go_to_email_signup(self):
        self.manager.current = 'email_signup'
        
    def back_to_login(self):
        self.manager.current = 'login' 