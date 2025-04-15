from kivy.app import App
from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition
from kivy.lang import Builder
from kivy.properties import ObjectProperty

# Load KV file
Builder.load_file('screens/info/info_screen.kv')

class InfoBaseScreen(Screen):
    """Base class for all info screens with common functionality"""
    
    def on_next(self):
        """Navigate to the next screen"""
        # This will be overridden by child classes
        pass
    
    def on_previous(self):
        """Navigate to the previous screen"""
        # This will be overridden by child classes
        pass
    
    def go_home(self):
        """Return to the home screen"""
        # The correct screen name appears to be 'home' based on the error
        try:
            # Need to use the root manager, not the info screen manager
            app = App.get_running_app()
            app.root.current = 'home'
            print("Successfully navigated back to home screen")
        except Exception as e:
            import traceback
            print(f"Error returning to home screen: {str(e)}")
            traceback.print_exc()
    
class InfoStep1Screen(InfoBaseScreen):
    """First info screen: Create an Account"""
    
    def on_next(self):
        """Go to step 2"""
        # Set the transition direction first
        self.manager.transition.direction = 'left'
        # Then change the screen
        self.manager.current = 'info_step2'

class InfoStep2Screen(InfoBaseScreen):
    """Second info screen: Connect to Device"""
    
    def on_next(self):
        """Go to step 3"""
        # Set the transition direction first
        self.manager.transition.direction = 'left'
        # Then change the screen
        self.manager.current = 'info_step3'
    
    def on_previous(self):
        """Go back to step 1"""
        # Set the transition direction first
        self.manager.transition.direction = 'right'
        # Then change the screen
        self.manager.current = 'info_step1'

class InfoStep3Screen(InfoBaseScreen):
    """Third info screen: Alert"""
    
    def on_next(self):
        """Go to step 4"""
        # Set the transition direction first
        self.manager.transition.direction = 'left'
        # Then change the screen
        self.manager.current = 'info_step4'
    
    def on_previous(self):
        """Go back to step 2"""
        # Set the transition direction first
        self.manager.transition.direction = 'right'
        # Then change the screen
        self.manager.current = 'info_step2'

class InfoStep4Screen(InfoBaseScreen):
    """Fourth info screen: Location Sharing & Alerts"""
    
    def on_previous(self):
        """Go back to step 3"""
        # Set the transition direction first
        self.manager.transition.direction = 'right'
        # Then change the screen
        self.manager.current = 'info_step3'

# Main Info Screen Manager
class InfoScreenManager(ScreenManager):
    """Screen manager for the info walkthrough"""
    pass

class InfoMainScreen(Screen):
    """Main container for the info screens"""
    screen_manager = ObjectProperty(None)
    
    def on_enter(self):
        """Reset to first step when entering the info screens"""
        # Import here to avoid circular imports
        from kivy.uix.screenmanager import SlideTransition
        
        # Set transition before changing screen to prevent overlapping views
        self.screen_manager.transition = SlideTransition(duration=0.15)
        self.screen_manager.current = 'info_step1'
