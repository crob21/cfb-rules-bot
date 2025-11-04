# Timer Persistence Testing Guide

## How to Verify Timer Persistence Works

The timer persistence feature uses Discord messages to store timer state, allowing it to survive deployments and restarts.

## Testing Procedure

### Step 1: Start a Timer
1. In Discord, run: `/advance hours:2` (or any custom duration)
2. Check the logs for:
   ```
   💾 Timer state saved to file
   💾 Created timer state message in Discord
   ```
3. **Verify in Discord**: Look at the channel where you started the timer. You should see a message from Harry containing JSON (it will be sent silently, so no notifications)

### Step 2: Check State Message
1. Scroll up in the channel where you started the timer
2. Find the most recent message from Harry (the bot)
3. Look for a message with JSON code block containing:
   ```json
   {
     "channel_id": 123456789,
     "start_time": "2025-11-04T...",
     "end_time": "2025-11-04T...",
     "duration_hours": 2,
     "is_active": true,
     "notifications_sent": {...}
   }
   ```
4. This is your timer state stored in Discord!

### Step 3: Trigger a Deployment/Restart
1. **Option A - Manual Restart**: In Render/Railway dashboard, click "Restart" service
2. **Option B - Deploy**: Push a commit to trigger auto-deployment
3. **Option C - Wait**: Just wait for the next deployment

### Step 4: Verify Timer Restored
After restart, check the logs for:
```
📂 Found timer state message in #channel-name
📂 Loaded timer state from Discord
✅ Restored timer for #channel-name
⏰ Time remaining: X.X hours
⏰ End time: 2025-11-04T...
```

You should also see a message in Discord:
```
⏰ Timer Restored!
Right then! I've restored the advance countdown after a restart.
Time Remaining: Xh Xm
Ends At: XX:XX PM
```

### Step 5: Verify Timer Still Works
1. Run `/time_status` - should show the restored timer
2. Wait for notifications - they should still fire at the correct times
3. Timer should complete normally

## What to Look For

### ✅ Success Indicators:
- Log shows "💾 Created timer state message in Discord" when starting timer
- Log shows "📂 Found timer state message" on restart
- Log shows "✅ Restored timer" on restart
- Timer notification appears in Discord channel after restart
- `/time_status` shows correct remaining time after restart
- Timer continues counting down correctly

### ❌ Failure Indicators:
- Log shows "📂 No saved timer state found" after restart (when timer should exist)
- Log shows "❌ Failed to save timer state to Discord"
- Timer doesn't restore after restart
- Timer state message not visible in Discord channel

## Troubleshooting

### Timer Not Restoring?
1. Check logs for "📂 Found timer state message" - if missing, state wasn't saved
2. Check if state message exists in Discord channel
3. Verify bot has permission to read message history in the channel
4. Check logs for any errors during save/load

### State Message Not Found?
- Bot searches last 100 messages in each channel
- If state message is older than 100 messages, it won't be found
- Solution: State is saved/updated whenever timer changes, so this shouldn't happen

### Want to See Current State?
- Look for the JSON message in the channel where timer was started
- Run `/time_status` to see current timer status
- Check logs for "💾 Timer state saved" messages

## Log Messages Reference

### Saving State:
- `💾 Timer state saved to file` - Saved to local file (local dev)
- `💾 Created timer state message in Discord` - **NEW state message created**
- `💾 Updated timer state message in Discord` - **Existing state message updated**

### Loading State:
- `📂 Found timer state message in #channel-name` - **Found state in Discord**
- `📂 Loaded timer state from Discord` - **Successfully loaded from Discord**
- `📂 Loaded timer state from environment variable` - Loaded from env var (fallback)
- `📂 Loaded timer state from file` - Loaded from file (local dev fallback)
- `📂 No saved timer state found` - No state found anywhere

### Restoration:
- `✅ Restored timer for #channel-name` - **Timer successfully restored**
- `⏰ Time remaining: X.X hours` - Shows remaining time
- `⏰ End time: ...` - Shows when timer ends

## Quick Test

**Fastest way to test:**

1. Start timer: `/advance hours:1`
2. Check Discord channel for JSON message
3. Restart bot (Render dashboard → Restart)
4. Check logs for "✅ Restored timer"
5. Check Discord for "Timer Restored!" message
6. Run `/time_status` to verify

If all steps pass, persistence is working! 🎉

