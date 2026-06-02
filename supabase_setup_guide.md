# Supabase Setup Guide — Step-by-Step Dashboard Guide

This guide provides click-by-click, visual instructions to retrieve your Database Connection URI, create the `leaf-images` public storage bucket, and extract S3 connection keys in the Supabase Dashboard.

---

## 🔑 1. Finding the Database Connection String (URI)

Your FastAPI backend uses this URI to connect to PostgreSQL to read/write users, scans, and GIN drug classification history.

### Click-by-Click Instructions:
1. Open the [Supabase Dashboard](https://supabase.com/dashboard) and click on your **PlantGuard** project.
2. Look at the **vertical navigation sidebar** on the far-left of the screen.
3. Scroll down to the very bottom of the sidebar and click on the **Settings (Gear/Cog ⚙️ icon)**.
4. Clicking Settings opens a sub-menu panel. Look under the **Project Settings** section and click **Database**.
5. On the main Database Settings page, scroll down until you see the **Connection string** section.
6. You will see several tabs (e.g., `Node.js`, `Go`, `Python`, `URI`). Click the **URI** tab.
7. Click the **Copy** button on the right of the string.
8. Paste it somewhere safe! It will look like this:
   ```text
   postgresql://postgres.[your-project-id]:[your-password]@aws-0-[region].pooler.supabase.com:6543/postgres?sslmode=require&supa-pooler-port=6543
   ```
   > [!IMPORTANT]
   > Remember to replace `[your-password]` in that string with the **actual database password** you typed when creating the Supabase project!

---

## 🪣 2. Creating the Public Storage Bucket

This is where the leaf scan images uploaded by users from their mobile phones will be stored.

### Click-by-Click Instructions:
1. In the **vertical navigation sidebar** on the far-left, click on the **Storage (Bucket/Folder 📦 icon)**.
2. In the storage panel that opens, click the **New bucket** button (located in the upper-left of the storage navigation pane).
3. A dialog popup will appear:
   - In the **Name of bucket** text box, type exactly: `leaf-images`
   - Locate the **Public bucket** toggle switch and **enable it** (it should turn active/green/blue).
4. Click the **Save** button.
5. You should now see `leaf-images` appear under your buckets list on the left side!

---

## 🌐 3. Getting your S3 Connection Details

FastAPI connects to Supabase Storage using standard S3 protocol, so it needs S3 credentials and endpoint URLs.

### Click-by-Click Instructions:
1. Go back to the **Settings (Gear/Cog ⚙️ icon)** at the bottom-left sidebar.
2. In the sub-menu panel under **Project Settings**, locate and click on **Storage** (it is situated right below the *Database* option you clicked in Part 1).
3. Scroll down on the Storage page until you see the **S3 Connection** section.
4. Copy the **Endpoint** URL. It will look like this:
   ```text
   https://[your-project-id].supabase.co/storage/v1/s3
   ```
5. Below the endpoint, locate the **S3 Access Keys** card and click the **New Access Key** button.
6. A popup will ask you to name the key:
   - Type in: `plantguard-deploy`
   - Click **Create Key**.
7. **CRITICAL STEP**: The popup will now show you your **Access Key ID** and **Secret Access Key**:
   - Copy the **Access Key ID** and save it.
   - Copy the **Secret Access Key** and save it immediately.
   > [!WARNING]
   > The *Secret Access Key* is only shown once and cannot be recovered later. If you close the popup before copying it, you will have to generate a new key.

---

### 🎉 What's next?
Once you have copied these four items:
1. **Database URI**
2. **S3 Endpoint**
3. **S3 Access Key ID**
4. **S3 Secret Access Key**

Let me know, and we will run your Alembic DB migrations against the Supabase database to construct all your tables in 10 seconds!
