import asyncio
import threading
import time
import unittest
from unittest.mock import MagicMock, AsyncMock, patch
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from python_client.network.connection import Connection

class TestThreadSafeWrite(unittest.TestCase):
    def setUp(self):
        self.loop = None
        self.thread = None
        self.connection = Connection()
        self.connected_event = threading.Event()
        
    def tearDown(self):
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)
        if self.thread:
            self.thread.join(timeout=2)
            
    def test_write_from_another_thread(self):
        """Test calling write() from a thread different than the event loop"""
        
        # Mock asyncio.open_connection
        mock_reader = AsyncMock()
        mock_writer = MagicMock()
        mock_writer.drain = AsyncMock()
        mock_writer.close = MagicMock()
        mock_writer.wait_closed = AsyncMock()
        
        async def mock_open_connection(*args, **kwargs):
            return mock_reader, mock_writer
            
        # Configure mock_reader to sleep to keep connection open
        async def mock_read(*args, **kwargs):
            await asyncio.sleep(10)
            return b''
        mock_reader.read.side_effect = mock_read
            
        # Function to run in background thread
        def run_loop():
            print("Thread: Starting loop")
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            
            # Patch open_connection in this loop
            with patch('asyncio.open_connection', side_effect=mock_open_connection):
                # Connect
                print("Thread: Connecting...")
                self.loop.run_until_complete(self.connection.connect('127.0.0.1', 5900))
                print("Thread: Connected, setting event")
                self.connected_event.set()
                
                # Run forever
                print("Thread: Running forever")
                self.loop.run_forever()
                
                # Cleanup
                print("Thread: Cleaning up")
                self.loop.run_until_complete(self.connection.disconnect())
                self.loop.close()

        # Start background thread
        self.thread = threading.Thread(target=run_loop)
        self.thread.start()
        
        # Wait for connection
        self.assertTrue(self.connected_event.wait(timeout=5), "Connection timed out")
        
        # Call write from MAIN thread
        test_data = b'\x01\x02\x03'
        try:
            self.connection.write(test_data)
        except Exception as e:
            self.fail(f"write() raised exception: {e}")
            
        # Give some time for the threadsafe callback to execute
        time.sleep(0.5)
        
        # Verify writer.write was called
        mock_writer.write.assert_called_with(test_data)
        print("Success: write() called from main thread was executed in background loop")

if __name__ == '__main__':
    unittest.main()
