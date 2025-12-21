import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Add root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from librarian_agent.agent import LibrarianAgent

class TestLibrarianAgent(unittest.TestCase):
    def setUp(self):
        self.env_patcher = patch.dict(os.environ, {
            "LLM_API_KEY": "test_key",
            "LLM_MODEL": "test_model"
        })
        self.env_patcher.start()

    def tearDown(self):
        self.env_patcher.stop()

    @patch("librarian_agent.agent.LLM")
    @patch("librarian_agent.agent.Agent")
    def test_initialization(self, mock_agent_cls, mock_llm_cls):
        agent = LibrarianAgent(mcp_url="http://test-url")
        
        mock_llm_cls.assert_called_once()
        mock_agent_cls.assert_called_once()
        
        # Check MCP config
        call_args = mock_agent_cls.call_args
        mcp_config = call_args.kwargs.get("mcp_config")
        self.assertIsNotNone(mcp_config)
        self.assertEqual(mcp_config["mcpServers"]["vhl-library"]["url"], "http://test-url")

    @patch("librarian_agent.agent.LLM")
    @patch("librarian_agent.agent.Agent")
    @patch("librarian_agent.agent.Conversation")
    def test_process_scud(self, mock_conversation_cls, mock_agent_cls, mock_llm_cls):
        agent = LibrarianAgent()
        
        # Mock SCUD file existence
        with patch("os.path.exists", return_value=True):
            agent.process_scud("test_scud.md")
            
        mock_conversation_cls.assert_called_once()
        mock_conversation_instance = mock_conversation_cls.return_value
        
        # Verify message sent
        mock_conversation_instance.send_message.assert_called_once()
        args, _ = mock_conversation_instance.send_message.call_args
        self.assertIn("test_scud.md", args[0])
        
        # Verify run called
        mock_conversation_instance.run.assert_called_once()

    def test_missing_api_key(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                LibrarianAgent()

if __name__ == "__main__":
    unittest.main()
