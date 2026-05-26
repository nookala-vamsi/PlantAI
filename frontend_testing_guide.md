# 📱 Frontend Testing Guide — Physical Device

> Test the PlantGuard app on your physical Android phone connected via USB.

---

## Prerequisites Checklist

- [x] Phone connected to laptop via USB cable
- [x] USB Debugging enabled on phone (Settings → Developer Options → USB Debugging)
- [x] Backend code ready (`F:\ML_PROJECT\backend\`)
- [x] Frontend code ready (`F:\ML_PROJECT\frontend\`)
- [x] Docker Desktop running

---

## Step 1: Verify Phone is Detected

Open a **PowerShell terminal** and run:

```powershell
cd F:\ML_PROJECT\frontend
flutter devices
```

**Expected output:**
```
2 connected devices:

SM G991B (mobile) • R5CR1234567 • android-arm64 • Android 14 (API 34)
Chrome (web)      • chrome       • web-javascript • Google Chrome
```

You should see your phone listed with `android` in the description.

> [!WARNING]
> If your phone doesn't appear:
> 1. Check if a popup appeared on your phone asking **"Allow USB Debugging?"** — tap **Allow**
> 2. Try a different USB cable (some cables are charge-only, not data)
> 3. Make sure USB mode is set to **"File Transfer"** (not "Charging only")
> 4. Run `flutter doctor` to check for issues

---

## Step 2: Find Your Laptop's IP Address

Since the app runs on your phone but the backend runs on your laptop, they need to communicate over your WiFi network.

Run this command:

```powershell
ipconfig
```

Look for **"Wireless LAN adapter Wi-Fi"** section and find the **IPv4 Address**:

```
Wireless LAN adapter Wi-Fi:
   IPv4 Address. . . . . . . . . : 192.168.1.5    ← THIS IS YOUR IP
```

**Copy this IP address** — you need it in the next step.

> [!IMPORTANT]
> Both your phone and laptop MUST be connected to the **same WiFi network**.
> The IP will look something like `192.168.x.x` or `10.0.x.x`

---

## Step 3: Update the .env File

Open `F:\ML_PROJECT\frontend\.env` and update it with your laptop's IP:

**Before:**
```
API_BASE_URL=http://10.0.2.2:8000/api/v1
```

**After (replace with YOUR IP from Step 2):**
```
API_BASE_URL=http://192.168.1.5:8000/api/v1
```

> `10.0.2.2` is only for the Android emulator. For a physical device, you need the actual WiFi IP.

---

## Step 4: Start the Backend

You need **2 terminals** — one for Docker, one for the server.

### Terminal 1 — Start Docker Services

```powershell
cd F:\ML_PROJECT\backend
docker compose up -d
```

Wait for all 3 containers to be healthy:

```powershell
docker compose ps
```

You should see `plantai_postgres`, `plantai_redis`, and `plantai_minio` all **running (healthy)**.

### Terminal 2 — Start FastAPI Server

```powershell
cd F:\ML_PROJECT\backend
& F:\ML_PROJECT\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

> [!IMPORTANT]
> The `--host 0.0.0.0` is critical! It makes the server accessible to your phone over WiFi.
> Without it, the server only accepts connections from localhost (your laptop only).

**Expected output:**
```
🌿 PlantDiseaseAI v1.0.0 is ready!
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Quick Verify from Phone

Open your phone's browser and go to:

```
http://192.168.1.5:8000/api/v1/health
```

*(Replace with YOUR IP)*

If you see `{"status":"healthy"}`, the backend is reachable from your phone! ✅

> [!WARNING]
> If the page doesn't load:
> - Check Windows Firewall — it may be blocking port 8000
> - To allow it: search **"Windows Firewall"** → **"Allow an app through firewall"** → add port **8000** for **Private networks**
> - Or temporarily: `netsh advfirewall firewall add rule name="uvicorn" dir=in action=allow protocol=TCP localport=8000`

---

## Step 5: Run the Flutter App

Open a **new (3rd) terminal**:

```powershell
cd F:\ML_PROJECT\frontend
flutter run
```

### What happens:
1. Flutter compiles the Dart code → builds an Android APK
2. Installs the APK on your connected phone
3. Launches the app on your phone
4. Shows debug output in the terminal

**First build takes 2-5 minutes** (subsequent builds are much faster with hot reload).

### Expected terminal output:
```
Launching lib/main.dart on SM G991B in debug mode...

Running Gradle task 'assembleDebug'...
✓ Built build\app\outputs\flutter-apk\app-debug.apk

Installing build\app\outputs\flutter-apk\app-debug.apk...
Syncing files to device SM G991B...

Flutter run key commands:
r  Hot reload   🔥
R  Hot restart   🔄
q  Quit
```

The app should now be **open on your phone!** 📱

---

## Step 6: Test the Full App Flow

### 6.1 — Splash Screen (Automatic)
- You should see the **PlantGuard** logo with a green gradient
- After 2 seconds, it redirects to the Login screen

### 6.2 — Register
- Tap **"Register"** at the bottom
- Fill in:
  - **Username:** `testuser`
  - **Email:** `test@example.com`
  - **Password:** `Test@1234`
  - **Confirm Password:** `Test@1234`
- Tap **"Create Account"**
- You should see a **green success message** and be redirected to Login

### 6.3 — Login
- Enter:
  - **Email:** `test@example.com`
  - **Password:** `Test@1234`
- Tap **"Sign In"**
- You should be redirected to the **Home Screen**

### 6.4 — Home Screen (Crop Grid)
- You should see a **grid of 14 crops** (Apple, Blueberry, Cherry, Corn, etc.)
- Each crop has a colored card with an icon
- The top-right has a **history button** and **logout button**

### 6.5 — Scan a Leaf 🌿
1. Tap any crop card (e.g., **Tomato**)
2. You'll see the **Camera Screen** with "Scanning: Tomato"
3. Tap **"Take Photo"** → your phone camera opens
4. Take a photo of a leaf (any plant leaf for testing)
5. You'll see a **preview** of the image
6. Tap **"Analyze Leaf"**
7. Wait for the loading overlay → results appear!

### 6.6 — Result Screen
- **If the model detects a disease:**
  - Red/orange header with disease name
  - Confidence percentage with progress bar
  - Severity badge (Low/Medium/High)
  - Symptoms, Remedies, and Prevention sections
- **If healthy:**
  - Green header with "Healthy Plant! 🌱"

### 6.7 — History
- Tap **"View History"** or the history icon on Home
- You should see your previous prediction(s)

### 6.8 — Logout
- On Home screen, tap the **red logout icon** (top-right)
- You should be redirected back to Login

---

## Step 7: Hot Reload (While Testing)

While the app is running, you can make code changes and see them instantly:

- Press **`r`** in the terminal → **Hot Reload** (keeps state, updates UI)
- Press **`R`** in the terminal → **Hot Restart** (resets state, full restart)
- Press **`q`** in the terminal → **Quit** (closes the app)

Hot reload is one of Flutter's best features — change a color, font, or layout and see it update in under 1 second!

---

## Step 8: Stop Everything

### Stop the Flutter app:
Press **`q`** in the terminal running `flutter run`

### Stop the backend server:
Press **`Ctrl+C`** in the terminal running uvicorn

### Stop Docker services:
```powershell
cd F:\ML_PROJECT\backend
docker compose down
```

---

## Troubleshooting

| Problem | Solution |
|---|---|
| Phone not detected by `flutter devices` | Enable USB Debugging, try different cable, set USB to "File Transfer" |
| `Connection refused` in app | Check the IP in `.env`, ensure backend is running with `--host 0.0.0.0` |
| App can't reach backend | Both devices must be on same WiFi. Check Windows Firewall. |
| Gradle build fails | Run `flutter clean` then `flutter run` again |
| `INSTALL_FAILED` on phone | Unlock your phone, check for install permission popup |
| App crashes on launch | Check terminal for error logs. Run `flutter run --verbose` for details |
| Camera doesn't open | Check if camera permission was granted on phone |
| Slow first build | Normal — first build takes 2-5 min. Subsequent builds use hot reload. |

---

## Terminal Layout Summary

You need **3 terminals** open:

| Terminal | What's Running | Keep Open? |
|---|---|---|
| Terminal 1 | `docker compose up -d` | Can close after starting |
| Terminal 2 | `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` | ✅ Keep open |
| Terminal 3 | `flutter run` | ✅ Keep open |
