# GeoIP Setup Guide

This guide explains how to set up IP geolocation for the Photo Restoration application. IP geolocation enables the application to display approximate geographic locations (city, state, country) for user sessions based on their IP addresses.

## Overview

**Status:** Optional Feature
**Default Behavior:** Without GeoIP database, sessions show "📍Unknown location"
**With GeoIP:** Sessions show approximate location like "San Francisco, CA, United States"

## Why is this optional?

The GeoIP2 database:
- Requires registration with MaxMind (free for GeoLite2)
- Is ~70MB in size
- Has licensing restrictions (cannot be redistributed in git repositories)
- Is not essential for core application functionality

## Prerequisites

1. **Free MaxMind Account** - Required to download GeoLite2 database
2. **GeoLite2-City Database** - The actual database file (.mmdb)

## Step 1: Create MaxMind Account

1. Visit [MaxMind GeoLite2 Registration](https://dev.maxmind.com/geoip/geolite2-free-geolocation-data)
2. Click "Sign Up for GeoLite2" or "Create Account"
3. Complete registration with your email
4. Verify your email address
5. Log in to your account

## Step 2: Generate License Key

1. Log in to your MaxMind account
2. Navigate to "My License Key" in the left sidebar
3. Click "Generate new license key"
4. Enter a description (e.g., "Photo Restoration App")
5. Select "No" for "Will this key be used for GeoIP Update?"
6. Click "Confirm"
7. **Save the license key** - you'll need it for downloads

## Step 3: Download GeoLite2-City Database

### Option A: Direct Download (Web Interface)

1. Log in to your MaxMind account
2. Navigate to "Download Files" → "GeoIP2 / GeoLite2"
3. Find "GeoLite2 City" in the list
4. Click "Download GZIP" for the `.mmdb` format
5. Extract the `.tar.gz` file:
   ```bash
   tar -xzf GeoLite2-City_*.tar.gz
   ```
6. Locate the `.mmdb` file inside the extracted directory:
   ```bash
   cd GeoLite2-City_*/
   ls -la GeoLite2-City.mmdb
   ```

### Option B: Command Line (with geoipupdate)

```bash
# Install geoipupdate tool
# Ubuntu/Debian:
sudo apt-get install geoipupdate

# macOS:
brew install geoipupdate

# Configure geoipupdate
sudo nano /etc/GeoIP.conf

# Add your credentials:
AccountID YOUR_ACCOUNT_ID
LicenseKey YOUR_LICENSE_KEY
EditionIDs GeoLite2-City

# Run update
sudo geoipupdate

# Database will be at: /usr/share/GeoIP/GeoLite2-City.mmdb
```

## Step 4: Install Database

Choose the installation method based on your deployment:

### For Docker Deployment (Recommended)

1. **Choose a location** for the database file on your host:
   ```bash
   # Example: /opt/geoip/
   sudo mkdir -p /opt/geoip
   ```

2. **Copy the database file** to your chosen location:
   ```bash
   sudo cp GeoLite2-City.mmdb /opt/geoip/GeoLite2-City.mmdb
   sudo chmod 644 /opt/geoip/GeoLite2-City.mmdb
   ```

3. **Update docker-compose.yml** - Uncomment the GeoIP volume mount:
   ```yaml
   services:
     backend:
       volumes:
         - backend_data:/data
         - ./backend/config:/app/config
         # Uncomment and update this line:
         - /opt/geoip/GeoLite2-City.mmdb:/app/GeoLite2-City.mmdb:ro
   ```

4. **Restart the backend container**:
   ```bash
   docker-compose restart backend
   ```

### For Local Development

1. **Copy to backend directory**:
   ```bash
   cp GeoLite2-City.mmdb /path/to/photo-restoration-webpage/backend/GeoLite2-City.mmdb
   ```

2. **Or set custom path** via environment variable:
   ```bash
   # In backend/.env
   GEOIP_DB_PATH=/path/to/GeoLite2-City.mmdb
   ```

3. **Restart the development server**:
   ```bash
   # In backend directory
   source venv/bin/activate
   uvicorn app.main:app --reload
   ```

## Step 5: Verify Installation

### Check Startup Logs

When the application starts, check the logs:

**With GeoIP database found:**
```
2025-12-30 12:00:00 - app.utils.session_metadata - DEBUG - ✓ Found database at: /app/GeoLite2-City.mmdb
```

**Without GeoIP database (expected warning):**
```
2025-12-30 12:00:00 - app.utils.session_metadata - WARNING - GeoIP2 database not found - IP geolocation disabled. Session location will show as 'Unknown location'. To enable: Download GeoLite2-City.mmdb from MaxMind and place at /app/GeoLite2-City.mmdb See docs/GEOIP_SETUP.md for instructions.
```

### Enable DEBUG Mode for Detailed Logs

To see detailed GeoIP lookup information, enable DEBUG mode:

1. **Edit your configuration** (production.json or .env):
   ```json
   {
     "application": {
       "debug": true
     }
   }
   ```

   Or in `.env`:
   ```
   DEBUG=true
   ```

2. **Restart the application**:
   ```bash
   docker-compose restart backend
   ```

3. **Perform a login** and check logs:
   ```bash
   docker-compose logs -f backend | grep -i geoip
   ```

   You should see detailed output like:
   ```
   DEBUG - Attempting to locate IP address: 192.168.1.100
   DEBUG - Searching for GeoIP2 database in 5 locations...
   DEBUG -   Checking: /app/GeoLite2-City.mmdb
   DEBUG -   ✓ Found database at: /app/GeoLite2-City.mmdb
   DEBUG - Opening GeoIP2 database: /app/GeoLite2-City.mmdb
   DEBUG - Successfully resolved IP 8.8.8.8 to: Mountain View, CA, United States
   DEBUG - Session metadata for admin: browser=Chrome 120.0.0.0, device=Desktop, ip=8.8.8.8, location=Mountain View, CA, United States
   ```

### Test with a Login

1. Log in to the application
2. Navigate to Profile → Active Sessions
3. Check if your current session shows a location instead of "📍Unknown location"

**Expected results:**
- **With GeoIP:** "📍San Francisco, CA, United States" (or your actual location)
- **Without GeoIP:** "📍Unknown location"

## Troubleshooting

### Issue: "GeoIP2 database not found" warning

**Cause:** The database file is not in a location the application can find.

**Solutions:**

1. **Verify file exists** at the mounted location:
   ```bash
   # For Docker:
   docker exec photo-restoration-backend ls -la /app/GeoLite2-City.mmdb

   # Should show:
   # -rw-r--r-- 1 root root 71234567 Dec 30 12:00 /app/GeoLite2-City.mmdb
   ```

2. **Check volume mount** in docker-compose.yml:
   ```bash
   docker-compose config | grep -A 5 volumes
   ```

3. **Verify host file permissions**:
   ```bash
   ls -la /opt/geoip/GeoLite2-City.mmdb
   # Should be readable (644)
   ```

### Issue: "IP address not found in GeoIP2 database"

**Cause:** The IP address is private/local (127.0.0.1, 192.168.x.x, etc.) or not in the database.

**Expected behavior:** This is normal for:
- Local development (127.0.0.1)
- Private network IPs (192.168.x.x, 10.x.x.x)
- Some cloud/hosting provider IPs

**Solution:** Test with a public login from a real external IP address.

### Issue: Location always shows "Unknown location"

**Debugging steps:**

1. **Enable DEBUG mode** (see above)
2. **Check logs** during login:
   ```bash
   docker-compose logs -f backend | grep -i location
   ```
3. **Verify database** is being loaded:
   ```bash
   docker-compose logs backend | grep -i "Found database"
   ```

### Issue: "geoip2 library not installed" warning

**Cause:** The geoip2 Python package is missing.

**Solution:** Reinstall dependencies:
```bash
# For Docker: Rebuild the image
docker-compose build backend

# For local development:
pip install -r requirements.txt
```

## Database Updates

MaxMind updates the GeoLite2 databases weekly. To keep your database current:

### Manual Update

```bash
# Download new version from MaxMind
# Extract and replace the old file
sudo cp GeoLite2-City.mmdb /opt/geoip/GeoLite2-City.mmdb

# Restart backend to reload database
docker-compose restart backend
```

### Automated Updates (with geoipupdate)

Set up a cron job to update automatically:

```bash
# Create update script
sudo nano /usr/local/bin/update-geoip.sh
```

```bash
#!/bin/bash
# Update GeoIP database and restart backend

geoipupdate
cp /usr/share/GeoIP/GeoLite2-City.mmdb /opt/geoip/GeoLite2-City.mmdb
cd /path/to/photo-restoration-webpage
docker-compose restart backend
```

```bash
# Make executable
sudo chmod +x /usr/local/bin/update-geoip.sh

# Add to crontab (weekly on Sunday at 3am)
sudo crontab -e
# Add: 0 3 * * 0 /usr/local/bin/update-geoip.sh
```

## Database Search Paths

The application searches for the database in these locations (in order):

1. **Custom path** from `GEOIP_DB_PATH` environment variable
2. **Docker location:** `/app/GeoLite2-City.mmdb` (recommended for containers)
3. **System-wide:** `/usr/share/GeoIP/GeoLite2-City.mmdb` (Linux)
4. **Alternative system:** `/var/lib/GeoIP/GeoLite2-City.mmdb`
5. **Current directory:** `GeoLite2-City.mmdb`
6. **Development:** `backend/GeoLite2-City.mmdb`

You can specify a custom location using the `GEOIP_DB_PATH` environment variable in `.env`:

```bash
GEOIP_DB_PATH=/custom/path/to/GeoLite2-City.mmdb
```

## Licensing and Terms

**Important:** The GeoLite2 database is provided by MaxMind under the Creative Commons Attribution-ShareAlike 4.0 International License.

- **Free to use** for this application
- **Cannot be redistributed** in git repositories or Docker images
- **Requires attribution** in documentation
- **Terms:** https://www.maxmind.com/en/geolite2/eula

**Attribution:**
This product includes GeoLite2 data created by MaxMind, available from https://www.maxmind.com

## Privacy Considerations

**What is logged:**
- IP addresses are stored in the database for session management
- Geographic locations (city, state, country) are derived from IP addresses
- No personally identifiable information beyond IP is collected

**User privacy:**
- Location data is approximate (city-level, not exact coordinates)
- Users can see which sessions/locations are associated with their account
- Users can terminate sessions remotely

**Data retention:**
- Sessions are automatically cleaned up after 24 hours (configurable)
- Old session data including IP addresses are deleted

## Performance Impact

**Database size:** ~70MB
**Lookup speed:** <1ms per lookup (in-memory after first read)
**Memory impact:** Minimal (database is read from disk as needed)
**Network impact:** None (all lookups are local)

## Support

For issues or questions:
- Check application logs with DEBUG=true
- Review this documentation
- Check MaxMind documentation: https://dev.maxmind.com/geoip/docs
- Open an issue in the project repository

## References

- MaxMind GeoLite2: https://dev.maxmind.com/geoip/geolite2-free-geolocation-data
- geoip2 Python library: https://github.com/maxmind/GeoIP2-python
- Database formats: https://dev.maxmind.com/geoip/docs/databases
