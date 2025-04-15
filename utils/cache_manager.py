import os
import shutil
import glob
from kivy.app import App
import traceback

class CacheManager:
    """
    Utility class to manage cache files in the application.
    Handles clearing image caches and temporary files.
    """
    
    def __init__(self):
        # Define cache directories
        self.app_cache_dir = os.path.join(os.path.expanduser('~'), '.safinity', 'cache')
        self.profile_cache_dir = os.path.join(self.app_cache_dir, 'profile_pictures')
        
        # Create cache directories if they don't exist
        os.makedirs(self.app_cache_dir, exist_ok=True)
        os.makedirs(self.profile_cache_dir, exist_ok=True)
    
    def get_cached_profile_path(self, user_id, filename):
        """
        Get the path to a cached profile picture.
        
        Args:
            user_id (str): The user ID
            filename (str): Original filename
            
        Returns:
            str: Path to the cached file
        """
        # Extract file extension
        _, ext = os.path.splitext(filename)
        
        # Create cache filename
        cache_filename = f"{user_id}{ext}"
        
        # Return full path
        return os.path.join(self.profile_cache_dir, cache_filename)
    
    def cache_profile_picture(self, user_id, source_path):
        """
        Cache a profile picture for faster loading.
        
        Args:
            user_id (str): The user ID
            source_path (str): Path to the source image
            
        Returns:
            str: Path to the cached file or None on error
        """
        try:
            if not os.path.exists(source_path):
                print(f"Source file does not exist: {source_path}")
                return None
                
            # Get cache path
            cache_path = self.get_cached_profile_path(user_id, source_path)
            
            # Copy file to cache
            shutil.copy2(source_path, cache_path)
            
            print(f"Profile picture cached: {cache_path}")
            return cache_path
        except Exception as e:
            print(f"Error caching profile picture: {str(e)}")
            traceback.print_exc()
            return None
    
    def clear_profile_cache(self, user_id=None):
        """
        Clear cached profile pictures.
        
        Args:
            user_id (str, optional): Specific user ID to clear cache for.
                                    If None, clears all profile caches.
        """
        try:
            if user_id:
                # Clear specific user's cache
                pattern = os.path.join(self.profile_cache_dir, f"{user_id}.*")
                files = glob.glob(pattern)
                for file in files:
                    os.remove(file)
                print(f"Cleared profile cache for user {user_id}")
            else:
                # Clear all profile caches
                if os.path.exists(self.profile_cache_dir):
                    for file in os.listdir(self.profile_cache_dir):
                        file_path = os.path.join(self.profile_cache_dir, file)
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                print("Cleared all profile picture caches")
        except Exception as e:
            print(f"Error clearing profile cache: {str(e)}")
            traceback.print_exc()
    
    def clear_all_caches(self):
        """
        Clear all application caches including profile pictures and other temporary files.
        """
        try:
            # Clear profile picture cache
            self.clear_profile_cache()
            
            # Clear other cache directories if they exist
            for subdir in os.listdir(self.app_cache_dir):
                if subdir != 'profile_pictures':  # Skip the profile pictures we already cleared
                    subdir_path = os.path.join(self.app_cache_dir, subdir)
                    if os.path.isdir(subdir_path):
                        shutil.rmtree(subdir_path)
                        os.makedirs(subdir_path, exist_ok=True)
            
            # Clear Kivy cache if needed
            try:
                from kivy.cache import Cache
                Cache.remove('kv.image')
                Cache.remove('kv.texture')
                print("Cleared Kivy image and texture cache")
            except Exception as e:
                print(f"Error clearing Kivy cache: {str(e)}")
            
            print("All caches cleared successfully")
        except Exception as e:
            print(f"Error clearing all caches: {str(e)}")
            traceback.print_exc()

# Singleton instance
cache_manager = CacheManager()