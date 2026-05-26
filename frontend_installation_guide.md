# 🛠️ Frontend Phase — Installation Guide

> Everything you need to install **before** writing any Flutter code.

---

## Overview: What Are We Installing?

The frontend is a **Flutter mobile app** (Android). You need **3 categories** of tools:

| Category | Tools | Purpose |
|---|---|---|
| **Framework** | Flutter SDK + Dart | Build the mobile app |
| **IDE & Plugins** | Android Studio + VS Code Extensions | Android emulator, build tools, coding |
| **Testing** | Android Emulator or Physical Device | Run and test the app |

---

## 1. Flutter SDK (Required)

### What is it?
Flutter is Google's UI toolkit for building natively compiled mobile apps from a single codebase. You write code **once in Dart** and it runs on both Android and iOS.

### Why Flutter?
| Feature | Benefit |
|---|---|
| **Hot Reload** | See code changes instantly without restarting the app |
| **Single Codebase** | One codebase for Android + iOS (we're targeting Android first) |
| **Rich Widgets** | Beautiful pre-built UI components |
| **Dart Language** | Simple, modern, and fast — similar to Java/JavaScript |
| **Strong Ecosystem** | Thousands of packages for camera, storage, networking, etc. |

### Install

1. Go to [flutter.dev/docs/get-started/install/windows](https://docs.flutter.dev/get-started/install/windows)
2. Download the **Flutter SDK** zip file
3. Extract to a location like `C:\flutter` (avoid `Program Files` — permission issues)
4. **Add Flutter to PATH:**
   - Open Start Menu → search **"Environment Variables"**
   - Click **"Edit the system environment variables"**
   - Click **"Environment Variables"** button
   - Under **User variables**, find `Path` → click **Edit**
   - Click **New** → add `C:\flutter\bin`
   - Click **OK** on all dialogs

> [!IMPORTANT]
> The path should point to the `bin` folder inside your Flutter directory. For example, if you extracted Flutter to `C:\flutter`, add `C:\flutter\bin` to PATH.

### Verify
```powershell
flutter --version
```

Should show something like:
```
Flutter 3.x.x • channel stable
Dart 3.x.x
```

---

## 2. Dart SDK (Comes with Flutter)

### What is it?
Dart is the programming language used to write Flutter apps. Think of it like JavaScript but for mobile apps — it's simple, strongly typed, and optimized for building UIs.

### Do I need to install it separately?
**No!** Dart comes bundled with Flutter. When you install Flutter, Dart is automatically included.

### Verify
```powershell
dart --version
```

---

## 3. Android Studio (Required)

### What is it?
Android Studio is the official IDE for Android development. We don't write code in it (we use VS Code), but we need it for **two critical things**:

| Component | Why We Need It |
|---|---|
| **Android SDK** | The actual Android platform tools — compilers, libraries, and APIs needed to build Android apps. Flutter can't build an APK without this. |
| **Android Emulator** | A virtual Android phone on your computer to test the app (if you don't have a physical Android device). |

### Why can't I skip this?
Without Android Studio, Flutter has no way to compile your Dart code into an Android APK. The Android SDK contains the tools (`adb`, `gradle`, `build-tools`) that Flutter uses under the hood.

### Install

1. Go to [developer.android.com/studio](https://developer.android.com/studio)
2. Download **Android Studio** (latest version)
3. Run the installer — keep all default options
4. On first launch, Android Studio will download:
   - **Android SDK** (~1.5 GB)
   - **Android SDK Command-line Tools**
   - **Android SDK Build-Tools**
   - **Android Emulator**
5. Wait for the setup to complete

### Accept Android Licenses
After installation, open PowerShell and run:

```powershell
flutter doctor --android-licenses
```

Type **y** (yes) for every license prompt. This is required before Flutter can build Android apps.

---

## 4. Android Emulator (or Physical Device)

### What is it?
A **virtual Android phone** that runs on your computer. It lets you test the app without a physical device. It simulates a real phone — camera, storage, GPS, everything.

### Option A: Android Emulator (Recommended for Development)

#### Set Up in Android Studio:
1. Open **Android Studio**
2. Click **"More Actions"** (or **"Tools"** menu) → **"Virtual Device Manager"**
3. Click **"Create Virtual Device"**
4. Select a phone: **Pixel 7** or **Pixel 8** (good default)
5. Select a system image: **API 34** (Android 14) — click "Download" if needed
6. Click **Finish**

#### Launch the Emulator:
- In Virtual Device Manager, click the **▶ Play** button next to your device
- The emulator window opens — it looks like a phone on your screen
- Keep it running while developing

> [!TIP]
> **Hardware Acceleration:** For smooth emulator performance, make sure **Intel HAXM** (for Intel CPUs) or **Windows Hypervisor Platform** (for AMD CPUs) is enabled. Android Studio usually prompts you to install this during setup.

### Option B: Physical Android Device

If you have an Android phone, you can test directly on it:

1. **Enable Developer Options:**
   - Go to `Settings → About Phone`
   - Tap **"Build Number"** 7 times — you'll see "You are now a developer!"
2. **Enable USB Debugging:**
   - Go to `Settings → Developer Options`
   - Turn on **"USB Debugging"**
3. **Connect via USB:**
   - Connect your phone to your computer with a USB cable
   - When prompted on your phone, tap **"Allow USB Debugging"**
4. **Verify Flutter detects it:**
   ```powershell
   flutter devices
   ```
   Your phone should appear in the list.

> [!TIP]
> Physical device testing is more realistic (real camera, real touch) but the emulator is more convenient for iterating quickly. I recommend using **both** — emulator for coding, physical device for final testing.

---

## 5. VS Code Extensions (Required)

### What are they?
VS Code extensions add Flutter/Dart support — code highlighting, auto-completion, debugging, and hot reload directly from VS Code.

### Install These Extensions:

1. Open **VS Code**
2. Go to **Extensions** (Ctrl+Shift+X)
3. Search and install:

| Extension | What It Does |
|---|---|
| **Flutter** (by Dart Code) | Full Flutter development support — run, debug, hot reload, widget inspector |
| **Dart** (by Dart Code) | Dart language support — syntax highlighting, auto-complete, code formatting |

> These two are the only **required** extensions. Installing "Flutter" usually auto-installs "Dart" as well.

#### Optional but Helpful:

| Extension | What It Does |
|---|---|
| **Error Lens** | Shows errors inline in the editor (easier than checking the Problems panel) |
| **Pubspec Assist** | Helps add packages to pubspec.yaml quickly |
| **Flutter Widget Snippets** | Code snippets for common Flutter widgets |

---

## 6. Flutter Packages (Installed Automatically)

Unlike the backend where we ran `pip install`, Flutter packages are defined in a `pubspec.yaml` file and installed automatically with `flutter pub get`. **You don't need to install them manually now** — they'll be added when we start coding.

Here's what we'll use and why:

### Core Packages

| Package | What It Does |
|---|---|
| **dio** | HTTP client for API calls. Better than the built-in `http` package because it supports interceptors (auto-attach JWT to every request, auto-refresh expired tokens). |
| **flutter_riverpod** | State management — manages app-wide state (logged-in user, prediction results, history). Riverpod is type-safe, testable, and doesn't depend on BuildContext. |
| **go_router** | Navigation — handles screen routing, deep linking, and redirects (e.g., redirect to login if not authenticated). |
| **flutter_secure_storage** | Securely stores JWT tokens on the device using Android Keystore. Unlike SharedPreferences, the data is encrypted and can't be read by other apps. |

### Camera & Image

| Package | What It Does |
|---|---|
| **image_picker** | Accesses the device camera and photo gallery. Returns the selected image as a file we can upload to the backend. |
| **cached_network_image** | Loads images from URLs (MinIO) with automatic caching. Once an image is loaded, it's cached on the device — no re-downloading on next view. |

### UI & Animations

| Package | What It Does |
|---|---|
| **google_fonts** | Uses modern fonts (Inter, Outfit) instead of default Android fonts. Makes the app look professional without bundling font files. |
| **lottie** | Plays Lottie animations — lightweight, high-quality animations exported from After Effects. We'll use these for loading states (leaf scanning animation), empty states, and success animations. |
| **shimmer** | Creates shimmering placeholder effects while content loads (like Facebook/Instagram loading). |
| **fl_chart** | Beautiful charts for displaying confidence scores and prediction statistics. |

### Utilities

| Package | What It Does |
|---|---|
| **intl** | Date/time formatting — displays "2 hours ago", "May 13, 2026" instead of raw timestamps. |
| **connectivity_plus** | Detects internet connectivity — shows "No connection" message when offline. |
| **flutter_dotenv** | Loads environment variables from a `.env` file — keeps the backend URL configurable. |

---

## 7. Install Everything (Step by Step)

### Step 1: Install Flutter SDK
```powershell
# After downloading and extracting to C:\flutter
# Verify:
flutter --version
```

### Step 2: Install Android Studio
Download → Install → Let it download Android SDK.

### Step 3: Accept Licenses
```powershell
flutter doctor --android-licenses
```

### Step 4: Install VS Code Extensions
Extensions panel → Install "Flutter" and "Dart"

### Step 5: Run Flutter Doctor
This command checks your entire setup and tells you what's missing:

```powershell
flutter doctor -v
```

**You want ALL green checkmarks ✓:**

```
[✓] Flutter (Channel stable, 3.x.x)
[✓] Windows Version (Installed version of Windows is version 10 or higher)
[✓] Android toolchain - develop for Android devices (Android SDK version 34.x.x)
[✓] Android Studio (version 2024.x)
[✓] VS Code (version 1.x.x)
[✓] Connected device (1 available)    ← emulator or physical device
```

If any item shows ✗ or !, follow the instructions `flutter doctor` provides.

---

## Summary Checklist

- [ ] Flutter SDK installed and in PATH (`flutter --version` works)
- [ ] Dart installed (comes with Flutter)
- [ ] Android Studio installed (Android SDK downloaded)
- [ ] Android licenses accepted (`flutter doctor --android-licenses`)
- [ ] Emulator created OR physical device connected
- [ ] VS Code extensions: Flutter + Dart installed
- [ ] `flutter doctor` shows all green ✓

> [!TIP]
> You **don't** need to install any Flutter packages manually. They're defined in `pubspec.yaml` and downloaded with `flutter pub get` when we start coding. The only things to install are **Flutter SDK**, **Android Studio**, and the **VS Code extensions**.
