import unittest
from fastapi.testclient import TestClient
from server.main import app
from core.app_state import TaskStatus
from core.events import AppEvent, EventKind

class TestServerE2E(unittest.TestCase):
    def test_e2e_workflow(self):
        """Tests full E2E lifecycle: WebSockets connect, task enqueue, and stats update broadcasts."""
        with TestClient(app) as client:
            token = app.state.server.startup_token
            ws_url = f"/api/ws?token={token}"
            
            # 1. Establish WebSocket connection
            with client.websocket_connect(ws_url) as websocket:
                # 2. Add a video download task to queue
                response = client.post(
                    "/api/queue",
                    json={
                        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                        "settings": {
                            "video_profile": "Full HD (1080p)",
                            "video_container": "mp4",
                            "metadata_flag": True
                        }
                    },
                    headers={"X-Baynuman-Token": token}
                )
                
                self.assertEqual(response.status_code, 201)
                self.assertTrue(response.json()["success"])
                self.assertEqual(response.json()["added_count"], 1)

                # 3. Intercept WebSocket broadcast: task_added event
                event_data = websocket.receive_json()
                self.assertEqual(event_data["type"], "task_added")
                task = event_data["task"]
                self.assertEqual(task["url"], "https://www.youtube.com/watch?v=dQw4w9WgXcQ")
                self.assertEqual(task["preset"], "Full HD (1080p)")
                
                # Grab the generated task ID
                task_id = task["task_id"]

                # 4. Simulate a mock download progress event from the downloader thread
                server = app.state.server
                emitter = server.ws_manager
                
                # Emit percent_complete event
                server.controller.on_task_added = None  # mute controller hook during emission
                ws_msg_percent = {
                    "type": "percent_complete",
                    "task_id": task_id,
                    "payload": 42.5
                }
                
                # Broadcast directly using WebSocket ConnectionManager
                client.post(  # use health to yield thread control briefly if needed
                    "/health"
                )
                
                # Trigger broadcast of progress stats
                import asyncio
                asyncio.run_coroutine_threadsafe(
                    emitter.broadcast(ws_msg_percent),
                    server.loop
                )
                
                # Receive the percent complete broadcast on the websocket client
                prog_event = websocket.receive_json()
                self.assertEqual(prog_event["type"], "percent_complete")
                self.assertEqual(prog_event["task_id"], task_id)
                self.assertEqual(prog_event["payload"], 42.5)

                # 5. Clean up: Delete task from queue
                delete_res = client.delete(
                    f"/api/queue/{task_id}",
                    headers={"X-Baynuman-Token": token}
                )
                self.assertEqual(delete_res.status_code, 200)
                self.assertTrue(delete_res.json()["success"])

                # Receive task_removed broadcast
                remove_event = websocket.receive_json()
                self.assertEqual(remove_event["type"], "task_removed")
                self.assertEqual(remove_event["task_id"], task_id)
