[app]
 # (str) Title of your application
 title = Safinity
 
 # (str) Target platform (android, ios, etc)
 target = android
 
 # (str) Package name
 package.name = safinity
 
 # (str) Package domain (needed for android/ios packaging)
 package.domain = org.safinity
 
 
 
 # (str) Source code where the main.py live
 source.dir = .
 
 
 # (list) Source files to include (let empty to include all the files)
 source.include_exts =py,png,jpg,kv,atlas,ttf,json
 # (list) List of inclusions using pattern matching
 source.include_patterns = assets/*,screens/**/*,models/**/*,utils/**/*,migrations/**/*
 
 # (list) Source files to exclude (let empty to not exclude anything)
 #source.exclude_exts = spec
 
 # (str) Application versioning
 version = 0.1
 
 icon.filename = assets/logo.png
 #presplash.filename = assets/logo.png
 
 # (list) Application requirements
 requirements = 
      python3,alembic==1.13.1,
      kivy==2.3.0,
      kivymd==1.1.1,
      python-dotenv,
      plyer,
      requests,
      pillow,
      pyjnius,
      android,
      sqlite3,
      openssl,
      certifi,
      chardet,
      idna,
      urllib3,
      bcrypt,
      twilio
 
 # (list) Supported orientations
 orientation = portrait
 
 # (bool) Indicate if the application should be fullscreen or not
 fullscreen = 0
 
 # (list) Permissions
 android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,CAMERA,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,READ_CONTACTS,WRITE_CONTACTS,BLUETOOTH,BLUETOOTH_ADMIN,BLUETOOTH_ADVERTISE,BLUETOOTH_CONNECT,BLUETOOTH_SCAN,BATTERY_STATS
 
 # (int) Target Android API, should be as high as possible.
 android.api = 33
 
 # (int) Minimum API your APK / AAB will support.
 android.minapi = 21

 
 # (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
 log_level = 2
 
 # (bool) Use --private data storage (True) or --dir public storage (False)
 android.private_storage = True
 
 # (bool) If True, then automatically accept SDK license
 android.accept_sdk_license = True
 
 # (list) The Android archs to build for
 android.archs = armeabi-v7a, arm64-v8a
 
 # (str) python-for-android branch to use
 p4a.branch = develop
 
 # (bool) enables Android auto backup feature (Android API >=23)
 android.allow_backup = True
 android.entrypoint = org.kivy.android.PythonActivity
 # (str) Android entry point
 
 
 # (str) Android app theme, default is ok for Kivy-based app
 android.apptheme = @android:style/Theme.NoTitleBar
 
 # (bool) Copy library instead of making a libpymodules.so
 android.copy_libs = 1

